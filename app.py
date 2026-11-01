"""DocImmune – AICTE Approval Validation Console (prototype, synthetic data).
Single-file app: engine (OCR, tamper scan, QR, memory, source verification, compliance) + UI.
All institutions, documents and registries below are SYNTHETIC and for demonstration only."""
import io, re, zlib, difflib, random, time, html, csv
from datetime import datetime, timedelta, timezone, date
import numpy as np
import streamlit as st
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageFilter

st.set_page_config(page_title="DocImmune · AICTE Validation", page_icon="🛡️", layout="wide", initial_sidebar_state="collapsed")

# =============================================================== THEME
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');
html, body, .stApp, h1, h2, h3, h4, p, label, li, button, input, textarea, [data-testid="stMarkdownContainer"]{font-family:'Manrope',sans-serif}
.stApp{background:radial-gradient(1200px 500px at 85% -10%,rgba(20,184,166,.10),transparent 60%),radial-gradient(900px 500px at -10% 10%,rgba(56,130,246,.10),transparent 60%),#06121A}
footer{visibility:hidden}
[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"],[data-testid="stExpandSidebarButton"]{display:none}
.block-container{padding:4.2rem 2.4rem 3rem;max-width:1240px}
@media(max-width:640px){.block-container{padding:4.2rem 1rem 3rem}.hero{padding:22px!important}.stp{flex-direction:column}}
h1,h2,h3{letter-spacing:-.02em;color:#E8F3F6}
.ph{margin-bottom:20px}.ph h1{font-size:1.85rem;font-weight:800;margin:0}.ph p{margin:4px 0 0;color:#8FA9B5}
.hero{background:linear-gradient(125deg,#0A2F45 0%,#0B5F78 55%,#0F766E 105%);border:1px solid #14485C;border-radius:22px;padding:30px 34px;margin-bottom:18px;position:relative;overflow:hidden}
.hero:after{content:"";position:absolute;right:-60px;top:-60px;width:260px;height:260px;border-radius:50%;background:radial-gradient(circle,rgba(45,212,191,.30),transparent 70%)}
.hero h1{margin:0;font-size:1.8rem;font-weight:800;color:#fff}.hero p{margin:6px 0 0;color:#CFE9EE;max-width:680px}
.card{background:linear-gradient(180deg,#0D2230,#0B1C28);border:1px solid #1A3A4B;border-radius:18px;padding:20px;box-shadow:0 6px 24px rgba(0,0,0,.28)}
.card h4{margin:0 0 12px;font-size:.98rem;font-weight:700;color:#E8F3F6}
.kpi{display:flex;gap:14px;align-items:center;background:linear-gradient(180deg,#0D2230,#0B1C28);border:1px solid #1A3A4B;border-radius:18px;padding:16px;box-shadow:0 6px 24px rgba(0,0,0,.28)}
.kpi .ic{width:44px;height:44px;border-radius:13px;display:grid;place-items:center;flex:none}
.kpi b{display:block;font-size:1.6rem;line-height:1.1;color:#fff}.kpi span{color:#8FA9B5;font-size:.82rem}
.row{display:flex;align-items:center;gap:12px;padding:11px 0;border-bottom:1px solid #16303F}.row:last-child{border:0}
.av{width:36px;height:36px;border-radius:11px;background:#123A4A;color:#5EEAD4;display:grid;place-items:center;font-weight:800;flex:none}
.row .n{font-weight:700;color:#E8F3F6}.row .m{font-size:.78rem;color:#8FA9B5}.row .r{margin-left:auto;text-align:right}
.pill{padding:3px 11px;border-radius:20px;font-weight:700;font-size:.72rem;display:inline-block;white-space:nowrap}
.tag{font-size:.66rem;background:#16303F;color:#8FA9B5;border-radius:6px;padding:1px 7px;margin-left:6px}
.tip{background:rgba(45,212,191,.10);border:1px solid rgba(45,212,191,.25);border-radius:12px;padding:11px 15px;color:#BFEDE7;margin:6px 0 14px;font-size:.9rem}
.warn{background:rgba(251,191,36,.10);border:1px solid rgba(251,191,36,.28);border-radius:12px;padding:11px 15px;color:#F6DFA0;margin:6px 0 14px;font-size:.88rem}
.stp{display:flex;gap:10px;margin-bottom:20px}.stp div{flex:1;background:#0D2230;border:1px solid #1A3A4B;border-radius:14px;padding:12px 14px;color:#6F8D9A;font-weight:600;display:flex;gap:10px;align-items:center}
.stp b{width:28px;height:28px;border-radius:50%;background:#16303F;color:#8FA9B5;display:grid;place-items:center;flex:none;font-size:.85rem}
.stp .on{border-color:#2DD4BF;color:#fff;box-shadow:0 0 0 1px rgba(45,212,191,.25),0 8px 24px rgba(20,184,166,.15)}.stp .on b{background:#14B8A6;color:#04141A}
.stp .done{color:#CFE9EE}.stp .done b{background:#34D399;color:#04141A}
.vc{border-radius:20px;padding:24px;text-align:center;border:1px solid rgba(255,255,255,.08)}
.vc h2{margin:8px 0 2px;color:#fff;font-weight:800;font-size:1.5rem}.vc p{margin:0;opacity:.95;color:#fff}
.f-ESC{background:linear-gradient(145deg,#7F1D2D,#C2415A)}.f-RECT{background:linear-gradient(145deg,#8A3B0B,#D9772B)}.f-MAN{background:linear-gradient(145deg,#7A5A0B,#C79A1F)}.f-READY{background:linear-gradient(145deg,#0B6B55,#1FA382)}
.ck{display:flex;gap:13px;align-items:flex-start;padding:12px 0;border-bottom:1px solid #16303F}.ck:last-child{border:0}
.ck .b{width:28px;height:28px;border-radius:9px;display:grid;place-items:center;flex:none;font-weight:800}
.ok{background:rgba(52,211,153,.15);color:#34D399}.bad{background:rgba(251,113,133,.15);color:#FB7185}.mid{background:rgba(251,191,36,.15);color:#FBBF24}
.ck .t{font-weight:700;color:#E8F3F6}.ck .d{color:#8FA9B5;font-size:.86rem}
.fc{border:1px solid #1A3A4B;border-left:4px solid #FB7185;background:#0B1C28;border-radius:12px;padding:12px 15px;margin-bottom:10px}
.fc.medium{border-left-color:#FBBF24}.fc.low{border-left-color:#60A5FA}
.fc .t{font-weight:700;color:#E8F3F6}.fc .e{color:#B9D3DC;font-size:.86rem;margin-top:3px}.fc .r{color:#8FA9B5;font-size:.8rem;margin-top:3px}
div.stButton>button,div.stDownloadButton>button{border-radius:12px;font-weight:700;padding:.5rem 1.1rem;border:1px solid #1F4A5E;background:#0D2230;color:#DDEEF2}
div.stButton>button:hover{border-color:#2DD4BF;color:#fff}
div.stButton>button[kind="primary"]{background:linear-gradient(120deg,#0E9488,#0E7FA8);border:0;color:#fff}
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea,[data-testid="stNumberInput"] input,[data-baseweb="select"]>div{border-radius:12px}
.st-key-mobnav{display:none}@media(max-width:900px){.st-key-mobnav{display:block;margin-bottom:10px}}
</style>
""", unsafe_allow_html=True)

# =============================================================== TIME
IST = timezone(timedelta(hours=5, minutes=30))
def now(): return datetime.now(IST)
def today(): return now().date()
def fmt(d): return d.strftime("%d-%m-%Y") if d else "Permanent"

# =============================================================== ENGINE: validation helpers
def name_sim(a, b): return difflib.SequenceMatcher(None, (a or "").lower(), (b or "").lower()).ratio()

def ocr_read(img):
    try:
        import pytesseract
        return pytesseract.image_to_string(img.convert("RGB"))
    except Exception:
        return None

DATE_RE = re.compile(r"(\d{2})[-/.](\d{2})[-/.](\d{4})")
def pdate(s):
    m = DATE_RE.search(s or "")
    try: return date(int(m[3]), int(m[2]), int(m[1])) if m else None
    except ValueError: return None

def parse_doc(text):
    out = dict(title="", issuer="", holder="", ref="", issued=None, valid=None, permanent=False, clauses=[])
    lines = [l.strip() for l in (text or "").splitlines() if l.strip()]
    if lines: out["title"] = lines[0]
    for l in lines:
        for key, pat in (("issuer", r"Issued\s*by\s*[:;\-]\s*(.+)"), ("holder", r"Issued\s*to\s*[:;\-]\s*(.+)"), ("ref", r"Reference\s*No\.?\s*[:;\-]?\s*(\S+)")):
            m = re.search(pat, l, re.I)
            if m and not out[key]: out[key] = m.group(1).strip()
        if re.match(r"The institution (shall|may)\b", l, re.I): out["clauses"].append(l)
        if re.search(r"Issue\s*date", l, re.I) and not out["issued"]: out["issued"] = pdate(l)
        if re.search(r"Valid\s*up\s*to", l, re.I):
            if re.search(r"permanent", l, re.I): out["permanent"] = True
            else: out["valid"] = pdate(l)
    return out

KEYWORDS = {"prev_eoa": "EXTENSION OF APPROVAL", "ter": "TER PAYMENT", "building": "BUILDING STABILITY", "fire": "FIRE SAFETY", "accred": "ACCREDITATION",
            "affil": "AFFILIATION", "society": "SOCIETY", "land": "LAND DOCUMENT", "affidavit": "AFFIDAVIT"}
def classify(text):
    up = (text or "").upper()
    for k, kw in KEYWORDS.items():
        if kw in up: return k
    return None

def qr_locate(img):
    try:
        import cv2
        arr = cv2.cvtColor(np.asarray(img.convert("RGB")), cv2.COLOR_RGB2GRAY)
        dets = [cv2.QRCodeDetector()]
        if hasattr(cv2, "QRCodeDetectorAruco"): dets.insert(0, cv2.QRCodeDetectorAruco())
        for sc in (1.0, 1.5, 0.8, 2.0):
            a = arr if sc == 1.0 else cv2.resize(arr, None, fx=sc, fy=sc, interpolation=cv2.INTER_CUBIC if sc > 1 else cv2.INTER_AREA)
            for det in dets:
                txt, pts, _ = det.detectAndDecode(a)
                if pts is not None and txt:
                    p = pts.reshape(-1, 2) / sc
                    return txt, (int(p[:, 0].min()), int(p[:, 1].min()), int(p[:, 0].max()), int(p[:, 1].max()))
    except Exception:
        pass
    return None, None

def parse_qr(txt):
    d = {}
    for part in (txt or "").split("|")[1:]:
        if ":" in part:
            k, v = part.split(":", 1); d[k.strip().upper()] = v.strip()
    return d

def seal_locate(img):
    try:
        import cv2
        hsv = cv2.cvtColor(cv2.cvtColor(np.asarray(img.convert("RGB")), cv2.COLOR_RGB2BGR), cv2.COLOR_BGR2HSV)
        m = cv2.inRange(hsv, (0, 90, 70), (10, 255, 255)) | cv2.inRange(hsv, (170, 90, 70), (180, 255, 255)) | cv2.inRange(hsv, (100, 90, 70), (130, 255, 255))
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in cnts:
            a = cv2.contourArea(c); p = cv2.arcLength(c, True)
            if a > 1500 and p > 0 and 4 * np.pi * a / (p * p) > 0.6:
                x, y, w, h = cv2.boundingRect(c); return (x, y, x + w, y + h)
    except Exception:
        pass
    return None

def ela_blocks(img, g=16, skip=()):
    b = io.BytesIO(); img.convert("RGB").save(b, "JPEG", quality=90); b.seek(0)
    diff = np.asarray(ImageChops.difference(img.convert("RGB"), Image.open(b)).convert("L"), float)
    for (x0, y0, x1, y1) in skip: diff[max(y0 - 10, 0):y1 + 10, max(x0 - 10, 0):x1 + 10] = 0
    h, w = diff.shape; bh, bw = max(h // g, 1), max(w // g, 1)
    return np.array([diff[i*bh:(i+1)*bh, j*bw:(j+1)*bw].mean() for i in range(g) for j in range(g)])
def ela_score(img, skip=()):
    bl = ela_blocks(img, skip=skip); return float((bl.max() - np.median(bl)) * 5)
def heatmap(img, skip=()):
    b = io.BytesIO(); img.convert("RGB").save(b, "JPEG", quality=90); b.seek(0)
    d = np.asarray(ImageChops.difference(img.convert("RGB"), Image.open(b)).convert("L"), float)
    for (x0, y0, x1, y1) in skip: d[max(y0 - 10, 0):y1 + 10, max(x0 - 10, 0):x1 + 10] = 0
    return Image.fromarray(np.clip(d * 25, 0, 255).astype("uint8"))

def dhash(img, size=16):
    g = np.asarray(img.convert("L").resize((size + 1, size), Image.LANCZOS), float)
    return int("".join("1" if v else "0" for v in (g[:, 1:] > g[:, :-1]).flatten()), 2)
def hamming(a, b): return bin(a ^ b).count("1")
DUP_DIST = 10   # of 256 bits

class Memory:
    """Remembers every document/photo fingerprint to spot reuse across institutions."""
    def __init__(self): self.items = []
    def find_other(self, h, inst):
        best = None
        for m in self.items:
            if m["inst"] != inst and hamming(h, m["hash"]) <= DUP_DIST:
                d = hamming(h, m["hash"])
                if best is None or d < best[0]: best = (d, m)
        return best[1] if best else None
    def add(self, h, inst, kind, label): self.items.append(dict(hash=h, inst=inst, kind=kind, label=label))

def img_bytes(img):
    b = io.BytesIO(); img.save(b, "PNG"); return b.getvalue()

@st.cache_data(show_spinner=False)
def read_doc(png):
    txt = ocr_read(Image.open(io.BytesIO(png)))
    return (txt is not None), (parse_doc(txt) if txt else None), (classify(txt) if txt else None)

def clause_align(doc_clauses, required):
    """Document DNA: align each required clause with the document text (Smith-Waterman local alignment)."""
    try:
        from Bio import Align
        al = Align.PairwiseAligner(); al.mode = "local"; al.match_score = 2; al.mismatch_score = -1; al.open_gap_score = -2; al.extend_gap_score = -1
        score = lambda r, d: al.score(r.lower(), d.lower()) / (2 * len(r))
    except Exception:
        score = lambda r, d: difflib.SequenceMatcher(None, r.lower(), d.lower()).ratio()
    return [(r, round(max((score(r, d) for d in doc_clauses), default=0.0), 2)) for r in required]

# =============================================================== SYNTHETIC DATA (institutions, document types, rules, sources)
INST = {
 "1-4521836": dict(name="Aaruvi Demo Institute of Technology", short="Aaruvi DIT", state="Tamil Nadu", code="TN", prev_eoa="2025-26", eoa_status="Approved",
                   programmes={"B.E. Computer Science & Engg": 120, "B.E. Electronics & Communication": 60, "B.E. Mechanical Engg": 60}, accr_days=600, ter_paid=True, deficiency="None"),
 "1-5530927": dict(name="Kaveri Demo College of Engineering", short="Kaveri DCE", state="Karnataka", code="KA", prev_eoa="2025-26", eoa_status="Approved with conditions",
                   programmes={"B.E. Civil Engg": 60, "B.E. Information Technology": 90}, accr_days=70, ter_paid=False, deficiency="Pending: faculty shortage"),
 "1-6112045": dict(name="Nilgiri Demo Institute of Technology", short="Nilgiri DIT", state="Tamil Nadu", code="TN", prev_eoa="2025-26", eoa_status="Approved",
                   programmes={"B.E. Electrical & Electronics": 60, "B.E. Computer Science & Engg": 60}, accr_days=400, ter_paid=True, deficiency="None"),
}
def intake_of(i): return sum(INST[i]["programmes"].values())

DT = {
 "affidavit": dict(title="AFFIDAVIT / UNDERTAKING", short="Affidavit / undertaking", issuer="Notary Public (simulated)", source=None, valid_days=None, qr=False),
 "society": dict(title="CERTIFICATE OF SOCIETY REGISTRATION", short="Society / trust registration", issuer="Registrar of Societies (simulated)", source="Registrar of Societies", valid_days=None, qr=True),
 "land": dict(title="LAND DOCUMENT - LEASE DEED", short="Land / lease document", issuer="Sub-Registrar Office (simulated)", source="Land Records Office", valid_days=9000, qr=True),
 "fire": dict(title="FIRE SAFETY NO OBJECTION CERTIFICATE", short="Fire safety NOC", issuer="State Fire Services (simulated)", source="State Fire Services", valid_days=330, qr=True),
 "building": dict(title="BUILDING STABILITY CERTIFICATE", short="Building stability certificate", issuer="Chartered Structural Engineer (simulated)", source=None, valid_days=700, qr=False),
 "accred": dict(title="ACCREDITATION CERTIFICATE", short="Accreditation certificate", issuer="Accreditation Board (simulated)", source="Accreditation Board", valid_days=500, qr=True),
 "affil": dict(title="UNIVERSITY AFFILIATION LETTER", short="University affiliation / NOC", issuer="Affiliating University (simulated)", source="Affiliating University", valid_days=400, qr=True),
 "prev_eoa": dict(title="EXTENSION OF APPROVAL LETTER", short="Previous EoA letter", issuer="AICTE Records (simulated)", source="AICTE records", valid_days=150, qr=True),
 "ter": dict(title="TER PAYMENT RECEIPT", short="TER payment receipt", issuer="AICTE Records (simulated)", source="AICTE records", valid_days=None, qr=True),
}
PREFIX = dict(affidavit="AFF", society="SOC", land="LND", fire="FIRE", building="BSC", accred="ACC", affil="AFL", prev_eoa="EOA", ter="TER")
CATS = {
 "Extension of Approval (EoA) - continuing institution": ["affidavit", "society", "land", "fire", "building", "accred", "affil", "prev_eoa", "ter"],
 "Addition of programme / change in intake": ["affidavit", "accred", "affil", "prev_eoa", "ter", "fire"],
 "Change of name / location": ["affidavit", "society", "land", "fire", "building", "affil", "prev_eoa"],
}
SOURCES = ["Registrar of Societies", "Land Records Office", "State Fire Services", "Accreditation Board", "Affiliating University", "AICTE records"]
STATUSES = ["Verified", "Mismatch detected", "Expired", "Verification pending", "Source unavailable", "Manual review required", "Missing"]
STATUS_CLR = {"Verified": ("#34D399", "rgba(52,211,153,.14)"), "Mismatch detected": ("#FB7185", "rgba(251,113,133,.15)"), "Expired": ("#FB923C", "rgba(251,146,60,.15)"),
              "Verification pending": ("#60A5FA", "rgba(96,165,250,.15)"), "Source unavailable": ("#FBBF24", "rgba(251,191,36,.15)"),
              "Manual review required": ("#2DD4BF", "rgba(45,212,191,.14)"), "Missing": ("#F87171", "rgba(248,113,113,.18)")}
REC_CLR = {"Escalate for senior review": ("#FB7185", "rgba(251,113,133,.15)", "f-ESC"), "Needs rectification": ("#FB923C", "rgba(251,146,60,.15)", "f-RECT"),
           "Manual verification required": ("#FBBF24", "rgba(251,191,36,.15)", "f-MAN"), "Ready for scrutiny": ("#34D399", "rgba(52,211,153,.14)", "f-READY")}
SEV_CLR = {"high": ("#FB7185", "rgba(251,113,133,.15)"), "medium": ("#FBBF24", "rgba(251,191,36,.15)"), "low": ("#60A5FA", "rgba(96,165,250,.15)")}

DEFAULT_CLAUSES = ["The institution shall maintain the prescribed faculty student ratio", "The institution shall not admit students beyond the approved intake", "The institution shall comply with all AICTE norms and regulations"]
def default_rules():
    return dict(clauses=list(DEFAULT_CLAUSES), name_thr=0.90, tamper_thr=5.0, warn_days=90, min_land=2.5, builtup_per_student=4.0, max_ratio=20.0, min_labs=6, blur_min=60.0, min_photo_w=640,
                cats={k: list(v) for k, v in CATS.items()})

# =============================================================== DOCUMENT + PHOTO GENERATORS (synthetic specimens)
def ref_for(dtype, inst_id, tag=""):
    n = zlib.crc32(f"{inst_id}{dtype}{tag}".encode()) % 90000 + 10000
    return f"{PREFIX[dtype]}/{INST[inst_id]['code']}/{today().year}/{n}"

def clean_spec(dtype, inst_id, holder=None):
    t = DT[dtype]; vd = INST[inst_id]["accr_days"] if dtype == "accred" else t["valid_days"]
    return dict(dtype=dtype, issuer=t["issuer"], holder=holder or INST[inst_id]["name"], ref=ref_for(dtype, inst_id), issued=today() - timedelta(days=300),
                valid=(today() + timedelta(days=vd)) if vd else None, qr_valid=None, edits=[], clauses=list(DEFAULT_CLAUSES) if dtype == "affidavit" else [])

def truth_of(spec, status="Active"):
    return dict(holder=spec["holder"], valid=spec["valid"].isoformat() if spec["valid"] else None, status=status)

_LINE_Y = lambda i: 100 + i * 58
def gen_doc(spec):
    t = DT[spec["dtype"]]; F = ImageFont.load_default(size=21); FB = ImageFont.load_default(size=27); FS = ImageFont.load_default(size=11)
    im = Image.new("RGB", (900, 620), (250, 248, 240)); d = ImageDraw.Draw(im)
    d.text((60, 30), t["title"], fill=(20, 40, 90), font=FB)
    lines = [f"Issued by: {spec['issuer']}", f"Issued to: {spec['holder']}", f"Reference No: {spec['ref']}", f"Issue date: {fmt(spec['issued'])}",
             f"Valid upto: {fmt(spec['valid'])}", "Synthetic specimen created for prototype testing only."]
    for i, l in enumerate(lines): d.text((60, _LINE_Y(i)), l, fill=(30, 30, 30), font=F)
    d.ellipse((720, 30, 840, 150), outline=(180, 30, 40), width=6); d.ellipse((732, 42, 828, 138), outline=(180, 30, 40), width=2); d.text((748, 78), "SEAL", fill=(180, 30, 40), font=F)
    if t["qr"]:
        import qrcode
        qv = spec["qr_valid"] or (spec["valid"].isoformat() if spec["valid"] else "PERMANENT")
        q = qrcode.QRCode(box_size=6, border=2); q.add_data(f"DOCIMMUNE|REF:{spec['ref']}|VALID:{qv}|NAME:{spec['holder']}"); q.make(fit=True)
        im.paste(q.make_image(fill_color="black", back_color="white").convert("RGB").resize((200, 200)), (690, 400))
    for i, cl in enumerate(spec.get("clauses", [])): d.text((60, 440 + i * 34), cl, fill=(30, 30, 30), font=ImageFont.load_default(size=17))
    for y in range(580, 610, 12): d.text((60, y), "DocImmune prototype - all content in this document is fictional", fill=(120, 120, 120), font=FS)
    rng = np.random.default_rng(zlib.crc32(spec["ref"].encode()))
    arr = np.asarray(im).astype(int) + rng.integers(-6, 7, (620, 900, 3)); im = Image.fromarray(arr.clip(0, 255).astype("uint8"))
    b = io.BytesIO(); im.save(b, "JPEG", quality=90); b.seek(0); im = Image.open(b).convert("RGB")
    for field, text in spec["edits"]:   # edits pasted after the original was saved
        i = {"holder": 1, "ref": 2, "issued": 3, "valid": 4}[field]; label = {"holder": "Issued to", "ref": "Reference No", "issued": "Issue date", "valid": "Valid upto"}[field]
        d = ImageDraw.Draw(im); d.rectangle((55, _LINE_Y(i) - 4, 690, _LINE_Y(i) + 30), fill=(250, 248, 240)); d.text((60, _LINE_Y(i)), f"{label}: {text}", fill=(30, 30, 30), font=F)
    return im

def gen_photo(seed, blur=False):
    r = np.random.default_rng(seed); W, H = 720, 480; im = Image.new("RGB", (W, H)); d = ImageDraw.Draw(im)
    for y in range(H): d.line((0, y, W, y), fill=(110, 150 + int(60 * y / H), 200))
    d.rectangle((0, 330, W, H), fill=(72, 112, 72)); bx = int(r.integers(60, 160)); d.rectangle((bx, 140, bx + 440, 330), fill=(176, 150, 128))
    for i in range(7):
        for j in range(3): d.rectangle((bx + 24 + i * 60, 160 + j * 54, bx + 62 + i * 60, 196 + j * 54), fill=(int(r.integers(60, 120)), int(r.integers(90, 150)), int(r.integers(140, 200))))
    d.rectangle((bx + 190, 262, bx + 250, 330), fill=(64, 50, 40))
    arr = np.asarray(im).astype(int) + r.integers(-14, 15, (H, W, 3)); im = Image.fromarray(arr.clip(0, 255).astype("uint8"))
    if blur: im = im.filter(ImageFilter.GaussianBlur(7))
    b = io.BytesIO(); im.save(b, "JPEG", quality=88); b.seek(0); return Image.open(b).convert("RGB")

def other_inst(inst_id): return next(i for i in INST if i != inst_id)

def make_pack(kind, inst_id, category, rules):
    """kind 'A' = complete & clean, 'B' = application with seeded issues. Returns the documents, what the (simulated) sources hold, and infra evidence."""
    req = rules["cats"][category]; items, down, history, notes = {}, set(), [], []
    for dt in req: s = clean_spec(dt, inst_id); items[dt] = dict(spec=s, truth=truth_of(s))
    oth = other_inst(inst_id)
    infra = dict(land=8.0, builtup=14000, labs=14, faculty=52, intake=intake_of(inst_id))
    photos = [("Campus front view", gen_photo(zlib.crc32(inst_id.encode()))), ("Laboratory block", gen_photo(zlib.crc32(inst_id.encode()) + 1))]
    if kind == "B":
        if "affidavit" in items:
            s = clean_spec("affidavit", inst_id); s["clauses"][1] = "The institution may admit students beyond the approved intake"; items["affidavit"] = dict(spec=s, truth=None); notes.append("Affidavit clause changed")
        if "building" in items: items["building"] = None; notes.append("Building stability certificate not submitted")
        if "fire" in items:
            s = clean_spec("fire", inst_id); s["valid"] = today() - timedelta(days=40); items["fire"] = dict(spec=s, truth=truth_of(s)); notes.append("Fire NOC expired")
        if "land" in items:
            s = clean_spec("land", inst_id); orig = s["valid"].isoformat(); s["edits"] = [("valid", fmt(today() + timedelta(days=20000)))]; s["qr_valid"] = orig
            items["land"] = dict(spec=s, truth=truth_of(clean_spec("land", inst_id))); notes.append("Lease validity altered after issue")
        if "accred" in items:
            s = clean_spec("accred", inst_id); s["valid"] = today() + timedelta(days=70); items["accred"] = dict(spec=s, truth=truth_of(s)); down.add("Accreditation Board"); notes.append("Accreditation source unavailable")
        if "affil" in items:
            s = clean_spec("affil", inst_id, holder=INST[inst_id]["name"].replace("College of Engineering", "Engg College").replace("Institute of Technology", "Inst. of Tech.")); items["affil"] = dict(spec=s, truth=truth_of(s)); notes.append("Institution name differs on affiliation letter")
        if "society" in items:
            s = clean_spec("society", oth); items["society"] = dict(spec=s, truth=truth_of(s)); history.append((gen_doc(s), oth, "society", "Society registration (earlier submission)")); notes.append("Society certificate already submitted by another institution")
        if "prev_eoa" in items:
            s = clean_spec("prev_eoa", inst_id); s["ref"] = s["ref"][:-1] + "0"; items["prev_eoa"] = dict(spec=s, truth=None); notes.append("Previous EoA reference not found in AICTE records")
        if "ter" in items:
            s = clean_spec("ter", inst_id); items["ter"] = dict(spec=s, truth=truth_of(s, status="Not paid")); notes.append("TER payment not recorded as paid")
        infra = dict(land=2.0, builtup=3200, labs=5, faculty=38, intake=300)
        ph = gen_photo(zlib.crc32(oth.encode()) + 5); history.append((ph, oth, "photo", "Campus photo (earlier submission)"))
        photos = [("Campus front view", ph), ("Laboratory block", gen_photo(77, blur=True))]
        notes += ["Claimed intake exceeds approved intake", "Infrastructure below configured norms", "Campus photo reused from another institution", "Laboratory photo is blurred"]
    return dict(items=items, down=down, history=history, infra=infra, photos=photos, notes=notes)

# =============================================================== PIPELINE
ss = st.session_state
ANOMALY = {"TAMPER", "QR_MISMATCH", "REUSE", "SRC_MISMATCH", "PHOTO_REUSE"}
MANUAL = {"UNAVAILABLE", "PENDING", "NOT_FOUND"}
RECTIFY = {"CLAUSE", "MISSING", "EXPIRED", "INCOMPLETE", "NAME", "TYPE", "DATES", "COMPLIANCE", "RECORDS", "EXPIRING", "PHOTO_QUALITY"}

def audit(app_id, kind, detail):
    ss.audit.append(dict(time=now(), actor=ss.role, app=app_id, kind=kind, detail=detail))

def make_ctx(down=()):
    return dict(rules=ss.rules, memory=ss.memory, registry=ss.registry, sources=ss.sources, down=set(down))

def verify_source(slot, p, payload, c):
    R = c["rules"]; T = today(); src = DT[slot]["source"]; ts = now()
    if p["valid"] and p["valid"] < T: return dict(status="Expired", source=src or "Document", ts=ts, text=f"Printed validity ended on {fmt(p['valid'])}.")
    if not src: return dict(status="Manual review required", source="No source configured", ts=ts, text="No authorized source is configured for this document type; routed for routine manual confirmation.")
    if not c["sources"].get(src, True) or src in c["down"]: return dict(status="Source unavailable", source=src, ts=ts, text=f"{src} could not be reached; routed for manual confirmation.")
    ref = p["ref"] or parse_qr(payload).get("REF")
    if not ref: return dict(status="Verification pending", source=src, ts=ts, text="Reference number could not be read, so the source cannot be queried yet.")
    rec = c["registry"].get(src, {}).get(ref)
    if rec is None: return dict(status="Manual review required", source=src, ts=ts, text=f"Reference {ref} was not found at {src}; routed for manual confirmation.", code="NOT_FOUND")
    diffs = []
    if name_sim(rec["holder"], p["holder"]) < R["name_thr"]: diffs.append(f'holder is "{rec["holder"]}"')
    pv = p["valid"].isoformat() if p["valid"] else None
    if (rec["valid"] or None) != pv and not (rec["valid"] is None and p["permanent"]): diffs.append(f'validity is {rec["valid"] or "permanent"}')
    if rec["status"] != "Active": diffs.append(f'status is "{rec["status"]}"')
    if diffs: return dict(status="Mismatch detected", source=src, ts=ts, text=f"{src} holds a different record: " + ", ".join(diffs) + ".")
    if rec["valid"] and date.fromisoformat(rec["valid"]) < T: return dict(status="Expired", source=src, ts=ts, text=f"{src} shows the validity ended on {rec['valid']}.")
    return dict(status="Verified", source=src, ts=ts, text=f"Details match the record held by {src}.")

def validate_doc(img, slot, inst_id, c, meta=None, label=None):
    R = c["rules"]; T = today(); inst = INST[inst_id]; F = []; short = DT[slot]["short"]
    def add(sev, code, title, evidence, reason): F.append(dict(sev=sev, code=code, title=title, evidence=evidence, reason=reason, doc=short))
    ok, p, det = read_doc(img_bytes(img)); note = None
    if not ok: p, det, note = meta, (slot if meta else None), ("OCR engine not available here: values taken from the submission metadata." if meta else "OCR engine not available: automatic reading skipped.")
    p = p or dict(title="", issuer="", holder="", ref="", issued=None, valid=None, permanent=False)
    if det and det != slot: add("medium", "TYPE", "Document type differs from checklist", f"Reads as '{DT[det]['short']}', checklist expects '{short}'", "A different document may have been uploaded for this slot.")
    miss = [n for n, v in (("holder name", p["holder"]), ("reference number", p["ref"]), ("issue date", p["issued"])) if not v]
    if DT[slot]["valid_days"] is not None and not p["valid"] and not p["permanent"]: miss.append("validity date")
    if slot == "affidavit":
        al = clause_align(p.get("clauses") or [], R["clauses"]); bad = [f'"{r[:48]}…" (match {sc:.2f})' for r, sc in al if sc < 0.85]
        if bad: add("medium", "CLAUSE", "Required undertaking clause missing or changed", "; ".join(bad), "Clause alignment (Smith-Waterman) found no close match to the configured regulatory text.")
    if miss: add("medium", "INCOMPLETE", "Incomplete document", "Missing: " + ", ".join(miss), "Fields required for verification could not be read.")
    if p["issued"] and (p["issued"] > T or (p["valid"] and p["issued"] > p["valid"])): add("medium", "DATES", "Irregular dates", f"Issued {fmt(p['issued'])}, valid upto {fmt(p['valid'])}", "Issue date is in the future or after the validity date.")
    if p["valid"] and p["valid"] < T: add("high", "EXPIRED", "Document expired", f"Valid upto {fmt(p['valid'])} (today {fmt(T)})", "Expired documents must be renewed before processing.")
    elif p["valid"] and (p["valid"] - T).days <= R["warn_days"]: add("medium", "EXPIRING", "Expiring soon", f"Valid upto {fmt(p['valid'])} ({(p['valid'] - T).days} days left)", "Renewal may be needed before the approval cycle completes.")
    if p["holder"]:
        sim = name_sim(p["holder"], inst["name"])
        if sim < R["name_thr"]: add("medium", "NAME", "Institution name inconsistent", f'Document: "{p["holder"]}" | record: "{inst["name"]}" ({int(sim*100)}% match)', "Name on the document differs from the AICTE institutional record.")
    payload, qbox = qr_locate(img); sbox = seal_locate(img); qr_state = "n/a"
    if DT[slot]["qr"]:
        if not payload: qr_state = "absent"; add("low", "QR_ABSENT", "QR code not found", "Expected on this document type", "Verification through the QR code could not be done.")
        else:
            q = parse_qr(payload); bad = []
            if q.get("REF") and p["ref"] and q["REF"] != p["ref"]: bad.append(f'reference (QR {q["REF"]} vs printed {p["ref"]})')
            pv = p["valid"].isoformat() if p["valid"] else "PERMANENT"
            if q.get("VALID") and q["VALID"] != pv: bad.append(f'validity (QR {q["VALID"]} vs printed {pv})')
            if q.get("NAME") and p["holder"] and name_sim(q["NAME"], p["holder"]) < R["name_thr"]: bad.append("holder name")
            qr_state = "mismatch" if bad else "match"
            if bad: add("high", "QR_MISMATCH", "QR code disagrees with printed details", "; ".join(bad), "The QR carries the original issue data; the printed text may have been altered.")
    if sbox is None: add("low", "SEAL", "Official seal not detected", "No round stamp found", "Seal presence is a supporting indicator only.")
    skip = [b for b in (qbox, sbox) if b]; t = ela_score(img, skip)
    if t >= R["tamper_thr"]: add("high", "TAMPER", "Possible alteration in the image", f"Edit score {t:.1f} (threshold {R['tamper_thr']:.1f}); the edited area is highlighted", "Regions that re-compress differently from the rest often indicate editing.")
    h = dhash(img); m = c["memory"].find_other(h, inst_id)
    if m: add("high", "REUSE", "Same document found in another institution's submission", f"Matches: {m['label']} ({INST[m['inst']]['short']})", "A document reused across institutions needs verification with the issuing authority.")
    c["memory"].add(h, inst_id, "document", label or short)
    v = verify_source(slot, p, payload, c)
    if v["status"] == "Mismatch detected": add("high", "SRC_MISMATCH", "Issuing-authority record differs", v["text"], "The authorized source holds details that do not match the submission.")
    elif v["status"] == "Source unavailable": add("medium", "UNAVAILABLE", "Source unavailable", v["text"], "Verification could not be completed automatically.")
    elif v["status"] == "Verification pending": add("medium", "PENDING", "Verification pending", v["text"], "The source cannot be queried until the reference is available.")
    elif v.get("code") == "NOT_FOUND": add("medium", "NOT_FOUND", "Reference not found at source", v["text"], "Could not confirm the document with the issuing authority.")
    elif v["status"] == "Manual review required" and not DT[slot]["source"]: add("low", "ROUTINE", "Routine manual confirmation", v["text"], "No automated source exists for this type.")
    status = v["status"]
    if status == "Verified" and any(f["code"] in ANOMALY for f in F): status = "Manual review required"
    return dict(slot=slot, title=short, status=status, vtext=v["text"], source=v["source"], ts=v["ts"], findings=F, fields=p, tamper=round(t, 1), qr=qr_state, seal=sbox is not None,
                images=(img, heatmap(img, skip)), note=note)

def infra_review(infra, inst_id, R):
    students = max(infra["intake"] * 4, 1); rows = []
    def row(label, value, norm, ok): rows.append(dict(label=label, value=value, norm=norm, ok=ok))
    row("Land area", f"{infra['land']:.1f} acres", f"at least {R['min_land']:.1f} acres", infra["land"] >= R["min_land"])
    bps = infra["builtup"] / students; row("Built-up area per student", f"{bps:.1f} sq m", f"at least {R['builtup_per_student']:.1f} sq m", bps >= R["builtup_per_student"])
    ratio = students / max(infra["faculty"], 1); row("Student-faculty ratio", f"{ratio:.1f} : 1", f"at most {R['max_ratio']:.0f} : 1", ratio <= R["max_ratio"])
    row("Laboratories", f"{infra['labs']}", f"at least {R['min_labs']}", infra["labs"] >= R["min_labs"])
    appr = intake_of(inst_id); row("Intake claimed vs approved", f"{infra['intake']}", f"approved {appr}", infra["intake"] <= appr)
    F = [dict(sev="medium", code="COMPLIANCE", title=f"Compliance gap: {r['label']}", evidence=f"{r['value']} (expected {r['norm']})", reason="Advisory: additional evidence or physical inspection may be required.", doc="Infrastructure") for r in rows if not r["ok"]]
    return rows, F

def photo_review(photos, inst_id, c):
    R = c["rules"]; out, F = [], []
    for label, im in photos:
        try:
            import cv2; blur = float(cv2.Laplacian(cv2.cvtColor(np.asarray(im.convert("RGB")), cv2.COLOR_RGB2GRAY), cv2.CV_64F).var())
        except Exception: blur = 999.0
        h = dhash(im); m = c["memory"].find_other(h, inst_id); c["memory"].add(h, inst_id, "photo", label)
        issues = []
        if im.width < R["min_photo_w"]: issues.append(("low", "PHOTO_QUALITY", "Low-resolution photo", f"{im.width}px wide (minimum {R['min_photo_w']})"))
        if blur < R["blur_min"]: issues.append(("medium", "PHOTO_QUALITY", "Photo is blurred", f"Sharpness {blur:.0f} (minimum {R['blur_min']:.0f})"))
        if m: issues.append(("high", "PHOTO_REUSE", "Photo reused from another institution", f"Matches: {m['label']} ({INST[m['inst']]['short']})"))
        for sev, code, title, ev in issues: F.append(dict(sev=sev, code=code, title=f"{title}: {label}", evidence=ev, reason="Infrastructure evidence must be original and legible; flagged for review.", doc="Infrastructure photos"))
        out.append(dict(label=label, image=im, sharp=blur, issues=[i[2] for i in issues]))
    return out, F

def records_review(app):
    inst = INST[app["inst_id"]]; T = today(); rows, F = [], []
    names_bad = [i for i in app["items"].values() if any(f["code"] == "NAME" for f in i["findings"])]
    rows.append(("Institution name on documents", f"{len(names_bad)} document(s) differ", inst["name"], not names_bad))
    ter = app["items"].get("ter"); rows.append(("TER payment", "Receipt submitted" if ter else "Not required / not submitted", "Paid" if inst["ter_paid"] else "Payment pending", inst["ter_paid"]))
    if not inst["ter_paid"]: F.append(dict(sev="medium", code="RECORDS", title="TER payment pending in AICTE records", evidence="AICTE record: payment pending", reason="Confirm payment status before processing.", doc="Institutional records"))
    rows.append(("Previous EoA", inst["prev_eoa"] + " (" + inst["eoa_status"] + ")", "As per AICTE record", True))
    rows.append(("Intake claimed", str(app["infra"]["intake"]), f"Approved {intake_of(app['inst_id'])}", app["infra"]["intake"] <= intake_of(app["inst_id"])))
    if app["infra"]["intake"] > intake_of(app["inst_id"]): F.append(dict(sev="high", code="RECORDS", title="Claimed intake exceeds approved intake", evidence=f"Claimed {app['infra']['intake']} vs approved {intake_of(app['inst_id'])}", reason="Intake increases need a separate approval.", doc="Institutional records"))
    rows.append(("Compliance / deficiency status", "-", inst["deficiency"], inst["deficiency"] == "None"))
    if inst["deficiency"] != "None": F.append(dict(sev="medium", code="RECORDS", title="Open deficiency in AICTE records", evidence=inst["deficiency"], reason="Existing deficiency should be reviewed with this application.", doc="Institutional records"))
    ac = app["items"].get("accred")
    if ac and ac["fields"].get("valid"):
        exp = T + timedelta(days=inst["accr_days"]); ok = abs((ac["fields"]["valid"] - exp).days) <= 31
        rows.append(("Accreditation validity", fmt(ac["fields"]["valid"]), fmt(exp), ok))
        if not ok: F.append(dict(sev="medium", code="RECORDS", title="Accreditation validity differs from record", evidence=f"Document {fmt(ac['fields']['valid'])} vs record {fmt(exp)}", reason="Dates should agree with AICTE records.", doc="Institutional records"))
    return rows, F

def finalize(app):
    items = list(app["items"].values()); F = [f for i in items for f in i["findings"]] + app["extra"]
    app["findings"] = F; app["counts"] = {s: sum(i["status"] == s for i in items) for s in STATUSES}
    cleared = sum(1 for i in items if i["status"] != "Missing" and not any(f["code"] not in ("ROUTINE", "SEAL", "QR_ABSENT") for f in i["findings"]) and i["status"] in ("Verified", "Manual review required"))
    app["readiness"] = int(round(cleared / max(len(items), 1) * 100))
    app["risk"] = min(100, sum({"high": 22, "medium": 9, "low": 3}[f["sev"]] for f in F if f["code"] not in ("ROUTINE", "SEAL", "QR_ABSENT")))
    codes = {f["code"] for f in F}
    app["rec"] = ("Escalate for senior review" if codes & ANOMALY else "Needs rectification" if codes & RECTIFY else "Manual verification required" if codes & MANUAL else "Ready for scrutiny")
    app["routine"] = sum(any(f["code"] == "ROUTINE" for f in i["findings"]) for i in items)
    return app

ALERT_KIND = {"MISSING": "Missing document", "EXPIRED": "Expired document", "EXPIRING": "Expiring document", "PENDING": "Verification pending", "UNAVAILABLE": "Pending source verification",
              "NOT_FOUND": "Pending source verification", "TAMPER": "Suspected anomaly", "QR_MISMATCH": "Suspected anomaly", "REUSE": "Suspected anomaly", "SRC_MISMATCH": "Unresolved discrepancy",
              "PHOTO_REUSE": "Suspected anomaly", "COMPLIANCE": "Compliance gap", "RECORDS": "Unresolved discrepancy", "NAME": "Unresolved discrepancy", "INCOMPLETE": "Missing information",
              "CLAUSE": "Unresolved discrepancy", "TYPE": "Unresolved discrepancy", "DATES": "Unresolved discrepancy", "PHOTO_QUALITY": "Compliance gap"}
def raise_alerts(app, only_doc=None):
    n = 0
    for f in app["findings"]:
        if f["code"] in ALERT_KIND and f["sev"] in ("high", "medium") and (only_doc is None or f["doc"] == only_doc):
            ss.alerts.append(dict(id=f"AL-{len(ss.alerts)+1:04d}", app=app["id"], doc=f["doc"], sev=f["sev"], kind=ALERT_KIND[f["code"]], text=f"{f['doc']}: {f['title']}", time=now(), status="Open", by="")); n += 1
    return n

def register_truth(spec, truth):
    src = DT[spec["dtype"]]["source"]
    if src and truth: ss.registry.setdefault(src, {})[spec["ref"]] = truth

def run_validation(inst_id, category, mode, uploads, infra, photos, progress=None):
    t0 = time.time(); R = ss.rules; req = R["cats"][category]; aid = f"APP-{10241 + len([a for a in ss.apps if not a['sample']])}"
    audit(aid, "Rule applied", f"Checklist '{category}': {len(req)} required documents")
    audit(aid, "Rule applied", f"Thresholds: name match ≥ {R['name_thr']:.2f}, edit score ≥ {R['tamper_thr']:.1f}, expiry warning {R['warn_days']} days")
    audit(aid, "Record checked", f"AICTE institutional record loaded for {inst_id} ({INST[inst_id]['name']})")
    pack = make_pack(mode, inst_id, category, R) if mode in ("A", "B") else None
    down = pack["down"] if pack else set(); c = make_ctx(down)
    if pack:
        for im, oi, kind, lab in pack["history"]: c["memory"].add(dhash(im), oi, kind, lab)
        for it in pack["items"].values():
            if it: register_truth(it["spec"], it["truth"])
        infra = pack["infra"]; photos = pack["photos"]
    items, slots = {}, list(req)
    sources_used = []
    if pack:
        for k, dt in enumerate(slots):
            if progress: progress.progress(k / (len(slots) + 1), text=f"Checking {DT[dt]['short']}…")
            it = pack["items"][dt]
            if it is None: items[dt] = dict(slot=dt, title=DT[dt]["short"], status="Missing", vtext="Required document was not submitted.", source="-", ts=now(), findings=[dict(sev="high", code="MISSING", title="Required document missing", evidence=f"{DT[dt]['short']} is required for this category", reason="The checklist cannot be completed without it.", doc=DT[dt]["short"])], fields={}, tamper=0, qr="n/a", seal=False, images=None, note=None, spec=None, truth=None); continue
            s = it["spec"]; img = gen_doc(s); meta = dict(holder=s["holder"], ref=s["ref"], issued=s["issued"], valid=s["valid"], permanent=s["valid"] is None, issuer=s["issuer"], title=DT[dt]["title"], clauses=s.get("clauses", []))
            r = validate_doc(img, dt, inst_id, c, meta=meta); r["spec"] = s; r["truth"] = it["truth"]; items[dt] = r
    else:
        unmatched = []
        for k, (name, im) in enumerate(uploads):
            if progress: progress.progress(k / (len(uploads) + 1), text=f"Reading {name}…")
            ok, p, det = read_doc(img_bytes(im)); slot = det if det in slots and det not in items else None
            if slot is None: unmatched.append(name); continue
            r = validate_doc(im, slot, inst_id, c, label=name); r["spec"] = None; r["truth"] = None; items[slot] = r
        for dt in slots:
            if dt not in items: items[dt] = dict(slot=dt, title=DT[dt]["short"], status="Missing", vtext="Required document was not submitted.", source="-", ts=now(), findings=[dict(sev="high", code="MISSING", title="Required document missing", evidence=f"{DT[dt]['short']} is required for this category", reason="The checklist cannot be completed without it.", doc=DT[dt]["short"])], fields={}, tamper=0, qr="n/a", seal=False, images=None, note=None, spec=None, truth=None)
        pack = dict(notes=[f"Could not classify: {', '.join(unmatched)}"] if unmatched else [])
    irows, iF = infra_review(infra, inst_id, R); prow, pF = photo_review(photos, inst_id, c)
    app = dict(id=aid, inst_id=inst_id, category=category, created=now(), by=ss.role, sample=False, mode=mode, items=items, infra=infra, infra_rows=irows, photos=prow, extra=iF + pF, notes=pack["notes"], decision=None, recs=[], down=sorted(down))
    rrows, rF = records_review(app); app["records"] = rrows; app["extra"] += rF; finalize(app)
    for it in items.values():
        if it["status"] != "Missing": audit(aid, "Source response", f"{it['title']}: {it['source']} → {it['status']}")
    for f in app["findings"]:
        if f["sev"] == "high": audit(aid, "Observation", f"{f['doc']}: {f['title']} ({f['evidence']})")
    n = raise_alerts(app); app["dur"] = round(time.time() - t0, 1)
    audit(aid, "Alert", f"{n} alert(s) raised"); audit(aid, "Action", f"Validation completed in {app['dur']} s. Recommendation: {app['rec']}")
    if progress: progress.progress(1.0, text="Done")
    ss.apps.insert(0, app); return app

def rectify(app, slot, img=None):
    inst_id = app["inst_id"]; c = make_ctx(); old = app["items"][slot]
    if img is None:
        s = clean_spec(slot, inst_id); register_truth(s, truth_of(s)); img = gen_doc(s)
        meta = dict(holder=s["holder"], ref=s["ref"], issued=s["issued"], valid=s["valid"], permanent=s["valid"] is None, issuer=s["issuer"], title=DT[slot]["title"], clauses=s.get("clauses", []))
    else: s, meta = None, None
    r = validate_doc(img, slot, inst_id, c, meta=meta, label="rectified"); r["spec"] = s; r["truth"] = truth_of(s) if s else None
    app["items"][slot] = r
    for a in ss.alerts:
        if a["app"] == app["id"] and a["doc"] == DT[slot]["short"] and a["status"] == "Open": a["status"] = "Resolved"; a["by"] = "rectification"
    rrows, rF = records_review(app); app["records"] = rrows
    app["extra"] = [f for f in app["extra"] if f["doc"] != "Institutional records"] + rF; finalize(app); raise_alerts(app, only_doc=DT[slot]["short"])
    audit(app["id"], "Action", f"Document rectified: {DT[slot]['short']} → {r['status']}")
    return r

def retry_source(app, slot):
    """Re-run verification for a document whose source was unavailable."""
    it = app["items"][slot]; s = it.get("spec")
    if not s: return it
    app_down = [d for d in app["down"] if DT[slot]["source"] != d]; app["down"] = app_down
    img = gen_doc(s); meta = dict(holder=s["holder"], ref=s["ref"], issued=s["issued"], valid=s["valid"], permanent=s["valid"] is None, issuer=s["issuer"], title=DT[slot]["title"], clauses=s.get("clauses", []))
    c = make_ctx(); r = validate_doc(img, slot, app["inst_id"], c, meta=meta, label="retry"); r["spec"] = s; r["truth"] = it.get("truth"); app["items"][slot] = r
    for a in ss.alerts:
        if a["app"] == app["id"] and a["doc"] == DT[slot]["short"] and a["status"] == "Open": a["status"] = "Resolved"; a["by"] = "source restored"
    finalize(app); raise_alerts(app, only_doc=DT[slot]["short"]); audit(app["id"], "Source response", f"{DT[slot]['short']}: retry → {r['status']}"); return r

# =============================================================== STATE + SAMPLE RECORDS
def fake_item(slot, status, fl=()):
    F = [dict(sev=s, code=c, title=t, evidence=e, reason="Preliminary indicator: human verification required.", doc=DT[slot]["short"]) for s, c, t, e in fl]
    return dict(slot=slot, title=DT[slot]["short"], status=status, vtext="Sample record (details not stored).", source=DT[slot]["source"] or "No source configured", ts=now(), findings=F,
                fields={}, tamper=0, qr="n/a", seal=True, images=None, note=None, spec=None, truth=None)

def seed_apps():
    cat = list(CATS)[0]; out = []
    def mk(aid, inst, items, extra, mins, dur, rec_note=""):
        app = dict(id=aid, inst_id=inst, category=cat, created=now() - timedelta(minutes=mins), by="Scrutiny Officer", sample=True, mode="seed", items=items, infra=dict(land=0, builtup=0, labs=0, faculty=0, intake=intake_of(inst)),
                   infra_rows=[], photos=[], extra=extra, notes=[], decision=None, recs=[], down=[], dur=dur, records=[])
        return finalize(app)
    g = lambda dt: fake_item(dt, "Verified" if DT[dt]["source"] else "Manual review required", [] if DT[dt]["source"] else [("low", "ROUTINE", "Routine manual confirmation", "No automated source")])
    i3 = "1-6112045"; out.append(mk("APP-10238", i3, {d: g(d) for d in CATS[cat]}, [], 340, 11.2))
    i1 = "1-4521836"; it = {d: g(d) for d in CATS[cat]}
    it["fire"] = fake_item("fire", "Expired", [("high", "EXPIRED", "Document expired", "Valid upto 12-08-2026")]); it["accred"] = fake_item("accred", "Verified", [("medium", "EXPIRING", "Expiring soon", "78 days left")])
    out.append(mk("APP-10239", i1, it, [], 150, 12.4))
    i2 = "1-5530927"; it = {d: g(d) for d in CATS[cat]}
    it["land"] = fake_item("land", "Mismatch detected", [("high", "TAMPER", "Possible alteration in the image", "Edit score 7.8"), ("high", "QR_MISMATCH", "QR code disagrees with printed details", "validity")])
    it["society"] = fake_item("society", "Manual review required", [("high", "REUSE", "Same document found in another institution's submission", "Matches an earlier submission")])
    it["building"] = fake_item("building", "Missing", [("high", "MISSING", "Required document missing", "Building stability certificate is required")])
    out.append(mk("APP-10240", i2, it, [dict(sev="high", code="RECORDS", title="Claimed intake exceeds approved intake", evidence="Claimed 300 vs approved 150", reason="Intake increases need a separate approval.", doc="Institutional records")], 40, 13.1))
    return out

def seed_alerts(apps):
    out = []
    for a in apps:
        for f in a["findings"]:
            if f["code"] in ALERT_KIND and f["sev"] in ("high", "medium"):
                out.append(dict(id=f"AL-{len(out)+1:04d}", app=a["id"], doc=f["doc"], sev=f["sev"], kind=ALERT_KIND[f["code"]], text=f"{f['doc']}: {f['title']}", time=a["created"], status="Open", by=""))
    return out

def init_state():
    if "init" in ss: return
    ss.role = "Scrutiny Officer"; ss.rules = default_rules(); ss.sources = {s: True for s in SOURCES}; ss.registry = {}; ss.memory = Memory(); ss.audit = []
    ss.apps = seed_apps(); ss.alerts = seed_alerts(ss.apps); ss.step = 1; ss.wiz = {}; ss.open_app = None; ss.evalres = None
    for a in ss.apps: ss.audit.append(dict(time=a["created"], actor="Scrutiny Officer", app=a["id"], kind="Action", detail="Sample record loaded (synthetic)"))
    ss.init = True

# =============================================================== UI HELPERS
ROLES = ["Scrutiny Officer", "Senior Officer", "Administrator", "Viewer"]
PERM = {"Scrutiny Officer": {"validate", "ack", "recommend", "audit"}, "Senior Officer": {"validate", "ack", "decide", "audit"}, "Administrator": {"rules", "audit"}, "Viewer": set()}
def can(p): return p in PERM.get(ss.role, set())
ICON = lambda p: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' + p + '</svg>'
SV = dict(doc=ICON('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 13h8M8 17h5"/>'), ok=ICON('<circle cx="12" cy="12" r="10"/><path d="m8 12 3 3 5-6"/>'),
          bell=ICON('<path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.7 21a2 2 0 0 1-3.4 0"/>'), bad=ICON('<path d="M7.9 2h8.2L22 7.9v8.2L16.1 22H7.9L2 16.1V7.9z"/><path d="m15 9-6 6M9 9l6 6"/>'),
          clock=ICON('<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>'), app=ICON('<rect x="3" y="3" width="18" height="18" rx="3"/><path d="M3 9h18M9 21V9"/>'))

def pill(text, clr, bg): return f'<span class="pill" style="color:{clr};background:{bg}">{html.escape(str(text))}</span>'
def spill(s): c, b = STATUS_CLR[s]; return pill(s, c, b)
def vpill(s): c, b = SEV_CLR[s]; return pill(s.upper(), c, b)
def rpill(r): c, b, _ = REC_CLR[r]; return pill(r, c, b)
def kpi(icon, color, val, label): return f'<div class="kpi"><div class="ic" style="background:{color}22;color:{color}">{icon}</div><div><b>{val}</b><span>{label}</span></div></div>'

def gauge(risk, color):
    C = 2 * 3.14159 * 54
    return (f'<svg width="150" height="150" viewBox="0 0 140 140"><circle cx="70" cy="70" r="54" fill="none" stroke="rgba(255,255,255,.22)" stroke-width="12"/>'
            f'<circle cx="70" cy="70" r="54" fill="none" stroke="#fff" stroke-width="12" stroke-linecap="round" stroke-dasharray="{C*min(risk,100)/100} {C}" transform="rotate(-90 70 70)"/>'
            f'<text x="70" y="68" text-anchor="middle" font-size="30" font-weight="800" fill="#fff">{int(risk)}</text><text x="70" y="88" text-anchor="middle" font-size="11" fill="#fff" opacity=".9">RISK / 100</text></svg>')

def top(title, sub):
    a, b = st.columns([4, 1.4], vertical_alignment="center")
    a.markdown(f'<div class="ph"><h1>{title}</h1><p>{sub}</p></div>', unsafe_allow_html=True)
    b.selectbox("Signed in as", ROLES, key="role", label_visibility="collapsed", help="Demo roles. A production deployment would use the portal's single sign-on.")

def notice(text, kind="tip"): st.markdown(f'<div class="{kind}">{text}</div>', unsafe_allow_html=True)
def open_alerts(): return [a for a in ss.alerts if a["status"] == "Open"]

def to_csv(rows):
    b = io.StringIO(); w = csv.writer(b); w.writerow(["Time", "Actor", "Application", "Type", "Detail"])
    for r in rows: w.writerow([f"{r['time']:%Y-%m-%d %H:%M:%S}", r["actor"], r["app"], r["kind"], r["detail"]])
    return b.getvalue().encode()

# =============================================================== APPLICATION REPORT (shared by wizard + applications page)
def app_detail(app, k):
    inst = INST[app["inst_id"]]; rc, rbg, rcls = REC_CLR[app["rec"]]; items = list(app["items"].values())
    high = sum(f["sev"] == "high" for f in app["findings"]); med = sum(f["sev"] == "medium" for f in app["findings"])
    a, b = st.columns([1, 2.3], gap="large")
    with a:
        msg = {"Escalate for senior review": "Preliminary anomalies need a senior officer's review.", "Needs rectification": "Missing, expired or inconsistent items need correction.",
               "Manual verification required": "Some documents could not be confirmed automatically.", "Ready for scrutiny": "No blocking issues found. Proceed with routine scrutiny."}[app["rec"]]
        st.markdown(f'<div class="vc {rcls}">{gauge(app["risk"], rc)}<h2>{app["rec"]}</h2><p>{msg}</p></div>', unsafe_allow_html=True)
    with b:
        tag = '<span class="tag">sample record</span>' if app["sample"] else ""
        st.markdown(f'<div class="card"><h4>{html.escape(inst["name"])}{tag}</h4><div style="color:#8FA9B5;font-size:.88rem;line-height:1.7">'
                    f'{app["id"]} · AICTE ID {app["inst_id"]} · {inst["state"]}<br>{app["category"]}<br>Validated {app["created"]:%d %b %Y, %H:%M} by {app["by"]} · {app["dur"]} s</div></div>', unsafe_allow_html=True)
        st.write("")
        m = st.columns(4)
        m[0].markdown(kpi(SV["ok"], "#34D399", f'{app["readiness"]}%', "Checklist cleared"), unsafe_allow_html=True)
        m[1].markdown(kpi(SV["doc"], "#2DD4BF", f'{app["counts"]["Verified"]}/{len(items)}', "Verified at source"), unsafe_allow_html=True)
        m[2].markdown(kpi(SV["bad"], "#FB7185", f"{high} / {med}", "High / medium flags"), unsafe_allow_html=True)
        m[3].markdown(kpi(SV["bell"], "#FBBF24", len([x for x in ss.alerts if x["app"] == app["id"] and x["status"] == "Open"]), "Open alerts"), unsafe_allow_html=True)
    if app["notes"] and not app["sample"]:
        notice("<b>What this demo set contains:</b> " + " · ".join(app["notes"]), "warn")
    t1, t2, t3, t4, t5 = st.tabs(["Documents", "Findings & evidence", "Compliance", "Records check", "Decision & audit"])
    with t1:
        rows = "".join(f'<div class="row"><div class="n" style="min-width:230px">{i["title"]}</div><div>{spill(i["status"])}</div><div class="m" style="margin-left:14px">{html.escape(i["source"])}</div></div>' for i in items)
        st.markdown(f'<div class="card">{rows}</div>', unsafe_allow_html=True); st.write("")
        for i in items:
            with st.expander(f'{i["title"]} · {i["status"]}'):
                st.markdown(f'**Verification:** {i["vtext"]}  \n**Source:** {i["source"]} · {i["ts"]:%d %b %Y %H:%M:%S}')
                if i.get("note"): st.caption(i["note"])
                f = i["fields"]
                if f: st.caption(f'Read from document → holder: {f.get("holder") or "-"} · ref: {f.get("ref") or "-"} · issued: {fmt(f.get("issued")) if f.get("issued") else "-"} · valid upto: {"Permanent" if f.get("permanent") else (fmt(f.get("valid")) if f.get("valid") else "-")}')
                for fi in i["findings"]:
                    if fi["code"] not in ("ROUTINE",): st.markdown(f'<div class="fc {fi["sev"]}"><div class="t">{vpill(fi["sev"])} &nbsp;{html.escape(fi["title"])}</div><div class="e">{html.escape(fi["evidence"])}</div></div>', unsafe_allow_html=True)
                if i.get("images"):
                    c1, c2 = st.columns(2); c1.image(i["images"][0], caption="Submitted document", width="stretch"); c2.image(i["images"][1], caption="Edit map (bright = edited)", width="stretch")
                fixable = {"NAME", "INCOMPLETE", "TYPE", "DATES", "REUSE", "TAMPER", "QR_MISMATCH", "NOT_FOUND", "EXPIRING", "SRC_MISMATCH", "EXPIRED"}
                if not app["sample"] and (i["status"] in ("Missing", "Expired", "Mismatch detected", "Verification pending", "Source unavailable") or any(x["code"] in fixable for x in i["findings"])):
                    st.markdown("**Rectification**")
                    if not can("validate"): st.caption("Your role cannot submit corrected documents.")
                    else:
                        r1, r2, r3 = st.columns([2, 1.4, 1.4])
                        up = r1.file_uploader("Upload corrected document", type=["png", "jpg", "jpeg"], key=f"rfu_{k}_{i['slot']}")
                        if r2.button("Re-validate upload", key=f"rfb_{k}_{i['slot']}", disabled=up is None): rectify(app, i["slot"], Image.open(up).convert("RGB")); st.rerun()
                        if app["mode"] in ("A", "B") and r3.button("Use corrected demo document", key=f"rfd_{k}_{i['slot']}"): rectify(app, i["slot"]); st.rerun()
                        if i["status"] == "Source unavailable" and i.get("spec") and st.button("Retry source verification", key=f"rfr_{k}_{i['slot']}"): retry_source(app, i["slot"]); st.rerun()
    with t2:
        notice("Flags are <b>preliminary indicators</b> that need human verification. They are not proof of forgery or misconduct.", "warn")
        F = [f for f in app["findings"] if f["code"] not in ("ROUTINE", "SEAL", "QR_ABSENT")]
        if not F: notice("No findings. Nothing needs attention.")
        for f in sorted(F, key=lambda x: ["high", "medium", "low"].index(x["sev"])):
            st.markdown(f'<div class="fc {f["sev"]}"><div class="t">{vpill(f["sev"])} &nbsp;{html.escape(f["title"])} <span class="tag">{html.escape(f["doc"])}</span></div><div class="e"><b>Evidence:</b> {html.escape(f["evidence"])}</div><div class="r"><b>Why flagged:</b> {html.escape(f["reason"])}</div></div>', unsafe_allow_html=True)
    with t3:
        if not app["infra_rows"]: notice("Infrastructure evidence is not stored for sample records.")
        else:
            body = "".join(f'<div class="ck"><div class="b {"ok" if r["ok"] else "bad"}">{"✓" if r["ok"] else "✕"}</div><div><div class="t">{r["label"]}</div><div class="d">{r["value"]} · expected {r["norm"]}</div></div></div>' for r in app["infra_rows"])
            st.markdown(f'<div class="card"><h4>Infrastructure norms (configurable)</h4>{body}</div>', unsafe_allow_html=True); st.write("")
            notice("Norm values are placeholders set on the Rules page. Findings are advisory; inspection decisions remain with the competent authority.", "warn")
            cols = st.columns(max(len(app["photos"]), 1))
            for col, p in zip(cols, app["photos"]):
                col.image(p["image"], caption=f'{p["label"]} · sharpness {p["sharp"]:.0f}', width="stretch")
                col.markdown(spill("Verified") if not p["issues"] else "".join(pill(x, "#FB7185", "rgba(251,113,133,.15)") for x in p["issues"]), unsafe_allow_html=True)
    with t4:
        if not app["records"]: notice("Records cross-check is not stored for sample records.")
        else:
            body = "".join(f'<div class="ck"><div class="b {"ok" if ok else "bad"}">{"✓" if ok else "✕"}</div><div><div class="t">{lab}</div><div class="d">Application / documents: {html.escape(str(a))} · AICTE record: {html.escape(str(r))}</div></div></div>' for lab, a, r, ok in app["records"])
            st.markdown(f'<div class="card"><h4>Application vs institutional records</h4>{body}</div>', unsafe_allow_html=True)
    with t5:
        st.markdown("**Officer action**")
        remark = st.text_area("Remark", key=f"rm_{k}", placeholder="Record the reason for your decision or recommendation", height=80)
        if can("decide"):
            d = st.selectbox("Final decision", ["Approve for further processing", "Request additional documents", "Order physical inspection", "Reject application"], key=f"dc_{k}")
            rev = st.checkbox("I have reviewed the evidence and flags for this application", key=f"rv_{k}")
            adverse = d == "Reject application"
            if st.button("Record final decision", type="primary", key=f"db_{k}", disabled=not rev or (adverse and not remark.strip())):
                app["decision"] = d; app["recs"].append((now(), ss.role, d, remark)); audit(app["id"], "Action", f"Final decision: {d}. Remark: {remark or '-'}"); st.rerun()
            if adverse and not remark.strip(): st.caption("A remark is required before any adverse action.")
        elif can("recommend"):
            d = st.selectbox("Recommendation", ["Recommend approval for further processing", "Recommend requesting additional documents", "Recommend physical inspection", "Recommend rejection"], key=f"rc_{k}")
            if st.button("Submit recommendation", type="primary", key=f"rb_{k}"): app["recs"].append((now(), ss.role, d, remark)); audit(app["id"], "Action", f"Recommendation: {d}. Remark: {remark or '-'}"); st.rerun()
            st.caption("Final decisions are taken by a Senior Officer.")
        else: st.caption("Your role has read-only access.")
        if app["decision"]: notice(f"<b>Final decision recorded:</b> {app['decision']}")
        for t, who, d, rm in app["recs"]: st.markdown(f"`{t:%d %b %H:%M}` **{who}**: {d}" + (f" · _{rm}_" if rm else ""))
        if can("audit"):
            st.markdown("**Audit trail for this application**")
            rows = [r for r in ss.audit if r["app"] == app["id"]]
            st.dataframe([{"Time": f"{r['time']:%d %b %H:%M:%S}", "Actor": r["actor"], "Type": r["kind"], "Detail": r["detail"]} for r in rows], width="stretch", hide_index=True)
            st.download_button("Download audit (CSV)", to_csv(rows), file_name=f"{app['id']}_audit.csv", mime="text/csv", key=f"ad_{k}")

# =============================================================== PAGES
def page_dashboard():
    top("Approval Validation Console", "AICTE Extension of Approval · decision support for scrutiny officers")
    apps = ss.apps; al = open_alerts(); docs = [i for a in apps for i in a["items"].values() if i["status"] != "Missing"]
    st.markdown('<div class="hero"><h1>Validate applications at the earliest stage</h1><p>DocImmune checks every document against the checklist, the institutional records and the issuing authority, flags anomalies with evidence, and leaves the final decision to the competent officer.</p></div>', unsafe_allow_html=True)
    b1, b2, _ = st.columns([1.4, 1.4, 4])
    b1.button("New validation", type="primary", icon=":material/add:", on_click=lambda: st.switch_page(P_NEW), disabled=not can("validate"))
    b2.button("Open alerts", icon=":material/notifications:", on_click=lambda: st.switch_page(P_ALERTS))
    if not can("validate"): st.caption(f"Signed in as {ss.role}: this role cannot start validations.")
    k = st.columns(5); ver = sum(i["status"] == "Verified" for i in docs)
    k[0].markdown(kpi(SV["app"], "#2DD4BF", len(apps), "Applications validated"), unsafe_allow_html=True)
    k[1].markdown(kpi(SV["doc"], "#38BDF8", len(docs), "Documents checked"), unsafe_allow_html=True)
    k[2].markdown(kpi(SV["ok"], "#34D399", f"{int(ver / max(len(docs), 1) * 100)}%", "Verified at source"), unsafe_allow_html=True)
    k[3].markdown(kpi(SV["bell"], "#FBBF24", len(al), "Open alerts"), unsafe_allow_html=True)
    k[4].markdown(kpi(SV["clock"], "#A78BFA", f'{np.mean([a["dur"] for a in apps]):.0f} s', "Avg validation time"), unsafe_allow_html=True)
    st.write("")
    l, r = st.columns([1.7, 1], gap="large")
    rows = "".join(f'<div class="row"><div class="av">{INST[a["inst_id"]]["short"][0]}</div><div><div class="n">{INST[a["inst_id"]]["short"]}{"<span class=tag>sample</span>" if a["sample"] else ""}</div><div class="m">{a["id"]} · {a["created"]:%d %b, %H:%M}</div></div>'
                   f'<div class="r">{rpill(a["rec"])}<div class="m">risk {a["risk"]}/100 · cleared {a["readiness"]}%</div></div></div>' for a in sorted(apps, key=lambda x: -x["risk"])[:5])
    l.markdown(f'<div class="card"><h4>Applications needing attention</h4>{rows}</div>', unsafe_allow_html=True)
    cnt = {s: sum(i["status"] == s for a in apps for i in a["items"].values()) for s in STATUSES}; mx = max(max(cnt.values()), 1)
    bars = "".join(f'<div style="margin:9px 0"><div style="display:flex;justify-content:space-between;font-size:.82rem;color:#B9D3DC"><span>{s}</span><b>{cnt[s]}</b></div><div style="height:8px;background:#16303F;border-radius:6px;overflow:hidden"><div style="width:{cnt[s]/mx*100}%;height:100%;background:{STATUS_CLR[s][0]}"></div></div></div>' for s in STATUSES)
    r.markdown(f'<div class="card"><h4>Document verification status</h4>{bars}</div>', unsafe_allow_html=True)
    st.write("")
    a2, b2 = st.columns([1.7, 1], gap="large")
    al_rows = "".join(f'<div class="row"><div><div class="n">{html.escape(x["text"])}</div><div class="m">{x["app"]} · {x["kind"]} · {x["time"]:%d %b %H:%M}</div></div><div class="r">{vpill(x["sev"])}</div></div>' for x in sorted(al, key=lambda z: z["time"], reverse=True)[:5]) or '<div class="m">No open alerts.</div>'
    a2.markdown(f'<div class="card"><h4>Latest open alerts</h4>{al_rows}</div>', unsafe_allow_html=True)
    ac = "".join(f'<div class="row"><div><div class="n" style="font-size:.86rem">{html.escape(x["detail"][:70])}</div><div class="m">{x["app"]} · {x["kind"]}</div></div></div>' for x in ss.audit[-5:][::-1])
    b2.markdown(f'<div class="card"><h4>Recent activity</h4>{ac}</div>', unsafe_allow_html=True)
    st.caption("All institutions, documents and registries in this prototype are synthetic. AI output is decision support only; final decisions rest with the competent authority.")

def page_new():
    top("New validation", "Check an application and its supporting documents in three steps")
    if not can("validate"): notice(f"Your role ({ss.role}) cannot start validations. Switch to Scrutiny Officer or Senior Officer at the top right.", "warn"); return
    step = ss.step; W = ss.wiz
    st.markdown('<div class="stp">' + "".join(f'<div class="{"on" if i == step else "done" if i < step else ""}"><b>{"✓" if i < step else i}</b>{t}</div>' for i, t in enumerate(["Application", "Documents & evidence", "Result"], 1)) + "</div>", unsafe_allow_html=True)
    ids = list(INST); cats = list(ss.rules["cats"]); modes = ["Demo set A: complete and clean", "Demo set B: application with issues", "Upload documents"]
    if step == 1:
        W.setdefault("inst", ids[0]); W.setdefault("cat", cats[0]); W.setdefault("mode", modes[0])
        a, b = st.columns(2, gap="large")
        inst_id = a.selectbox("Institution (from AICTE records)", ids, index=ids.index(W["inst"]), format_func=lambda i: f"{INST[i]['name']}  ·  {i}")
        cat = a.selectbox("Application category", cats, index=cats.index(W["cat"]) if W["cat"] in cats else 0)
        mode = a.radio("Documents", modes, index=modes.index(W["mode"]))
        r = INST[inst_id]; progs = "".join(f"<div class='m'>{k}: {v}</div>" for k, v in r["programmes"].items())
        b.markdown(f'<div class="card"><h4>Institutional record</h4><div style="color:#B9D3DC;font-size:.9rem;line-height:1.7"><b>{r["name"]}</b><br>AICTE ID {inst_id} · {r["state"]}<br>Previous EoA: {r["prev_eoa"]} ({r["eoa_status"]})<br>'
                   f'TER payment: {"Paid" if r["ter_paid"] else "Pending"} · Deficiency: {r["deficiency"]}<br><span style="color:#8FA9B5">Approved intake: {intake_of(inst_id)}</span></div>{progs}</div>', unsafe_allow_html=True)
        notice("Required documents for this category: " + ", ".join(DT[d]["short"] for d in ss.rules["cats"][cat]))
        if st.button("Continue", type="primary", icon=":material/arrow_forward:"): W.update(inst=inst_id, cat=cat, mode=mode); ss.step = 2; st.rerun()
    elif step == 2:
        mode = W["mode"]; mk = "A" if mode.startswith("Demo set A") else "B" if mode.startswith("Demo set B") else "U"
        st.markdown(f"**{INST[W['inst']]['name']}** · {W['cat']}")
        up, photos_up, infra = [], [], None
        if mk == "U":
            files = st.file_uploader("Upload the supporting documents (PNG / JPG)", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
            up = [(f.name, Image.open(f).convert("RGB")) for f in files or []]
            c1, c2, c3 = st.columns(3)
            infra = dict(land=c1.number_input("Land area (acres)", 0.0, 500.0, 8.0), builtup=c2.number_input("Built-up area (sq m)", 0, 500000, 14000), labs=c3.number_input("Laboratories", 0, 200, 14),
                         faculty=c1.number_input("Faculty strength", 1, 5000, 52), intake=c2.number_input("Total intake claimed", 1, 5000, intake_of(W["inst"])))
            pf = st.file_uploader("Infrastructure photos (optional)", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="photos")
            photos_up = [(f.name, Image.open(f).convert("RGB")) for f in pf or []]
        else:
            notice("This demo set includes ready-made documents, infrastructure figures and photos." + (" It contains several seeded problems so you can see every kind of finding." if mk == "B" else " Everything is consistent and valid."))
            req = ss.rules["cats"][W["cat"]]
            st.markdown('<div class="card"><h4>Checklist</h4>' + "".join(f'<div class="row"><div class="n" style="min-width:250px">{DT[d]["short"]}</div><div class="m">{DT[d]["issuer"]} · source: {DT[d]["source"] or "manual confirmation"}</div></div>' for d in req) + "</div>", unsafe_allow_html=True)
        b1, b2, _ = st.columns([1, 1.6, 3]); b1.button("Back", icon=":material/arrow_back:", on_click=lambda: ss.update(step=1))
        if b2.button("Run validation", type="primary", icon=":material/search:", disabled=(mk == "U" and not up)):
            prog = st.progress(0.0, text="Starting…"); ss.last = run_validation(W["inst"], W["cat"], mk, up, infra, photos_up, prog); ss.step = 3; st.rerun()
    else:
        app_detail(ss.last, "wiz")
        n1, n2, _ = st.columns([1.4, 1.4, 3]); n1.button("Validate another", type="primary", icon=":material/add:", on_click=lambda: ss.update(step=1))
        n2.button("Open all applications", icon=":material/folder_open:", on_click=lambda: st.switch_page(P_APPS))

def page_apps():
    top("Applications", "Every validated application, with its documents, findings and decision")
    apps = ss.apps; c1, c2 = st.columns([2, 2])
    f = c1.segmented_control("Show", ["All"] + list(REC_CLR), default="All"); s = c2.text_input("Search institution", placeholder="Type a name…")
    rows = [a for a in apps if (f in (None, "All") or a["rec"] == f) and s.lower() in INST[a["inst_id"]]["name"].lower()]
    if not rows: notice("No applications to show."); return
    st.dataframe([{"Application": a["id"], "Institution": INST[a["inst_id"]]["name"], "Category": a["category"][:38], "Recommendation": a["rec"], "Risk": a["risk"], "Cleared %": a["readiness"],
                   "Decision": a["decision"] or "Pending", "Validated": f"{a['created']:%d %b %H:%M}"} for a in rows], width="stretch", hide_index=True)
    st.subheader("Open an application")
    pick = st.selectbox("Application", [a["id"] for a in rows], label_visibility="collapsed")
    app_detail(next(a for a in rows if a["id"] == pick), "apps")

def page_alerts():
    top("Alerts", "Items that need an officer's attention")
    c1, c2 = st.columns(2); stt = c1.segmented_control("Status", ["Open", "Acknowledged", "Resolved", "All"], default="Open"); sv = c2.segmented_control("Severity", ["All", "high", "medium"], default="All")
    rows = [a for a in sorted(ss.alerts, key=lambda z: z["time"], reverse=True) if (stt in (None, "All") or a["status"] == stt) and (sv in (None, "All") or a["sev"] == sv)]
    st.caption(f"{len(rows)} alert(s). In-app alerts only; e-mail or SMS notification would be added at portal integration.")
    for a in rows[:30]:
        x, y = st.columns([6, 1.3], vertical_alignment="center")
        x.markdown(f'<div class="fc {a["sev"]}"><div class="t">{vpill(a["sev"])} &nbsp;{html.escape(a["text"])}</div><div class="e">{a["app"]} · {a["kind"]} · {a["time"]:%d %b %H:%M} · {a["status"]}{(" by " + a["by"]) if a["by"] else ""}</div></div>', unsafe_allow_html=True)
        if a["status"] == "Open" and y.button("Acknowledge", key=f"ack_{a['id']}", disabled=not can("ack")):
            a["status"] = "Acknowledged"; a["by"] = ss.role; audit(a["app"], "Alert", f"{a['id']} acknowledged: {a['text']}"); st.rerun()
    if not can("ack"): st.caption("Your role cannot acknowledge alerts.")

def page_audit():
    top("Audit trail", "Rules applied, records checked, source responses, alerts, observations and actions")
    if not can("audit"): notice(f"Your role ({ss.role}) does not have access to the audit trail.", "warn"); return
    c1, c2 = st.columns(2); app = c1.selectbox("Application", ["All"] + [a["id"] for a in ss.apps]); kinds = c2.multiselect("Type", ["Rule applied", "Record checked", "Source response", "Alert", "Observation", "Action"])
    rows = [r for r in ss.audit if (app == "All" or r["app"] == app) and (not kinds or r["kind"] in kinds)]
    st.dataframe([{"Time": f"{r['time']:%d %b %H:%M:%S}", "Actor": r["actor"], "Application": r["app"], "Type": r["kind"], "Detail": r["detail"]} for r in rows[::-1]], width="stretch", hide_index=True)
    st.download_button("Download audit (CSV)", to_csv(rows), file_name="docimmune_audit.csv", mime="text/csv")

def quick_check(img, spec):
    ok, p, det = read_doc(img_bytes(img)); payload, qb = qr_locate(img); sb = seal_locate(img); t = ela_score(img, [b for b in (qb, sb) if b]); qm = False
    if payload and p:
        q = parse_qr(payload); pv = p["valid"].isoformat() if p["valid"] else "PERMANENT"; qm = (q.get("REF") != p["ref"]) or (q.get("VALID") != pv)
    return ok, p, t, qm

def page_eval():
    top("Evaluation", "Measured on a labelled synthetic test set generated on the spot")
    c1, c2, c3 = st.columns(3); n = c1.slider("Documents per class", 3, 10, 5); mins = c2.number_input("Assumed manual scrutiny time per document (min)", 1.0, 60.0, 5.0)
    c3.write(""); go = c3.button("Run evaluation", type="primary", icon=":material/play_arrow:")
    if go:
        R = ss.rules; rng = random.Random(11); prog = st.progress(0.0, text="Generating test documents…"); res = []; types = list(DT)
        for k in range(2 * n):
            alt = k >= n; dt = types[(k * 2 + (1 if alt else 0)) % len(types)]; inst = list(INST)[k % 3]; s = clean_spec(dt, inst); s["ref"] = ref_for(dt, inst, tag=str(k))
            if alt:
                if s["valid"] is not None and rng.random() < .6: s["qr_valid"] = s["valid"].isoformat(); s["edits"] = [("valid", fmt(s["valid"] + timedelta(days=rng.randint(200, 2000))))]
                else: s["edits"] = [(rng.choice(["holder", "issued"]), "Altered Entry" if rng.random() < .5 else fmt(today() - timedelta(days=rng.randint(10, 900))))]
            img = gen_doc(s); t0 = time.time(); ok, p, t, qm = quick_check(img, s); dt_s = time.time() - t0
            flagged = t >= R["tamper_thr"] or qm; right = (ok and p["ref"] == s["ref"] and (p["valid"] == s["valid"] or (s["valid"] is None and p["permanent"]))) if not alt else None
            res.append(dict(alt=alt, flagged=flagged, ok=ok, right=right, secs=dt_s)); prog.progress((k + 1) / (2 * n), text=f"Document {k + 1} of {2 * n}")
        ss.evalres = dict(res=res, mins=mins, n=n)
    E = ss.evalres
    if not E: notice("Press <b>Run evaluation</b>. The test set has clean documents and documents that were edited after issue, so the detection rate and false-alarm rate can be measured."); return
    res = E["res"]; clean = [r for r in res if not r["alt"]]; alt = [r for r in res if r["alt"]]
    rec = sum(r["flagged"] for r in alt) / len(alt); fa = sum(r["flagged"] for r in clean) / len(clean); acc = (sum(r["flagged"] for r in alt) + sum(not r["flagged"] for r in clean)) / len(res)
    exr = [r for r in clean if r["ok"]]; ext = (sum(1 for r in exr if r["right"]) / len(exr)) if exr else None; avg = np.mean([r["secs"] for r in res]); cleared = sum(not r["flagged"] for r in clean)
    k = st.columns(4)
    k[0].markdown(kpi(SV["ok"], "#34D399", f"{rec*100:.0f}%", "Alteration detection rate"), unsafe_allow_html=True); k[1].markdown(kpi(SV["bad"], "#FB7185", f"{fa*100:.0f}%", "False-alarm rate"), unsafe_allow_html=True)
    k[2].markdown(kpi(SV["doc"], "#2DD4BF", f"{acc*100:.0f}%", "Overall validation accuracy"), unsafe_allow_html=True); k[3].markdown(kpi(SV["doc"], "#38BDF8", "n/a" if ext is None else f"{ext*100:.0f}%", "Field-extraction accuracy"), unsafe_allow_html=True)
    st.write("")
    k = st.columns(4)
    k[0].markdown(kpi(SV["clock"], "#A78BFA", f"{avg:.1f} s", "Avg check time per document"), unsafe_allow_html=True); k[1].markdown(kpi(SV["ok"], "#34D399", f"{cleared}/{len(clean)}", "Clean documents auto-cleared"), unsafe_allow_html=True)
    k[2].markdown(kpi(SV["clock"], "#FBBF24", f"{cleared * E['mins']:.0f} min", "Manual time saved (assumed)"), unsafe_allow_html=True); k[3].markdown(kpi(SV["app"], "#2DD4BF", f"{len(res)}", "Documents tested"), unsafe_allow_html=True)
    notice(f"Test set: {len(clean)} clean and {len(alt)} edited synthetic documents. Time saved assumes {E['mins']:.0f} min of manual scrutiny per document and counts only documents that need no human attention. "
           "Results on real scans and photographs will differ. Field-extraction accuracy needs the OCR engine." , "warn")

def page_rules():
    top("Rules & sources", "Configurable checklists, thresholds and (simulated) issuing-authority sources")
    ok = can("rules"); R = ss.rules
    if not ok: notice(f"Read-only for {ss.role}. Only an Administrator can change rules.", "warn")
    with st.form("rules"):
        st.markdown("**Checklists by application category**")
        new_cats = {c: st.multiselect(c, list(DT), default=R["cats"][c], format_func=lambda d: DT[d]["short"], disabled=not ok) for c in R["cats"]}
        st.markdown("**Required undertaking clauses** (one per line; checked against the affidavit by sequence alignment)")
        cl_txt = st.text_area("Clauses", "\n".join(R["clauses"]), height=100, disabled=not ok, label_visibility="collapsed")
        st.markdown("**Validation thresholds**")
        a, b, c = st.columns(3)
        nt = a.slider("Name match threshold", 0.5, 1.0, R["name_thr"], 0.01, disabled=not ok); tt = b.slider("Edit (tamper) score threshold", 2.0, 12.0, R["tamper_thr"], 0.5, disabled=not ok); wd = c.slider("Expiry warning (days)", 0, 365, R["warn_days"], disabled=not ok)
        st.markdown("**Infrastructure norms** (placeholder values: set them from the Approval Process Handbook)")
        a, b, c, d = st.columns(4)
        ml = a.number_input("Min land (acres)", 0.0, 100.0, R["min_land"], disabled=not ok); bp = b.number_input("Min built-up per student (sq m)", 0.0, 50.0, R["builtup_per_student"], disabled=not ok)
        mr = c.number_input("Max students per faculty", 1.0, 60.0, R["max_ratio"], disabled=not ok); mb = d.number_input("Min laboratories", 0, 100, R["min_labs"], disabled=not ok)
        st.markdown("**Issuing-authority sources** (simulated registries)")
        cols = st.columns(3); av = {s: cols[i % 3].checkbox(f"{s} available", value=ss.sources[s], disabled=not ok) for i, s in enumerate(SOURCES)}
        if st.form_submit_button("Save rules", type="primary", disabled=not ok):
            R.update(clauses=[c.strip() for c in cl_txt.splitlines() if c.strip()], name_thr=nt, tamper_thr=tt, warn_days=wd, min_land=ml, builtup_per_student=bp, max_ratio=mr, min_labs=mb, cats=new_cats); ss.sources = av
            audit("-", "Rule applied", f"Rules updated by {ss.role}: name ≥ {nt:.2f}, edit ≥ {tt:.1f}, warning {wd} days; sources down: {[s for s, v in av.items() if not v] or 'none'}"); st.success("Rules saved. New validations will use them.")

def page_help():
    top("Help", "How to use the console and what it does")
    with st.expander("How do I run a validation?", expanded=True): st.write("Open **New validation**, choose an institution and category, pick Demo set A (clean) or B (with issues) or upload your own documents, then press **Run validation**. The report opens with a recommendation, every document's status, evidence-linked findings, compliance checks and the decision panel.")
    with st.expander("What do the verification statuses mean?"): st.write("**Verified**: matches the issuing authority. **Mismatch detected**: the source holds different details. **Expired**: validity has ended. **Verification pending**: the reference could not be read. **Source unavailable**: the source could not be reached. **Manual review required**: no automated source or inconclusive. **Missing**: required document not submitted.")
    with st.expander("What does DocImmune check?"): st.write("Checklist completeness, OCR extraction, expiry and date sanity, name consistency with the institutional record, QR code vs printed details, image alteration (error-level analysis), seal presence, duplicate documents and photos across institutions, issuing-authority records, infrastructure norms and photo quality.")
    with st.expander("Who can do what?"): st.write("**Scrutiny Officer**: validate, rectify, acknowledge alerts, recommend. **Senior Officer**: validate, acknowledge and take the final decision (rejection needs a remark and a review tick). **Administrator**: configure rules and sources, view the audit. **Viewer**: read-only.")
    with st.expander("Is this real data?"): st.write("No. Institutions, documents, registries and QR codes are synthetic. Issuing-authority sources are simulated, and the app does not connect to any restricted database. Findings are preliminary indicators for human verification, never proof of forgery. Final decisions remain with the competent authority.")
    with st.expander("Demo script (3 minutes)"): st.write("1. Dashboard: show the status mix and alerts.  2. New validation → Demo set A → clean result.  3. Demo set B → recommendation Escalate; open the land document: edit map, QR mismatch, registry mismatch.  4. Rectify the fire NOC with the corrected demo document.  5. Switch to Senior Officer and record a decision.  6. Audit trail and Evaluation page.")
    st.caption("DocImmune · prototype by Team ZYMORA for Smart India Hackathon 2026")

# =============================================================== NAVIGATION
init_state()
P_DASH = st.Page(page_dashboard, title="Dashboard", icon=":material/dashboard:", default=True, url_path="dashboard")
P_NEW = st.Page(page_new, title="New validation", icon=":material/add_circle:", url_path="validate")
P_APPS = st.Page(page_apps, title="Applications", icon=":material/folder_open:", url_path="applications")
P_ALERTS = st.Page(page_alerts, title="Alerts", icon=":material/notifications:", url_path="alerts")
P_AUDIT = st.Page(page_audit, title="Audit trail", icon=":material/history:", url_path="audit")
P_EVAL = st.Page(page_eval, title="Evaluation", icon=":material/query_stats:", url_path="evaluation")
P_RULES = st.Page(page_rules, title="Rules & sources", icon=":material/tune:", url_path="rules")
P_HELP = st.Page(page_help, title="Help", icon=":material/help:", url_path="help")
st.logo('<svg xmlns="http://www.w3.org/2000/svg" width="200" height="40" viewBox="0 0 200 40"><path d="M20 3 6 8v10c0 9 6 16 14 19 8-3 14-10 14-19V8z" fill="#14B8A6"/><path d="M14 20l5 5 8-9" fill="none" stroke="#04141A" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/><text x="44" y="27" font-family="Arial" font-weight="800" font-size="20" fill="#E8F3F6">DocImmune</text></svg>', size="large")
pg = st.navigation([P_DASH, P_NEW, P_APPS, P_ALERTS, P_AUDIT, P_EVAL, P_RULES, P_HELP], position="top")
with st.container(key="mobnav"):
    for row in ([(P_DASH, "Home", ":material/dashboard:"), (P_NEW, "Validate", ":material/add_circle:"), (P_APPS, "Apps", ":material/folder_open:"), (P_ALERTS, "Alerts", ":material/notifications:")],
                [(P_AUDIT, "Audit", ":material/history:"), (P_EVAL, "Eval", ":material/query_stats:"), (P_RULES, "Rules", ":material/tune:"), (P_HELP, "Help", ":material/help:")]):
        for col, (p_, lab, ic) in zip(st.columns(4), row): col.page_link(p_, label=lab, icon=ic)
pg.run()
