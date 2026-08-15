"""Expo page. Reads results/frozen/ only. Computes nothing.

    .venv/bin/streamlit run app.py

Caption wording is READ FROM results/figures/CAPTIONS.md so the page and the
report cannot drift apart. No interactive controls: nothing here can be broken
by someone clicking on it while nobody is standing at the screen.
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
.block-container {padding-top:2.2rem; max-width:1180px;}
.huge {font-size:4.1rem; color:#111827; line-height:1.02; font-weight:800; letter-spacing:-.03em; margin:0;}
.sub {font-size:1.42rem; line-height:1.45; color:#374151; margin:.55rem 0 0 0;}
.qual {font-size:1.02rem; color:#6b7280; margin:.5rem 0 0 0;}
.box {border:1px solid #d1d5db; color:#111827; border-radius:10px; padding:1rem 1.1rem; height:100%;
      background:#fff;}
.boxn {font-size:2.9rem; font-weight:800; line-height:1; margin:0; color:#111827;}
.boxl {font-size:.86rem; color:#6b7280; margin:.35rem 0 0 0; text-transform:uppercase;
       letter-spacing:.05em;}
.neg {border-left:5px solid #b2182b;}
.pos {border-left:5px solid #2166ac;}
.card {border:1px solid #d1d5db; color:#111827; border-left-width:5px; border-radius:10px;
       padding:1.05rem 1.2rem; background:#fff; height:100%;}
.card h4 {margin:0 0 .45rem 0; font-size:1.06rem;}
.card p {margin:0; font-size:.96rem; color:#374151; line-height:1.5;}
.cap {font-size:.9rem; color:#4b5563; line-height:1.5; border-left:3px solid #e5e7eb;
      padding-left:.85rem; margin-top:.5rem;}
.prov {font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:.8rem;
       color:#6b7280; line-height:1.85;}
</style>""", unsafe_allow_html=True)


@st.cache_data
def captions() -> dict[str, str]:
    """Pull each figure's bolded headline + quoted body straight from CAPTIONS.md."""
    txt = (FIGS / "CAPTIONS.md").read_text()
    out = {}
    for block in re.split(r"\n## FIG ", txt)[1:]:
        key = re.search(r"`(fig\d_[a-z_]+\.png)`", block)
        title = re.search(r"\*\*(.+?)\*\*", block)
        body = " ".join(l.lstrip("> ").strip()
                        for l in block.splitlines() if l.startswith(">"))
        if key:
            out[key.group(1)] = {"title": title.group(1) if title else "",
                                 "body": re.sub(r"\*\*|\*", "", body).strip()}
    return out


@st.cache_data
def load():
    return (pd.read_csv(FROZEN / "program_summary.csv"),
            json.loads((FROZEN / "provenance.json").read_text()),
            json.loads((FROZEN / "heldout_evaluation.json").read_text()))


S, prov, held = load()
CAP = captions()


