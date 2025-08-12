import os, json, base64, email, re, datetime as dt
from functools import wraps
from flask import redirect, url_for, session, flash
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

class GoogleClient:
    def __init__(self, creds: Credentials):
        self.creds = creds
        self.gmail = build('gmail','v1', credentials=creds)
        self.drive = build('drive','v3', credentials=creds)
        self.docs = build('docs','v1', credentials=creds)
        self.docs = build('docs','v1', credentials=creds)

    @classmethod
    def from_env(cls):
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
        scopes = os.getenv("GOOGLE_SCOPES","").split()
        flow = Flow.from_client_config(
            {"web": {"client_id": client_id, "project_id":"caseflow",
                     "auth_uri":"https://accounts.google.com/o/oauth2/auth",
                     "token_uri":"https://oauth2.googleapis.com/token",
                     "client_secret": client_secret,
                     "redirect_uris":[redirect_uri]}},
            scopes=scopes
        )
        flow.redirect_uri = redirect_uri
        obj = object.__new__(cls)
        obj._flow = flow
        obj.creds = None
        obj.gmail = None
        obj.drive = None
        return obj

    def build_auth_url(self):
        auth_url, state = self._flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        return auth_url, state

    def fetch_token(self, code, state=None):
        if state and session.get("oauth_state") != state:
            raise ValueError("Invalid OAuth state")
        self._flow.fetch_token(code=code)
        self.creds = self._flow.credentials

    def serialize_token(self):
        return self.creds.to_json()

    @classmethod
    def from_user(cls, user):
        creds = Credentials.from_authorized_user_info(json.loads(user.google_token))
        return cls(creds)

    def pull_gmail(self, query=""):
        msgs = self.gmail.users().messages().list(userId='me', q=query, maxResults=50).execute().get('messages',[])
        out = []
        for m in msgs:
            msg = self.gmail.users().messages().get(userId='me', id=m['id'], format='full').execute()
            headers = {h['name']:h['value'] for h in msg.get('payload',{}).get('headers',[])}
            payload_parts = msg.get('payload',{}).get('parts',[]) or []
            text = ""
            for p in payload_parts:
                if p.get('mimeType') in ('text/plain','text/html'):
                    data = p.get('body',{}).get('data')
                    if data:
                        text += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            out.append({
                "id": msg['id'],
                "internalDate": msg.get('internalDate'),
                "subject": headers.get('Subject',''),
                "from": headers.get('From',''),
                "snippet": msg.get('snippet',''),
                "payload_text": text
            })
        return out

    def pull_drive(self):
        results = self.drive.files().list(
            pageSize=50, fields="files(id, name, mimeType, modifiedTime)",
            q="mimeType='application/vnd.google-apps.document' or mimeType='application/vnd.google-apps.spreadsheet'"
        ).execute()
        return results.get('files', [])

    # Google Docs: cria um documento novo ou atualiza um existente
    def create_or_update_doc(self, title: str, text_body: str, doc_id: str = None):
        if doc_id:
            # Apaga conteúdo (exceto o índice 0) e reinsere o texto
            self.docs.documents().batchUpdate(
                documentId=doc_id,
                body={
                    "requests": [
                        {"deleteContentRange": {"range": {"startIndex": 1, "endIndex": 1000000}}},
                        {"insertText": {"location": {"index": 1}, "text": text_body}}
                    ]
                }
            ).execute()
            return doc_id
        else:
            # Cria documento novo e insere o texto
            doc = self.docs.documents().create(body={"title": title}).execute()
            new_id = doc.get("documentId")
            self.docs.documents().batchUpdate(
                documentId=new_id,
                body={"requests": [{"insertText": {"location": {"index": 1}, "text": text_body}}]}
            ).execute()
            return new_id

def require_google(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        from flask_login import current_user
        if not getattr(current_user, "google_token", None):
            flash("Connect your Google account first.", "warning")
            return redirect(url_for("connect_google"))
        return fn(*args, **kwargs)
    return wrapper

    # Google Docs: cria um documento novo (ou atualiza se doc_id for dado)
    def create_or_update_doc(self, title: str, text_body: str, doc_id: str = None):
        if doc_id:
            # Limpa e reinsere o conteúdo
            self.docs.documents().batchUpdate(
                documentId=doc_id,
                body={
                    "requests": [
                        {"deleteContentRange": {"range": {"startIndex": 1, "endIndex": 1_000_000}}},
                        {"insertText": {"location": {"index": 1}, "text": text_body}}
                    ]
                }
            ).execute()
            return doc_id
        else:
            # Cria novo documento e insere conteúdo
            doc = self.docs.documents().create(body={"title": title}).execute()
            new_id = doc.get("documentId")
            self.docs.documents().batchUpdate(
                documentId=new_id,
                body={"requests": [{"insertText": {"location": {"index": 1}, "text": text_body}}]}
            ).execute()
            # Opcional: mover/compartilhar via Drive API se quiser
            return new_id
