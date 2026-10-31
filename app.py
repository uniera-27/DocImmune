import io, html
from datetime import datetime, timedelta, timezone
import numpy as np
import streamlit as st
from PIL import Image, ImageChops, ImageDraw, ImageFont
from docimmune_proto import verify, REG_DEFAULT, Memory, ocr_read, parse_fields

st.set_page_config(page_title="DocImmune", page_icon="🛡️", layout="wide", initial_sidebar_state="collapsed")

# =========================================================== STYLE
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');
html, body, .stApp, h1, h2, h3, h4, p, label, li, button, input, textarea, [data-testid="stMarkdownContainer"]{font-family:'Manrope',sans-serif}
footer{visibility:hidden}
[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"],[data-testid="stExpandSidebarButton"]{display:none}
.block-container{padding:4.2rem 2.6rem 3rem;max-width:1180px}
@media(max-width:640px){.block-container{padding:4.2rem 1rem 3rem}.hero{padding:22px}.stp{flex-direction:column}}
h1,h2,h3{letter-spacing:-.02em}
.ph{margin-bottom:22px}.ph h1{font-size:1.9rem;font-weight:800;margin:0;color:#0B2A2E}.ph p{margin:4px 0 0;color:#587378}
.card{background:#fff;border:1px solid #DCE9E8;border-radius:18px;padding:22px;box-shadow:0 2px 10px rgba(27,31,59,.04)}
.card h4{margin:0 0 14px;font-size:1rem;font-weight:700;color:#0B2A2E}
.kpi{display:flex;gap:14px;align-items:center;background:#fff;border:1px solid #DCE9E8;border-radius:18px;padding:18px;box-shadow:0 2px 10px rgba(27,31,59,.04)}
.kpi .ic{width:46px;height:46px;border-radius:13px;display:grid;place-items:center;font-size:1.3rem;flex:none}
.kpi b{display:block;font-size:1.7rem;line-height:1.1;color:#0B2A2E}.kpi span{color:#587378;font-size:.85rem}
.hero{background:linear-gradient(120deg,#0B3C49 0%,#0F766E 65%,#14B8A6 130%);border-radius:22px;padding:30px 32px;color:#fff;margin-bottom:20px}
.hero h1{margin:0;font-size:1.8rem;font-weight:800;color:#fff}.hero p{margin:6px 0 0;opacity:.92;max-width:620px}
.row{display:flex;align-items:center;gap:12px;padding:12px 0;border-bottom:1px solid #E8F0F0}.row:last-child{border:0}
.av{width:38px;height:38px;border-radius:50%;background:#DDF3F0;color:#0F766E;display:grid;place-items:center;font-weight:700;flex:none}
.row .n{font-weight:600;color:#0B2A2E}.row .m{font-size:.8rem;color:#587378}.row .r{margin-left:auto;text-align:right}
.pill{padding:3px 11px;border-radius:20px;font-weight:700;font-size:.75rem;display:inline-block}
.p-PASS{background:#DDF6EA;color:#0E8F57}.p-REVIEW{background:#FFF0D1;color:#B26A00}.p-ESCALATE{background:#FFE1E4;color:#C62A3B}.p-NONE{background:#E8F0F0;color:#587378}
.tag{font-size:.68rem;background:#E8F0F0;color:#587378;border-radius:6px;padding:1px 7px;margin-left:6px}
.stp{display:flex;gap:10px;margin-bottom:22px}.stp div{flex:1;background:#fff;border:1px solid #DCE9E8;border-radius:14px;padding:12px 14px;color:#8AA3A6;font-weight:600;display:flex;gap:10px;align-items:center}
.stp b{width:28px;height:28px;border-radius:50%;background:#E8F0F0;color:#587378;display:grid;place-items:center;flex:none;font-size:.85rem}
.stp .on{border-color:#0F766E;color:#0B2A2E;box-shadow:0 4px 14px rgba(15,118,110,.18)}.stp .on b{background:#0F766E;color:#fff}
.stp .done b{background:#12B76A;color:#fff}.stp .done{color:#0B2A2E}
.tip{background:#E6F6F4;border-radius:12px;padding:12px 16px;color:#0F5F58;margin:6px 0 16px;font-size:.92rem}
.vc{border-radius:20px;padding:26px;color:#fff;text-align:center}
.vc h2{margin:10px 0 2px;color:#fff;font-weight:800}.vc p{margin:0;opacity:.95}
.v-PASS{background:linear-gradient(145deg,#0E9F6E,#34D399)}.v-REVIEW{background:linear-gradient(145deg,#D97706,#FBBF24)}.v-ESCALATE{background:linear-gradient(145deg,#C81E3A,#FB7185)}
.ck{display:flex;gap:14px;align-items:flex-start;padding:13px 0;border-bottom:1px solid #E8F0F0}.ck:last-child{border:0}
.ck .b{width:30px;height:30px;border-radius:9px;display:grid;place-items:center;flex:none;font-weight:800}
.ok{background:#DDF6EA;color:#0E8F57}.bad{background:#FFE1E4;color:#C62A3B}
.ck .t{font-weight:700;color:#0B2A2E}.ck .d{color:#587378;font-size:.88rem}
div.stButton>button{border-radius:12px;font-weight:700;padding:.55rem 1.2rem}
div.stButton>button[kind="primary"]{background:#0F766E;border:0;color:#fff}
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea,[data-baseweb="select"]>div{border-radius:12px}
.st-key-mobnav{display:none}
@media(max-width:900px){.st-key-mobnav{display:block;margin-bottom:10px}}
</style>
""", unsafe_allow_html=True)

# =========================================================== HELPERS
NOW = lambda: datetime.now(timezone(timedelta(hours=5, minutes=30)))
GOOD = "The applicant shall hold a valid licence\nLicence shall be renewed every five years\nRecords shall be retained for three years"
BAD = "The applicant shall hold a valid licence\nLicence may be renewed at any time"
DOC_TYPES = ["Food safety licence", "Pharma licence", "Scholarship certificate", "Identity + address proof", "Other"]
VTXT = {"PASS": ("Looks genuine", "Safe to approve. No problems found."),
        "REVIEW": ("Needs a human look", "Some details don't add up. An officer should check."),
        "ESCALATE": ("High risk", "Strong signs of editing or wrong details. Send to a senior officer.")}
VICON = {"PASS": "✓", "REVIEW": "!", "ESCALATE": "✕"}

def sample_img(forged):
    rng = np.random.default_rng(1)
    F = ImageFont.load_default(size=20); FB = ImageFont.load_default(size=28); FS = ImageFont.load_default(size=11)
    im = Image.new("RGB", (900, 620), (250, 248, 240)); d = ImageDraw.Draw(im)
    d.text((60, 30), "FOOD SAFETY LICENCE", fill=(20, 40, 90), font=FB)
    lines = ["Name: Priya Raman", "Aadhaar: 2341 2341 2346", "PAN: ABCDE1234F", "Licence No: FSS/TN/2026/0457", "Valid upto: 2029",
             "Clause 4.1 The applicant shall hold a valid licence", "Clause 4.2 Licence shall be renewed every five years",
             "Clause 4.3 Records shall be retained for three years"]
    for i, t in enumerate(lines): d.text((60, 100 + i * 58), t, fill=(30, 30, 30), font=F)
    for y in range(580, 610, 12): d.text((60, y), "This certificate is issued under the Food Safety and Standards Act", fill=(120, 120, 120), font=FS)
    arr = np.asarray(im).astype(int) + rng.integers(-6, 7, (620, 900, 3))
    im = Image.fromarray(arr.clip(0, 255).astype("uint8"))
    b = io.BytesIO(); im.save(b, "JPEG", quality=90); b.seek(0); im = Image.open(b).convert("RGB")
    if forged:  # edited after the original was saved: Aadhaar digits and clause 4.2 pasted over
        d = ImageDraw.Draw(im)
        for y, t in ((158, "Aadhaar: 2341 2341 2347"), (448, "Clause 4.2 Licence may be renewed at any time")):
            d.rectangle((55, y - 4, 800, y + 30), fill=(250, 248, 240)); d.text((60, y), t, fill=(30, 30, 30), font=F)
    return im

@st.cache_data(show_spinner=False)
def read_doc(png_bytes):
    """OCR once per image. Returns (available, parsed fields)."""
    txt = ocr_read(Image.open(io.BytesIO(png_bytes)))
    return (txt is not None), parse_fields(txt)

def img_bytes(img):
    b = io.BytesIO(); img.save(b, "PNG"); return b.getvalue()

def heatmap(img):
    b = io.BytesIO(); img.convert("RGB").save(b, "JPEG", quality=90); b.seek(0)
    diff = ImageChops.difference(img.convert("RGB"), Image.open(b)).convert("L")
    return Image.fromarray(np.clip(np.asarray(diff, float) * 25, 0, 255).astype("uint8"))

SV = {'doc': '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 13h8M8 17h5"/></svg>', 'ok': '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="m8 12 3 3 5-6"/></svg>', 'warn': '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4M12 17h.01"/></svg>', 'bad': '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7.9 2h8.2L22 7.9v8.2L16.1 22H7.9L2 16.1V7.9z"/><path d="m15 9-6 6M9 9l6 6"/></svg>'}

def head(title, sub):
    st.markdown(f'<div class="ph"><h1>{title}</h1><p>{sub}</p></div>', unsafe_allow_html=True)

def kpi(icon, bg, val, label):
    return f'<div class="kpi"><div class="ic" style="background:{bg}">{icon}</div><div><b>{val}</b><span>{label}</span></div></div>'

def gauge(risk, verdict):
    col = {"PASS": "#fff", "REVIEW": "#fff", "ESCALATE": "#fff"}[verdict]
    C = 2 * 3.14159 * 54
    return (f'<svg width="150" height="150" viewBox="0 0 140 140"><circle cx="70" cy="70" r="54" fill="none" stroke="rgba(255,255,255,.28)" stroke-width="12"/>'
            f'<circle cx="70" cy="70" r="54" fill="none" stroke="{col}" stroke-width="12" stroke-linecap="round" stroke-dasharray="{C*min(risk,1)} {C}" transform="rotate(-90 70 70)"/>'
            f'<text x="70" y="68" text-anchor="middle" font-size="30" font-weight="800" fill="#fff">{int(round(risk*100))}</text>'
            f'<text x="70" y="88" text-anchor="middle" font-size="11" fill="#fff" opacity=".9">RISK / 100</text></svg>')

def seed():
    t = NOW()
    mk = lambda i, who, doc, v, risk, iss, mins: dict(id=f"A-{10470+i}", who=who, doc=doc, verdict=v, risk=risk, issues=iss, decision="Approved" if v == "PASS" else "Pending",
                                                    time=t - timedelta(minutes=mins), sample=True, checks=None)
    return [mk(4, "Meena R", "Pharma licence", "PASS", .08, [], 35), mk(3, "Karthik S", "Food safety licence", "ESCALATE", .78, ["Edited image", "Clauses"], 80),
            mk(2, "Anita Sharma", "Identity + address proof", "REVIEW", .31, ["Name"], 190), mk(1, "Rahul Menon", "Scholarship certificate", "PASS", .05, [], 400)]

ss = st.session_state
ss.setdefault("mem", Memory()); ss.setdefault("queue", seed()); ss.setdefault("step", 1); ss.setdefault("result", None); ss.setdefault("open", None)
ss.setdefault("S", dict(nm="", nd="", ad="", pn="", doc=DOC_TYPES[0], src="Genuine sample"))

def checks_for(r):
    extra = []
    if r.get("ocr_checked"):
        extra.append((r["details_match"], "Form matches the document", "Aadhaar and PAN read from the document match the form." if r["details_match"] else "Aadhaar or PAN printed on the document differs from the form."))
    m = r.get("memory", {})
    if m:
        extra.append((m.get("status") in ("new", "resubmission"), "Not a copied or reused document", m.get("text", "")))
    return [(r["aadhaar"], "Aadhaar number", "Passes the official checksum rule." if r["aadhaar"] else "Fails the checksum. Likely a typing error or a made-up number."),
            (r["pan"], "PAN format", "Format is valid." if r["pan"] else "Wrong format. It should look like ABCDE1234F."),
            (r["name_match"] >= .9, "Name matches the form", f"Form and document match {int(r['name_match']*100)}%."),
            (r["tamper_score"] < 6, "Image not edited", "No edited area found." if r["tamper_score"] < 6 else "An area of the image looks edited."),
            (not r["missing_or_mutated"], "Rules and clauses", "All regulation clauses found." if not r["missing_or_mutated"] else "Missing or changed: " + ", ".join(r["missing_or_mutated"]) + ".")] + extra


def pill(v): return f'<span class="pill p-{v}">{v}</span>'

def report_html(r):
    rows = "".join(f"<tr><td>{'PASS' if ok else 'FAIL'}</td><td><b>{t}</b><br>{d}</td></tr>" for ok, t, d in checks_for(r))
    return (f"<html><body style='font-family:Arial;max-width:720px;margin:30px auto'><h1>DocImmune verification report</h1>"
            f"<p>Case {r['id']} · {html.escape(r['who'])} · {r['doc']} · {r['time']:%d %b %Y %H:%M}</p><h2>{r['verdict']} · risk {int(r['risk']*100)}/100</h2>"
            f"<table border='1' cellpadding='8' cellspacing='0' width='100%'>{rows}</table><p>Officer decision: <b>{r['decision']}</b></p>"
            f"<p style='color:#666'>Generated by DocImmune. The AI flags; the officer decides.</p></body></html>").encode()

def decide(r, d):
    r["decision"] = d
    r.setdefault("log", []).append((NOW(), f"Officer decision: {d}"))

def report(r, key):
    a, b = st.columns([1, 1.5], gap="large")
    with a:
        t, m = VTXT[r["verdict"]]
        st.markdown(f'<div class="vc v-{r["verdict"]}">{gauge(r["risk"], r["verdict"])}<h2>{r["verdict"]} · {t}</h2><p>{m}</p></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="tip" style="margin-top:14px">Case <b>{r["id"]}</b> · {r["doc"]}<br>Applicant: <b>{html.escape(r["who"])}</b></div>', unsafe_allow_html=True)
    with b:
        if r.get("aadhaar") is None:
            st.markdown('<div class="card"><h4>What we checked</h4><div class="d">Detailed checks are not stored for sample cases.</div></div>', unsafe_allow_html=True)
        else:
            body = "".join(f'<div class="ck"><div class="b {"ok" if ok else "bad"}">{"✓" if ok else "✕"}</div><div><div class="t">{t}</div><div class="d">{d}</div></div></div>' for ok, t, d in checks_for(r))
            st.markdown(f'<div class="card"><h4>What we checked</h4>{body}</div>', unsafe_allow_html=True)
    st.write("")
    st.markdown(f'**Officer decision:** {pill(r["decision"].upper()) if r["decision"] in ("PASS","REVIEW","ESCALATE") else r["decision"]}')
    d1, d2, d3, d4 = st.columns([1, 1, 1.3, 1.6])
    d1.button("Approve", icon=":material/check_circle:", key=f"ap{key}", on_click=decide, args=(r, "Approved"))
    d2.button("Reject", icon=":material/block:", key=f"rj{key}", on_click=decide, args=(r, "Rejected"))
    d3.button("Ask for more info", icon=":material/mail:", key=f"mi{key}", on_click=decide, args=(r, "More info requested"))
    if r.get("aadhaar") is not None:
        d4.download_button("Download report", report_html(r), icon=":material/download:", file_name=f"{r['id']}_report.html", mime="text/html", key=f"dl{key}")
    if r.get("images"):
        with st.expander("See the image scan"):
            c1, c2 = st.columns(2)
            c1.image(r["images"][0], caption="Document", width="stretch"); c2.image(r["images"][1], caption="Edit map: bright = edited", width="stretch")
    if r.get("log"):
        with st.expander("Activity log"):
            for t, ev in r["log"]:
                st.write(f"`{t:%d %b %H:%M:%S}`  {ev}")
    st.caption("The AI only flags. The officer always makes the final decision.")

# =========================================================== PAGES
def page_dashboard():
    q = ss.queue; h = NOW().hour
    greet = "Good morning" if h < 12 else "Good afternoon" if h < 17 else "Good evening"
    st.markdown(f'<div class="hero"><h1>{greet}, Officer</h1><p>DocImmune checks IDs, certificates and licences, spots edits, and tells you what to do next.</p></div>', unsafe_allow_html=True)
    a, b = st.columns([1.6, 4]); a.button("New verification", type="primary", icon=":material/add:", on_click=lambda: st.switch_page(P_VERIFY))
    k = st.columns(4)
    k[0].markdown(kpi(SV["doc"], "#DDF3F0;color:#0F766E", len(q), "Total checked"), unsafe_allow_html=True)
    k[1].markdown(kpi(SV["ok"], "#DDF6EA;color:#0E8F57", sum(x["verdict"] == "PASS" for x in q), "Looks genuine"), unsafe_allow_html=True)
    k[2].markdown(kpi(SV["warn"], "#FFF0D1;color:#B26A00", sum(x["verdict"] == "REVIEW" for x in q), "Need review"), unsafe_allow_html=True)
    k[3].markdown(kpi(SV["bad"], "#FFE1E4;color:#C62A3B", sum(x["verdict"] == "ESCALATE" for x in q), "High risk"), unsafe_allow_html=True)
    st.write("")
    l, r = st.columns([1.7, 1], gap="large")
    rows = "".join(f'<div class="row"><div class="av">{x["who"][0]}</div><div><div class="n">{html.escape(x["who"])}{"<span class=tag>sample</span>" if x["sample"] else ""}</div>'
                   f'<div class="m">{x["doc"]} · {x["time"]:%d %b, %H:%M}</div></div><div class="r">{pill(x["verdict"])}<div class="m">risk {int(x["risk"]*100)}/100</div></div></div>' for x in q[:5])
    l.markdown(f'<div class="card"><h4>Recent activity</h4>{rows}</div>', unsafe_allow_html=True)
    n = max(len(q), 1)
    bars = "".join(f'<div style="margin:12px 0"><div style="display:flex;justify-content:space-between;font-size:.85rem"><span>{v.title()}</span><b>{c}</b></div>'
                   f'<div style="height:9px;background:#E8F0F0;border-radius:6px;overflow:hidden"><div style="width:{c/n*100}%;height:100%;background:{col}"></div></div></div>'
                   for v, col in (("PASS", "#12B76A"), ("REVIEW", "#F59E0B"), ("ESCALATE", "#EF4455")) for c in [sum(x["verdict"] == v for x in q)])
    r.markdown(f'<div class="card"><h4>Risk overview</h4>{bars}<div class="tip" style="margin:16px 0 0">Tip: press <b>New verification</b> and try a sample document in under a minute.</div></div>', unsafe_allow_html=True)

def fill_sample(kind):
    bad = kind == "forged"
    ss.S.update(nm="Priya Raman", nd="Priya R" if bad else "Priya Raman", ad="2341 2341 2347" if bad else "2341 2341 2346", pn="ABCDE1234F", src="Forged sample" if bad else "Genuine sample")
    for k, v in dict(w_nm=ss.S["nm"], w_nd=ss.S["nd"], w_ad=ss.S["ad"], w_pn=ss.S["pn"]).items(): ss[k] = v

def page_verify():
    head("New verification", "Three quick steps. We'll tell you whether the document can be trusted.")
    step = ss.step
    lab = ["Applicant details", "Add document", "Result"]
    st.markdown('<div class="stp">' + "".join(f'<div class="{"on" if i == step else "done" if i < step else ""}"><b>{"✓" if i < step else i}</b>{t}</div>' for i, t in enumerate(lab, 1)) + "</div>", unsafe_allow_html=True)
    S = ss.S
    if step == 1:
        st.markdown('<div class="tip">New here? Try a sample: it fills everything in for you.</div>', unsafe_allow_html=True)
        c1, c2, _ = st.columns([1, 1, 2.5])
        c1.button("Try genuine sample", icon=":material/task_alt:", on_click=fill_sample, args=("genuine",)); c2.button("Try forged sample", icon=":material/report:", on_click=fill_sample, args=("forged",))
        for k, f in (("w_nm", "nm"), ("w_nd", "nd"), ("w_ad", "ad"), ("w_pn", "pn")):
            ss.setdefault(k, S[f])
        a, b = st.columns(2)
        nm = a.text_input("Applicant name", key="w_nm", placeholder="e.g. Priya Raman")
        nd = b.text_input("Name printed on the document", key="w_nd", placeholder="Should match the form")
        ad = a.text_input("Aadhaar number", key="w_ad", placeholder="12 digits")
        pn = b.text_input("PAN", key="w_pn", placeholder="ABCDE1234F")
        doc = a.selectbox("Document type", DOC_TYPES, index=DOC_TYPES.index(S["doc"]), key="w_doc")
        ok = all(x.strip() for x in (nm, nd, ad, pn))
        if st.button("Continue", type="primary", icon=":material/arrow_forward:", disabled=not ok):
            S.update(nm=nm, nd=nd, ad=ad, pn=pn, doc=doc); ss.step = 2; st.rerun()
        if not ok: st.caption("Fill in all four fields to continue.")
    elif step == 2:
        opts = ["Genuine sample", "Forged sample", "Upload my own"]
        src = st.radio("Which document?", opts, index=opts.index(S["src"]), horizontal=True, key="w_src")
        l, r = st.columns([1.2, 1], gap="large")
        img = None
        if src == "Upload my own":
            up = l.file_uploader("Drop a photo or scan here (PNG / JPG)", type=["png", "jpg", "jpeg"])
            img = Image.open(up).convert("RGB") if up else None
        else:
            img = sample_img(src == "Forged sample")
        ocr_ok, fields = (False, {}) if img is None else read_doc(img_bytes(img))
        if img is not None: l.image(img, caption="Preview", width="stretch")
        default = "\n".join(fields.get("clauses", [])) if ocr_ok and fields.get("clauses") else (BAD if src == "Forged sample" else GOOD)
        cl = r.text_area("Rules found on the document (one per line)", default, height=170, key=f"w_cl_{src}")
        if img is not None:
            with r.expander("Text read from the document (OCR)", expanded=ocr_ok):
                if ocr_ok:
                    st.write(f"**Aadhaar:** {fields.get('aadhaar') or 'not found'}  \n**PAN:** {fields.get('pan') or 'not found'}  \n**Name:** {fields.get('name') or 'not found'}")
                    st.caption("Clauses were read automatically. You can correct them above.")
                else:
                    st.caption("The OCR engine is not available here, so type or paste the clauses above.")
        r.markdown('<div class="tip">Compared with: licence held · renewed every 5 years · records kept 3 years.</div>', unsafe_allow_html=True)
        b1, b2, _ = st.columns([1, 1.5, 3])
        b1.button("Back", icon=":material/arrow_back:", on_click=lambda: ss.update(step=1))
        if b2.button("Run verification", type="primary", icon=":material/search:", disabled=img is None):
            S["src"] = src
            with st.spinner("Scanning document…"):
                res = verify(dict(name=S["nm"], name_on_doc=S["nd"], aadhaar=S["ad"], pan=S["pn"].strip().upper()), img, [c for c in cl.split("\n") if c.strip()], REG_DEFAULT, memory=ss.mem, ocr=fields if ocr_ok else None)
            cid = f"A-{10481 + len([x for x in ss.queue if not x['sample']])}"
            fam = ss.mem.add(res["hash"], res["key"], cid, res["verdict"], res["memory"], res["tamper_score"])
            res.update(id=cid, who=S["nm"], doc=S["doc"], time=NOW(), sample=False, decision="Pending", images=(img, heatmap(img)), family=fam)
            res["log"] = [(res["time"], "Case created and document received"), (res["time"], f"AI verification: {res['verdict']} (risk {int(res['risk']*100)}/100)")]
            if fam: res["log"].append((res["time"], f"Remembered as forgery family {fam}"))
            res["issues"] = [n for n, bad in [("Aadhaar", not res["aadhaar"]), ("PAN", not res["pan"]), ("Name", res["name_match"] < .9), ("Edited image", res["tamper_score"] >= 6), ("Clauses", bool(res["missing_or_mutated"]))] if bad]
            ss.queue.insert(0, res); ss.result = res; ss.step = 3; st.rerun()
    else:
        report(ss.result, "v")
        n1, n2, _ = st.columns([1.3, 1.3, 2.5])
        n1.button("Verify another", type="primary", icon=":material/add:", on_click=lambda: ss.update(step=1, result=None))
        n2.button("Open all cases", icon=":material/folder_open:", on_click=lambda: st.switch_page(P_CASES))

def page_cases():
    head("Cases", "Every document checked, with the officer's decision.")
    q = ss.queue
    c1, c2, c3 = st.columns([2, 2, 1.2])
    f = c1.segmented_control("Filter", ["All", "PASS", "REVIEW", "ESCALATE"], default="All")
    s = c2.text_input("Search by applicant", placeholder="Type a name…")
    if c3.button("Clear sample data") and any(x["sample"] for x in q):
        ss.queue = [x for x in q if not x["sample"]]; st.rerun()
    q = ss.queue
    rows = [x for x in q if (f in (None, "All") or x["verdict"] == f) and s.lower() in x["who"].lower()]
    if not rows:
        st.markdown('<div class="tip">No cases to show yet. Start a new verification.</div>', unsafe_allow_html=True); return
    st.dataframe([{"Case": x["id"], "Applicant": x["who"], "Document": x["doc"], "Verdict": x["verdict"], "Risk": int(x["risk"] * 100), "Issues": ", ".join(x["issues"]) or "none",
                   "Decision": x["decision"], "Time": f"{x['time']:%d %b %H:%M}"} for x in rows], width="stretch", hide_index=True)
    st.subheader("Open a case")
    ids = [x["id"] for x in rows]
    pick = st.selectbox("Case", ids, label_visibility="collapsed")
    report(next(x for x in rows if x["id"] == pick), "c")

def page_help():
    head("Help", "Everything you need to know in one minute.")
    with st.expander("How do I use DocImmune?", expanded=True):
        st.write("Open **New verification**, enter the applicant details (or press a sample button), add the document, and press **Run verification**. Then read the verdict and record your decision.")
    with st.expander("What do PASS, REVIEW and ESCALATE mean?"):
        st.write("**PASS** (risk below 20): looks genuine. **REVIEW** (20–49): an officer should look. **ESCALATE** (50+): high risk, send to a senior officer.")
    with st.expander("How is an edited image detected?"):
        st.write("The image is re-saved as JPEG and compared with the original. Edited areas compress differently and show up bright on the edit map.")
    with st.expander("How are Aadhaar, PAN and rules checked?"):
        st.write("Aadhaar uses the Verhoeff checksum, PAN uses its official format, and rules are matched to the regulation text with Smith-Waterman alignment, an algorithm from gene sequence analysis. Aadhaar is not checked against the government database.")
    with st.expander("What does the document memory do?"):
        st.write("Every checked document is remembered by a visual fingerprint. DocImmune can then spot a document reused for another applicant, an edited copy of an approved document, and repeated forgeries from the same family. Memory lasts for your current session.")
    with st.expander("How is the text read from the document?"):
        st.write("OCR reads the Aadhaar, PAN and clauses from the image, and they are compared with the form. If OCR is not available, the clauses can be typed.")
    with st.expander("Is the data real?"):
        st.write("Cases marked *sample* and the built-in documents are synthetic. This is a working prototype, not a production system.")
    st.caption("DocImmune · prototype built by Team ZYMORA for Smart India Hackathon 2026")

P_HOME = st.Page(page_dashboard, title="Dashboard", icon=":material/dashboard:", default=True, url_path="dashboard")
P_VERIFY = st.Page(page_verify, title="New verification", icon=":material/verified_user:", url_path="verify")
P_CASES = st.Page(page_cases, title="Cases", icon=":material/folder_open:", url_path="cases")
P_HELP = st.Page(page_help, title="Help", icon=":material/help:", url_path="help")
st.logo('<svg xmlns="http://www.w3.org/2000/svg" width="190" height="40" viewBox="0 0 190 40"><path d="M20 3 6 8v10c0 9 6 16 14 19 8-3 14-10 14-19V8z" fill="#14B8A6"/><path d="M14 20l5 5 8-9" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/><text x="44" y="27" font-family="Arial" font-weight="800" font-size="20" fill="#0B2A2E">DocImmune</text></svg>', size="large")
pg = st.navigation([P_HOME, P_VERIFY, P_CASES, P_HELP], position="top")
with st.container(key="mobnav"):  # shown only on phones, where the top menu is hidden
    mc = st.columns(4)
    for col, (pg_, lab, ic) in zip(mc, [(P_HOME, "Home", ":material/dashboard:"), (P_VERIFY, "Verify", ":material/verified_user:"), (P_CASES, "Cases", ":material/folder_open:"), (P_HELP, "Help", ":material/help:")]):
        col.page_link(pg_, label=lab, icon=ic)
pg.run()
