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
    
def render_report_text():
    from datetime import datetime
    lines = []
    lines.append("Relatório CaseFlow")
    lines.append(f"Gerado em: {datetime.utcnow().strftime('%d/%m/%Y %H:%M UTC')}")
    lines.append("")

    # Resumo por órgão
    org_counts = db.session.execute(
        db.select(Case.organization_id, db.func.count(Case.id)).group_by(Case.organization_id)
    ).all()
    lines.append("Casos por órgão:")
    from models import Organization
    org_map = {o.id: o.name for o in db.session.execute(db.select(Organization)).scalars().all()}
    for org_id, cnt in org_counts:
        name = org_map.get(org_id, "(não classificado)")
        lines.append(f"- {name}: {cnt}")
    lines.append("")

    # Próximos prazos (30 dias)
    from datetime import timedelta
    upcoming = db.session.execute(
        db.select(Deadline).where(Deadline.due_on <= datetime.utcnow() + timedelta(days=30)).order_by(Deadline.due_on.asc())
    ).scalars().all()
    lines.append("Próximos prazos (30 dias):")
    if not upcoming:
        lines.append("- (nenhum prazo encontrado)")
    else:
        for d in upcoming:
            lines.append(f"- {d.due_on.strftime('%d/%m/%Y')} — {d.title}")
    lines.append("")

    # Totais
    total_cases = db.session.execute(db.select(db.func.count(Case.id))).scalar_one()
    total_events = db.session.execute(db.select(db.func.count(Event.id))).scalar_one()
    total_deadlines = db.session.execute(db.select(db.func.count(Deadline.id))).scalar_one()
    lines.append(f"Totais: casos={total_cases}, eventos={total_events}, prazos={total_deadlines}")

    return "\n".join(lines)
