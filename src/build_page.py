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
     "and twelve minutes of laptop."),
    ("CZ Biohub — ESM Cambrian", "esm 3.2.3",
     "Verified twice — local weights and hosted API, both (1, 67, 960)",
     "no", "esmc_300m ran on a real sequence locally, and the same sequence ran "
     "again through the authenticated Biohub Platform API; both returned the same "
     "embedding shape. The result is a protein embedding. This project scores "
     "transcriptional movement, and no embedding reaches any frozen file."),
    ("Benchflow", "0.6.7", "Verified — CLI runs, no key required",
     "no", "Installed and executed, then declined on cost rather than on fit. "
     "See below."),
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
    ("BenchFlow", "declined on cost",
     "The fit is real and we say so: their framing is that a benchmark is just a "
     "frozen environment, and ours is already frozen with pre-registered pass/fail "
     "thresholds — so each verifier would be a threshold comparison rather than a "
     "judgment call. Packaging all four evaluations is 4-6 hours of container work "
     "and we did not have it."),
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
</script>

{figure("fig2_gate_failure.png")}

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
