"""DocImmune prototype - working core: validation + immune (ELA) tamper scan + clause alignment + verdict."""
import sys, io, re, difflib, json
from PIL import Image, ImageChops
import numpy as np
from Bio import Align

# ---- 1. VALIDATION: Aadhaar (Verhoeff checksum), PAN format, cross-document name match
_d=[[0,1,2,3,4,5,6,7,8,9],[1,2,3,4,0,6,7,8,9,5],[2,3,4,0,1,7,8,9,5,6],[3,4,0,1,2,8,9,5,6,7],[4,0,1,2,3,9,5,6,7,8],[5,9,8,7,6,0,4,3,2,1],[6,5,9,8,7,1,0,4,3,2],[7,6,5,9,8,2,1,0,4,3],[8,7,6,5,9,3,2,1,0,4],[9,8,7,6,5,4,3,2,1,0]]
_p=[[0,1,2,3,4,5,6,7,8,9],[1,5,7,6,2,8,3,0,9,4],[5,8,0,3,7,9,6,1,4,2],[8,9,1,6,0,4,3,5,2,7],[9,4,5,3,1,2,6,8,7,0],[4,2,8,6,5,7,3,9,0,1],[2,7,9,3,8,0,6,4,1,5],[7,0,4,6,9,1,3,2,5,8]]
def aadhaar_ok(n):
    n=re.sub(r"\s","",n)
    if not re.fullmatch(r"[2-9]\d{11}",n): return False
    c=0
    for i,ch in enumerate(reversed(n)): c=_d[c][_p[i%8][int(ch)]]
    return c==0
def pan_ok(p): return bool(re.fullmatch(r"[A-Z]{5}\d{4}[A-Z]",p))
def name_match(a,b): return difflib.SequenceMatcher(None,a.lower(),b.lower()).ratio()

# ---- 2. IMMUNE SCAN: error-level analysis -> tamper score (edited regions re-compress differently)
def ela_score(img):
    buf=io.BytesIO(); img.convert("RGB").save(buf,"JPEG",quality=90); buf.seek(0)
    diff=np.asarray(ImageChops.difference(img.convert("RGB"),Image.open(buf)).convert("L"),float)
    h,w=diff.shape; bh,bw=max(h//8,1),max(w//8,1)
    blocks=np.array([diff[i:i+bh,j:j+bw].mean() for i in range(0,h-bh+1,bh) for j in range(0,w-bw+1,bw)])
    return float((blocks.max()-np.median(blocks))/(blocks.mean()+1e-6)), blocks

# ---- 3. DNA ALIGNMENT: Smith-Waterman local alignment of document clauses vs regulation clauses
def clause_align(doc,reg):
    al=Align.PairwiseAligner(); al.mode="local"; al.match_score=2; al.mismatch_score=-1; al.open_gap_score=-2; al.extend_gap_score=-1
    out=[]
    for rid,rtxt in reg.items():
        best=max((al.score(rtxt.lower(),d.lower())/(2*len(rtxt)) for d in doc),default=0)
        out.append((rid,round(best,2)))
    return out

REG_DEFAULT={"4.1":"applicant shall hold valid licence","4.2":"licence shall be renewed every five years","4.3":"records shall be retained for three years"}

def verify(app,doc_img,doc_clauses,reg):
    rep={}
    rep["aadhaar"]=aadhaar_ok(app["aadhaar"]); rep["pan"]=pan_ok(app["pan"])
    rep["name_match"]=round(name_match(app["name"],app["name_on_doc"]),2)
    t,_=ela_score(doc_img); rep["tamper_score"]=round(t,2)
    al=clause_align(doc_clauses,reg); rep["clauses"]=al
    missing=[r for r,s in al if s<0.85]; rep["missing_or_mutated"]=missing
    risk=0.25*(not rep["aadhaar"])+0.15*(not rep["pan"])+0.2*(rep["name_match"]<0.9)+0.3*min(t/10,1)+0.1*min(len(missing)/3,1)
    rep["risk"]=round(risk,2); rep["verdict"]="PASS" if risk<0.2 else "REVIEW" if risk<0.5 else "ESCALATE"
    return rep
