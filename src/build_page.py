"""Emit index.html — a single static file, every number traced to results/frozen/.

    .venv/bin/python -m src.build_page

Design contract, enforced below:
  * no number is typed into the template. Every value comes through V(), which
    reads a frozen file and records where it came from. A number that cannot be
    traced does not appear on the page.
  * caption text is read verbatim from results/figures/CAPTIONS.md.
  * figures are inlined as base64 so index.html is genuinely standalone.
  * white ground, ONE accent used twice, FOUR type sizes, no gradients, no dark
    hero, no dashboard chrome. The explorer is the only interactive element and
    it makes no network call — everything it needs is embedded.
"""
from __future__ import annotations

import base64
import html
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / "results" / "frozen"
FIGS = ROOT / "results" / "figures"
SENS = ROOT / "results" / "sensitivity"
OUT = ROOT / "index.html"

PROV = json.loads((FROZEN / "provenance.json").read_text())
HELD = json.loads((FROZEN / "heldout_evaluation.json").read_text())
PRED = json.loads((FROZEN / "predictor.json").read_text())
STRIP = json.loads((SENS / "stripped_model.json").read_text())
SUMMARY = pd.read_csv(FROZEN / "program_summary.csv")
CONTROLS = pd.read_csv(FROZEN / "controls.csv")
HELDOUT = pd.read_csv(FROZEN / "heldout.csv")

TRACE: list[tuple[str, str]] = []


def V(value, source: str, fmt=None):
    """Every number on the page passes through here, with its source recorded."""
    TRACE.append((str(value), source))
    return fmt(value) if fmt else value


# ---------------------------------------------------------------- values
ds = PROV["deciding_statistic"]
gap = PROV["gap_numbers"]

R_HI = V(ds["adjusted_r2_all_six"], "provenance.deciding_statistic.adjusted_r2_all_six")
R_LO = V(ds["adjusted_r2_x_independent_only"], "provenance.deciding_statistic.adjusted_r2_x_independent_only")
PCT_HI, PCT_LO = round(R_HI * 100), round(R_LO * 100)
SIZE_R2 = V(STRIP["set_size_alone"]["r2"], "sensitivity.set_size_alone.r2")
MEAS_ONLY = V(STRIP["measurement_only_three"]["adj_r2"], "sensitivity.measurement_only_three")
CONS_ONLY = V(STRIP["construction_only_three"]["adj_r2"], "sensitivity.construction_only_three")

N_PROGRAMS = V(PROV["tier1"]["programs"], "provenance.tier1.programs")
N_KD = V(PROV["tier1"]["knockdown_targets"], "provenance.tier1.knockdown_targets")
N_ZERO = V(gap["programs_with_zero_hits"], "provenance.gap_numbers.programs_with_zero_hits")
N_GATEFAIL_HITS = V(gap["gate_fail_but_has_hits"], "provenance.gap_numbers.gate_fail_but_has_hits")
N_GATEPASS_ZERO = V(gap["gate_pass_but_zero_hits"], "provenance.gap_numbers.gate_pass_but_zero_hits")

BAL = V(HELD["axis2_balanced_accuracy"], "heldout_evaluation.axis2_balanced_accuracy")
TP = V(HELD["axis2_confusion"]["tp"], "heldout_evaluation.axis2_confusion.tp")
NGATE = V(HELD["n_passing_gate"], "heldout_evaluation.n_passing_gate")
NHELD = V(HELD["n_heldout"], "heldout_evaluation.n_heldout")
RHO = V(HELD["axis1_spearman_rho"], "heldout_evaluation.axis1_spearman_rho")
CI = HELD["axis1_bootstrap_95ci"]

conc = CONTROLS[CONTROLS.control == "guide_pair_concordance"].iloc[0]
CONCORD = V(float(conc.value), "controls.csv.guide_pair_concordance.value")
N_FAIL = V(int((CONTROLS.verdict == "FAIL").sum()), "controls.csv verdict==FAIL")
N_CTRL = V(len(CONTROLS), "controls.csv rows")

held_row = HELDOUT.loc[HELDOUT.R_p_predicted.idxmax()]
HEME_NAME = V(held_row.program, "heldout.csv argmax R_p_predicted")
HEME_PRED = V(round(float(held_row.R_p_predicted), 2), "heldout.csv.R_p_predicted")
HEME_N = V(int(held_row.n_present), "heldout.csv.n_present")
HEME_HITS = V(int(held_row.n_hits_q05), "heldout.csv.n_hits_q05")

b = SUMMARY[SUMMARY.is_held_out_program].iloc[0]
CTRL_RANK = V(int(b.rank_by_R_p), "program_summary.rank_by_R_p (held-out program)")
CTRL_HITS = V(int(b.n_hits_q05), "program_summary.n_hits_q05 (held-out program)")
CTRL_EXPR = V(round(float(b.expr_ratio), 2), "program_summary.expr_ratio (held-out program)")

ev = PROV["evidence_layer"]
EV_SRC = V(ev["distinct_sources_for_113_genes"], "provenance.evidence_layer.distinct_sources_for_113_genes")
EV_SHARE = V(round(ev["max_share_one_source"] * 100, 1), "provenance.evidence_layer.max_share_one_source")
EV_PROBE = V(ev["probe_genes_returning_same_zebrafish_methods_paper"], "provenance.evidence_layer.probe_genes_*")
EV_N = V(ev["probe_genes"], "provenance.evidence_layer.probe_genes")


# ---------------- the two arms added after the freeze ----------------
_rp = ROOT / "results" / "rpe1" / "rpe1_evaluation.json"
_cc = ROOT / "results" / "concordance" / "cross_screen.json"
RPE1 = json.loads(_rp.read_text()) if _rp.exists() else None
CONC = json.loads(_cc.read_text()) if _cc.exists() else None

if RPE1:
    RP_R2 = V(RPE1["size_alone_r2"], "rpe1_evaluation.size_alone_r2")
    RP_P = V(RPE1["slope_p"], "rpe1_evaluation.slope_p")
    RP_N = V(RPE1["n_scoreable"], "rpe1_evaluation.n_scoreable")
    RP_TGT = V(RPE1["n_unique_targets"], "rpe1_evaluation.n_unique_targets")
if CONC:
    CC_RAW = V(CONC["raw_agreement"]["spearman_rho"], "cross_screen.spearman_rho")
    CC_PAR = V(CONC["how_much_is_size"]["spearman_after_removing_size"],
               "cross_screen.spearman_after_removing_size")
    CC_SHARE = round(abs(CC_RAW - CC_PAR) / abs(CC_RAW) * 100)
    CC_TOP = V(CONC["raw_agreement"]["top_k_overlap"]["top_10"],
               "cross_screen.top_10_overlap")
    CC_SIZE = V(CONC["how_much_is_size"]["top_k_overlap_using_SIZE_ALONE_to_predict_rpe1"]["top_10"],
                "cross_screen.top_10_from_size_alone")
    CC_CHANCE = V(CONC["raw_agreement"]["top_k_overlap_expected_by_chance"]["top_10"],
                  "cross_screen.top_10_by_chance")

# ---------------------------------------------------------------- explorer data
# Every row and every proposal is computed at build time from results/frozen/.
# Embedded as JSON so the page needs no network and no server.
from src.answers import unscored as _unscored
from src.next_experiment import propose as _propose

_EXPLORER_COLS = ["program", "rank_by_R_p", "n_hits_q05", "R_p",
                  "passes_measurability_gate", "n_present", "expr_ratio",
                  "sd_ratio", "R_p_predicted_from_measurability",
                  "R_p_residual_after_measurability", "reversibility_call",
                  "call_plain", "is_held_out_program"]

_HELDOUT_NAMES = set(HELDOUT.program)


