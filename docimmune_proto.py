"""DocImmune core engine: validation, OCR, tamper scan, Document-DNA alignment, document memory and risk verdict."""
import io, re, difflib
import numpy as np
from PIL import Image, ImageChops
from Bio import Align

REG_DEFAULT = {"4.1": "applicant shall hold valid licence", "4.2": "licence shall be renewed every five years", "4.3": "records shall be retained for three years"}

# ---- 1. VALIDATION: Aadhaar (Verhoeff checksum), PAN format, name similarity
_d = [[0,1,2,3,4,5,6,7,8,9],[1,2,3,4,0,6,7,8,9,5],[2,3,4,0,1,7,8,9,5,6],[3,4,0,1,2,8,9,5,6,7],[4,0,1,2,3,9,5,6,7,8],[5,9,8,7,6,0,4,3,2,1],[6,5,9,8,7,1,0,4,3,2],[7,6,5,9,8,2,1,0,4,3],[8,7,6,5,9,3,2,1,0,4],[9,8,7,6,5,4,3,2,1,0]]
_p = [[0,1,2,3,4,5,6,7,8,9],[1,5,7,6,2,8,3,0,9,4],[5,8,0,3,7,9,6,1,4,2],[8,9,1,6,0,4,3,5,2,7],[9,4,5,3,1,2,6,8,7,0],[4,2,8,6,5,7,3,9,0,1],[2,7,9,3,8,0,6,4,1,5],[7,0,4,6,9,1,3,2,5,8]]
def aadhaar_ok(n):
    n = re.sub(r"\s", "", n)
    if not re.fullmatch(r"[2-9]\d{11}", n): return False
    c = 0
    for i, ch in enumerate(reversed(n)): c = _d[c][_p[i % 8][int(ch)]]
    return c == 0
def pan_ok(p): return bool(re.fullmatch(r"[A-Z]{5}\d{4}[A-Z]", p))
def name_match(a, b): return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()
def _digits(s): return re.sub(r"\D", "", s or "")

# ---- 2. OCR: read the document text (needs the Tesseract engine; returns None if unavailable)
def ocr_read(img):
    try:
        import pytesseract
        return pytesseract.image_to_string(img.convert("RGB"))
    except Exception:
        return None

def parse_fields(text):
    """Pull Aadhaar, PAN, name and clause lines out of OCR text."""
    out = dict(aadhaar="", pan="", name="", licence="", clauses=[])
    if not text: return out
    m = re.search(r"\b([2-9]\d{3})\s?(\d{4})\s?(\d{4})\b", text)
    if m: out["aadhaar"] = " ".join(m.groups())
    m = re.search(r"\b[A-Z]{5}\d{4}[A-Z]\b", text)
    if m: out["pan"] = m.group(0)
    m = re.search(r"Licen[cs]e\s*No\s*[:\-]?\s*([A-Z0-9/\-]+)", text, re.I)
    if m: out["licence"] = m.group(1).strip()
    m = re.search(r"Name\s*[:\-]\s*(.+)", text)
    if m: out["name"] = m.group(1).strip()
    for line in text.splitlines():
        line = line.strip()
        if re.search(r"\bshall\b|\bmay be\b", line, re.I):
            out["clauses"].append(re.sub(r"^Clause\s*[\d.]+\s*", "", line, flags=re.I))
    return out

