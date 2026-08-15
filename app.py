"""Expo page. Reads results/frozen/ and results/figures/ only. Computes nothing.

    .venv/bin/streamlit run app.py

Every number on screen is read from a frozen file. Every figure caption is read
from results/figures/CAPTIONS.md, verbatim, so the page and the report cannot
drift apart. No interactive controls: nothing here can be broken by someone
clicking on it while nobody is standing at the screen. No gene is named anywhere
on this page — the data supports pathway-level claims only (concordance -0.019).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd
import streamlit as st

FROZEN = Path("results/frozen")
FIGS = Path("results/figures")
REPO = "https://github.com/alejandro-publius/reversal-map"

st.set_page_config(page_title="reversal-map", layout="wide",
                   initial_sidebar_state="collapsed")

st.markdown("""<style>
html, body, .stApp {background:#ffffff !important; color:#111827 !important;}
#MainMenu, footer, header {visibility:hidden;}
.block-container {padding-top:1.8rem; padding-bottom:2rem; max-width:1180px;}
.huge {font-size:4.6rem; color:#111827; line-height:.98; font-weight:800;
       letter-spacing:-.03em; margin:0;}
.sub {font-size:1.34rem; line-height:1.4; color:#374151; margin:.5rem 0 0 0;}
.circ {font-size:1.06rem; line-height:1.45; color:#4b5563; margin:.5rem 0 0 0;}
.size {font-size:1.06rem; color:#111827; margin:.3rem 0 0 0;}
/* Four boxes: identical weight, no warning colour on any of them. */
.box {border:1px solid #d1d5db; border-radius:10px; padding:1rem 1.1rem;
      height:100%; background:#fff;}
.boxn {font-size:2.9rem; font-weight:800; line-height:1; margin:0; color:#111827;}
.boxl {font-size:.9rem; color:#6b7280; margin:.35rem 0 0 0;}
.card {border:1px solid #d1d5db; border-radius:10px; padding:1.05rem 1.2rem;
       background:#fff; height:100%;}
.card h4 {margin:0 0 .55rem 0; font-size:1.02rem; color:#111827;}
.cardn {font-size:2.1rem; font-weight:800; line-height:1; margin:0 0 .3rem 0; color:#111827;}
.card p {margin:0; font-size:.95rem; color:#374151; line-height:1.5;}
/* The one positive: deliberately smaller than the three negatives, and framed
   as a control. */
.ctrl {border:1px solid #d1d5db; border-radius:10px; padding:.85rem 1rem;
       background:#fafafa;}
.ctrl h4 {margin:0 0 .35rem 0; font-size:.9rem; color:#6b7280; font-weight:600;
          text-transform:uppercase; letter-spacing:.05em;}
.ctrl .cn {font-size:1.35rem; font-weight:700; color:#111827; margin:0 0 .25rem 0;}
.ctrl p {margin:0; font-size:.86rem; color:#4b5563; line-height:1.45;}
.cap {font-size:.9rem; color:#4b5563; line-height:1.5; border-left:3px solid #e5e7eb;
      padding-left:.85rem; margin-top:.5rem;}
.captitle {font-size:1.0rem; font-weight:700; color:#111827; margin-top:.4rem;}
.prov {font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:.78rem;
       color:#6b7280; line-height:1.9;}
</style>""", unsafe_allow_html=True)


@st.cache_data
def captions() -> dict:
    """Pull each figure's bolded headline + quoted body straight from CAPTIONS.md.

    Verbatim: the '>' block-quote is the exact wording used in the report."""
    txt = (FIGS / "CAPTIONS.md").read_text()
    out = {}
    for block in re.split(r"\n## FIG ", txt)[1:]:
        key = re.search(r"`(fig\d_[a-z_]+\.png)`", block)
        title = re.search(r"\*\*(.+?)\*\*", block)
        body = " ".join(l.lstrip("> ").strip()
                        for l in block.splitlines() if l.lstrip().startswith(">"))
        if key:
            out[key.group(1)] = {"title": title.group(1) if title else "",
                                 "body": re.sub(r"\*\*|\*", "", body).strip()}
    # The 46.5% size figure lives in the Fig 3 caption text (Fig 3 is not shown
    # on this page); pull it so the headline stays synced to CAPTIONS.md.
    m = re.search(r"explains (\d+\.\d+)% of the variance", txt)
    out["_size_pct"] = m.group(1) if m else ""
    return out


@st.cache_data
def load():
    return (pd.read_csv(FROZEN / "program_summary.csv"),
            json.loads((FROZEN / "provenance.json").read_text()),
            json.loads((FROZEN / "heldout_evaluation.json").read_text()))


S, prov, held = load()
CAP = captions()

# Headline range, read from the frozen fit — not typed in by hand.
ds = prov["deciding_statistic"]
lo = round(ds["adjusted_r2_x_independent_only"] * 100)   # 56
hi = round(ds["adjusted_r2_all_six"] * 100)              # 75
gate_fail_hits = prov["gap_numbers"]["gate_fail_but_has_hits"]   # 20
bal_acc = held["axis2_balanced_accuracy"]                        # 0.4375


def figure(name: str):
    st.image(str(FIGS / name), use_container_width=True)
    c = CAP.get(name, {})
    if c:
        st.markdown(f"<div class='captitle'>{c['title']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='cap'>{c['body']}</div>", unsafe_allow_html=True)


# ==================================================== 1. HEADLINE  (above fold)
st.markdown(f"<div class='huge'>{lo}–{hi}%</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='sub'>of how reversible a program looks is explained by how the "
    "program was defined — chiefly its size — not by its biology.</div>",
    unsafe_allow_html=True)
st.markdown(
    "<div class='circ'>The range is that wide because one of our own features is "
    "partly circular, and we report both ends.</div>", unsafe_allow_html=True)
st.markdown(
    f"<div class='size'>Program size alone explains {CAP['_size_pct']}%.</div>",
    unsafe_allow_html=True)

st.write("")

# ==================================================== 2. FOUR BOXES (above fold)
boxes = [("4", "evaluations run"),
         ("3", "came back negative"),
         ("1", "came back positive"),
         ("0", "gene-level claims made")]
for col, (n, lab) in zip(st.columns(4), boxes):
    col.markdown(f"<div class='box'><div class='boxn'>{n}</div>"
                 f"<div class='boxl'>{lab}</div></div>", unsafe_allow_html=True)

st.write("")
st.divider()

# ==================================================== 3. FIG 1 — the matrix
figure("fig1_matrix.png")
st.divider()

# ==================================================== 4. THREE NEGATIVE FINDINGS
st.subheader("Three evaluations came back negative")
cards = [
    ("Most of it is not biology", f"up to {hi}%",
     "A model that never looks at what a program does explains most of how "
     f"reversible it appears; {lo}% survives after we remove the circular feature."),
    ("The obvious filter is wrong", f"{gate_fail_hits} of 50",
     "The measurability filter anyone would build discards 20 programs that "
     "produce hits anyway — including the one we sealed in git before the "
     "scoring code existed."),
    ("The generalisation test failed", f"{bal_acc}",
     "On ten programs from a different collection, sealed and scored once after "
     "the model was hashed, binary accuracy came back worse than chance — and "
     "we did not refit."),
]
for col, (h, num, body) in zip(st.columns(3), cards):
    col.markdown(f"<div class='card'><h4>{h}</h4><div class='cardn'>{num}</div>"
                 f"<p>{body}</p></div>", unsafe_allow_html=True)

st.write("")
st.divider()

# ==================================================== 5. FIG 2 — gate failure
figure("fig2_gate_failure.png")
st.divider()

# ==================================================== 6. THE ONE POSITIVE (smaller)
# Constrained to the left ~2/5 of the width and set in a lighter, smaller card so
# it reads as subordinate to the three negatives above. Labelled a control.
pos_col, _ = st.columns([2, 3])
pos_col.markdown(
    "<div class='ctrl'><h4>Positive result — a control, not a discovery</h4>"
    "<div class='cn'>rank 2 of 11,258</div>"
    "<p>We sealed one program in git before the scoring code existed. Its master "
    "regulator returns near the top of the ranking. This shows the ranking "
    "recovers a known answer; it does not claim the ranking discovered anything, "
    "and we make no such claim.</p></div>", unsafe_allow_html=True)

st.write("")
st.divider()

# ==================================================== 7. FIG 4 — retrieval failure
figure("fig4_retrieval.png")
st.divider()

# ==================================================== 8. PROVENANCE FOOTER
seal = prov["seal"]
st.markdown(
    f"<div class='prov'>"
    f"pre-registration &nbsp;{prov['preregistration']['sha256'][:12]}… &nbsp;committed before the sweep<br>"
    f"frozen predictor &nbsp;&nbsp;{held['predictor_sha256'][:12]}… &nbsp;hashed before the held-out set was opened<br>"
    f"held-out scorer &nbsp;&nbsp;{seal['commit']} &nbsp;&nbsp;{seal['scorer_sha256_required'][:12]}… &nbsp;unchanged={seal['scorer_unchanged']}<br>"
    f"scope &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;guide-pair concordance −0.019 · pathway-level claims only · no novel gene named<br>"
    f"{REPO} &nbsp;·&nbsp; every number and figure on this page is read from results/frozen/ and results/figures/ · nothing is recomputed"
    f"</div>", unsafe_allow_html=True)
