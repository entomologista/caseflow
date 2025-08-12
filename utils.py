import re, datetime as dt

# Extract NUP/SEI/PJe like identifiers
REF_PATTERNS = [
    r'\bNUP\s*\d{5,}\S*\b',
    r'\bSEI\s*[\d\./-]+\b',
    r'\b\d{7}-\d{2}\.\d{4}\.5\.\d{2}\.\d{4}\b',  # CNJ pattern sample
    r'\b\d{8}/\d{4}-\d\b'
]

def parse_case_refs(text: str):
    refs = []
    for pat in REF_PATTERNS:
        refs.extend(re.findall(pat, text or "", flags=re.IGNORECASE))
    # Deduplicate while preserving order
    seen = set(); out = []
    for r in refs:
        if r not in seen:
            seen.add(r); out.append(r)
    return out

# Simple deadline inference from phrases like "prazo de 10 dias" or dates like "15/09/2025"
DATE_PAT = r'(\b\d{1,2}/\d{1,2}/\d{2,4}\b)'
PRAZO_PAT = r'prazo(?:\s+de)?\s+(\d{1,3})\s*(dia|dias)'
def infer_deadlines(text: str):
    out = []
    import re
    # Absolute dates
    for m in re.findall(DATE_PAT, text or "", flags=re.IGNORECASE):
        d,mn,y = re.split(r'[\/]', m)
        y = int(y); y = 2000+y if y<100 else y
        out.append({"title": "Prazo (data no texto)", "due_on": dt.datetime(int(y),int(mn),int(d))})
    # Relative
    rel = re.search(PRAZO_PAT, text or "", flags=re.IGNORECASE)
    if rel:
        days = int(rel.group(1))
        due = dt.datetime.utcnow() + dt.timedelta(days=days)
        out.append({"title": f"Prazo {days} dias", "due_on": due})
    return out