# ---- 2b. QR + SEAL: the QR on a genuine licence carries its details; they must match what is printed
def qr_locate(img):
    """Decode a QR code if present. Returns (payload or None, bounding box or None)."""
    try:
        import cv2
        arr = cv2.cvtColor(np.asarray(img.convert("RGB")), cv2.COLOR_RGB2GRAY)
        det = cv2.QRCodeDetector()
        for scale in (1.0, 2.0):
            a = arr if scale == 1.0 else cv2.resize(arr, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
            txt, pts, _ = det.detectAndDecode(a)
            if pts is not None:
                p = pts.reshape(-1, 2) / scale
                box = (int(p[:, 0].min()), int(p[:, 1].min()), int(p[:, 0].max()), int(p[:, 1].max()))
                if txt: return txt, box
    except Exception:
        pass
    return None, None

def qr_read(img): return qr_locate(img)[0]

def parse_qr(txt):
    d = {}
    for part in (txt or "").split("|")[1:]:
        if ":" in part:
            k, v = part.split(":", 1); d[k.strip().upper()] = v.strip()
    return d

def seal_locate(img):
    """Look for a round, coloured stamp (red or blue ring). Returns bounding box or None."""
    try:
        import cv2
        bgr = cv2.cvtColor(np.asarray(img.convert("RGB")), cv2.COLOR_RGB2BGR)
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, (0, 90, 70), (10, 255, 255)) | cv2.inRange(hsv, (170, 90, 70), (180, 255, 255)) | cv2.inRange(hsv, (100, 90, 70), (130, 255, 255))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in cnts:
            area = cv2.contourArea(c); per = cv2.arcLength(c, True)
            if area > 1500 and per > 0 and 4 * np.pi * area / (per * per) > 0.6:
                x, y, w, h = cv2.boundingRect(c); return (x, y, x + w, y + h)
    except Exception:
        pass
    return None

def seal_present(img): return seal_locate(img) is not None

def qr_check(app, ocr, payload):
    """Compare QR contents with the form and the printed text."""
    if not payload: return dict(status="absent", issues=[], text="No QR code found on this document.")
    q = parse_qr(payload); issues = []
    if not q: return dict(status="mismatch", issues=["unreadable"], text="A QR code was found but it is not a DocImmune / licence QR.")
    last4 = _digits(app["aadhaar"])[-4:]
    if q.get("AAD4") and last4 and q["AAD4"] != last4: issues.append("Aadhaar")
    if ocr and ocr.get("aadhaar") and q.get("AAD4") and _digits(ocr["aadhaar"])[-4:] != q["AAD4"]: issues.append("Aadhaar on document")
    if q.get("LIC") and ocr and ocr.get("licence") and q["LIC"].upper() != ocr["licence"].upper(): issues.append("Licence number")
    if q.get("NAME") and name_match(q["NAME"], app["name_on_doc"]) < 0.9: issues.append("Name")
    issues = list(dict.fromkeys(issues))
    if issues: return dict(status="mismatch", issues=issues, text="QR code disagrees with the printed details: " + ", ".join(issues) + ".")
    return dict(status="match", issues=[], text="QR code details match the printed document.")

