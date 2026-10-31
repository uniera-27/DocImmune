import io
import numpy as np
import streamlit as st
from PIL import Image, ImageChops, ImageDraw, ImageFont
from docimmune_proto import verify, REG_DEFAULT

st.set_page_config(page_title="DocImmune", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

# ------------------------------------------------------------------ THEME
st.markdown("""
<style>
.block-container{padding-top:2rem;max-width:1100px}
#MainMenu,footer{visibility:hidden}
.hero{background:linear-gradient(135deg,#1c3a8a 0%,#0e7490 100%);border-radius:22px;padding:34px 36px;margin-bottom:22px}
.hero h1{margin:0 0 6px;font-size:2.1rem;color:#fff}.hero p{margin:0;color:#d8e6ff;font-size:1.05rem}
.card{background:#111B33;border:1px solid #22325a;border-radius:18px;padding:20px;height:100%}
.card h4{margin:6px 0 6px;color:#fff}.card p{margin:0;color:#9fb0cf;font-size:.92rem}
.ico{font-size:1.9rem}
.steps{display:flex;gap:10px;margin:4px 0 22px}
.step{flex:1;display:flex;align-items:center;gap:10px;background:#111B33;border:1px solid #22325a;border-radius:14px;padding:12px 14px;color:#8ea0c4}
.step b{width:30px;height:30px;border-radius:50%;display:grid;place-items:center;background:#22325a;color:#fff;flex:none}
.step.on{border-color:#5B8CFF;color:#fff;background:#14244a}.step.on b{background:#5B8CFF}
.step.done b{background:#22c58b}.step.done{color:#cfe}
.verdict{border-radius:20px;padding:26px 30px;margin-bottom:16px}
.verdict h2{margin:0;font-size:2rem;color:#fff}.verdict p{margin:6px 0 0;color:#fff;opacity:.92}
.v-PASS{background:linear-gradient(135deg,#0f7a4f,#22c58b)}.v-REVIEW{background:linear-gradient(135deg,#a8690a,#f0b040)}.v-ESCALATE{background:linear-gradient(135deg,#a3202f,#ef5a6a)}
.chk{display:flex;gap:12px;background:#111B33;border:1px solid #22325a;border-radius:14px;padding:13px 16px;margin-bottom:10px}
.chk .t{font-weight:600;color:#fff}.chk .d{color:#9fb0cf;font-size:.9rem}.chk .i{font-size:1.4rem}
.tip{background:#14244a;border-left:4px solid #5B8CFF;border-radius:10px;padding:12px 16px;color:#cfdcff;margin:6px 0 14px}
.pill{padding:3px 12px;border-radius:20px;font-weight:700;font-size:.8rem}
.p-PASS{background:#123f31;color:#4be0a4}.p-REVIEW{background:#4a3410;color:#f5c05a}.p-ESCALATE{background:#4a1a22;color:#ff8c98}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------ HELPERS
def sample(forged):
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

GOOD = "The applicant shall hold a valid licence\nLicence shall be renewed every five years\nRecords shall be retained for three years"
BAD = "The applicant shall hold a valid licence\nLicence may be renewed at any time"

def stepper(cur):
    labels = ["Applicant details", "Document", "Result"]
    html = '<div class="steps">'
    for i, t in enumerate(labels, 1):
        cls = "on" if i == cur else "done" if i < cur else ""
        html += f'<div class="step {cls}"><b>{"✓" if i < cur else i}</b>{t}</div>'
    st.markdown(html + "</div>", unsafe_allow_html=True)

def card(icon, title, text):
    return f'<div class="card"><div class="ico">{icon}</div><h4>{title}</h4><p>{text}</p></div>'

def go(page):
    st.session_state.page = page

def fill_demo(kind):
    bad = kind == "forged"
    st.session_state.nm = "Priya Raman"
    st.session_state.nd = "Priya R" if bad else "Priya Raman"
    st.session_state.ad = "2341 2341 2347" if bad else "2341 2341 2346"
    st.session_state.pn = "ABCDE1234F"
    st.session_state.src = "Forged sample" if bad else "Genuine sample"

# ------------------------------------------------------------------ STATE
for k, v in dict(page="Home", step=1, queue=[], nm="", nd="", ad="", pn="", src="Genuine sample", result=None).items():
    st.session_state.setdefault(k, v)

with st.sidebar:
    st.markdown("## 🛡️ DocImmune")
    st.caption("AI document verification")
    st.radio("Menu", ["Home", "Verify a document", "Case queue", "Help"], key="page", label_visibility="collapsed")
    st.divider()
    st.caption("Team ZYMORA · SIH26261")

page = st.session_state.page

# ------------------------------------------------------------------ HOME
if page == "Home":
    st.markdown('<div class="hero"><h1>Catch fake documents in seconds</h1>'
                '<p>DocImmune checks IDs, certificates and licences, spots edits, and tells the officer what to do next.</p></div>',
                unsafe_allow_html=True)
    c = st.columns(3)
    c[0].markdown(card("📝", "1 · Enter details", "Type the applicant's name, Aadhaar and PAN."), unsafe_allow_html=True)
    c[1].markdown(card("📄", "2 · Add the document", "Upload a photo or scan, or try a ready sample."), unsafe_allow_html=True)
    c[2].markdown(card("✅", "3 · Get the verdict", "PASS, REVIEW or ESCALATE, with simple reasons."), unsafe_allow_html=True)
    st.write("")
    st.button("🚀 Start verifying", type="primary", on_click=go, args=("Verify a document",))
    q = st.session_state.queue
    st.write("")
    m = st.columns(3)
    m[0].metric("Documents checked", len(q))
    m[1].metric("Approved (PASS)", sum(x["verdict"] == "PASS" for x in q))
    m[2].metric("Need attention", sum(x["verdict"] != "PASS" for x in q))
    st.markdown('<div class="tip">💡 New here? Click <b>Start verifying</b>, then choose <b>Try with a demo</b>. It takes 20 seconds.</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------ VERIFY
elif page == "Verify a document":
    st.title("Verify a document")
    step = st.session_state.step
    stepper(step)

    if step == 1:
        st.subheader("Step 1 · Who is applying?")
        st.markdown('<div class="tip">Not sure what to type? Press a demo button to fill everything in.</div>', unsafe_allow_html=True)
        d1, d2, _ = st.columns([1, 1, 2])
        d1.button("✨ Demo: genuine", on_click=fill_demo, args=("genuine",))
        d2.button("🚨 Demo: forged", on_click=fill_demo, args=("forged",))
        a, b = st.columns(2)
        a.text_input("Applicant name", key="nm", placeholder="e.g. Priya Raman", help="Name as written in the application form")
        b.text_input("Name printed on the document", key="nd", placeholder="Must match the form")
        a.text_input("Aadhaar number", key="ad", placeholder="12 digits", help="We check the official checksum rule")
        b.text_input("PAN", key="pn", placeholder="ABCDE1234F", help="5 letters, 4 digits, 1 letter")
        ok = all(st.session_state[k].strip() for k in ("nm", "nd", "ad", "pn"))
        if st.button("Next →", type="primary", disabled=not ok):
            st.session_state.step = 2; st.rerun()
        if not ok:
            st.caption("Fill all four fields to continue.")

    elif step == 2:
        st.subheader("Step 2 · Add the document")
        st.radio("Choose a document", ["Genuine sample", "Forged sample", "Upload my own"], key="src", horizontal=True)
        src = st.session_state.src
        left, right = st.columns([1.2, 1])
        if src == "Upload my own":
            up = left.file_uploader("Upload a photo or scan (PNG / JPG)", type=["png", "jpg", "jpeg"])
            img = Image.open(up).convert("RGB") if up else None
            default = GOOD
        else:
            img = sample(src == "Forged sample"); default = BAD if src == "Forged sample" else GOOD
        if img is not None:
            left.image(img, caption="Document preview", width="stretch")
        right.text_area("Clauses found on the document (one per line)", default, key=f"cl_{src}", height=190,
                        help="These are compared with the regulation clauses.")
        right.markdown('<div class="tip">Regulation reference: licence held · renewed every 5 years · records kept 3 years.</div>', unsafe_allow_html=True)
        b1, b2, _ = st.columns([1, 1.4, 3])
        b1.button("← Back", on_click=lambda: st.session_state.update(step=1))
        if b2.button("🔍 Run verification", type="primary", disabled=img is None):
            with st.spinner("Scanning document…"):
                r = verify(dict(name=st.session_state.nm, name_on_doc=st.session_state.nd,
                                aadhaar=st.session_state.ad, pan=st.session_state.pn.strip().upper()),
                           img, [c for c in st.session_state[f"cl_{src}"].split("\n") if c.strip()], REG_DEFAULT)
            r["id"] = f"A-{10481 + len(st.session_state.queue)}"; r["who"] = st.session_state.nm
            r["issues"] = [n for n, bad in [("Aadhaar", not r["aadhaar"]), ("PAN", not r["pan"]), ("Name", r["name_match"] < .9),
                                            ("Edited image", r["tamper_score"] >= 6), ("Clauses", bool(r["missing_or_mutated"]))] if bad]
            st.session_state.queue.insert(0, r); st.session_state.result = (r, heatmap(img), img)
            st.session_state.step = 3; st.rerun()

    else:
        r, heat, img = st.session_state.result
        msg = {"PASS": ("Looks genuine", "Safe to approve. No problems found."),
               "REVIEW": ("Needs a human look", "A few things don't add up. An officer should check."),
               "ESCALATE": ("High risk – do not approve", "Strong signs of editing or wrong details. Send to a senior officer.")}[r["verdict"]]
        icon = {"PASS": "✅", "REVIEW": "⚠️", "ESCALATE": "🚨"}[r["verdict"]]
        st.markdown(f'<div class="verdict v-{r["verdict"]}"><h2>{icon} {r["verdict"]} · {msg[0]}</h2><p>{msg[1]} (Case {r["id"]}, risk {r["risk"]})</p></div>', unsafe_allow_html=True)
        st.progress(min(r["risk"], 1.0), text=f"Risk score {r['risk']}  (0 = safe, 1 = high risk)")
        st.subheader("What we checked")
        rows = [
            (r["aadhaar"], "Aadhaar number", "Passes the official checksum rule." if r["aadhaar"] else "Fails the checksum. Likely a typing error or a made-up number."),
            (r["pan"], "PAN format", "Format is valid." if r["pan"] else "Wrong format. It should look like ABCDE1234F."),
            (r["name_match"] >= .9, "Name matches", f"Form and document match {int(r['name_match']*100)}%."),
            (r["tamper_score"] < 6, "Image not edited", "No edited area found." if r["tamper_score"] < 6 else "An area of the image looks edited (see the red map below)."),
            (not r["missing_or_mutated"], "Rules / clauses", "All regulation clauses found." if not r["missing_or_mutated"] else "Missing or changed clauses: " + ", ".join(r["missing_or_mutated"]) + "."),
        ]
        for ok, t, d in rows:
            st.markdown(f'<div class="chk"><div class="i">{"✅" if ok else "❌"}</div><div><div class="t">{t}</div><div class="d">{d}</div></div></div>', unsafe_allow_html=True)
        with st.expander("🔬 See the image scan"):
            a, b = st.columns(2)
            a.image(img, caption="Document", width="stretch"); b.image(heat, caption="Edit map: bright = edited", width="stretch")
        st.markdown('<div class="tip">The AI only flags. The officer always makes the final decision.</div>', unsafe_allow_html=True)
        n1, n2, _ = st.columns([1.3, 1.3, 2])
        n1.button("➕ Verify another", type="primary", on_click=lambda: st.session_state.update(step=1, result=None))
        n2.button("🗂️ Open case queue", on_click=go, args=("Case queue",))

# ------------------------------------------------------------------ CASES
elif page == "Case queue":
    st.title("Case queue")
    q = st.session_state.queue
    if not q:
        st.markdown('<div class="tip">No cases yet. Verify a document and it will appear here.</div>', unsafe_allow_html=True)
        st.button("Start verifying", type="primary", on_click=go, args=("Verify a document",))
    else:
        f = st.segmented_control("Show", ["All", "PASS", "REVIEW", "ESCALATE"], default="All")
        data = [{"Case": x["id"], "Applicant": x["who"], "Verdict": x["verdict"], "Risk": x["risk"], "Issues": ", ".join(x["issues"]) or "none"}
                for x in q if f in (None, "All") or x["verdict"] == f]
        st.dataframe(data, width="stretch", hide_index=True)

# ------------------------------------------------------------------ HELP
else:
    st.title("Help")
    with st.expander("How do I use this?", expanded=True):
        st.write("Open **Verify a document**, fill in the details (or press a demo button), add a document, and press **Run verification**.")
    with st.expander("What do PASS, REVIEW and ESCALATE mean?"):
        st.write("**PASS** (risk below 0.20): looks genuine. **REVIEW** (0.20–0.49): an officer should look. **ESCALATE** (0.50+): high risk.")
    with st.expander("How is an edited image detected?"):
        st.write("The image is re-saved as JPEG and compared with the original. Edited areas compress differently and show up bright on the edit map.")
    with st.expander("How are Aadhaar and clauses checked?"):
        st.write("Aadhaar uses the Verhoeff checksum. Clauses are aligned to the regulation text using Smith-Waterman, an algorithm from gene sequence analysis.")
    with st.expander("Is the data real?"):
        st.write("Samples are synthetic. This is a working prototype, not a production system.")
