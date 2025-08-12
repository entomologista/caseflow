import os, datetime as dt
from apscheduler.schedulers.background import BackgroundScheduler
from models import db, User
from google_integration import GoogleClient

_scheduler = None

def scheduler_init(app):
    global _scheduler
    if _scheduler:
        return
    _scheduler = BackgroundScheduler(daemon=True, timezone="UTC")
    _scheduler.start()

def _sync_all(app):
    with app.app_context():
        for user in db.session.execute(db.select(User)).scalars().all():
            if not user.google_token: 
                continue
            client = GoogleClient.from_user(user)
            client.pull_gmail(query=os.getenv("DEFAULT_GMAIL_QUERY",""))
            client.pull_drive()

def schedule_jobs(app):
    _scheduler.add_job(lambda: _sync_all(app), "interval", minutes=int(os.getenv("SYNC_INTERVAL_MINUTES","30")), id="sync_all", replace_existing=True)