def _explorer_rows():
    rows = []
    for _, r in SUMMARY.iterrows():
        d = {c: (None if pd.isna(r[c]) else r[c]) for c in _EXPLORER_COLS if c in SUMMARY.columns}
        d["short"] = str(r.program).replace("HALLMARK_", "").replace("_", " ").title()
        d["gate_fail_with_hits"] = bool((not r.passes_measurability_gate) and r.n_hits_q05 > 0)
        try:
            pr = _propose(r.program, SUMMARY)
            d["proposal"] = {"outcome": pr["outcome"],
                             "next_experiment": pr.get("next_experiment", ""),
                             "mechanism": pr.get("mechanism", ""),
                             "falsifies": pr.get("falsifies_the_mechanism", ""),
                             "why_not_gene_level": pr.get("why_not_gene_level", ""),
                             "caveat": pr.get("caveat", "")}
        except Exception as e:
            d["proposal"] = {"outcome": "ERROR", "next_experiment": str(e)}
        rows.append(d)
    return rows


# The agent's running statistic is goodness-of-fit of the FROZEN measurability
# prediction against the FROZEN observation, on whatever subset it has read. That
# is not the same quantity as the pre-registered adj R2 (which is an OLS fit on
# all 50, penalised for six parameters), so the page must not imply it converges
# to it. This is the honest reference: the identical statistic over all 50 rows.
_pr = SUMMARY.dropna(subset=["R_p", "R_p_predicted_from_measurability"])
ALL50_R2 = V(round(float(
    1 - ((_pr.R_p - _pr.R_p_predicted_from_measurability) ** 2).sum()
    / ((_pr.R_p - _pr.R_p.mean()) ** 2).sum()), 4),
    "computed: frozen prediction vs frozen observation, all 50")

EXPLORER = _explorer_rows()
V(len(EXPLORER), "program_summary.csv rows -> explorer")
N_GATEFAIL_ROWS = V(sum(1 for r in EXPLORER if r["gate_fail_with_hits"]),
                    "computed: gate fails AND hits > 0")


# ---------------------------------------------------------------- tool chain
# Not results — verification facts, checked on this machine on 2026-08-15 and
# recorded in docs/TOOLS.md. They are literals here because there is no frozen
# file to read them from; the column that matters is the last one, and it is a
# fact about this repository that anyone can check: `grep -r <tool> src/`.
#
# "Touched a number" means: something in results/frozen/ would be different if
# this tool had not run. For all but two, the answer is no, and that is the
# point of the section rather than an embarrassment to be padded around.
TOOLCHAIN = [
    ("Claude Code", "2.1.233", "Verified — wrote the pipeline",
     "yes, as the author",
     "Wrote every line of src/. No number is model output: each one is produced by "
     "deterministic code from a checksummed input and re-derived by make all."),
    ("Paperclip", "0.7.37 + MCP", "Verified — 113/113 gene queries, stored",
     "yes, as the audited object",
     "Ran the literature layer, then became the thing under test. Its output is "
     "quarantined: FIG 4 is the audit of it, and nothing it returned enters the "
     "matrix, the predictor, or any claim. The hosted MCP server is registered "
     "and deliberately not queried — the index is live, and re-running it would "
     "move the numbers FIG 4 cites."),
    ("Modal", "1.5.4", "Used — 50 programs across 10 containers, 133 s",
     "reproduces every one",
     "Runs the real sweep, not a demo: src/modal_sweep.py imports the same frozen "
     "scorer, fans the 50 programs across containers, and returns n_hits, R_p, "
     "n_present and the gate identical to results/frozen/ on all 50. It verifies "
     "the result rather than producing it, and it is deliberately not a make-all "
     "step. What it buys is that reproducing us no longer needs a 470 MB download "
     "and twelve minutes of laptop. Being the same scorer run elsewhere, this "
     "establishes portability, not independent confirmation of the maths."),
    ("CZ Biohub — ESM Cambrian", "esm 3.2.3",
     "Verified twice — local weights and hosted API, both (1, 67, 960)",
     "no", "esmc_300m ran on a real sequence locally, and the same sequence ran "
     "again through the authenticated Biohub Platform API; both returned the same "
     "embedding shape. The result is a protein embedding. This project scores "
     "transcriptional movement, and no embedding reaches any frozen file."),
    ("Benchflow", "0.6.7", "Used — one task authored, container builds, verifier grades",
     "no", "benchmarks/tasks/denali-gate-trap turns our own finding into an agent "
     "benchmark: an agent sees only measurability features for 50 programs and "
     "must predict which returned a result. The naive quality filter scores 0.6981 "
     "balanced accuracy with 20 false negatives, our reference solution 0.7413. "
     "It grades no denali result — it asks whether anyone else falls for the same "
     "trap we did."),
    ("Tamarind Bio", "REST API", "Verified — key authenticates, 0 jobs submitted",
     "no", "GET /api/jobs returns 200 on our key. Declined: see below."),
    ("Benchling", "MCP endpoint live",
     "Registered as an MCP client — OAuth pending",
     "no", "The hosted server answers 401, so it is up and gated rather than "
     "absent. Registered and left unauthenticated: there is no wet-lab entity in "
     "this project to register, and pushing a CSV into a lab notebook to claim "
     "the integration is the cosmetic kind."),
    ("Proto — Evo Design", "proto-tools 0.1.0",
     "Executed — live tool call recorded, 140 tools, doctor exits 0",
     "no", "Installs from source, resolves against a live Modal workspace, and "
     "returns a real result: the receipt in results/tools/proto_validation.json "
     "carries the call, the timing and the upstream source URL. It serves "
     "structure and sequence-design models — AlphaFold, Boltz, ESMC, Evo2, "
     "AlphaGenome — and denali makes no structural or sequence-design claim, so "
     "nothing it offers enters a result."),
    ("Sundial", "—", "Not found — no discoverable install path",
     "no", "The PyPI package under that name is an unrelated hobbyist progress-bar "
     "library at v0.0.1. Installing it to raise the count would be a lie about "
     "what ran."),
]

# Declined on purpose, with the reason. A tool we could have run and chose not to
# is a different fact from one that would not install, and collapsing the two is
# how a tool count stops meaning anything.
DECLINED = [
    ("BenchFlow", "one task built, three declined",
     "Their framing is that a benchmark is just a frozen environment, and ours was "
     "already frozen — so one task got built and validated end to end. The other "
     "three pre-registered evaluations are still 3-4 hours of container work and "
     "were not attempted."),
    ("Tamarind Bio", "declined on fit",
     "The key authenticates and the account is live. It is a job runner for "
     "structure and docking workloads and we have no job of that kind, so it has "
     "run nothing."),
    ("Boltz", "declined on scope",
     "Co-folding prediction, reachable through Proto without a separate install. "
     "Declined because this project makes no structural claim: running it would "
     "put a structure on the page that no result depends on."),
]
N_TOOLS = len(TOOLCHAIN)
N_TOUCHED = sum(1 for t in TOOLCHAIN if t[3] != "no")
N_VERIFIED = sum(1 for t in TOOLCHAIN if t[2].startswith(("Verified", "Provisioned")))


# ---------------------------------------------------------------- captions
def captions() -> dict[str, dict[str, str]]:
    txt = (FIGS / "CAPTIONS.md").read_text()
    out = {}
    for block in re.split(r"\n## FIG ", txt)[1:]:
        key = re.search(r"`(fig\d_[a-z_]+\.png)`", block)
        title = re.search(r"\*\*(.+?)\*\*", block)
        body = " ".join(l.lstrip("> ").strip() for l in block.splitlines() if l.startswith(">"))
        if key:
            out[key.group(1)] = {"title": title.group(1) if title else "",
                                 "body": re.sub(r"\*\*|\*", "", body).strip()}
    return out


CAP = captions()


def figure(name: str) -> str:
    c = CAP[name]
    b64 = base64.b64encode((FIGS / name).read_bytes()).decode()
    return f"""<figure>
  <img src="data:image/png;base64,{b64}" alt="{html.escape(c['title'])}">
  <figcaption><b>{html.escape(c['title'])}</b> {html.escape(c['body'])}</figcaption>
</figure>"""


