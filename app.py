import io, html
from datetime import datetime, timedelta, timezone
import numpy as np
import streamlit as st
from PIL import Image, ImageChops, ImageDraw, ImageFont
from docimmune_proto import verify, REG_DEFAULT

st.set_page_config(page_title="DocImmune", page_icon="🛡️", layout="wide")

# =========================================================== STYLE
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
html, body, .stApp, h1, h2, h3, h4, p, label, li, button, input, textarea, [data-testid="stMarkdownContainer"]{font-family:'Plus Jakarta Sans',sans-serif}
#MainMenu, footer, header [data-testid="stToolbar"]{visibility:hidden}
.block-container{padding:4rem 2.6rem 3rem;max-width:1180px}
h1,h2,h3{letter-spacing:-.02em}
.ph{margin-bottom:22px}.ph h1{font-size:1.9rem;font-weight:800;margin:0;color:#1B1F3B}.ph p{margin:4px 0 0;color:#6B7194}
.card{background:#fff;border:1px solid #E7E9F2;border-radius:18px;padding:22px;box-shadow:0 2px 10px rgba(27,31,59,.04)}
.card h4{margin:0 0 14px;font-size:1rem;font-weight:700;color:#1B1F3B}
.kpi{display:flex;gap:14px;align-items:center;background:#fff;border:1px solid #E7E9F2;border-radius:18px;padding:18px;box-shadow:0 2px 10px rgba(27,31,59,.04)}
.kpi .ic{width:46px;height:46px;border-radius:13px;display:grid;place-items:center;font-size:1.3rem;flex:none}
.kpi b{display:block;font-size:1.7rem;line-height:1.1;color:#1B1F3B}.kpi span{color:#6B7194;font-size:.85rem}
.hero{background:linear-gradient(120deg,#5B4BFF 0%,#8A5CFF 55%,#00B8A9 130%);border-radius:22px;padding:30px 32px;color:#fff;margin-bottom:20px}
.hero h1{margin:0;font-size:1.8rem;font-weight:800;color:#fff}.hero p{margin:6px 0 0;opacity:.92;max-width:620px}
.row{display:flex;align-items:center;gap:12px;padding:12px 0;border-bottom:1px solid #EEF0F7}.row:last-child{border:0}
.av{width:38px;height:38px;border-radius:50%;background:#ECE9FF;color:#5B4BFF;display:grid;place-items:center;font-weight:700;flex:none}
.row .n{font-weight:600;color:#1B1F3B}.row .m{font-size:.8rem;color:#6B7194}.row .r{margin-left:auto;text-align:right}
.pill{padding:3px 11px;border-radius:20px;font-weight:700;font-size:.75rem;display:inline-block}
.p-PASS{background:#DDF6EA;color:#0E8F57}.p-REVIEW{background:#FFF0D1;color:#B26A00}.p-ESCALATE{background:#FFE1E4;color:#C62A3B}.p-NONE{background:#EEF0F7;color:#6B7194}
.tag{font-size:.68rem;background:#EEF0F7;color:#6B7194;border-radius:6px;padding:1px 7px;margin-left:6px}
.stp{display:flex;gap:10px;margin-bottom:22px}.stp div{flex:1;background:#fff;border:1px solid #E7E9F2;border-radius:14px;padding:12px 14px;color:#9AA0C0;font-weight:600;display:flex;gap:10px;align-items:center}
.stp b{width:28px;height:28px;border-radius:50%;background:#EEF0F7;color:#6B7194;display:grid;place-items:center;flex:none;font-size:.85rem}
.stp .on{border-color:#5B4BFF;color:#1B1F3B;box-shadow:0 4px 14px rgba(91,75,255,.15)}.stp .on b{background:#5B4BFF;color:#fff}
.stp .done b{background:#12B76A;color:#fff}.stp .done{color:#1B1F3B}
.tip{background:#F0EEFF;border-radius:12px;padding:12px 16px;color:#3B3294;margin:6px 0 16px;font-size:.92rem}
.vc{border-radius:20px;padding:26px;color:#fff;text-align:center}
.vc h2{margin:10px 0 2px;color:#fff;font-weight:800}.vc p{margin:0;opacity:.95}
.v-PASS{background:linear-gradient(145deg,#0E9F6E,#34D399)}.v-REVIEW{background:linear-gradient(145deg,#D97706,#FBBF24)}.v-ESCALATE{background:linear-gradient(145deg,#C81E3A,#FB7185)}
.ck{display:flex;gap:14px;align-items:flex-start;padding:13px 0;border-bottom:1px solid #EEF0F7}.ck:last-child{border:0}
.ck .b{width:30px;height:30px;border-radius:9px;display:grid;place-items:center;flex:none;font-weight:800}
.ok{background:#DDF6EA;color:#0E8F57}.bad{background:#FFE1E4;color:#C62A3B}
.ck .t{font-weight:700;color:#1B1F3B}.ck .d{color:#6B7194;font-size:.88rem}
div.stButton>button{border-radius:12px;font-weight:700;padding:.55rem 1.2rem}
div.stButton>button[kind="primary"]{background:linear-gradient(120deg,#5B4BFF,#8A5CFF);border:0;color:#fff}
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea,[data-baseweb="select"]>div{border-radius:12px}
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
    im = Image.new("RGB", (800, 500), (250, 248, 240)); d = ImageDraw.Draw(im); f = ImageFont.load_default()
    for y in range(40, 460, 28):
        d.text((60, y), "CERTIFICATE OF REGISTRATION   LICENCE NO. FSS/TN/2026/0457   VALID UPTO 2029", fill=(30, 30, 30), font=f)
    arr = np.asarray(im).astype(int) + rng.integers(-6, 7, (500, 800, 3))
    im = Image.fromarray(arr.clip(0, 255).astype("uint8"))
    b = io.BytesIO(); im.save(b, "JPEG", quality=90); b.seek(0); im = Image.open(b).convert("RGB")
    if forged:
        d = ImageDraw.Draw(im); d.rectangle((300, 200, 520, 222), fill=(250, 248, 240))
        d.text((305, 206), "LICENCE NO. FSS/TN/2031/9999", fill=(20, 20, 20), font=f)
    return im

def heatmap(img):
    b = io.BytesIO(); img.convert("RGB").save(b, "JPEG", quality=90); b.seek(0)
    diff = ImageChops.difference(img.convert("RGB"), Image.open(b)).convert("L")
    return Image.fromarray(np.clip(np.asarray(diff, float) * 25, 0, 255).astype("uint8"))

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
ss.setdefault("queue", seed()); ss.setdefault("step", 1); ss.setdefault("result", None); ss.setdefault("open", None)
ss.setdefault("S", dict(nm="", nd="", ad="", pn="", doc=DOC_TYPES[0], src="Genuine sample"))

def checks_for(r):
    return [(r["aadhaar"], "Aadhaar number", "Passes the official checksum rule." if r["aadhaar"] else "Fails the checksum. Likely a typing error or a made-up number."),
            (r["pan"], "PAN format", "Format is valid." if r["pan"] else "Wrong format. It should look like ABCDE1234F."),
            (r["name_match"] >= .9, "Name matches the form", f"Form and document match {int(r['name_match']*100)}%."),
            (r["tamper_score"] < 6, "Image not edited", "No edited area found." if r["tamper_score"] < 6 else "An area of the image looks edited."),
            (not r["missing_or_mutated"], "Rules and clauses", "All regulation clauses found." if not r["missing_or_mutated"] else "Missing or changed: " + ", ".join(r["missing_or_mutated"]) + ".")]

def pill(v): return f'<span class="pill p-{v}">{v}</span>'

def report_html(r):
    rows = "".join(f"<tr><td>{'PASS' if ok else 'FAIL'}</td><td><b>{t}</b><br>{d}</td></tr>" for ok, t, d in checks_for(r))
    return (f"<html><body style='font-family:Arial;max-width:720px;margin:30px auto'><h1>DocImmune verification report</h1>"
            f"<p>Case {r['id']} · {html.escape(r['who'])} · {r['doc']} · {r['time']:%d %b %Y %H:%M}</p><h2>{r['verdict']} · risk {int(r['risk']*100)}/100</h2>"
            f"<table border='1' cellpadding='8' cellspacing='0' width='100%'>{rows}</table><p>Officer decision: <b>{r['decision']}</b></p>"
            f"<p style='color:#666'>Generated by DocImmune. The AI flags; the officer decides.</p></body></html>").encode()

def decide(r, d):
    r["decision"] = d

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
    d1.button("✅ Approve", key=f"ap{key}", on_click=decide, args=(r, "Approved"))
    d2.button("⛔ Reject", key=f"rj{key}", on_click=decide, args=(r, "Rejected"))
    d3.button("📨 Ask for more info", key=f"mi{key}", on_click=decide, args=(r, "More info requested"))
    if r.get("aadhaar") is not None:
        d4.download_button("⬇ Download report", report_html(r), file_name=f"{r['id']}_report.html", mime="text/html", key=f"dl{key}")
    if r.get("images"):
        with st.expander("🔬 See the image scan"):
            c1, c2 = st.columns(2)
            c1.image(r["images"][0], caption="Document", width="stretch"); c2.image(r["images"][1], caption="Edit map: bright = edited", width="stretch")
    st.caption("The AI only flags. The officer always makes the final decision.")

# =========================================================== PAGES
def page_dashboard():
    q = ss.queue; h = NOW().hour
    greet = "Good morning" if h < 12 else "Good afternoon" if h < 17 else "Good evening"
    st.markdown(f'<div class="hero"><h1>{greet}, Officer 👋</h1><p>DocImmune checks IDs, certificates and licences, spots edits, and tells you what to do next.</p></div>', unsafe_allow_html=True)
    a, b = st.columns([1.6, 4]); a.button("＋ New verification", type="primary", on_click=lambda: st.switch_page(P_VERIFY))
    k = st.columns(4)
    k[0].markdown(kpi("📄", "#ECE9FF", len(q), "Total checked"), unsafe_allow_html=True)
    k[1].markdown(kpi("✅", "#DDF6EA", sum(x["verdict"] == "PASS" for x in q), "Looks genuine"), unsafe_allow_html=True)
    k[2].markdown(kpi("⚠️", "#FFF0D1", sum(x["verdict"] == "REVIEW" for x in q), "Need review"), unsafe_allow_html=True)
    k[3].markdown(kpi("🚨", "#FFE1E4", sum(x["verdict"] == "ESCALATE" for x in q), "High risk"), unsafe_allow_html=True)
    st.write("")
    l, r = st.columns([1.7, 1], gap="large")
    rows = "".join(f'<div class="row"><div class="av">{x["who"][0]}</div><div><div class="n">{html.escape(x["who"])}{"<span class=tag>sample</span>" if x["sample"] else ""}</div>'
                   f'<div class="m">{x["doc"]} · {x["time"]:%d %b, %H:%M}</div></div><div class="r">{pill(x["verdict"])}<div class="m">risk {int(x["risk"]*100)}/100</div></div></div>' for x in q[:5])
    l.markdown(f'<div class="card"><h4>Recent activity</h4>{rows}</div>', unsafe_allow_html=True)
    n = max(len(q), 1)
    bars = "".join(f'<div style="margin:12px 0"><div style="display:flex;justify-content:space-between;font-size:.85rem"><span>{v.title()}</span><b>{c}</b></div>'
                   f'<div style="height:9px;background:#EEF0F7;border-radius:6px;overflow:hidden"><div style="width:{c/n*100}%;height:100%;background:{col}"></div></div></div>'
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
        c1.button("✨ Try genuine sample", on_click=fill_sample, args=("genuine",)); c2.button("🚨 Try forged sample", on_click=fill_sample, args=("forged",))
        for k, f in (("w_nm", "nm"), ("w_nd", "nd"), ("w_ad", "ad"), ("w_pn", "pn")):
            ss.setdefault(k, S[f])
        a, b = st.columns(2)
        nm = a.text_input("Applicant name", key="w_nm", placeholder="e.g. Priya Raman")
        nd = b.text_input("Name printed on the document", key="w_nd", placeholder="Should match the form")
        ad = a.text_input("Aadhaar number", key="w_ad", placeholder="12 digits")
        pn = b.text_input("PAN", key="w_pn", placeholder="ABCDE1234F")
        doc = a.selectbox("Document type", DOC_TYPES, index=DOC_TYPES.index(S["doc"]), key="w_doc")
        ok = all(x.strip() for x in (nm, nd, ad, pn))
        if st.button("Continue →", type="primary", disabled=not ok):
            S.update(nm=nm, nd=nd, ad=ad, pn=pn, doc=doc); ss.step = 2; st.rerun()
        if not ok: st.caption("Fill in all four fields to continue.")
    elif step == 2:
        opts = ["Genuine sample", "Forged sample", "Upload my own"]
        src = st.radio("Which document?", opts, index=opts.index(S["src"]), horizontal=True, key="w_src")
        l, r = st.columns([1.2, 1], gap="large")
        img = None
        if src == "Upload my own":
            up = l.file_uploader("Drop a photo or scan here (PNG / JPG)", type=["png", "jpg", "jpeg"])
            img = Image.open(up).convert("RGB") if up else None; default = GOOD
        else:
            img = sample_img(src == "Forged sample"); default = BAD if src == "Forged sample" else GOOD
        if img is not None: l.image(img, caption="Preview", width="stretch")
        cl = r.text_area("Rules found on the document (one per line)", default, height=170, key=f"w_cl_{src}")
        r.markdown('<div class="tip">Compared with: licence held · renewed every 5 years · records kept 3 years.</div>', unsafe_allow_html=True)
        b1, b2, _ = st.columns([1, 1.5, 3])
        b1.button("← Back", on_click=lambda: ss.update(step=1))
        if b2.button("🔍 Run verification", type="primary", disabled=img is None):
            S["src"] = src
            with st.spinner("Scanning document…"):
                res = verify(dict(name=S["nm"], name_on_doc=S["nd"], aadhaar=S["ad"], pan=S["pn"].strip().upper()), img, [c for c in cl.split("\n") if c.strip()], REG_DEFAULT)
            res.update(id=f"A-{10481 + len([x for x in ss.queue if not x['sample']])}", who=S["nm"], doc=S["doc"], time=NOW(), sample=False, decision="Pending", images=(img, heatmap(img)))
            res["issues"] = [n for n, bad in [("Aadhaar", not res["aadhaar"]), ("PAN", not res["pan"]), ("Name", res["name_match"] < .9), ("Edited image", res["tamper_score"] >= 6), ("Clauses", bool(res["missing_or_mutated"]))] if bad]
            ss.queue.insert(0, res); ss.result = res; ss.step = 3; st.rerun()
    else:
        report(ss.result, "v")
        n1, n2, _ = st.columns([1.3, 1.3, 2.5])
        n1.button("＋ Verify another", type="primary", on_click=lambda: ss.update(step=1, result=None))
        n2.button("🗂️ Open all cases", on_click=lambda: st.switch_page(P_CASES))

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
    with st.expander("Is the data real?"):
        st.write("Cases marked *sample* and the built-in documents are synthetic. This is a working prototype, not a production system.")
    st.caption("DocImmune · prototype built by Team ZYMORA for Smart India Hackathon 2026")

P_HOME = st.Page(page_dashboard, title="Dashboard", icon="📊", default=True, url_path="dashboard")
P_VERIFY = st.Page(page_verify, title="New verification", icon="🔍", url_path="verify")
P_CASES = st.Page(page_cases, title="Cases", icon="🗂️", url_path="cases")
P_HELP = st.Page(page_help, title="Help", icon="💡", url_path="help")
st.logo('<svg xmlns="http://www.w3.org/2000/svg" width="190" height="40" viewBox="0 0 190 40"><path d="M20 3 6 8v10c0 9 6 16 14 19 8-3 14-10 14-19V8z" fill="#9B8CFF"/><path d="M14 20l5 5 8-9" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/><text x="44" y="27" font-family="Arial" font-weight="800" font-size="20" fill="#fff">DocImmune</text></svg>', size="large")
pg = st.navigation([P_HOME, P_VERIFY, P_CASES, P_HELP])
pg.run()
