# CaseFlow — Guia simples (sem programação)

Você quer usar no **navegador**, sem instalar nada no seu computador. Há duas opções bem simples.

---

## Opção A) Render (estável e gratuito no plano básico)

**O que você precisa:** uma conta no GitHub e no Render (ambas gratuitas).

1. **Crie uma conta no GitHub** (github.com) e no **Render** (render.com).
2. No GitHub, clique **New repository** e suba esta pasta (ou faça upload do ZIP e depois "Add file > Upload files").
3. No Render, clique **New > Blueprint** e selecione seu repositório com o arquivo `render.yaml`.
4. Render vai mostrar as variáveis. Preencha:
   - `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET`: crie no **Google Cloud Console** (consent screen + OAuth Client "Web application").
   - `GOOGLE_REDIRECT_URI`: use a URL do seu app no Render + `/oauth2/callback` (ex.: `https://caseflow-xxxx.onrender.com/oauth2/callback`). Você vê a URL após o primeiro deploy; depois volte no Google e ajuste se necessário.
5. Clique **Deploy**. Após alguns minutos, seu sistema terá uma URL pública (ex.: `https://caseflow-xxxx.onrender.com`).

**Conectar ao Google (uma vez):**
- Acesse sua URL, clique **Entrar** (e-mail temporário) e depois **Conectar Google**.
- Autorize Gmail e Drive (somente leitura).
- Pronto: o sistema vai listar casos, eventos e prazos. Você pode **Exportar CSV/PDF/ICS** e ver **Dashboard**.

> Dica: para o botão “Conectar Google” funcionar, a **mesma** URL pública precisa estar cadastrada como Redirect URI no Google Cloud.

---

## Opção B) Replit (muito simples, rápido para testar)

1. Crie uma conta em **replit.com**.
2. Clique **Create Repl > Import from Zip** e envie o arquivo ZIP.
3. No painel, vá em **Secrets (Environment variables)** e preencha:
   - `FLASK_SECRET_KEY` (qualquer texto)
   - `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
   - `GOOGLE_REDIRECT_URI` (será a URL do seu Repl + `/oauth2/callback`)
   - `GOOGLE_SCOPES` (use o padrão do `.env.example`)
4. Clique **Run**. Abra a URL pública que o Replit gera. Siga o fluxo “Entrar” + “Conectar Google”.

---

## Como criar as credenciais do Google (uma vez)

1. Acesse **console.cloud.google.com** e crie um projeto (ex.: “CaseFlow do Cherre”).
2. Em **APIs & Services > Enabled APIs & services > + ENABLE APIS**, ative **Gmail API** e **Google Drive API**.
3. Em **OAuth consent screen**, selecione “External”, preencha nome do app e e-mail.
4. Em **Credentials > Create Credentials > OAuth client ID > Web application**:
   - **Authorized redirect URI:** cole a **URL pública** do seu app + `/oauth2/callback`.
5. Copie **Client ID** e **Client Secret** para o Render/Replit.

---

## Usando no celular (iPhone)
- Abra sua URL e **adicione à Tela de Início** (share > Add to Home Screen). O app vira um atalho tipo PWA.
- Para receber prazos no Calendário, exporte o `.ics` e importe no Apple Calendar.

---

## Observações importantes
- Este é um **MVP**. Ele já busca e-mails/Docs e cria prazos simples. Podemos depois refinar:
  - Regras específicas para NUP/SEI/Fala.BR/SEI/CGU/CPPCAM/CEE.
  - Kanban de status, etiquetas por órgão, filtros e relatórios avançados.
  - Usuários e permissões.
- **Privacidade:** o app só lê o que você autorizar e apenas na sua conta. Hospede em conta sua para controle total.
