from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import func
import datetime as dt

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=False)
    name = db.Column(db.String, default="")
    google_token = db.Column(db.Text, default=None)

class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)

class Case(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    number = db.Column(db.String, index=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=True)
    status = db.Column(db.String, default="open")
    tags = db.Column(db.String, default="")
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

    @staticmethod
    def get_or_create_by_refs(db, refs, default_title="Case"):
        number = refs[0] if refs else None
        if number:
            existing = db.session.execute(db.select(Case).filter_by(number=number)).scalar_one_or_none()
            if existing:
                return existing
        c = Case(title=default_title, number=number)
        db.session.add(c); db.session.flush()
        return c

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'), nullable=False)
    kind = db.Column(db.String)
    title = db.Column(db.String, default="")
    occurred_on = db.Column(db.DateTime, default=dt.datetime.utcnow)
    raw_id = db.Column(db.String)
    source = db.Column(db.String, default="manual")

class Deadline(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'), nullable=False)
    title = db.Column(db.String, default="")
    due_on = db.Column(db.DateTime, nullable=False)
    source = db.Column(db.String, default="manual")
    done = db.Column(db.Boolean, default=False)

def init_db():
    db.drop_all()
    db.create_all()
    for name in ["CGU","MPT","CEE","CPPCAM","Ouvidoria Embrapa","Corregedoria","Justiça do Trabalho","SEI","Fala.BR"]:
        db.session.add(Organization(name=name))
    db.session.commit()