# ---- 3. IMMUNE SCAN: error-level analysis. Edited regions re-compress differently from the rest.
def ela_blocks(img, g=16, skip=()):
    b = io.BytesIO(); img.convert("RGB").save(b, "JPEG", quality=90); b.seek(0)
    diff = np.asarray(ImageChops.difference(img.convert("RGB"), Image.open(b)).convert("L"), float)
    for (x0, y0, x1, y1) in skip:  # QR codes and seals are machine-printed, not edited text
        diff[max(y0 - 10, 0):y1 + 10, max(x0 - 10, 0):x1 + 10] = 0
    h, w = diff.shape; bh, bw = max(h // g, 1), max(w // g, 1)
    return np.array([diff[i*bh:(i+1)*bh, j*bw:(j+1)*bw].mean() for i in range(g) for j in range(g)])
def ela_score(img, skip=()):
    bl = ela_blocks(img, skip=skip)
    return float((bl.max() - np.median(bl)) * 5), bl

# ---- 4. DOCUMENT DNA: Smith-Waterman local alignment of clauses vs regulation text
def clause_align(doc, reg):
    al = Align.PairwiseAligner(); al.mode = "local"; al.match_score = 2; al.mismatch_score = -1; al.open_gap_score = -2; al.extend_gap_score = -1
    return [(rid, round(max((al.score(rtxt.lower(), d.lower()) / (2 * len(rtxt)) for d in doc), default=0), 2)) for rid, rtxt in reg.items()]

# ---- 5. MEMORY: remembers every document (perceptual hash) to spot reuse, edited copies and forgery families
def dhash(img, size=8):
    g = np.asarray(img.convert("L").resize((size + 1, size), Image.LANCZOS), float)
    return int("".join("1" if v else "0" for v in (g[:, 1:] > g[:, :-1]).flatten()), 2)
def hamming(a, b): return bin(a ^ b).count("1")

class Memory:
    def __init__(self): self.items = []; self.families = 0
    def check(self, h, key, tamper):
        near = [(hamming(h, m["hash"]), m) for m in self.items if hamming(h, m["hash"]) <= 6]
        near.sort(key=lambda x: x[0])
        for dist, m in near:
            if m["verdict"] == "ESCALATE" and tamper >= 5:
                return dict(status="family", family=m["family"], case=m["id"], text=f"Matches known forgery family {m['family']} (first seen in case {m['id']}).")
        for dist, m in near:
            if m["verdict"] == "PASS" and tamper >= 5:
                return dict(status="edited_copy", case=m["id"], text=f"Looks like an edited copy of document already approved in case {m['id']}.")
        for dist, m in near:
            if m["verdict"] == "PASS" and m["key"] != key:
                return dict(status="reused", case=m["id"], text=f"Same document was already approved for a different applicant (case {m['id']}).")
            if m["key"] == key:
                return dict(status="resubmission", case=m["id"], text=f"Same applicant resubmitted this document (earlier case {m['id']}).")
        return dict(status="new", text="New document: not seen before.")
    def add(self, h, key, case_id, verdict, mem, tamper=0):
        fam = None
        if verdict == "ESCALATE" and tamper >= 5:
            fam = mem.get("family")
            if not fam: self.families += 1; fam = f"F-{self.families}"
        self.items.append(dict(hash=h, key=key, id=case_id, verdict=verdict, family=fam))
        return fam

# ---- 6. RISK ENGINE
def verify(app, doc_img, doc_clauses, reg=REG_DEFAULT, memory=None, ocr=None):
    rep = {}
    rep["aadhaar"] = aadhaar_ok(app["aadhaar"]); rep["pan"] = pan_ok(app["pan"])
    rep["name_match"] = round(name_match(app["name"], app["name_on_doc"]), 2)
    payload, qbox = qr_locate(doc_img); sbox = seal_locate(doc_img)
    t, _ = ela_score(doc_img, skip=[b for b in (qbox, sbox) if b]); rep["tamper_score"] = round(t, 2)
    al = clause_align(doc_clauses, reg); rep["clauses"] = al
    rep["missing_or_mutated"] = [r for r, s in al if s < 0.85]
    # details written on the document (OCR) must match the form
    rep["ocr_checked"] = bool(ocr and (ocr.get("aadhaar") or ocr.get("pan")))
    rep["details_match"] = True
    if rep["ocr_checked"]:
        if ocr.get("aadhaar") and _digits(ocr["aadhaar"]) != _digits(app["aadhaar"]): rep["details_match"] = False
        if ocr.get("pan") and ocr["pan"].upper() != app["pan"].upper(): rep["details_match"] = False
    rep["qr"] = qr_check(app, ocr, payload); rep["seal"] = sbox is not None; rep["skip"] = [b for b in (qbox, sbox) if b]
    key = _digits(app["aadhaar"]) or app["name"].lower()
    h = dhash(doc_img); rep["hash"] = h; rep["key"] = key
    rep["memory"] = memory.check(h, key, t) if memory else dict(status="new", text="Memory not used.")
    ms = rep["memory"]["status"]
    risk = (0.25 * (not rep["aadhaar"]) + 0.15 * (not rep["pan"]) + 0.2 * (rep["name_match"] < 0.9) + 0.3 * min(t / 10, 1)
            + 0.1 * min(len(rep["missing_or_mutated"]) / 3, 1) + 0.2 * (not rep["details_match"])
            + {"family": 0.3, "edited_copy": 0.3, "reused": 0.25}.get(ms, 0)
            + 0.3 * (rep["qr"]["status"] == "mismatch") + 0.05 * (not rep["seal"]))
    rep["risk"] = round(min(risk, 1.0), 2)
    rep["verdict"] = "PASS" if rep["risk"] < 0.2 else "REVIEW" if rep["risk"] < 0.5 else "ESCALATE"
    return rep
