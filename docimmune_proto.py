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
    out = dict(aadhaar="", pan="", name="", clauses=[])
    if not text: return out
    m = re.search(r"\b([2-9]\d{3})\s?(\d{4})\s?(\d{4})\b", text)
    if m: out["aadhaar"] = " ".join(m.groups())
    m = re.search(r"\b[A-Z]{5}\d{4}[A-Z]\b", text)
    if m: out["pan"] = m.group(0)
    m = re.search(r"Name\s*[:\-]\s*(.+)", text)
    if m: out["name"] = m.group(1).strip()
    for line in text.splitlines():
        line = line.strip()
        if re.search(r"\bshall\b|\bmay be\b", line, re.I):
            out["clauses"].append(re.sub(r"^Clause\s*[\d.]+\s*", "", line, flags=re.I))
    return out

# ---- 3. IMMUNE SCAN: error-level analysis. Edited regions re-compress differently from the rest.
def ela_blocks(img, g=16):
    b = io.BytesIO(); img.convert("RGB").save(b, "JPEG", quality=90); b.seek(0)
    diff = np.asarray(ImageChops.difference(img.convert("RGB"), Image.open(b)).convert("L"), float)
    h, w = diff.shape; bh, bw = max(h // g, 1), max(w // g, 1)
    return np.array([diff[i*bh:(i+1)*bh, j*bw:(j+1)*bw].mean() for i in range(g) for j in range(g)])
def ela_score(img):
    bl = ela_blocks(img)
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
            if m["verdict"] == "ESCALATE" and tamper >= 6:
                return dict(status="family", family=m["family"], case=m["id"], text=f"Matches known forgery family {m['family']} (first seen in case {m['id']}).")
        for dist, m in near:
            if m["verdict"] == "PASS" and tamper >= 6:
                return dict(status="edited_copy", case=m["id"], text=f"Looks like an edited copy of document already approved in case {m['id']}.")
        for dist, m in near:
            if m["verdict"] == "PASS" and m["key"] != key:
                return dict(status="reused", case=m["id"], text=f"Same document was already approved for a different applicant (case {m['id']}).")
            if m["key"] == key:
                return dict(status="resubmission", case=m["id"], text=f"Same applicant resubmitted this document (earlier case {m['id']}).")
        return dict(status="new", text="New document: not seen before.")
    def add(self, h, key, case_id, verdict, mem, tamper=0):
        fam = None
        if verdict == "ESCALATE" and tamper >= 6:
            fam = mem.get("family")
            if not fam: self.families += 1; fam = f"F-{self.families}"
        self.items.append(dict(hash=h, key=key, id=case_id, verdict=verdict, family=fam))
        return fam

# ---- 6. RISK ENGINE
def verify(app, doc_img, doc_clauses, reg=REG_DEFAULT, memory=None, ocr=None):
    rep = {}
    rep["aadhaar"] = aadhaar_ok(app["aadhaar"]); rep["pan"] = pan_ok(app["pan"])
    rep["name_match"] = round(name_match(app["name"], app["name_on_doc"]), 2)
    t, _ = ela_score(doc_img); rep["tamper_score"] = round(t, 2)
    al = clause_align(doc_clauses, reg); rep["clauses"] = al
    rep["missing_or_mutated"] = [r for r, s in al if s < 0.85]
    # details written on the document (OCR) must match the form
    rep["ocr_checked"] = bool(ocr and (ocr.get("aadhaar") or ocr.get("pan")))
    rep["details_match"] = True
    if rep["ocr_checked"]:
        if ocr.get("aadhaar") and _digits(ocr["aadhaar"]) != _digits(app["aadhaar"]): rep["details_match"] = False
        if ocr.get("pan") and ocr["pan"].upper() != app["pan"].upper(): rep["details_match"] = False
    key = _digits(app["aadhaar"]) or app["name"].lower()
    h = dhash(doc_img); rep["hash"] = h; rep["key"] = key
    rep["memory"] = memory.check(h, key, t) if memory else dict(status="new", text="Memory not used.")
    ms = rep["memory"]["status"]
    risk = (0.25 * (not rep["aadhaar"]) + 0.15 * (not rep["pan"]) + 0.2 * (rep["name_match"] < 0.9) + 0.3 * min(t / 10, 1)
            + 0.1 * min(len(rep["missing_or_mutated"]) / 3, 1) + 0.2 * (not rep["details_match"])
            + {"family": 0.3, "edited_copy": 0.3, "reused": 0.25}.get(ms, 0))
    rep["risk"] = round(min(risk, 1.0), 2)
    rep["verdict"] = "PASS" if rep["risk"] < 0.2 else "REVIEW" if rep["risk"] < 0.5 else "ESCALATE"
    return rep
