import os, re, csv, io, datetime as dt
from flask import Flask, render_template, redirect, url_for, request, session, send_file, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from dotenv import load_dotenv
from models import db, User, Case, Event, Deadline, Organization, init_db
from scheduler import scheduler_init, schedule_jobs
from google_integration import GoogleClient, require_google
from reports import export_csv, export_pdf, export_ics
from utils import parse_case_refs, infer_deadlines

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///caseflow.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# --- Auto DB init & seed on first run ---
from sqlalchemy import inspect
with app.app_context():
    insp = inspect(db.engine)
    if not insp.get_table_names():
        init_db()

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.before_first_request
def _bootstrap():
    scheduler_init(app)
    schedule_jobs(app)

@app.route("/")
@login_required
def index():
    upcoming = Deadline.query.order_by(Deadline.due_on.asc()).limit(10).all()
    open_cases = Case.query.filter(Case.status.in_(["open","appeal","investigation"])).count()
    by_org = db.session.execute(db.select(Organization.name, db.func.count(Case.id))
                     .join(Case, Case.organization_id==Organization.id, isouter=True)
                     .group_by(Organization.name)).all()
    return render_template("dashboard.html", upcoming=upcoming, open_cases=open_cases, by_org=by_org)

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        user = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()
        if not user:
            user = User(email=email, name=email.split("@")[0])
            db.session.add(user); db.session.commit()
        login_user(user)
        return redirect(url_for("index"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))

# --- Google OAuth (simplified) ---
@app.route("/connect/google")
@login_required
def connect_google():
    client = GoogleClient.from_env()
    auth_url, state = client.build_auth_url()
    session["oauth_state"] = state
    return redirect(auth_url)

@app.route("/oauth2/callback")
def oauth2_callback():
    state = session.get("oauth_state")
    code = request.args.get("code")
    client = GoogleClient.from_env()
    client.fetch_token(code, state=state)
    user = current_user if current_user.is_authenticated else None
    if not user:
        flash("Please log in first.", "warning")
        return redirect(url_for("login"))
    user.google_token = client.serialize_token()
    db.session.commit()
    flash("Google connected.", "success")
    return redirect(url_for("index"))

# --- Sync endpoints ---
@app.route("/sync/gmail")
@login_required
@require_google
def sync_gmail():
    client = GoogleClient.from_user(current_user)
    pulled = client.pull_gmail(query=os.getenv("DEFAULT_GMAIL_QUERY",""))
    created = 0
    for msg in pulled:
        refs = parse_case_refs(msg.get("snippet","") + " " + msg.get("subject",""))
        case = Case.get_or_create_by_refs(db, refs, default_title=msg.get("subject","Email"))
        event = Event(case_id=case.id, kind="email", title=msg.get("subject","Email"),
                      occurred_on=dt.datetime.utcfromtimestamp(int(msg["internalDate"])/1000.0),
                      raw_id=msg["id"], source="gmail")
        db.session.add(event)
        for d in infer_deadlines(msg.get("payload_text","")):
            db.session.add(Deadline(case_id=case.id, title=d["title"], due_on=d["due_on"], source="parser"))
        created += 1
    db.session.commit()
    flash(f"Synced {created} email events.", "success")
    return redirect(url_for("index"))

@app.route("/sync/drive")
@login_required
@require_google
def sync_drive():
    client = GoogleClient.from_user(current_user)
    files = client.pull_drive()
    created = 0
    for f in files:
        refs = parse_case_refs(f.get("name",""))
        if not refs: continue
        case = Case.get_or_create_by_refs(db, refs, default_title=f.get("name","Doc"))
        event = Event(case_id=case.id, kind="doc", title=f.get("name","Doc"),
                      occurred_on=dt.datetime.utcnow(), raw_id=f["id"], source="drive")
        db.session.add(event); created += 1
    db.session.commit()
    flash(f"Indexed {created} Drive items.", "success")
    return redirect(url_for("index"))

# --- Cases ---
@app.route("/cases")
@login_required
def cases():
    q = request.args.get("q","")
    stmt = db.select(Case).order_by(Case.updated_at.desc())
    if q:
        stmt = stmt.filter(Case.title.ilike(f"%{q}%"))
    items = db.session.execute(stmt).scalars().all()
    return render_template("cases.html", items=items, q=q)

@app.route("/cases/<int:case_id>")
@login_required
def case_detail(case_id):
    case = db.session.get(Case, case_id)
    events = db.session.execute(db.select(Event).filter_by(case_id=case_id).order_by(Event.occurred_on.desc())).scalars().all()
    deadlines = db.session.execute(db.select(Deadline).filter_by(case_id=case_id).order_by(Deadline.due_on.asc())).scalars().all()
    return render_template("case_detail.html", case=case, events=events, deadlines=deadlines)

# --- Exports ---
@app.route("/export/csv")
@login_required
def export_cases_csv():
    out = export_csv()
    return send_file(out, mimetype="text/csv", as_attachment=True, download_name="cases.csv")

@app.route("/export/pdf")
@login_required
def export_cases_pdf():
    out = export_pdf()
    return send_file(out, mimetype="application/pdf", as_attachment=True, download_name="report.pdf")

@app.route("/export/ics")
@login_required
def export_deadlines_ics():
    out = export_ics()
    return send_file(out, mimetype="text/calendar", as_attachment=True, download_name="deadlines.ics")

if __name__ == "__main__":
    app.run(debug=True)
