import io, csv
from models import db, Case, Deadline, Event
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from ics import Calendar, Event as CalEvent

def export_csv():
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["Case ID","Title","Number","Status","Deadlines","Events"])
    for c in db.session.execute(db.select(Case)).scalars().all():
        dls = db.session.execute(db.select(Deadline).filter_by(case_id=c.id)).scalars().all()
        evs = db.session.execute(db.select(Event).filter_by(case_id=c.id)).scalars().all()
        w.writerow([c.id, c.title, c.number or "", c.status, len(dls), len(evs)])
    bio = io.BytesIO(out.getvalue().encode("utf-8"))
    bio.seek(0); return bio

def export_pdf():
    bio = io.BytesIO()
    c = canvas.Canvas(bio, pagesize=A4)
    width, height = A4
    y = height - 50
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "CaseFlow — Summary Report"); y -= 30
    c.setFont("Helvetica", 10)
    for case in db.session.execute(db.select(Case)).scalars().all():
        c.drawString(50, y, f"[{case.id}] {case.title} — {case.number or '-'} — {case.status}")
        y -= 15
        if y < 80: c.showPage(); y = height - 50
    c.save()
    bio.seek(0); return bio

def export_ics():
    cal = Calendar()
    for d in db.session.execute(db.select(Deadline)).scalars().all():
        e = CalEvent()
        e.name = d.title or "Deadline"
        e.begin = d.due_on
        e.make_all_day()
        cal.events.add(e)
    bio = io.BytesIO(str(cal).encode("utf-8"))
    bio.seek(0); return bio