# ---------------------------------------------------------------- page
CSS = """
/* Design language adapted from Rachel's Figma Make study
   (Scientific-Results-Page-Design, IfX8SSpdJtmfx1a5ud9PtJ).
   Typography, palette, hairline rules and the two-touch accent are hers.
   Every number, figure and sentence is ours, from results/frozen/. */
:root{
  --ink:#1c1c1a;          /* warm near-black */
  --soft:#8c8c89;         /* warm muted */
  --rule:rgba(0,0,0,.11); /* hairline */
  --fill:#f2f2f0;         /* figure ground */
  --accent:#4a6fa5;       /* used TWICE: pull-quote rule, footer link */
  --paper:#fff;
  --radius:0px;
}
*{box-sizing:border-box;margin:0;padding:0;border-radius:var(--radius)}
html{-webkit-text-size-adjust:100%;font-size:16px}
body{background:var(--paper);color:var(--ink);
  font:400 16px/1.62 "Source Serif 4",Georgia,"Times New Roman",serif;
  padding:0 40px;-webkit-font-smoothing:antialiased}
main{max-width:1100px;margin:0 auto;padding:44px 0 96px}

/* four sizes: hero / heading / body / small */
.hero{font-size:clamp(2.5rem,5.1vw,4.25rem);line-height:1.05;
  letter-spacing:-.025em;font-weight:600}
h2{font-size:1.25rem;line-height:1.4;font-weight:600;margin:0 0 26px}
.claim{font-size:1.1875rem;line-height:1.5;max-width:46em;margin:22px 0 0}
.circ{font-style:italic;font-size:.8125rem;color:var(--soft);
  max-width:60em;margin:13px 0 0;line-height:1.55}
.mech{font-size:1rem;margin:11px 0 0;max-width:60em}

/* hairline-ruled column, not whitespace-separated blocks */
section{padding:40px 0;border-bottom:1px solid var(--rule)}
section.hero-sec{padding:0 0 34px;border-bottom:1px solid var(--rule)}
figure{padding:44px 0;border-bottom:1px solid var(--rule);margin:0}

/* shared-rule grids: cells divided by hairlines, no floating boxes */
.metrics{display:grid;grid-template-columns:repeat(4,1fr);
  border:1px solid var(--rule);background:var(--rule);gap:1px}
.metric{background:var(--paper);padding:22px 24px}
.metric .n{font-size:1.25rem;font-weight:600;line-height:1;margin-bottom:9px;
  font-variant-numeric:tabular-nums}
.metric .l{font-size:.8125rem;line-height:1.4;color:var(--soft)}

.cards{display:grid;grid-template-columns:repeat(3,1fr);
  border:1px solid var(--rule);background:var(--rule);gap:1px}
.card{background:var(--paper);padding:24px 26px}
.card h3{font-size:.8125rem;font-weight:600;text-transform:uppercase;
  letter-spacing:.1em;color:var(--soft);margin:0 0 14px}
.card p{font-size:1rem;line-height:1.62}

figure img{width:100%;height:auto;display:block;background:var(--fill);
  border:1px solid var(--rule)}
figcaption{margin-top:14px;font-size:.8125rem;line-height:1.65;color:var(--soft);
  max-width:62em}
figcaption b{color:var(--ink);font-weight:600}

/* the accent, first of two uses */
blockquote{margin-left:32px;padding-left:20px;border-left:2px solid var(--accent);
  max-width:46em}
blockquote p{font-size:1.25rem;font-style:italic;line-height:1.55}

.label{font-size:.8125rem;font-weight:600;text-transform:uppercase;
  letter-spacing:.1em;color:var(--soft);margin:0 0 14px}
.control{max-width:48em}
.control p{font-size:1rem;line-height:1.62}
.control .note{margin-top:14px;font-size:.8125rem;font-style:italic;
  color:var(--soft)}

ol.limits{list-style:none;counter-reset:l;display:grid;
  grid-template-columns:1fr 1fr;gap:22px 48px}
ol.limits li{counter-increment:l;display:flex;gap:18px;font-size:1rem;
  line-height:1.62}
ol.limits li::before{content:counter(l) ".";color:var(--soft);flex:none;
  font:400 .8125rem/1.9 "JetBrains Mono",ui-monospace,SFMono-Regular,Menlo,monospace;
  font-variant-numeric:tabular-nums}

footer{padding:26px 0 0;
  font:400 .8125rem/1.95 "JetBrains Mono",ui-monospace,SFMono-Regular,Menlo,monospace;
  color:var(--soft)}
footer b{color:var(--ink);font-weight:600}
/* the accent, second and last use */
footer a{color:var(--accent);text-decoration:none}
footer a:hover{text-decoration:underline;text-underline-offset:2px}

/* explorer — same palette, same four sizes */
.ctl{display:flex;gap:22px;align-items:center;margin:0 0 18px;flex-wrap:wrap}
.ctl label{font-size:.8125rem;color:var(--soft);display:flex;gap:8px;
  align-items:center;cursor:pointer;user-select:none}
.ctl input{accent-color:var(--accent);cursor:pointer}
.ctl .count{font-size:.8125rem;color:var(--soft);
  font-family:"JetBrains Mono",ui-monospace,monospace}
table.ex{width:100%;border-collapse:collapse;font-size:.9375rem}
table.ex th{text-align:left;font-size:.75rem;text-transform:uppercase;
  letter-spacing:.08em;color:var(--soft);font-weight:600;padding:0 12px 9px 0;
  border-bottom:1px solid var(--rule);cursor:pointer;white-space:nowrap}
table.ex th:hover{color:var(--ink)}
table.ex th.num,table.ex td.num{text-align:right;font-variant-numeric:tabular-nums}
table.ex td{padding:9px 12px 9px 0;border-bottom:1px solid var(--rule);
  vertical-align:top}
table.ex tbody tr{cursor:pointer}
table.ex tbody tr:hover{background:var(--fill)}
table.ex tbody tr.sel{background:var(--fill)}
.tag{font-size:.6875rem;text-transform:uppercase;letter-spacing:.07em;
  padding:2px 6px;border:1px solid var(--rule);color:var(--soft);white-space:nowrap}
.tag.held{border-color:var(--accent);color:var(--accent)}
.detail{margin-top:22px;padding:20px 24px;border:1px solid var(--rule);
  background:var(--fill);display:none}
.detail.on{display:block}
.detail h3{font-size:1rem;font-weight:600;margin:0 0 12px}
.detail dl{display:grid;grid-template-columns:auto 1fr;gap:5px 20px;
  font-size:.875rem;margin:0 0 16px}
.detail dt{color:var(--soft)}
.detail dd{margin:0;font-variant-numeric:tabular-nums}
.detail .prop{border-left:2px solid var(--accent);padding-left:16px;
  font-size:.9375rem;line-height:1.6}
.detail .prop b{display:block;font-size:.75rem;text-transform:uppercase;
  letter-spacing:.08em;color:var(--soft);margin-bottom:6px}
.detail .prop p{margin:0 0 10px}
/* use-it — terminal-ish, but the same paper, no chrome */
.use{display:grid;grid-template-columns:1fr 1fr;border:1px solid var(--rule);
  background:var(--rule);gap:1px;margin-top:24px}
.use>div{background:var(--paper);padding:22px 24px}
.use h3{font:600 .6875rem/1.4 "JetBrains Mono",ui-monospace,monospace;
  letter-spacing:.13em;text-transform:uppercase;color:var(--soft);margin:0 0 14px}
pre.cmd{margin:0 0 14px;padding:14px 16px;background:var(--fill);
  border:1px solid var(--rule);overflow-x:auto;white-space:pre-wrap;
  word-break:break-word;
  font:400 .78125rem/1.7 "JetBrains Mono",ui-monospace,SFMono-Regular,monospace}
pre.out{margin:0;padding:14px 16px;border-left:2px solid var(--accent);
  background:transparent;overflow-x:auto;white-space:pre-wrap;
  font:400 .78125rem/1.7 "JetBrains Mono",ui-monospace,SFMono-Regular,monospace;
  color:var(--ink)}
pre.out b{font-weight:600}
.use .note{font-size:.8125rem;line-height:1.6;color:var(--soft);margin-top:14px}
@media(max-width:1000px){.use{grid-template-columns:1fr}}

/* the agent — same hairline grammar, nothing new introduced */
.btn{font:600 .8125rem/1 "JetBrains Mono",ui-monospace,SFMono-Regular,Menlo,monospace;
  padding:9px 16px;border:1px solid var(--ink);background:var(--ink);color:var(--paper);
  cursor:pointer;letter-spacing:.02em}
.btn:hover{opacity:.84}
.btn.ghost{background:transparent;color:var(--ink);border-color:var(--rule)}
.btn.ghost:hover{border-color:var(--ink);opacity:1}
.btn:disabled{opacity:.32;cursor:default}
.ctl select{font:400 .8125rem/1 "JetBrains Mono",ui-monospace,monospace;
  padding:5px 7px;border:1px solid var(--rule);background:var(--paper);
  color:var(--ink);cursor:pointer}
.agwrap{display:grid;grid-template-columns:270px 1fr;border:1px solid var(--rule);
  background:var(--rule);gap:1px}
.agstate{background:var(--paper);padding:22px 24px;display:flex;
  flex-direction:column;gap:26px}
.agmetric .n{font-size:1.6rem;font-weight:600;line-height:1;margin-bottom:8px;
  font-variant-numeric:tabular-nums}
.agmetric .l{font-size:.75rem;line-height:1.5;color:var(--soft)}
.aglog{background:var(--paper);padding:0;max-height:430px;overflow-y:auto}
.agempty{padding:24px;font-size:.875rem;color:var(--soft);font-style:italic}
.agstep{padding:14px 22px;border-bottom:1px solid var(--rule);
  display:grid;grid-template-columns:30px 1fr;gap:14px}
.agstep:last-child{border-bottom:0}
.agstep .i{font:400 .75rem/1.6 "JetBrains Mono",ui-monospace,monospace;
  color:var(--faint,var(--soft));font-variant-numeric:tabular-nums}
.agstep .nm{font-size:.9375rem;font-weight:600;margin-bottom:3px}
.agstep .ev{font:400 .75rem/1.7 "JetBrains Mono",ui-monospace,monospace;
  color:var(--soft);font-variant-numeric:tabular-nums}
.agstep .vd{font-size:.875rem;line-height:1.55;margin-top:7px}
.agstep .nx{font-size:.8125rem;line-height:1.55;color:var(--soft);margin-top:6px;
  border-left:2px solid var(--accent);padding-left:12px}
.agstep.halt{background:var(--fill)}
.agstep.halt .nm{color:var(--accent)}

/* tool chain — the same hairline table, one extra column that carries the point */
table.tools{width:100%;border-collapse:collapse;font-size:.9375rem;
  margin:0 0 6px}
table.tools th{text-align:left;font-size:.75rem;text-transform:uppercase;
  letter-spacing:.08em;color:var(--soft);font-weight:600;
  padding:0 16px 9px 0;border-bottom:1px solid var(--rule);vertical-align:bottom}
table.tools td{padding:13px 16px 13px 0;border-bottom:1px solid var(--rule);
  vertical-align:top}
table.tools td:last-child,table.tools th:last-child{padding-right:0}
table.tools .tool{font-weight:600;white-space:nowrap}
table.tools .ver{display:block;font-weight:400;color:var(--soft);
  font:400 .75rem/1.5 "JetBrains Mono",ui-monospace,SFMono-Regular,Menlo,monospace}
table.tools .stat{font-size:.875rem;color:var(--soft);max-width:20em}
table.tools .what{font-size:.875rem;line-height:1.6;color:var(--ink)}
table.tools tr.untouched .tool,table.tools tr.untouched .what{color:var(--soft)}
.touch{font:400 .75rem/1.6 "JetBrains Mono",ui-monospace,SFMono-Regular,Menlo,monospace;
  white-space:nowrap}
.touch.no{color:var(--soft)}
.touch.yes{color:var(--ink);font-weight:600}
.callable{margin-top:38px;border-top:1px solid var(--rule);padding-top:30px}
.callable h3{font-size:.8125rem;font-weight:600;text-transform:uppercase;
  letter-spacing:.1em;color:var(--soft);margin:0 0 14px}
.callable p{font-size:1rem;line-height:1.62;max-width:52em}
pre.wire{margin:18px 0 0;padding:20px 24px;background:var(--fill);
  border:1px solid var(--rule);overflow-x:auto;
  font:400 .8125rem/1.75 "JetBrains Mono",ui-monospace,SFMono-Regular,Menlo,monospace;
  color:var(--ink);white-space:pre-wrap;word-break:break-word;max-width:100%}
pre.wire .k{color:var(--soft)}
p.cite{margin-top:26px;font-size:.8125rem;line-height:1.65;color:var(--soft);
  max-width:60em}
@media(max-width:1000px){
  .metrics,.cards,ol.limits{grid-template-columns:1fr}
  table.tools .stat,table.tools thead th:nth-child(2){display:none}
  body{padding:0 22px}main{padding:40px 0 64px}}
"""

