import os, datetime as dt
from apscheduler.schedulers.background import BackgroundScheduler
from flask import current_app
from models import db, User, Case, Deadline, Event
from google_integration import GoogleClient

_scheduler = None

def scheduler_init(app):
    global _scheduler
    if _scheduler:
        return
    _scheduler = BackgroundScheduler(daemon=True, timezone="UTC")
    _scheduler.start()

def _sync_all():
    with current_app.app_context():
        interval = int(os.getenv("SYNC_INTERVAL_MINUTES","30"))
        now = dt.datetime.utcnow()
        for user in db.session.execute(db.select(User)).scalars().all():
            if not user.google_token: continue
            client = GoogleClient.from_user(user)
            # Minimal polling: use default query
            client.pull_gmail(query=os.getenv("DEFAULT_GMAIL_QUERY",""))
            client.pull_drive()
        # Here you can implement deadline reminders (e.g., email)

def schedule_jobs(app):
    _scheduler.add_job(_sync_all, "interval", minutes=int(os.getenv("SYNC_INTERVAL_MINUTES","30")), id="sync_all", replace_existing=True)
