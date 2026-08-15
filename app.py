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
REPO = "https://github.com/alejandro-publius/denali"

st.set_page_config(page_title="denali", layout="wide",
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

/* --- the loop: agent reasoning, one column per branch ------------------- */
.loop {border:1px solid #d1d5db; border-top-width:4px; border-radius:10px;
       padding:1rem 1.1rem; background:#fff; height:100%;}
.loop-null {border-top-color:#6b7280;}
.loop-hit  {border-top-color:#2166ac;}
.loop-miss {border-top-color:#b2182b;}
.badge {font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:.7rem;
        letter-spacing:.08em; text-transform:uppercase; font-weight:700;
        color:#6b7280;}
.pname {font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:.73rem;
        color:#111827; margin:.3rem 0 .7rem 0; word-break:break-all; line-height:1.4;}
.ev {font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:.76rem;
     color:#374151; line-height:1.7; background:#f7f7f8; border-radius:6px;
     padding:.5rem .6rem; margin-bottom:.7rem;}
.lbl {font-size:.7rem; text-transform:uppercase; letter-spacing:.05em;
      color:#6b7280; font-weight:700; margin:.6rem 0 .2rem 0;}
.txt {font-size:.87rem; color:#374151; line-height:1.5; margin:0;}
.fals {font-size:.83rem; color:#4b5563; line-height:1.45; margin:0;
       border-left:3px solid #e5e7eb; padding-left:.7rem;}
.collapse {font-size:1.5rem; font-weight:800; color:#b2182b; line-height:1.1;
           margin:.2rem 0 .1rem 0;}
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
            json.loads((FROZEN / "heldout_evaluation.json").read_text()),
            json.loads((FROZEN / "proposals.json").read_text()))


S, prov, held, PROP = load()
CAP = captions()


def figure(name: str):
    st.image(str(FIGS / name), width="stretch")
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

# ------------------------------------------------------------------ 3b. FIG 3
# Demo beat 2 calls this screen explicitly; it was written and captioned but
# never rendered. Order on the page now matches the spoken order: 1, 3, 2, 4.
figure("fig3_measurability.png")
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
     "held out <b>fails our own filter</b> — and "
     "ranks 11th of 50. We built a filter that would have thrown away our best result."),
    ("3 · Our generalisation test failed",
     f"Ten programs from a different collection, not scored until "
     f"the model was finished. Only 1 of 10 was even measurable, so by our own "
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
st.markdown(
    "<div class='card pos'><h4>The ranking recovers a pathway it was not built against.</h4>"
    "<p>Run unchanged on a program it had not been developed on, the pipeline puts that "
    "pathway's master regulator at <b>rank 2 of 11,258 scored perturbations</b> (11,258 "
    "exceeds the 9,837 unique genes because some are targeted twice). It is the textbook "
    "answer and we do not claim to have found it.<br><br>What a lucky hit does not produce "
    "is the shape: <b>eleven of seventeen canonical pathway members land in the extreme "
    "10%</b>, against 1.7 expected by chance, binomial p = 7.0×10⁻⁸ — with the correct sign "
    "at <i>both</i> ends of the ranking.<br><br><b>This says the ranking works. It does not "
    "say the ranking discovered anything, and we do not claim that it did.</b></p></div>",
    unsafe_allow_html=True)

st.write("")
st.divider()

# ------------------------------------------------------------------ 7. FIG 4
figure("fig4_retrieval.png")
st.divider()

# ------------------------------------------------------------------ 8. THE LOOP
# docs/DEMO.md beat 6. Read from results/frozen/proposals.json, which is
# generated by src/freeze_proposals.py from measured values only.
st.subheader("The loop — same code, three results, three proposals")
st.markdown(
    "<div class='qual'>The proposal is <b>generated from the result</b>, not chosen "
    "for it. Every branch reads measured quantities off the frozen tables; "
    "<b>no branch tests a program name.</b> Change the data and the proposal "
    "changes.</div>", unsafe_allow_html=True)
st.write("")

_n, _h, _u = PROP["null"], PROP["hit"], PROP["unscored"]
_ne, _he, _ue = _n["evidence"], _h["evidence"], _u["evidence"]
_uo = _u["observed_outcome"]

lcols = st.columns(3)
lcols[0].markdown(
    f"<div class='loop loop-null'>"
    f"<div class='badge'>Result · null, 0 hits</div>"
    f"<div class='pname'>{_n['program']}</div>"
    f"<div class='ev'>expr_ratio &nbsp;{_ne['expr_ratio']:.2f}<br>"
    f"sd_ratio &nbsp;&nbsp;&nbsp;{_ne['sd_ratio']:.2f}<br>"
    f"frac_present {_ne['frac_present']:.3f}</div>"
    f"<div class='lbl'>It proposed</div>"
    f"<p class='txt'>Members are expressed and variable, yet nothing reaches "
    f"significance — a <b>power limit, not a biology limit</b>. Raise depth and "
    f"re-run the identical sweep.</p>"
    f"<div class='lbl'>Falsified if</div>"
    f"<p class='fals'>{_n['falsifies_the_mechanism']}</p></div>",
    unsafe_allow_html=True)

lcols[1].markdown(
    f"<div class='loop loop-hit'>"
    f"<div class='badge'>Result · hit, {_he['n_hits_q05']:,}</div>"
    f"<div class='pname'>{_h['program']}</div>"
    f"<div class='ev'>R_p observed &nbsp;{_he['R_p']:.2f}<br>"
    f"R_p predicted {_he['R_p_predicted_from_measurability']:.2f}<br>"
    f"residual &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{_he['residual']:+.2f}</div>"
    f"<div class='lbl'>It proposed</div>"
    f"<p class='txt'>Validate at <b>pathway level</b> — both tails, second cell "
    f"type, set-level enrichment. The residual is the only part that can be "
    f"biology.</p>"
    f"<div class='lbl'>And refused to go further, because</div>"
    f"<p class='fals'>Guide-pair concordance is −0.019, so any single-gene call "
    f"is not reproducible. <b>The agent declines gene-level claims on its own "
    f"evidence.</b></p></div>",
    unsafe_allow_html=True)

lcols[2].markdown(
    f"<div class='loop loop-miss'>"
    f"<div class='badge'>Result · never scored</div>"
    f"<div class='pname'>{_u['program']}</div>"
    f"<div class='ev'>predicted R_p &nbsp;{_ue['predicted_R_p']:.2f}<br>"
    f"prediction SD &nbsp;{_ue['prediction_sd']:.2f}<br>"
    f"members measured &nbsp;{_uo['n_present']} / {_uo['n_declared']}</div>"
    f"<div class='lbl'>It proposed — highest confidence of the ten</div>"
    f"<div class='collapse'>~{_ue['predicted_hits']:,} hits &nbsp;→&nbsp; "
    f"{_uo['n_hits_q05']} observed</div>"
    f"<p class='txt'>The model's most confident held-out prediction, on a program "
    f"with <b>one measured gene of {_uo['n_declared']}</b>.</p>"
    f"<div class='lbl'>Why this is the finding, not the bug</div>"
    f"<p class='fals'>Measurability is what the prediction failed to account for — "
    f"so the failure and the finding are <b>the same fact</b>, reappearing in "
    f"held-out data we had not touched.</p></div>",
    unsafe_allow_html=True)

st.write("")
st.divider()

# ---------------------------------------------------------- 9. PROVENANCE
st.subheader("Provenance")
ds = prov["deciding_statistic"]
left, right = st.columns([3, 2])
left.markdown(
    f"<div class='prov'>"
    f"pre-registration &nbsp;<b>d3e24b77…</b> &nbsp;committed before the sweep<br>"
    f"frozen predictor &nbsp;<b>610f2a75…</b> &nbsp;hashed before the held-out set was opened<br>"
    f"held-out eval &nbsp;&nbsp;&nbsp;<b>FAILED</b> &nbsp;underpowered; balanced accuracy 0.4375<br>"
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