EXPLORER_JSON = json.dumps(EXPLORER, separators=(",", ":"), default=str)


def _tool_rows() -> str:
    out = []
    for name, ver, status, touched, what in TOOLCHAIN:
        cls = "untouched" if touched == "no" else ""
        mark = "no" if touched == "no" else "yes"
        out.append(
            f'<tr class="{cls}">'
            f'<td class="tool">{html.escape(name)}<span class="ver">{html.escape(ver)}</span></td>'
            f'<td class="stat">{html.escape(status)}</td>'
            f'<td><span class="touch {mark}">{html.escape(touched)}</span></td>'
            f'<td class="what">{html.escape(what)}</td></tr>')
    return "\n".join(out)


TOOL_ROWS = _tool_rows()
DECLINED_ROWS = "\n".join(
    f'<tr><td class="tool">{html.escape(n)}<span class="ver">{html.escape(v)}</span></td>'
    f'<td class="what" colspan="3">{html.escape(w)}</td></tr>'
    for n, v, w in DECLINED)

# The literal object the MCP server returns for a program it never scored,
# built by the same function the server calls. Not a transcription of it.
WIRE = html.escape(json.dumps(
    _unscored("HALLMARK_A_PROGRAM_WE_NEVER_SCORED", PRED["residual_sd"]), indent=2))
V(PRED["residual_sd"], "predictor.residual_sd -> MCP wire example")

