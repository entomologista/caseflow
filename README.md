# CaseFlow — Process & Complaint Tracker (MVP)

A small Flask-based web app to track administrative and judicial processes (incl. workplace-violence complaints),
sync with Gmail and Google Drive (Docs/Sheets), generate reports, stats, and send deadline alerts.

## Features (MVP)
- Google OAuth sign-in (placeholder): authenticate with your Google account.
- Gmail sync:
  - Pull emails matching configurable queries (labels/subjects/senders like CGU, MPT, CEE, CPPCAM, Ouvidoria, SEI, Fala.BR, PJe etc.).
  - Parse NUP/SEI numbers and hearing/appeal deadlines via regex rules.
- Google Drive sync:
  - Index Docs/Sheets and link them to cases.
- Cases module:
  - Parties, case numbers (NUP/SEI/PJe), deadlines, events, tasks, notes, tags.
- Dashboard:
  - Open cases, upcoming deadlines, status heatmap, volume by organ, and simple trends.
- Reports:
  - Export CSV/PDF summaries; generate .ics calendar for deadlines.
- Alerts:
  - Email alerts (SMTP) and on-screen notifications.
- Jobs:
  - Background scheduler (APScheduler) to poll Gmail/Drive at intervals.

> This is a scaffold to get you running fast. You will need to supply Google OAuth credentials
and enable APIs in a Google Cloud project (Gmail API, Drive API, People API optional).

## Quickstart
1. **Python 3.10+** recommended. Create a virtualenv and install deps:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Environment**: copy `.env.example` to `.env` and fill values.
3. **DB Init**:
   ```bash
   flask --app app.py db_init
   ```
4. **Run**:
   ```bash
   flask --app app.py run --debug
   ```
   Visit http://127.0.0.1:5000

## Notes on Google Setup
- Create a Google Cloud project, enable *Gmail API* and *Drive API*.
- Create OAuth 2.0 credentials (Web application) and set Authorized redirect URI to:
  - `http://localhost:5000/oauth2/callback`
- Download the JSON credentials and paste values into `.env`.
- For push notifications (optional), configure Gmail watch with Pub/Sub; otherwise the scheduler will poll.

## Next Steps / Ideas
- Fine-grained role-based access control.
- Full-text search across synced emails and Docs (e.g., sqlite FTS5 / Postgres + pgvector for semantic search).
- Court systems connectors (when official APIs exist) and Fala.BR/SEI inbox parsers.
- Multi-tenant, audit log, immutable evidence vault, hash stamping.
- PWA installable on iPhone with mobile-friendly UI.

## Security
- Store secrets only in environment variables.
- Use HTTPS in production (reverse proxy like Caddy/Traefik/nginx). Set `SESSION_COOKIE_SECURE=1`.
- Consider Postgres in production and proper OAuth session storage.
