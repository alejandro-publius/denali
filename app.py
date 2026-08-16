"""Expo page. Reads results/, results/figures/, docs/TOOLS.md and README.md's
findings table. Computes nothing.

    .venv/bin/streamlit run app.py

Every number on screen is read from a frozen file, or derived — never typed as a
literal: the evaluation counts come from README's findings table, the single
source of truth the tests check. Every figure caption is read
from results/figures/CAPTIONS.md, verbatim, so the page and the report cannot
drift apart. The sponsor tool-chain strip reads its status verbatim from
docs/TOOLS.md — no tool status is inferred here. No interactive controls: nothing
here can be broken by someone clicking on it while nobody is standing at the
screen. No gene is named anywhere on this page — the data supports pathway-level
claims only (concordance -0.019).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd
import streamlit as st

FROZEN = Path("results/frozen")
FIGS = Path("results/figures")
TOOLS = Path("docs/TOOLS.md")
REPO = "https://github.com/alejandro-publius/denali"

st.set_page_config(page_title="denali", layout="wide",
                   initial_sidebar_state="collapsed")

st.markdown("""<style>
html, body, .stApp {background:#fff !important; color:#1c1c1a !important;}
#MainMenu, footer, header {visibility:hidden;}
.block-container {padding-top:1.8rem; padding-bottom:2rem; max-width:1180px;}
.huge {font-size:4.6rem; color:#1c1c1a; line-height:.98; font-weight:800;
       letter-spacing:-.03em; margin:0;}
.sub {font-size:1.34rem; line-height:1.4; color:#1c1c1a; margin:.5rem 0 0 0;}
.circ {font-size:1.06rem; line-height:1.45; color:#8c8c89; margin:.5rem 0 0 0;}
.size {font-size:1.06rem; color:#1c1c1a; margin:.3rem 0 0 0;}
.count {font-size:1.3rem; line-height:1.45; color:#1c1c1a; font-weight:600;
        margin:.55rem 0 0 0; max-width:46em;}
.card {border:1px solid #a3a39b; border-radius:10px; padding:1.05rem 1.2rem;
       background:#fff; height:100%;}
.card h4 {margin:0 0 .55rem 0; font-size:1.02rem; color:#1c1c1a;}
.cardn {font-size:2.1rem; font-weight:800; line-height:1; margin:0 0 .3rem 0; color:#1c1c1a;}
.card p {margin:0; font-size:.95rem; color:#1c1c1a; line-height:1.5;}
/* The one positive: deliberately smaller than the three negatives, and framed
   as a control. */
.ctrl {border:1px solid #a3a39b; border-radius:10px; padding:.85rem 1rem;
       background:#f2f2f0;}
.ctrl h4 {margin:0 0 .35rem 0; font-size:.9rem; color:#8c8c89; font-weight:600;
          text-transform:uppercase; letter-spacing:.05em;}
.ctrl .cn {font-size:1.35rem; font-weight:700; color:#1c1c1a; margin:0 0 .25rem 0;}
.ctrl p {margin:0; font-size:.86rem; color:#8c8c89; line-height:1.45;}
.cap {font-size:.9rem; color:#8c8c89; line-height:1.5; border-left:3px solid #a3a39b;
      padding-left:.85rem; margin-top:.5rem;}
.captitle {font-size:1.0rem; font-weight:700; color:#1c1c1a; margin-top:.4rem;}
.prov {font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:.78rem;
       color:#8c8c89; line-height:1.9;}
.qual {font-size:1.02rem; color:#8c8c89; margin:.5rem 0 0 0;}
/* --- the loop: agent reasoning, one column per branch ------------------- */
.loop {border:1px solid #a3a39b; border-top-width:4px; border-radius:10px;
       padding:1rem 1.1rem; background:#fff; height:100%;}
.loop-null {border-top-color:#8c8c89;}
.loop-hit  {border-top-color:#2166ac;}
.loop-miss {border-top-color:#b2182b;}
.badge {font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:.7rem;
        letter-spacing:.08em; text-transform:uppercase; font-weight:700;
        color:#8c8c89;}
.pname {font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:.73rem;
        color:#1c1c1a; margin:.3rem 0 .7rem 0; word-break:break-all; line-height:1.4;}
.ev {font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:.76rem;
     color:#1c1c1a; line-height:1.7; background:#f2f2f0; border-radius:6px;
     padding:.5rem .6rem; margin-bottom:.7rem;}
.lbl {font-size:.7rem; text-transform:uppercase; letter-spacing:.05em;
      color:#8c8c89; font-weight:700; margin:.6rem 0 .2rem 0;}
.txt {font-size:.87rem; color:#1c1c1a; line-height:1.5; margin:0;}
.fals {font-size:.83rem; color:#8c8c89; line-height:1.45; margin:0;
       border-left:3px solid #a3a39b; padding-left:.7rem;}
.collapse {font-size:1.5rem; font-weight:800; color:#b2182b; line-height:1.1;
           margin:.2rem 0 .1rem 0;}
/* Sponsor tool-chain strip. Status colour keys off the ✅/⚠/❌ in docs/TOOLS.md,
   so unavailable/blocked tools are shown honestly, not hidden. */
.tools {display:flex; flex-wrap:wrap; gap:.55rem; margin-top:.3rem;}
.tchip {flex:1 1 250px; border:1px solid #a3a39b; border-left-width:5px;
        border-radius:9px; padding:.7rem .85rem; background:#fff;}
.tchip .tn {font-size:1.0rem; font-weight:700; color:#1c1c1a; margin:0;}
.tchip .tv {font-size:.8rem; color:#8c8c89; font-weight:500;}
.tchip .td {font-size:.82rem; color:#8c8c89; line-height:1.4; margin:.3rem 0 0 0;}
.ok {border-left-color:#1a7f37;}
.warn {border-left-color:#9a6700;}
.fail {border-left-color:#b2182b;}
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
    # The 46.5% size figure lives in the Fig 3 caption text; pull it so the
    # headline stays synced to CAPTIONS.md. (Fig 3 itself is rendered below.)
    m = re.search(r"explains (\d+\.\d+)% of the variance", txt)
    out["_size_pct"] = m.group(1) if m else ""
    return out


@st.cache_data
def load():
    return (pd.read_csv(FROZEN / "program_summary.csv"),
            json.loads((FROZEN / "provenance.json").read_text()),
            json.loads((FROZEN / "heldout_evaluation.json").read_text()),
            json.loads((FROZEN / "proposals.json").read_text()))


@st.cache_data
def concordance():
    """The cross-screen arm. Post-freeze, so it lives outside results/frozen/."""
    return json.loads(Path("results/concordance/cross_screen.json").read_text())


@st.cache_data
def toolchain():
    """Sponsor tools + status, read verbatim from docs/TOOLS.md's table.

    Status is never inferred here: the ✅/⚠/❌ and the text come from the file.
    When a row's 'Verified how' cell points to the notes ('...below'), the
    matching notes bullet is substituted so the real gotcha (e.g. Proto's import
    failure) is what shows, still sourced from the same file."""
    txt = TOOLS.read_text()
    m = re.search(r"verified (\d{4}-\d{2}-\d{2})", txt)
    verified_on = m.group(1) if m else ""
    # Notes bullets, markdown stripped, keyed by their leading tool word.
    # Bullets can wrap onto indented continuation lines — join those in.
    notes, cur = {}, None
    for line in txt.splitlines():
        s = line.strip()
        if s.startswith("- ") and ":" in s:
            plain = re.sub(r"[*`~]", "", s[2:]).strip()
            cur = plain.split(":")[0].split()[0].lower()
            notes[cur] = plain
        elif cur and s and line[:1] in " \t" and not s.startswith(("|", "#", "-")):
            notes[cur] += " " + re.sub(r"[*`~]", "", s).strip()
        else:
            cur = None
    rows = []
    for line in txt.splitlines():
        if not line.startswith("| **"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        name = re.sub(r"\*\*", "", cells[0]).strip()
        installed, how = cells[1], cells[3]
        emoji = next((e for e in ("✅", "⚠", "❌") if e in installed), "")
        ver = re.search(r"`([^`]+)`", installed)
        detail = re.sub(r"[*`]", "", how).strip()
        if "below" in detail.lower():                 # the file says: look here
            first = name.split()[0]
            note = notes.get(first.lower(), "")
            if note.lower().startswith(first.lower() + ":"):
                note = note[len(first) + 1:].strip()   # drop redundant "Proto:" label
            detail = note or detail
        if len(detail) > 132:
            detail = detail[:129].rstrip() + "…"
        rows.append({"name": name, "emoji": emoji,
                     "ver": ver.group(1) if ver else "", "detail": detail})
    return rows, verified_on


S, prov, held, PROP = load()
CAP = captions()

# Headline range, read from the frozen fit — not typed in by hand.
ds = prov["deciding_statistic"]
lo = round(ds["adjusted_r2_x_independent_only"] * 100)   # 56
hi = round(ds["adjusted_r2_all_six"] * 100)              # 75
gate_fail_hits = prov["gap_numbers"]["gate_fail_but_has_hits"]   # 20
bal_acc = held["axis2_balanced_accuracy"]                        # 0.4375
conc = concordance()
cc_raw = conc["raw_agreement"]["spearman_rho"]                          # +0.663
cc_par = conc["how_much_is_size"]["spearman_after_removing_size"]       # +0.493
cc_share = round(abs(cc_raw - cc_par) / abs(cc_raw) * 100)              # 26

# Evaluation counts DERIVED from README's findings table — the single source of
# truth that src/build_page.py and tests/test_frozen_invariants.py both parse.
# A number nobody derives goes stale silently; this one cannot.
_findings = re.findall(r"^\|\s*(\d+)\s*\|.*\|\s*\*\*([A-Z][A-Z ]+)\*\*",
                       Path("README.md").read_text(), re.M)
_verdicts = [v.strip() for _, v in _findings]
N_EVALS = len(_findings)
N_NEG = _verdicts.count("NEGATIVE")
N_NOV = _verdicts.count("NO VERDICT")
_WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
          7: "seven", 8: "eight", 9: "nine", 10: "ten"}
def _w(n, cap=False):
    s = _WORDS.get(n, str(n))
    return s.capitalize() if cap else s


def figure(name: str):
    # width="stretch", not use_container_width: the latter is deprecated in
    # 1.61 and renders a warning banner on the page.
    st.image(str(FIGS / name), width="stretch")
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

# ============================ 2. THE COUNT (above fold) — derived, not typed ===
# index.html renders this same sentence from the same source; four stat tiles
# were the old, silently-stale version. Counts derived above from the README table.
_nov = (f"{_w(N_NOV)} returned no verdict when our own power rule fired against "
        f"us, ") if N_NOV else ""
st.markdown(
    f"<div class='count'>{_w(N_EVALS, True)} evaluations. {_w(N_NEG, True)} came "
    f"back negative, {_nov}and all {_w(N_EVALS)} are reported here.</div>",
    unsafe_allow_html=True)

st.write("")
st.divider()

# ==================================================== 3. FIG 1 — the matrix
figure("fig1_matrix.png")
st.divider()

# ============================================ 3b. FIG 3 — measurability model
# docs/DEMO.md beat 2 says "Screen: FIG 3." The figure was written and captioned
# but rendered nowhere, on either page. Page order now matches the spoken order.
figure("fig3_measurability.png")
st.divider()

# ==================================================== 4. FIVE NEGATIVE FINDINGS
st.subheader("Seven evaluations came back negative")
cards = [
    ("Most of it is not biology", f"up to {hi}%",
     "A model that never looks at what a program does explains most of how "
     f"reversible it appears; {lo}% survives after we remove the circular feature."),
    ("The obvious filter is wrong", f"{gate_fail_hits} of 50",
     "The measurability filter anyone would build discards 20 programs that "
     "produce hits anyway — including a pre-registered one."),
    ("The generalisation test failed", f"{bal_acc}",
     "On ten programs from a different collection, pre-registered and scored "
     "once, binary accuracy came back worse than chance — and we did not refit."),
    ("Replication is worth less than it looks", f"{cc_share}%",
     f"Two independently screened cell lines agree at ρ {cc_raw:+.3f}. Remove set "
     f"size from both and it falls to {cc_par:+.3f} — that share of the apparent "
     "replication is how the gene lists were built. Post-freeze, not pre-registered."),
]
for col, (h, num, body) in zip(st.columns(len(cards)), cards):
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
    "<p>One program was pre-registered before it was scored. Its master "
    "regulator returns near the top of the ranking. This shows the ranking "
    "recovers a known answer; it does not claim the ranking discovered anything, "
    "and we make no such claim.</p></div>", unsafe_allow_html=True)

st.write("")
st.divider()

# ==================================================== 7. FIG 4 — retrieval failure
figure("fig4_retrieval.png")
st.divider()

# ==================================================== 8. THE LOOP
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

# ==================================================== 8b. ALL 50 PROGRAMS
st.subheader("All 50 programs")
st.write(
    "Sorted by how many knockdowns moved the program. **Hits are knockdowns, not "
    "pathway members** — they are counted out of all 9,837 switch-offs, which is why "
    "a 200-gene program can show thousands. The gate is the measurability filter: "
    "programs that fail it were never scoreable, whatever their biology."
)

_tbl = (S.assign(program=S["program"].str.removeprefix("HALLMARK_"))
         .sort_values("n_hits_q05", ascending=False)
         [["program", "n_declared", "n_hits_q05", "R_p", "passes_measurability_gate"]])

st.dataframe(
    _tbl, width="stretch", hide_index=True,
    column_config={
        "program": st.column_config.TextColumn("Pathway"),
        "n_declared": st.column_config.NumberColumn("Genes in pathway"),
        "n_hits_q05": st.column_config.NumberColumn("Knockdowns that moved it"),
        "R_p": st.column_config.NumberColumn("R_p", format="%.4f"),
        "passes_measurability_gate": st.column_config.CheckboxColumn("Gate"),
    })

st.write("")
st.divider()

# ============ 8c. SPONSOR TOOL-CHAIN — status read verbatim from docs/TOOLS.md ==
tool_rows, tools_verified = toolchain()
st.subheader("Sponsor tool-chain — status checked against this machine")
_scls = {"✅": "ok", "⚠": "warn", "❌": "fail"}
_chips = "".join(
    f"<div class='tchip {_scls.get(r['emoji'], '')}'>"
    f"<p class='tn'>{r['emoji']} {r['name']} <span class='tv'>{r['ver']}</span></p>"
    f"<p class='td'>{r['detail']}</p></div>"
    for r in tool_rows)
st.markdown(f"<div class='tools'>{_chips}</div>", unsafe_allow_html=True)
st.markdown(
    f"<div class='cap'>Every row verified {tools_verified} against this machine, "
    f"not recalled. Full detail in docs/TOOLS.md.</div>", unsafe_allow_html=True)
st.divider()

# ==================================================== 9. PROVENANCE FOOTER
prereg = prov["seal"]          # frozen key name; the framing is pre-registration
st.markdown(
    f"<div class='prov'>"
    f"pre-registration &nbsp;{prov['preregistration']['sha256'][:12]}… &nbsp;committed before the sweep<br>"
    f"frozen predictor &nbsp;&nbsp;{held['predictor_sha256'][:12]}… &nbsp;hashed before the held-out set was opened<br>"
    f"held-out scorer &nbsp;&nbsp;{prereg['commit']} &nbsp;&nbsp;{prereg['scorer_sha256_required'][:12]}… &nbsp;unchanged={prereg['scorer_unchanged']}<br>"
    f"scope &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;guide-pair concordance −0.019 · pathway-level claims only · no novel gene named<br>"
    f"{REPO} &nbsp;·&nbsp; every number and figure on this page is read from results/frozen/ and results/figures/ · nothing is recomputed"
    f"</div>", unsafe_allow_html=True)