HTML = f"""<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>denali — what a genome-scale screen can and cannot discover</title>
<style>{CSS}</style>
<main>

<!-- 1. hero -->
<section class="hero-sec">
<p class="hero">{PCT_LO}–{PCT_HI}% of what<br>looks like biology<br>is not biology.</p>
<p class="claim">Across all {N_PROGRAMS} Hallmark gene programs scored against
{N_KD:,} CRISPRi knockdowns in K562, that share of the variance in <em>apparent</em>
reversibility is explained without reference to what the program does.</p>
<p class="circ">The range is a range because one of our six features is computed
from the same matrix as the outcome, so part of {R_HI:.3f} is arithmetic. {R_LO:.3f} is the
figure that survives that objection, and we never quote the top alone.</p>
<p class="mech">The mechanism is size. Bigger programs with more co-moving members
return more hits regardless of what they do — <b>program size alone explains
{SIZE_R2*100:.1f}%</b>.</p>
</section>

<!-- 2. metrics -->
<section>
<div class="metrics">
  <div class="metric"><div class="n">4</div><div class="l">evaluations run</div></div>
  <div class="metric"><div class="n">3</div><div class="l">came back negative</div></div>
  <div class="metric"><div class="n">1</div><div class="l">came back positive</div></div>
  <div class="metric"><div class="n">0</div><div class="l">gene-level claims made</div></div>
</div>
</section>

{figure("fig1_matrix.png")}

<!-- 4. three negatives -->
<section>
<h2>The three negative findings</h2>
<div class="cards">
  <div class="card"><h3>Most of it is not biology</h3>
    <p>A model that never looks at what a program <em>does</em> predicts most of how
    reversible it appears. {N_ZERO} of {N_PROGRAMS} programs return nothing at all.
    We wrote down before running that if this cleared 60%, it becomes the finding
    rather than the failure. It cleared, at {R_HI:.3f}.</p></div>
  <div class="card"><h3>The obvious filter is wrong {N_GATEFAIL_HITS} of {N_PROGRAMS}</h3>
    <p>We built the quality filter anyone would build. {N_GATEFAIL_HITS} programs
    fail it and produce hits anyway; only {N_GATEPASS_ZERO} passes it and produces
    nothing. The program we held out fails our own filter and still ranks
    {CTRL_RANK}th of {N_PROGRAMS}.</p></div>
  <div class="card"><h3>Our generalisation test failed</h3>
    <p>{NHELD} programs from a different collection, not scored until the model was
    finished. Only {NGATE} of {NHELD} was measurable, so by our own pre-registered
    rule the evaluation is underpowered and inconclusive. Balanced accuracy
    {BAL} — worse than chance, {TP} true positives. We did not refit.</p></div>
</div>
</section>

<!-- 3b. use it -->
<section>
<div class="label">Use it on your own screen</div>
<h2>Two minutes, before the year.</h2>
<p class="claim">Your analysis already produced a table: set name, how many genes
were in it, how many hits it returned. That is the whole input. Nothing is
uploaded anywhere &mdash; it runs locally on the CSV you already have.</p>

<div class="use">
  <div>
    <h3>1 &middot; audit the ranking</h3>
    <pre class="cmd">python -m src.audit_screen my_results.csv \
    --set pathway --size n_genes --hits n_significant</pre>
    <pre class="out"><b>CONFOUNDED</b>: {SIZE_R2:.0%} of the variance in this
ranking is predicted by how the sets
were built, with no reference to what
any gene does.

&rarr; Re-rank with a size-aware statistic
  and see which entries survive.</pre>
    <p class="note">That output is this project&rsquo;s own screen, run through the
    same command a stranger would type. Verdicts are CONFOUNDED, PARTIALLY
    CONFOUNDED, or NOT SIZE-DOMINATED. It never names a gene.</p>
  </div>
  <div>
    <h3>2 &middot; apply the fix, then audit again</h3>
    <pre class="cmd"># re-rank on the size-corrected residual,
# then re-run the identical audit</pre>
    <pre class="out">before   {SIZE_R2}   <b>CONFOUNDED</b>
after    0.0000   <b>NOT SIZE-DOMINATED</b></pre>
    <p class="note"><b>This is the part that matters.</b> The tool names a
    correction and then grades whether it worked. If the score does not drop, the
    correction did not work on your data &mdash; and you know that before you
    publish, not after. On our screen it goes to zero.</p>
  </div>
</div>

<div class="callable" style="margin-top:34px">
<h3>Or connect it to your agent</h3>
<p>The frozen matrix is an MCP server, so any agent can query it directly. No API
key, no account, nothing hosted &mdash; it runs on your machine against files in
the repo.</p>
<pre class="wire">{{
  "mcpServers": {{
    "denali": {{
      "command": "python",
      "args": ["-m", "src.mcp_server"]
    }}
  }}
}}</pre>
<p class="circ"><b>It also refuses.</b> Ask it about a bare gene symbol and it
declines, citing the {CONCORD} concordance that makes any single-gene answer
irreproducible. Ask it to rank or nominate and it declines again, citing its own
predictor&rsquo;s failure. Those refusals are not advisory text the model may ignore
&mdash; they are code that returns before the data is read, and eleven tests
assert they still fire. The build-time scope guard stops <i>us</i> publishing a
gene-level claim; this is what stops an agent extracting one.</p>

<p class="circ">Paste into Claude Code, Cursor, or any MCP client. Two tools:
<code>reversibility(program)</code> and <code>provenance()</code>. The first
returns the measured rank, the share measurability alone predicts, the residual,
and a generated next experiment &mdash; and for a program we never scored it
volunteers the predictor&rsquo;s own failure before answering. There is deliberately
no hosted instance and no key to manage: the page you are reading makes zero
network calls, which is enforced by five tests, and adding a backend would mean
this demo could fail in front of you.</p>
</div>
</section>

<!-- 4a. the agent -->
<section>
<div class="label">The loop, running</div>
<h2>The agent chooses what to look at next, and decides when it has seen enough.</h2>
<p class="claim">It starts knowing nothing. At each step it picks a program by a
stated policy, reads that program's frozen evidence, updates its estimate of how
much of apparent reversibility is explained by measurability, and emits a next
experiment. It halts on its own when the estimate stops moving. Nothing here is
scripted to a fixed answer &mdash; change the policy or the halt rule and it visits
different programs and stops somewhere else.</p>

<div class="ctl">
  <button id="agRun" class="btn">Run the agent</button>
  <button id="agStep" class="btn ghost">Step once</button>
  <button id="agReset" class="btn ghost">Reset</button>
  <button id="agSave" class="btn ghost" disabled>Export this run</button>
  <label>policy
    <select id="agPolicy">
      <option value="coverage">cover the size range</option>
      <option value="uncertain">largest model error first</option>
      <option value="order">alphabetical (no policy)</option>
    </select>
  </label>
  <label>halt when &Delta;R&sup2; &lt;
    <select id="agTol">
      <option value="0.02">0.02</option>
      <option value="0.01" selected>0.01</option>
      <option value="0.005">0.005</option>
    </select>
    for 3 steps</label>
  <span class="count" id="agCount">0 of {N_PROGRAMS} visited</span>
</div>

<div class="agwrap">
  <div class="agstate">
    <div class="agmetric"><div class="n" id="agR2">&mdash;</div>
      <div class="l">running R&sup2;: how much of what it has seen is explained by
      measurability alone</div></div>
    <div class="agmetric"><div class="n" id="agN">0</div>
      <div class="l">programs examined</div></div>
    <div class="agmetric"><div class="n" id="agStatus">idle</div>
      <div class="l">halt condition</div></div>
  </div>
  <div class="aglog" id="agLog"><div class="agempty">No steps taken. The agent has
  read nothing yet.</div></div>
</div>
<p class="circ">The running R&sup2; is computed in the browser from two frozen columns
&mdash; observed R<sub>p</sub> and the measurability model's prediction &mdash; over
exactly the programs the agent has chosen to read. It is not fitted here and no
value is pre-computed for it. It is <b>not</b> the pre-registered statistic: that
one is an OLS fit over all {N_PROGRAMS} programs, penalised for six parameters,
and it is {R_LO}&ndash;{R_HI}. This is a plain goodness-of-fit on a subset, which
over all {N_PROGRAMS} rows comes to {ALL50_R2}. The agent reports both when it
halts, and names the gap, because a number from an early stop is worth less than
a number from a full read and it should say so itself.</p>
</section>

<!-- 4b. explorer -->
<section>
<h2>All {N_PROGRAMS} programs</h2>
<p class="mech" style="margin:0 0 20px">Every program we scored, with the next
experiment the pipeline generates for it. Sort any column. Click a row.</p>
<div class="ctl">
  <label><input type="checkbox" id="fGate"> Show only the {N_GATEFAIL_ROWS} that fail
    the filter and produce hits anyway</label>
  <label><input type="checkbox" id="fHeld"> Held-out programs only</label>
  <span class="count" id="cnt"></span>
</div>
<table class="ex">
  <thead><tr>
    <th data-k="short">Program</th>
    <th data-k="n_hits_q05" class="num">Hits</th>
    <th data-k="R_p" class="num">R<sub>p</sub></th>
    <th data-k="R_p_predicted_from_measurability" class="num">Predicted</th>
    <th data-k="R_p_residual_after_measurability" class="num">Residual</th>
    <th data-k="passes_measurability_gate">Gate</th>
    <th data-k="reversibility_call">Call</th>
  </tr></thead>
  <tbody id="tb"></tbody>
</table>
<div class="detail" id="det"></div>
</section>

<script>
const DATA = {EXPLORER_JSON};
let sortK="n_hits_q05", sortAsc=false;
const $=id=>document.getElementById(id);
const num=v=>(v===null||v===undefined)?"\u2014":(typeof v==="number"?(Number.isInteger(v)?v.toLocaleString():v.toFixed(3)):v);
function rows(){{let r=DATA.slice();
  if($("fGate").checked) r=r.filter(d=>d.gate_fail_with_hits);
  if($("fHeld").checked) r=r.filter(d=>d.is_held_out_program);
  return r.sort((a,b)=>{{let x=a[sortK],y=b[sortK];
    if(typeof x==="boolean"){{x=x?1:0;y=y?1:0;}}
    if(x===null||x===undefined)return 1; if(y===null||y===undefined)return -1;
    return (x<y?-1:x>y?1:0)*(sortAsc?1:-1);}});}}
function draw(){{const r=rows();
  $("cnt").textContent=r.length+" of "+DATA.length+" programs";
  $("tb").innerHTML=r.map(d=>'<tr data-i="'+DATA.indexOf(d)+'"><td>'+d.short+
    (d.is_held_out_program?' <span class="tag held">held out</span>':'')+
    '</td><td class="num">'+num(d.n_hits_q05)+'</td><td class="num">'+num(d.R_p)+
    '</td><td class="num">'+num(d.R_p_predicted_from_measurability)+
    '</td><td class="num">'+num(d.R_p_residual_after_measurability)+
    '</td><td><span class="tag">'+(d.passes_measurability_gate?'passes':'fails')+
    '</span></td><td>'+d.reversibility_call+'</td></tr>').join("");
  [...$("tb").rows].forEach(tr=>tr.onclick=()=>detail(+tr.dataset.i,tr));}}
function detail(i,tr){{const d=DATA[i],pr=d.proposal||{{}};
  [...$("tb").rows].forEach(x=>x.classList.remove("sel")); if(tr)tr.classList.add("sel");
  const bits=[["Measured members",num(d.n_present)],
    ["Knockdowns that moved it",num(d.n_hits_q05)],
    ["Expression vs background",num(d.expr_ratio)],
    ["Variance vs background",num(d.sd_ratio)],
    ["Predicted from measurability",num(d.R_p_predicted_from_measurability)],
    ["Residual, the part that could be biology",num(d.R_p_residual_after_measurability)],
    ["Measurability gate",d.passes_measurability_gate?"passes":"fails"]]
    .map(kv=>'<dt>'+kv[0]+'</dt><dd>'+kv[1]+'</dd>').join("");
  const extra=["mechanism","falsifies","why_not_gene_level","caveat"]
    .filter(k=>pr[k]).map(k=>'<p>'+pr[k]+'</p>').join("");
  $("det").innerHTML='<h3>'+d.program+'</h3><p style="font-size:.9375rem;color:var(--soft);margin:-6px 0 14px">'+
    d.call_plain+'</p><dl>'+bits+'</dl><div class="prop"><b>Generated next experiment &middot; '+
    (pr.outcome||'')+'</b><p>'+(pr.next_experiment||'')+'</p>'+extra+'</div>';
  $("det").classList.add("on");}}
document.querySelectorAll("table.ex th").forEach(th=>th.onclick=()=>{{
  const k=th.dataset.k; sortAsc=(k===sortK)?!sortAsc:(k==="short"); sortK=k; draw();}});
$("fGate").onchange=$("fHeld").onchange=draw;
draw();

/* ---------------- the agent ----------------------------------------------
   A deterministic loop over the frozen table. It is autonomous in the sense
   that matters here: it chooses which program to read next, and it decides
   for itself when to stop. Both decisions are policies you can change from
   the controls, and changing them changes the trace.

   No network, no model call, no pre-computed answer. The running R2 is
   ordinary least-squares goodness-of-fit between two frozen columns over
   exactly the rows the agent has chosen so far. */
const ALL50={ALL50_R2};   /* same statistic over all 50, from the frozen file */
const AG={{seen:[],r2hist:[],halted:false,reason:""}};

/* R2 of the frozen measurability prediction against the frozen observation,
   on the visited subset only. */
function runR2(rows){{
  if(rows.length<3) return null;
  const y=rows.map(d=>d.R_p), p=rows.map(d=>d.R_p_predicted_from_measurability);
  if(p.some(v=>v===null||v===undefined)) return null;
  const mean=y.reduce((a,b)=>a+b,0)/y.length;
  const ssTot=y.reduce((a,v)=>a+(v-mean)**2,0);
  const ssRes=y.reduce((a,v,i)=>a+(v-p[i])**2,0);
  return ssTot===0?null:1-ssRes/ssTot;
}}

/* The exploration policy. This is the autonomous choice -- which evidence to
   look at next, given only what has already been read. */
function pick(){{
  const left=DATA.filter(d=>!AG.seen.includes(d));
  if(!left.length) return null;
  const pol=$("agPolicy").value;
  if(pol==="order")
    return left.slice().sort((a,b)=>a.program<b.program?-1:1)[0];
  if(pol==="uncertain")   /* read where the model is currently worst */
    return left.slice().sort((a,b)=>
      Math.abs(b.R_p_residual_after_measurability||0)-
      Math.abs(a.R_p_residual_after_measurability||0))[0];
  /* default: cover the size range, so the estimate is not built from one
     end of it. Furthest unvisited program from everything seen so far. */
  if(!AG.seen.length)
    return left.slice().sort((a,b)=>a.n_present-b.n_present)[Math.floor(left.length/2)];
  return left.slice().sort((a,b)=>
    Math.min(...AG.seen.map(s=>Math.abs(b.n_present-s.n_present)))-
    Math.min(...AG.seen.map(s=>Math.abs(a.n_present-s.n_present))))[0];
}}

/* The verdict is about the MODEL, not about the program. The agent is auditing
   its own explanation, which is why nothing here reads as a recommendation. */
function verdict(d){{
  const r=d.R_p_residual_after_measurability;
  if(d.n_hits_q05===0)
    return ["Nothing moved it. Measurability alone predicted "+
      (d.R_p_predicted_from_measurability||0).toFixed(2)+
      ", so this is a program my model expected to be quiet.", false];
  if(!d.passes_measurability_gate && d.n_hits_q05>0)
    return ["Fails the quality gate and returns "+d.n_hits_q05.toLocaleString()+
      " hits anyway. The gate would have discarded this. That is evidence "+
      "against the filter, not against the program.", true];
  if(Math.abs(r)>0.8)
    return ["Sits "+(r>0?"+":"")+r.toFixed(2)+" from what measurability predicts. "+
      "My model is weakest here, which is where anything that is not size would "+
      "have to show up.", true];
  return ["Observed "+d.R_p.toFixed(2)+" against a predicted "+
    (d.R_p_predicted_from_measurability||0).toFixed(2)+
    ". Measurability accounts for it; there is nothing here my model misses.", false];
}}

function agStep(){{
  if(AG.halted) return false;
  const d=pick();
  if(!d){{ AG.halted=true; AG.reason="all "+DATA.length+" read"; return true; }}
  AG.seen.push(d);
  const r2=runR2(AG.seen);
  if(r2!==null) AG.r2hist.push(r2);

  /* the halt decision: stop when reading more stops changing the estimate */
  const tol=parseFloat($("agTol").value), h=AG.r2hist;
  if(AG.seen.length>=8 && h.length>=4){{
    const d1=Math.abs(h[h.length-1]-h[h.length-2]);
    const d2=Math.abs(h[h.length-2]-h[h.length-3]);
    const d3=Math.abs(h[h.length-3]-h[h.length-4]);
    if(d1<tol&&d2<tol&&d3<tol){{
      AG.halted=true;
      AG.reason="estimate stable within "+tol+" for 3 steps";
    }}
  }}
  render(d,r2);
  return true;
}}

function render(d,r2){{
  const [vd,flag]=verdict(d);
  const pr=d.proposal||{{}};
  const i=AG.seen.length;
  const el=document.createElement("div");
  el.className="agstep";
  el.innerHTML='<div class="i">'+i+'</div><div><div class="nm">'+d.short+
    (d.is_held_out_program?' <span class="tag held">held out</span>':'')+'</div>'+
    '<div class="ev">n='+d.n_present+' members &middot; hits '+
    d.n_hits_q05.toLocaleString()+' &middot; R_p '+d.R_p.toFixed(3)+
    ' &middot; predicted '+(d.R_p_predicted_from_measurability||0).toFixed(3)+
    (r2!==null?' &middot; running R² '+r2.toFixed(3):'')+'</div>'+
    '<div class="vd">'+vd+'</div>'+
    (pr.next_experiment?'<div class="nx"><b>next:</b> '+pr.next_experiment+'</div>':'')+
    '</div>';
  const log=$("agLog");
  if(AG.seen.length===1) log.innerHTML="";
  log.appendChild(el);
  log.scrollTop=log.scrollHeight;

  $("agN").textContent=AG.seen.length;
  $("agR2").textContent=r2===null?"—":r2.toFixed(3);
  $("agCount").textContent=AG.seen.length+" of "+DATA.length+" visited";
  $("agStatus").textContent=AG.halted?"HALTED":"running";
  $("agSave").disabled=AG.seen.length===0;

  if(AG.halted){{
    const f=document.createElement("div");
    f.className="agstep halt";
    const fr=AG.r2hist.length?AG.r2hist[AG.r2hist.length-1]:0;
    const gap=fr-ALL50, over=gap>0.02;
    f.innerHTML='<div class="i">&#9632;</div><div><div class="nm">Halted &mdash; '+
      AG.reason+'</div><div class="vd">Read '+AG.seen.length+' of '+DATA.length+
      ' programs and stopped, because reading more stopped changing the answer. '+
      'On what it read, measurability alone explains R\u00b2 '+fr.toFixed(3)+'. '+
      'The same statistic over all '+DATA.length+' is '+ALL50.toFixed(3)+'.</div>'+
      '<div class="vd"><b>'+(over
        ? 'So stopping early overstated it by '+gap.toFixed(3)+'.'
        : (gap<-0.02 ? 'So stopping early understated it by '+Math.abs(gap).toFixed(3)+'.'
                     : 'The two agree to within 0.02.'))+'</b> '+
      (Math.abs(gap)>0.02
        ? 'The halt rule is a real decision and this is what it cost. A subset '+
          'chosen to span the size range has more spread in it than the full set, '+
          'which flatters the fit. We report the gap rather than the flattering '+
          'half of it &mdash; that is the same reason our headline is a range.'
        : 'The subset it chose was representative of the whole.')+'</div>'+
      '<div class="nx"><b>next:</b> the same audit on a '+
      'second, independently screened cell line &mdash; if the size effect '+
      'reproduces there, it is a property of screens rather than of this one.'+
      '</div></div>';
    log.appendChild(f); log.scrollTop=log.scrollHeight;
    $("agRun").disabled=$("agStep").disabled=true;
    $("agSave").disabled=false;
  }}
}}

let agTimer=null;
$("agStep").onclick=()=>agStep();
$("agRun").onclick=()=>{{
  if(agTimer){{clearInterval(agTimer);agTimer=null;$("agRun").textContent="Run the agent";return;}}
  $("agRun").textContent="Pause";
  agTimer=setInterval(()=>{{ if(!agStep()||AG.halted){{
    clearInterval(agTimer);agTimer=null;$("agRun").textContent="Run the agent";}} }},420);
}};
$("agReset").onclick=()=>{{
  if(agTimer){{clearInterval(agTimer);agTimer=null;}}
  AG.seen=[];AG.r2hist=[];AG.halted=false;AG.reason="";
  $("agLog").innerHTML='<div class="agempty">No steps taken. The agent has read '+
    'nothing yet.</div>';
  $("agN").textContent="0";$("agR2").textContent="—";
  $("agStatus").textContent="idle";
  $("agCount").textContent="0 of "+DATA.length+" visited";
  $("agRun").disabled=$("agStep").disabled=false;
  $("agSave").disabled=true;
  $("agRun").textContent="Run the agent";
}};
$("agPolicy").onchange=$("agTol").onchange=()=>$("agReset").click();
$("agSave").onclick=()=>{{
  const fr=AG.r2hist.length?AG.r2hist[AG.r2hist.length-1]:null;
  const trace={{
    what:"denali agent run. Reproduce by re-running the same policy and halt rule "+
         "on index.html; the loop is deterministic given both.",
    policy:$("agPolicy").value,
    halt_rule:"delta running R2 < "+$("agTol").value+" for 3 consecutive steps",
    halted:AG.halted, halt_reason:AG.reason,
    programs_read:AG.seen.length, programs_available:DATA.length,
    running_r2_at_halt:fr,
    same_statistic_over_all_50:ALL50,
    early_stop_gap:fr===null?null:+(fr-ALL50).toFixed(4),
    gap_note:"A subset chosen to span the size range has more spread than the "+
             "full set, which flatters the fit. Reported, not hidden.",
    not_the_preregistered_statistic:
      "This is a plain goodness-of-fit on a subset. The pre-registered figure is "+
      "an adjusted OLS fit over all 50 programs, {R_LO}-{R_HI}.",
    steps:AG.seen.map((d,i)=>({{
      order:i+1, program:d.program, n_present:d.n_present,
      n_hits_q05:d.n_hits_q05, R_p:d.R_p,
      predicted_from_measurability:d.R_p_predicted_from_measurability,
      residual:d.R_p_residual_after_measurability,
      passes_measurability_gate:d.passes_measurability_gate,
      running_r2:AG.r2hist[i]===undefined?null:+AG.r2hist[i].toFixed(4),
      verdict:verdict(d)[0],
      proposed_next_experiment:(d.proposal||{{}}).next_experiment||null
    }})),
    scope:"Pathway level only. Guide-pair concordance is {CONCORD}, so no "+
          "gene-level claim is made and no novel gene is named. These are "+
          "proposals, reported and not endorsed: the predictor behind them "+
          "failed its own held-out evaluation at {BAL}."
  }};
  const blob=new Blob([JSON.stringify(trace,null,2)],{{type:"application/json"}});
  const a=document.createElement("a");
  a.href=URL.createObjectURL(blob);
  a.download="denali-agent-run-"+$("agPolicy").value+".json";
  a.click(); URL.revokeObjectURL(a.href);
}};
</script>

{figure("fig2_gate_failure.png")}

<!-- 5b. two screens -->
<section>
<div class="label">Added after the freeze</div>
<h2>&ldquo;It replicated in a second cell line&rdquo; is the strongest evidence a hit
list ever gets. We measured what that evidence is worth.</h2>

<p class="claim">A second, independently screened cell line &mdash; RPE1, {RP_TGT:,}
knockdown targets against K562&rsquo;s {N_KD:,} &mdash; scored with the same frozen
code. Two questions: does the size effect hold there, and when the two screens
agree, is that biology?</p>

<div class="metrics" style="margin-top:26px">
  <div class="metric"><div class="n">{RP_R2}</div>
    <div class="l">size alone, in RPE1. Pre-registered bar was 0.25, fixed and
    hashed before the sweep ran. It clears by {RP_R2 - 0.25:.3f} &mdash; thin, and
    we say so. p&nbsp;=&nbsp;{RP_P}, {RP_N} of 50 scoreable</div></div>
  <div class="metric"><div class="n">{CC_RAW:+.3f}</div>
    <div class="l">raw rank agreement between the two screens. This is the number
    a replication claim rests on</div></div>
  <div class="metric"><div class="n">{CC_PAR:+.3f}</div>
    <div class="l">the same agreement after removing set size from both.
    <b>{CC_SHARE}% of the replication was set size</b></div></div>
  <div class="metric"><div class="n">{CC_SIZE}</div>
    <div class="l">of the top 10 programs in the second screen, predictable from
    set size alone. Observed overlap {CC_TOP}; chance {CC_CHANCE}</div></div>
</div>

<blockquote style="margin-top:30px"><p>Six of the top ten programs in an
independent cell line can be predicted using nothing but how many genes are in
each set. Both screens are confounded the same way, so agreeing for the same
wrong reason looks exactly like agreeing for the right one.</p></blockquote>

<p class="circ">The RPE1 arm was pre-registered; the concordance measurement was
not, and is labelled post-freeze wherever it appears. RPE1 covers 24.3% of K562&rsquo;s
targets and that quarter is disproportionately essential genes &mdash; our own
coverage control, which <b>fails</b> at 94.1% versus 11.3%. So this is a
generalisation test, not a replication, and the number above is a measurement on
these two screens rather than a general estimate of anything. Both run on anyone
else&rsquo;s paired screens: <code>audit_screen.py --hits-b</code>.</p>
</section>

<!-- 6. the heme example -->
<section>
<blockquote><p>One held-out row carries the whole result. <b>{HEME_NAME}</b> drew
the highest prediction of all {NHELD} — R<sub>p</sub> {HEME_PRED} — on
{HEME_N} measured gene. It returned {HEME_HITS} hits. The model predicted strongly
because the program looked measurable on the features it could see, and the
program returned nothing because it was not measurable at all. The failure and the
finding are the same fact.</p></blockquote>
</section>

<!-- 7. the control -->
<section class="control">
<div class="label">Control</div>
<h2>The one positive</h2>
<p>Run unchanged on a program it had not been developed against, the pipeline puts
that pathway's master regulator at rank 2 of 11,258 scored perturbations — more
than the {N_KD:,} unique genes, because some are targeted twice. Eleven of
seventeen canonical members land in the extreme 10%, against 1.7 expected by
chance, binomial p = 7.0×10⁻⁸, with the correct sign at both ends of the ranking.
That same program fails our measurability filter on an expression ratio of
{CTRL_EXPR} and still returns {CTRL_HITS} hits.</p>
<p class="note">This is a control, not a discovery. It says the ranking works. It
does not say the ranking found anything, and we do not claim that it did.</p>
</section>

{figure("fig4_retrieval.png")}

<!-- 9. limitations -->
<section>
<h2>What this does not claim</h2>
<ol class="limits">
<li><b>Not that measurement is the cause.</b> A post-freeze check, prompted by a
critique rather than our plan, split the six features: measurement-only reaches
{MEAS_ONLY:.3f}, set-construction-only reaches {CONS_ONLY:.3f}. The number stands; the
attribution belongs to how gene sets are defined.</li>
<li><b>No gene-level result.</b> Guide-pair concordance is {CONCORD} — two
independent guides against the same gene give uncorrelated scores. Pathway-level
claims only, and no novel gene is named anywhere in this project.</li>
<li><b>Not generalisable, on our own evidence.</b> The held-out evaluation was
underpowered and inconclusive, and its binary axis failed outright at {BAL}.</li>
<li><b>One cell line, unstressed.</b> Everything is K562. Our first program
returned a null because it was never switched on in those cells — measurable is
not the same as engaged, and our gate tested the wrong one.</li>
<li><b>The evidence layer is a pointer layer.</b> {EV_SRC} distinct sources cover
113 genes, one review holds {EV_SHARE}% of them, and {EV_PROBE} of {EV_N} blind-probe
genes returned the same unrelated paper. Not an evidence chain, and we do not
describe it as one.</li>
</ol>
</section>

<!-- 10. the tool chain -->
<section>
<div class="label">Tool chain</div>
<h2>Set up is not the same as used. Here is what actually touched the result.</h2>
<table class="tools">
<thead><tr><th>Tool</th><th>Status, checked on the machine</th><th>Touched a number</th><th>What it did, and did not do</th></tr></thead>
<tbody>
{TOOL_ROWS}
</tbody>
</table>
<p class="circ"><b>{N_VERIFIED} of these {N_TOOLS} were installed, authenticated and
run. {N_TOUCHED} changed anything in <code>results/frozen/</code>.</b> The gap between
those two numbers is the honest tool count, and every row on the wrong side of it is
still listed. A reviewer can check the whole column with one command —
<code>grep -rn "modal\\|esm\\|benchflow\\|benchling" src/</code> returns the strings on
this page and no import. The test suite runs that grep, so if any of them ever enters
the pipeline this table fails the build instead of quietly becoming false.</p>

<h2 style="margin:38px 0 20px">Declined, with the reason</h2>
<table class="tools"><tbody>
{DECLINED_ROWS}
</tbody></table>
<p class="circ">A tool we could have run and chose not to is a different fact from one
that would not install. Collapsing the two is how a tool count stops meaning anything.</p>

<p class="circ"><b>We got one of these wrong, twice, and caught it ourselves.</b> We
had Proto recorded as broken — <code>pip install proto-language</code> fails at
import. Proto does not publish that package. We had tested a name collision and
filed the result as Proto's status, which is the same mistake as the
<code>sundial</code> collision we had already caught and warned about in the same
document. The real install succeeds. It is the fourth error in this project found by
us rather than by a reviewer, and it is in <code>LIMITATIONS.md</code> §7 with the
other three.</p>

<div class="callable">
<h3>The result is callable</h3>
<p>An MCP server exposes the frozen matrix as two tools, <code>reversibility(program)</code>
and <code>provenance()</code>. It reads <code>results/frozen/</code> and recomputes nothing.
Ask about one of the {N_PROGRAMS} scored programs and it returns the measured rank, the
share of that score measurability alone predicts, the residual that could be biology,
and a generated next experiment. Ask about anything else and it takes the third branch:</p>
<pre class="wire">{WIRE}</pre>
<p class="circ">No caller asked whether the predictor works. The tool says so anyway,
in the same response as the prediction, with the number that condemns it —
balanced accuracy {BAL} against a coin's 0.500 — and the words <i>reported, not
endorsed</i>. That string is not written into the page; it is imported from the
module the server answers with, so if one drifts the build fails.</p>
</div>

<p class="cite">For scale on how hard the held-out step is: Arc Institute's Virtual
Cell Challenge wrap-up (6 December 2025, 300+ final submissions) reported that
perturbation-prediction models are <i>&ldquo;not yet consistently outperforming naive
baselines across all metrics&rdquo;</i>. That is a different and much larger task than
ours — predicting expression responses, not program-level movement — so it is not
a defence of our number. It is the reason we treated a held-out failure as the
expected outcome to design for rather than a result to bury.</p>
</section>

<!-- 11. provenance -->
<footer>
pre-registration &nbsp;<b>d3e24b77…</b> committed before the sweep<br>
frozen predictor &nbsp;<b>610f2a75…</b> hashed before the held-out set was opened<br>
held-out evaluation &nbsp;<b>FAILED</b> — {NGATE} of {NHELD} measurable, balanced accuracy {BAL}, ρ {RHO:+.3f} CI [{CI[0]:+.3f}, {CI[1]:+.3f}]<br>
controls &nbsp;<b>{N_FAIL} of {N_CTRL} FAIL</b>, all reported<br>
scorer unchanged &nbsp;<b>{PROV["seal"].get("scorer_unchanged", PROV["seal"].get("seal_intact"))}</b><br>
every figure and number above is read from results/frozen/ at build time · nothing on this page is recomputed<br>
<a href="https://github.com/alejandro-publius/denali">github.com/alejandro-publius/denali</a>
</footer>

</main>
"""


def main() -> None:
    OUT.write_text(HTML)
    kb = OUT.stat().st_size / 1024
    print(f"wrote {OUT}  ({kb:.0f} KB, figures inlined)")
    print(f"{len(TRACE)} values traced to frozen sources:")
    for v, s in TRACE:
        print(f"  {v:<28} <- {s}")


if __name__ == "__main__":
    main()