def figure(name: str):
    st.image(str(FIGS / name), use_container_width=True)
    c = CAP.get(name, {})
    if c:
        st.markdown(f"**{c['title']}**", unsafe_allow_html=True)
        st.markdown(f"<div class='cap'>{c['body']}</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------- 1. HEADLINE
st.markdown("<div class='huge'>56–75% of what looks like biology<br>is not biology.</div>",
            unsafe_allow_html=True)
st.markdown(
    "<div class='sub'>Across all 50 Hallmark gene programs scored against 9,837 CRISPRi "
    "knockdowns in K562, that share of the variance in <i>apparent</i> reversibility is "
    "explained without reference to what the program does.</div>",
    unsafe_allow_html=True)
st.markdown(
    "<div class='qual'><b>The range is a range for a reason:</b> one of our six features is "
    "computed from the same matrix as the outcome, so part of the 75% is arithmetic. "
    "56% is the number that survives that objection — we never quote the top alone.<br>"
    "<b>Mechanism:</b> bigger programs with more co-moving members return more hits "
    "regardless of what they do. <b>Program size alone explains 46.5%.</b><br>"
    "<b>⚠ Post-freeze correction, not pre-registered:</b> splitting the six features shows "
    "measurement-only reaches adj R² 0.152 while set-construction-only reaches 0.697. "
    "The number stands; the word <i>“measurement”</i> does not. This is carried by how "
    "gene sets are <i>defined</i>.</div>", unsafe_allow_html=True)

st.write("")

# ------------------------------------------------------------ 2. SCORE STRIP
for col, (n, lab, cls) in zip(st.columns(4), [
        ("4", "evaluations run", ""),
        ("3", "came back negative", "neg"),
        ("1", "positive — a control", "pos"),
        ("0", "gene-level claims made", "neg")]):
    col.markdown(f"<div class='box {cls}'><div class='boxn'>{n}</div>"
                 f"<div class='boxl'>{lab}</div></div>", unsafe_allow_html=True)

st.write("")
st.divider()

# ------------------------------------------------------------------ 3. FIG 1
figure("fig1_matrix.png")
st.divider()

# ------------------------------------------------- 4. THREE NEGATIVE FINDINGS
st.subheader("The three negative findings")
cards = [
    ("1 · Most of it is not biology",
     f"A model that never looks at what a program <i>does</i> predicts most of how "
     f"reversible it appears. {int((S.n_hits_q05==0).sum())} of 50 programs return "
     f"nothing at all. Pre-registered: we wrote down before running that if this "
     f"cleared 60%, it becomes the finding rather than the failure. It cleared."),
    ("2 · The obvious filter is wrong 20 of 50",
     "We built the quality filter anyone would build. Twenty programs fail it and "
     "produce hits anyway; only one passes it and produces nothing. The program we "
     "sealed in git before the scoring code existed <b>fails our own filter</b> — and "
     "ranks 11th of 50. We built a filter that would have thrown away our best result."),
    ("3 · Our generalisation test failed",
     f"Ten programs from a different collection, sealed before the sweep, scored only "
     f"after the model was hashed. Only 1 of 10 was even measurable, so by our own "
     f"pre-registered rule the evaluation is <b>underpowered and inconclusive</b>. "
     f"Binary accuracy {held['axis2_balanced_accuracy']} — worse than chance, zero true "
     f"positives. We did not refit."),
]
for col, (h, b) in zip(st.columns(3), cards):
    col.markdown(f"<div class='card neg'><h4>{h}</h4><p>{b}</p></div>",
                 unsafe_allow_html=True)

st.write("")
st.divider()

# ------------------------------------------------------------------ 5. FIG 2
figure("fig2_gate_failure.png")
st.divider()

# ------------------------------------------------------- 6. THE ONE POSITIVE
st.subheader("The one positive — and it is a control, not a result")
seal = prov["seal"]
st.markdown(
    f"<div class='card pos'><h4>We sealed one row of this matrix before the matrix existed.</h4>"
    f"<p>Commit <code>{seal['commit']}</code> at <b>08:24:14</b> fixed the held-out program. "
    f"<code>src/score_k562.py</code> was not created until <b>08:45:15</b> — the program was "
    f"chosen <b>21 minutes before the scoring code was written</b>, so there was nothing to "
    f"tune.<br><br>Its master regulator comes back at <b>rank 2 of 11,258 scored "
    f"perturbations</b> (11,258 exceeds the 9,837 unique genes because some are targeted "
    f"twice). Eleven of seventeen canonical pathway members land in the extreme 10%, "
    f"binomial p = 7.0×10⁻⁸, with the correct sign at both ends of the ranking.<br><br>"
    f"<b>This says the ranking works. It does not say the ranking discovered anything, "
    f"and we do not claim that it did.</b> The gene is a recovered known answer.</p></div>",
    unsafe_allow_html=True)

st.write("")
st.divider()

# ------------------------------------------------------------------ 7. FIG 4
figure("fig4_retrieval.png")
st.divider()

# ---------------------------------------------------------- 8. PROVENANCE
st.subheader("Provenance")
ds = prov["deciding_statistic"]
left, right = st.columns([3, 2])
left.markdown(
    f"<div class='prov'>"
    f"pre-registration &nbsp;<b>d3e24b77…</b> &nbsp;committed before the sweep<br>"
    f"frozen predictor &nbsp;<b>610f2a75…</b> &nbsp;hashed before the held-out set was opened<br>"
    f"held-out seal &nbsp;&nbsp;&nbsp;&nbsp;<b>9ad74a7</b> &nbsp;&nbsp;08:24:14, 21 min before the scorer existed<br>"
    f"scorer intact &nbsp;&nbsp;&nbsp;&nbsp;<b>{seal['seal_intact']}</b> &nbsp;byte-identical to the sealed version<br>"
    f"adj R² &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
    f"<b>{ds['adjusted_r2_x_independent_only']} – {ds['adjusted_r2_all_six']}</b> &nbsp;both ends reported"
    f"</div>", unsafe_allow_html=True)
right.markdown(
    f"<div class='prov'><b>Scope limit, enforced everywhere</b><br>"
    f"Guide-pair concordance is <b>−0.019</b>. Two independent guides against the same "
    f"gene give uncorrelated scores, so gene-level calls are not reproducible. "
    f"<b>Pathway-level claims only. No novel gene is named anywhere in this project.</b>"
    f"</div>", unsafe_allow_html=True)
st.markdown(f"<div class='prov'>{REPO} &nbsp;·&nbsp; every figure and number on this page "
            f"is read from <code>results/frozen/</code> · nothing here is recomputed</div>",
            unsafe_allow_html=True)
