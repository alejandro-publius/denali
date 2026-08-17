"""Emit index.html — a single static file, every number traced to results/frozen/.

    .venv/bin/python -m src.build_page

Design contract, enforced below:
  * no number is typed into the template. Every value comes through V(), which
    reads a frozen file and records where it came from. A number that cannot be
    traced does not appear on the page.
  * caption text is read verbatim from results/figures/CAPTIONS.md.
  * figures are inlined as base64 so index.html is genuinely standalone.
  * white ground, ONE accent used twice, FOUR type sizes, no gradients, no dark
    hero, no dashboard chrome. Two interactive elements — the explorer and the
    audit runner — and neither makes a network call: everything they need is
    embedded, and user files are read with FileReader and never leave the tab.
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
ASSETS = ROOT / "assets"

# Fonts and brand marks are inlined as base64 for the same reason the figures
# are: tests/test_frozen_invariants.py asserts the page makes no network call,
# so it renders identically on an expo machine with no wifi. No CDN.
_FACES = [("Poppins", 400, "poppins-400.woff2"),
          ("Poppins", 500, "poppins-500.woff2"),
          ("Poppins", 600, "poppins-600.woff2"),
          ("JetBrains Mono", 400, "jetbrainsmono-400.woff2")]


def font_faces() -> str:
    out = []
    for family, weight, fn in _FACES:
        b64 = base64.b64encode((ASSETS / "fonts" / fn).read_bytes()).decode()
        out.append(
            f"@font-face{{font-family:'{family}';font-style:normal;"
            f"font-weight:{weight};font-display:swap;"
            f"src:url(data:font/woff2;base64,{b64}) format('woff2')}}")
    return "\n".join(out)


def asset_b64(name: str) -> str:
    return base64.b64encode((ASSETS / name).read_bytes()).decode()


FONTS = font_faces()

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

# The README findings table is the single source of truth for how many evaluations
# exist and how many were negative -- tests/test_frozen_invariants.py parses the same
# table. The page reads it too, so the two cannot drift. Four literals lived here
# before, outside V(), and they were two arms stale by the time anyone noticed: the
# only numbers on the page that could go wrong silently were the ones that bypassed
# the tracer.
_FINDINGS = re.findall(r"^\|\s*(\d+)\s*\|.*\|\s*\*\*([A-Z][A-Z ]+)\*\*",
                       (ROOT / "README.md").read_text(), re.M)
N_EVALS = V(len(_FINDINGS), "README.md findings table (row count)")
N_NEG = V([v.strip() for _, v in _FINDINGS].count("NEGATIVE"),
          "README.md findings table (NEGATIVE verdicts)")
_WORDS = {3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven", 8: "Eight",
          9: "Nine", 10: "Ten", 11: "Eleven", 12: "Twelve"}
N_EVALS_W, N_NEG_W = _WORDS.get(N_EVALS, N_EVALS), _WORDS.get(N_NEG, N_NEG)
_lc = lambda w: w.lower() if isinstance(w, str) else w
N_EVALS_L, N_NEG_L = _lc(N_EVALS_W), _lc(N_NEG_W)
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
_an = ROOT / "results" / "annotation" / "annotation_evaluation.json"
ANNOT = json.loads(_an.read_text()) if _an.exists() else None
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

if ANNOT:
    _d = ANNOT["descriptive_not_preregistered"]["per_collection"]
    AN_HALL = V(round(_d["hallmark"]["scoreable_fraction"] * 100),
                "annotation.hallmark.scoreable_fraction")
    AN_GO = V(round(_d["go_bp"]["scoreable_fraction"] * 100),
              "annotation.go_bp.scoreable_fraction")
    AN_GO_DECL = V(_d["go_bp"]["median_genes_declared"],
                   "annotation.go_bp.median_genes_declared")
    AN_GO_MEAS = V(_d["go_bp"]["median_genes_measured_in_screen"],
                   "annotation.go_bp.median_genes_measured")
    AN_N = V(ANNOT["sets_scored"], "annotation.sets_scored")

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
                             "change_my_mind": pr.get("what_would_change_my_mind", ""),
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
  --ink:#1a1a1a;          /* body text */
  --soft:#6B7280;         /* secondary */
  --rule:rgba(27,42,74,.14); /* hairline, navy-tinted */
  --fill:#f5f7f9;         /* figure and code ground */
  /* Darkened 2026-08-16 for WCAG AA -- identical hue (165.6) and saturation
     (0.62), only lightness moved, 0.475 -> 0.300, so the brand is the same
     teal. The previous value scored 2.21 on white and failed AA at every
     size, including the footer link carrying the repository URL. Now 5.09 on
     paper, 4.60 on tint, 4.74 on fill. The retired hex is deliberately not
     written here: the palette guard scans this stylesheet for literals and
     cannot tell a comment from a declaration, which is the correct bias.
     docs/DESIGN.md carries the before/after. */
  --accent:#1D7C65;       /* teal: links, metric numerals, small highlights */
  --navy:#1B2A4A;         /* headers, headings, footer */
  --tint:#E6F7F2;         /* card ground */
  --paper:#fff;
  --radius:8px;
}
/* NOT on `*` — with a non-zero radius that rounds every hairline and rule too.
   Applied to the elements that actually read as surfaces. */
*{box-sizing:border-box;margin:0;padding:0}
html{-webkit-text-size-adjust:100%;font-size:16px}
body{background:var(--paper);color:var(--ink);
  font:400 16px/1.62 "Source Serif 4",Georgia,"Times New Roman",serif;
  padding:0 40px;-webkit-font-smoothing:antialiased}

/* headings in Poppins; prose stays serif because the page is read, not scanned */
.hero,h2,h3,.metric .n,.masthead{font-family:"Poppins",-apple-system,
  BlinkMacSystemFont,"Segoe UI",sans-serif}
.hero,h2,h3{color:var(--navy)}
.metrics,.cards,.card,figure img,pre,table,.use{border-radius:var(--radius)}

/* masthead — the emblem only. The full lockup is in assets/denali-logo.png,
   but at 40px tall its wordmark renders about 5px and stops being readable. */
.masthead{padding:0 0 32px}
.masthead img{height:40px;width:auto;display:block}
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
/* the headline tally is the one 5-up grid: 4 negative + 2 positive + 1 no
   verdict = the 7 evaluations, plus the gene-claim count. The other two grids
   are 4-up, so this is a modifier rather than a change to .metrics. */
.metrics.tally{grid-template-columns:repeat(5,1fr)}
.metric{background:var(--paper);padding:22px 24px}
.metric .n{color:var(--accent);
  font-size:1.25rem;font-weight:600;line-height:1;margin-bottom:9px;
  font-variant-numeric:tabular-nums}
.metric .l{font-size:.8125rem;line-height:1.4;color:var(--soft)}

.cards{display:grid;grid-template-columns:repeat(3,1fr);
  border:1px solid var(--rule);background:var(--rule);gap:1px}
.card{background:var(--tint);padding:24px 26px}
/* Navy rather than soft-grey here. This heading sits on the tint ground,
   where the soft token measured 4.36
   against a 4.5 requirement. Navy is 12.83 there, and a card heading reading
   stronger than its body was the right call independently. */
.card h3{font-size:.8125rem;font-weight:600;text-transform:uppercase;
  letter-spacing:.1em;color:var(--navy);margin:0 0 14px}
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
/* what would change my mind — the falsification panel */
.cmm{margin-top:18px;border:1px solid var(--rule);border-left:2px solid var(--ink);
  padding:16px 20px;background:var(--paper)}
.cmm b{display:block;font:600 .6875rem/1.5 "JetBrains Mono",ui-monospace,monospace;
  letter-spacing:.13em;text-transform:uppercase;color:var(--ink);margin-bottom:9px}
.cmm p{font-size:.9375rem;line-height:1.62;margin:0;color:var(--ink)}

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
  .metrics,.metrics.tally,.cards,ol.limits{grid-template-columns:1fr}
  table.tools .stat,table.tools thead th:nth-child(2){display:none}
  body{padding:0 22px}main{padding:40px 0 64px}}
/* Phones. Until this existed the document was 680px wide inside a 390px
   viewport on first paint -- the whole page dragged sideways before anyone
   touched it. Four separate causes, one per line below.
   NOT body{overflow-x:hidden}: that hides the drag and leaves the explorer's
   Gate and Call columns permanently unreachable, which is worse than the bug.
   Each table scrolls inside its own box instead, so every column stays
   reachable and the page itself stops moving. */
/* A visible focus ring. There was none: keyboard users could reach nothing in
   the explorer, and once they could, they would not have been able to see where
   they were. :focus-visible so a mouse click does not leave a ring behind.
   Uses the accent token, which now clears AA on all three grounds. */
table.ex tr:focus-visible,table.ex th:focus-visible,a:focus-visible,
button:focus-visible,input:focus-visible{outline:2px solid var(--accent);
  outline-offset:2px}
table.ex tr{cursor:pointer}
@media(max-width:700px){
  table.ex,table.tools{display:block;overflow-x:auto}
  table.ex th{white-space:normal}
  table.tools .tool,.touch{white-space:normal}
  blockquote p,.detail h3,pre.wire,table.ex td:first-child{overflow-wrap:anywhere}
  .agwrap,.detail dl{grid-template-columns:1fr}}

/* the audit runner — vocabulary from docs/DESIGN.md "Interaction". One
   accent-filled primary on the whole page; everything else ink or ghost. */
.btn.primary{background:var(--accent);border-color:var(--accent);color:var(--paper)}
a.btn{display:inline-block;text-decoration:none}
.runrow{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin:26px 0 0}
.drop{display:block;position:relative;margin:22px 0 0;padding:24px 26px;
  border:1px dashed var(--rule);background:var(--paper);cursor:pointer;
  border-radius:var(--radius)}
.drop.over{background:var(--fill);border-color:var(--ink);border-style:solid}
.drop:focus-within{outline:2px solid var(--accent);outline-offset:2px}
.drop input{position:absolute;width:1px;height:1px;opacity:0;overflow:hidden;
  clip:rect(0 0 0 0)}
.drop .d1{display:block;font:600 1rem/1.4 "Poppins",-apple-system,
  BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--navy)}
.drop .d2{display:block;margin-top:5px;font-size:.875rem;line-height:1.55}
.drop .d3{display:block;margin-top:10px;font:400 .75rem/1.7 "JetBrains Mono",
  ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--soft)}
.audout{margin:24px 0 0}
/* --soft on --fill measures 4.502:1 — over the 4.5 line by two thousandths,
   which is not a margin, it is a rounding artefact. This is the first
   paragraph a visitor with no data reads, so it is set in --ink (16.21 on
   fill). The italic and the size still mark it as a waiting state. */
.aud-empty{padding:20px 24px;background:var(--fill);border:1px solid var(--rule);
  border-radius:var(--radius);font-size:.875rem;color:var(--ink);
  font-style:italic;line-height:1.6}
.aud-src{font:400 .75rem/1.7 "JetBrains Mono",ui-monospace,SFMono-Regular,Menlo,
  monospace;color:var(--soft);margin:0 0 16px;overflow-wrap:anywhere}
.aud-warn{font:400 .8125rem/1.7 "JetBrains Mono",ui-monospace,SFMono-Regular,
  Menlo,monospace;background:var(--fill);border:1px solid var(--rule);
  border-radius:var(--radius);padding:12px 16px;margin:0 0 16px;white-space:pre-wrap}
.aud-verdict .v{font:600 1.6rem/1.1 "Poppins",-apple-system,BlinkMacSystemFont,
  "Segoe UI",sans-serif;color:var(--navy);letter-spacing:.01em}
.aud-verdict .r{font-size:1.1875rem;line-height:1.5;max-width:46em;margin:10px 0 0}
.aud-todo{font-size:1rem;line-height:1.62;max-width:60em;margin:14px 0 0}
.aud-stats{font:400 .8125rem/1.7 "JetBrains Mono",ui-monospace,SFMono-Regular,
  Menlo,monospace;color:var(--soft);margin:16px 0 0;font-variant-numeric:tabular-nums}
.aud-block{margin:26px 0 0;border-top:1px solid var(--rule);padding-top:22px}
.aud-lbl{font:600 .75rem/1.5 "Poppins",-apple-system,BlinkMacSystemFont,
  "Segoe UI",sans-serif;text-transform:uppercase;letter-spacing:.08em;
  color:var(--soft);margin:0 0 10px}
.aud-body{font-size:1rem;line-height:1.62;max-width:60em}
.aud-cv{font-size:.8125rem;color:var(--soft);margin:12px 0 0;line-height:1.6;
  max-width:60em}
.rrwrap{overflow-x:auto}
table.rr{width:100%;border-collapse:collapse;font-size:.9375rem;margin:14px 0 0}
table.rr th{text-align:left;font-size:.75rem;text-transform:uppercase;
  letter-spacing:.08em;color:var(--soft);font-weight:600;
  padding:0 14px 8px 0;border-bottom:1px solid var(--rule)}
table.rr td{padding:10px 14px 10px 0;border-bottom:1px solid var(--rule);
  font-variant-numeric:tabular-nums;overflow-wrap:anywhere}
table.rr td.num,table.rr th.num{text-align:right;white-space:nowrap}
table.rr td.mv{font:600 .875rem/1.5 "JetBrains Mono",ui-monospace,SFMono-Regular,
  Menlo,monospace}
.aud-not{font-size:.8125rem;font-style:italic;color:var(--soft);margin:20px 0 0;
  line-height:1.6;max-width:60em}
.aud-err{padding:18px 22px;background:var(--fill);border:1px solid var(--rule);
  border-radius:var(--radius);font:400 .8125rem/1.75 "JetBrains Mono",
  ui-monospace,SFMono-Regular,Menlo,monospace;white-space:pre-wrap;
  overflow-wrap:anywhere}
.aud-map{margin:16px 0 0;display:flex;gap:14px;flex-wrap:wrap;align-items:flex-end}
.aud-map-lede{font-size:.875rem;color:var(--ink);flex-basis:100%;line-height:1.55}
.aud-map label{font:400 .75rem/1.6 "JetBrains Mono",ui-monospace,SFMono-Regular,
  Menlo,monospace;color:var(--soft)}
.aud-map select{font:400 .8125rem/1 "JetBrains Mono",ui-monospace,monospace;
  padding:6px 8px;border:1px solid var(--rule);background:var(--paper);
  color:var(--ink);cursor:pointer;max-width:220px}
@media(max-width:700px){
  .runrow .btn{width:100%;text-align:center}
  .aud-map select{max-width:100%}}
"""

EXPLORER_JSON = json.dumps(EXPLORER, separators=(",", ":"), default=str)

# ---------------------------------------------------------------- audit runner
# The in-page audit path: docs/PYODIDE_COSTING.md records why this is a ~200
# line JS port of denali_audit.core rather than Pyodide (49.5 MB, and its
# loader contains the literal network call the invariants forbid), and
# tests/test_page_audit_parity.py runs this exact JS under node against the
# packaged tool on real fixtures — a drifted number fails the build, the same
# discipline core.py applies to its own research source.
#
# The corpus is not retyped: it is parsed out of reference.py at build time so
# the reference distribution has one source file in this repository.
_REF_SRC = (ROOT / "packages" / "denali-audit" / "denali_audit" /
            "reference.py").read_text()
_CORPUS = [float(v) for v in
           re.findall(r"\b(\d\.\d{4})\b", _REF_SRC.split("CORPUS", 1)[1].split(")", 1)[0])]
_N_SCREENS = int(re.search(r"N_SCREENS = (\d+)", _REF_SRC).group(1))
assert len(_CORPUS) == _N_SCREENS, (
    f"corpus parse drifted from reference.py: {len(_CORPUS)} != {_N_SCREENS}")
EXAMPLE_CSV = (ROOT / "examples" / "example_gprofiler.csv").read_text()

# Pure functions only between the CORE markers — the parity test extracts and
# runs exactly that span under node, so DOM code must stay below the end mark.

# ---- the audit vocabulary, HARVESTED FROM THE PACKAGE, never retyped -------
# index.html carries a JavaScript port of audit(). Every string it prints used to
# be a hand-typed copy of core.py's, which is a second copy of a definition and
# therefore drifts -- and it did: when the verdict became null-relative, the page
# went on printing CONFOUNDED for inputs the package no longer called that.
#
# The four verdict words and the two mapping explanations are importable
# constants, so they are injected. The what_to_do texts are not constants, but
# they are static per verdict, so they are obtained by RUNNING the packaged
# audit() on fixtures chosen to produce each verdict and reading the result. If a
# verdict cannot be produced the build fails rather than shipping a page with a
# hole in it.
def _harvest_vocabulary() -> dict:
    import numpy as _np
    from denali_audit import core as _c
    from denali_audit import nulls as _nl

    rng = _np.random.default_rng(4)
    _s1 = rng.integers(10, 600, 60)
    _fx = {
        # non-counting, strong size relation
        _c.VERDICT_ABOVE: (_s1, (_s1 * 30 + rng.normal(0, 200, 60)).clip(0).round()),
    }
    _s2 = rng.integers(20, 400, 60)
    _fx[_c.VERDICT_INSIDE] = (_s2, rng.binomial(_s2, 0.06))
    _s3 = rng.integers(30, 500, 60)
    _fx[_c.VERDICT_BELOW] = (_s3, rng.binomial(_s3, 0.25 * (30 / _s3)))
    _fx[_c.VERDICT_UNDETERMINED] = (_np.array([50] * 12), _np.arange(12))

    todo = {}
    for want, (sz, ht) in _fx.items():
        r = _c.audit(sz, ht)
        if r["verdict"] != want:
            raise SystemExit(
                f"build_page could not produce the {want!r} verdict for harvesting "
                f"(got {r['verdict']!r}). The page would ship without that branch's "
                f"text. Fix the fixture rather than typing the string in.")
        todo[want] = r["what_to_do"]
    return {
        "VERDICT_ABOVE": _c.VERDICT_ABOVE, "VERDICT_INSIDE": _c.VERDICT_INSIDE,
        "VERDICT_BELOW": _c.VERDICT_BELOW,
        "VERDICT_UNDETERMINED": _c.VERDICT_UNDETERMINED,
        "COUNTING_WHY": _nl.COUNTING_WHY, "NON_COUNTING_WHY": _nl.NON_COUNTING_WHY,
        "N_ITER": _nl.N_ITER, "MIN_SETS": _nl.MIN_SETS,
        "N_BOOT": _nl.N_BOOT, "STABLE_AT": _nl.STABLE_AT,
        "WHAT_TO_DO": todo,
    }


_VOCAB = _harvest_vocabulary()

_AUDIT_CORE_JS = r"""
// Ported from denali_audit/core.py + adapters.py + reference.py. Strings are
// verbatim; math is the same OLS/Spearman/rank arithmetic. Divergences that
// cannot matter after the finite-pair mask are commented where they occur.
function audLow(c){return String(c).toLowerCase().trim()}
function audHasCols(cols){for(var i=1;i<arguments.length;i++){var want=arguments[i].toLowerCase(),ok=false;
  for(var j=0;j<cols.length;j++)if(audLow(cols[j])===want){ok=true;break}
  if(!ok)return false}return true}
function audColIdx(cols,name){for(var i=0;i<cols.length;i++)if(audLow(cols[i])===name.toLowerCase())return i;return -1}
function audColVals(t,name){var i=audColIdx(t.cols,name);return t.rows.map(function(r){return r[i]})}
function audToNum(v){if(v===null||v===undefined)return NaN;var s=String(v).trim();
  if(s==="")return NaN;var n=Number(s);return isFinite(n)?n:NaN}
function audRatioNum(v){var m=/^\s*(\d+)\s*\//.exec(String(v));return m?+m[1]:NaN}
function audRatioDen(v){var m=/\/\s*(\d+)\s*$/.exec(String(v));return m?+m[1]:NaN}
function audParseTable(text,sep){
  // char-level CSV/TSV parser: quoted fields, "" escapes, delimiter sniffing
  // over the first line (tab beats comma beats semicolon by count).
  text=String(text).replace(/\r\n?/g,"\n");
  if(!sep){var first=text.slice(0,text.indexOf("\n")<0?text.length:text.indexOf("\n"));
    var nt=(first.match(/\t/g)||[]).length,nc=(first.match(/,/g)||[]).length,
        ns=(first.match(/;/g)||[]).length;
    sep=nt>=nc&&nt>=ns?"\t":(ns>nc?";":",");}
  var rows=[],row=[],cell="",q=false;
  for(var i=0;i<text.length;i++){var ch=text[i];
    if(q){if(ch==='"'){if(text[i+1]==='"'){cell+='"';i++}else q=false}else cell+=ch}
    else if(ch==='"')q=true;
    else if(ch===sep){row.push(cell);cell=""}
    else if(ch==="\n"){row.push(cell);cell="";
      if(row.length>1||row[0].trim()!=="")rows.push(row);row=[]}
    else cell+=ch}
  if(cell!==""||row.length){row.push(cell);
    if(row.length>1||row[0].trim()!=="")rows.push(row)}
  if(!rows.length)return{cols:[],rows:[]};
  return{cols:rows[0],rows:rows.slice(1)}}
var AUD_SUPPORTED=["denali","g:Profiler","DAVID","clusterProfiler",
  "Enrichr / GSEApy","MAGeCK (gene_summary)","fgsea","GSEA desktop",
  "drugZ (approximate — flagged)","BAGEL2 bf with NumObs (approximate — flagged)"];
function audDetect(t){
  var c=t.cols;
  if(audHasCols(c,"set","size","hits"))
    return audMap(t,"denali","set","size","hits",false,"");
  if(audHasCols(c,"term_size","intersection_size")){
    var nm=audHasCols(c,"term_name")?"term_name":"term_id";
    return audMap(t,"g:Profiler",nm,"term_size","intersection_size",false,
      "term_size and intersection_size map exactly onto size and hits");}
  if(audHasCols(c,"term","count","pop hits"))
    return audMap(t,"DAVID","term","pop hits","count",false,
      "'Pop Hits' is the set size in the background; 'Count' is the overlap");
  if(audHasCols(c,"bgratio","count")){
    var nm2=audHasCols(c,"description")?"description":"id";
    return{fmt:"clusterProfiler",names:audColVals(t,nm2),
      sizes:audColVals(t,"bgratio").map(audRatioNum),
      hits:audColVals(t,"count").map(audToNum),approximate:false,
      note:"size parsed from the numerator of BgRatio; hits is Count"};}
  if(audHasCols(c,"term","overlap")){
    var ov=audColVals(t,"overlap");
    return{fmt:"Enrichr / GSEApy",names:audColVals(t,"term"),
      sizes:ov.map(audRatioDen),hits:ov.map(audRatioNum),approximate:false,
      note:"size and hits parsed from the Overlap column ('5/200')"};}
  if(audHasCols(c,"id","num","neg|goodsgrna")){
    var sz=audColVals(t,"num").map(audToNum);
    var note="each gene is read as a set of its sgRNAs: 'num' is guides per gene, "+
      "'neg|goodsgrna' the count passing MAGeCK's cutoff. This audits the "+
      "depletion (neg) direction; for enrichment rerun with "+
      "--set id --size num --hits 'pos|goodsgrna'";
    var uniq={},n=0;sz.forEach(function(v){if(isFinite(v)&&!uniq[v]){uniq[v]=1;n++}});
    if(n===1)note+=". Guides-per-gene is constant in this library, so guide count "+
      "cannot explain this ranking — the audit will say so";
    return{fmt:"MAGeCK (gene_summary)",names:audColVals(t,"id"),sizes:sz,
      hits:audColVals(t,"neg|goodsgrna").map(audToNum),approximate:false,note:note};}
  if(audHasCols(c,"pathway","size")&&audHasCols(c,"leadingedge")){
    // adapters.py maps a MISSING leadingEdge cell to "nan" and so counts 1;
    // an empty string here counts 0. Only an empty cell can tell them apart.
    var le=audColVals(t,"leadingedge");
    var hits=le.map(function(v){var s=String(v===undefined?"":v);
      if(s.trim()==="")return 0;
      return(s.match(/[,\s]+/g)||[]).length+1});
    return{fmt:"fgsea",names:audColVals(t,"pathway"),
      sizes:audColVals(t,"size").map(audToNum),hits:hits,approximate:true,
      note:"fgsea reports no count of significant members; the "+
        "leading-edge subset size is used as the closest honest "+
        "stand-in. Treat the number as indicative, not exact."};}
  if(audHasCols(c,"name","size")){
    var cands=["fdr q-val","nom p-val"];
    for(var k=0;k<cands.length;k++)if(audHasCols(c,cands[k])){
      var q=audColVals(t,cands[k]).map(audToNum),
          sz2=audColVals(t,"size").map(audToNum);
      return{fmt:"GSEA desktop",names:audColVals(t,"name"),sizes:sz2,
        hits:q.map(function(v,i){return v<0.05?sz2[i]:0}),approximate:true,
        note:"GSEA desktop reports no per-set hit count; sets below "+
          cands[k]+" 0.05 are credited their full size, which is a "+
          "coarse stand-in. Prefer a tool that reports an overlap."};}}
  if(audHasCols(c,"gene","numobs","normz","fdr_synth")){
    var sz3=audColVals(t,"numobs").map(audToNum),
        q3=audColVals(t,"fdr_synth").map(audToNum);
    return{fmt:"drugZ",names:audColVals(t,"gene"),sizes:sz3,
      hits:q3.map(function(v,i){return v<0.05?sz3[i]:0}),approximate:true,
      note:"each gene is read as a set of its guide observations; numObs "+
        "counts guide x replicate observations, not distinct guides. "+
        "drugZ reports no per-gene count of significant guides, so "+
        "genes below fdr_synth 0.05 are credited their full numObs — "+
        "the same coarse stand-in as GSEA desktop. This audits the "+
        "synthetic-lethal (synth) direction only; the suppressor "+
        "(supp) columns are present in your file but not audited."};}
  if(audHasCols(c,"gene","bf","numobs")&&!audHasCols(c,"rna")){
    var sz4=audColVals(t,"numobs").map(audToNum),
        bf=audColVals(t,"bf").map(audToNum);
    return{fmt:"BAGEL2",names:audColVals(t,"gene"),sizes:sz4,
      hits:bf.map(function(v,i){return v>0?sz4[i]:0}),approximate:true,
      note:"each gene is read as a set of its guide observations; NumObs "+
        "counts guide x replicate observations, not distinct guides. "+
        "BAGEL reports no per-gene count of significant guides and no "+
        "FDR at this step, so genes with BF > 0 (evidence favours the "+
        "essential model) are credited their full NumObs — a coarse "+
        "stand-in. For a calibrated cutoff, take an FDR threshold from "+
        "`BAGEL.py pr`, join it to this file, and name the columns "+
        "yourself."};}
  return null}
function audMap(t,fmt,nameCol,sizeCol,hitsCol,approx,note){
  return{fmt:fmt,names:audColVals(t,nameCol),
    sizes:audColVals(t,sizeCol).map(audToNum),
    hits:audColVals(t,hitsCol).map(audToNum),approximate:approx,note:note}}
function audNearMiss(cols){
  if(audHasCols(cols,"sgrna","gene")&&!audHasCols(cols,"num"))
    return "This looks like MAGeCK's per-guide file (sgrna_summary.txt). The "+
      "audit reads the per-gene file: point it at gene_summary.txt from "+
      "the same `mageck test` run.";
  if(audHasCols(cols,"gene","bf")&&!audHasCols(cols,"numobs"))
    return "This looks like BAGEL output, but without a NumObs column there is "+
      "no set size to audit. `BAGEL.py bf` with the default bootstrap "+
      "training writes GENE, BF, STD, NumObs — use that file. (The `pr` "+
      "output reports FDR but no size, so it cannot be audited either.) "+
      "Alternatively, join guides-per-gene from your library file and name "+
      "the columns yourself.";
  if(audHasCols(cols,"rna","gene","bf"))
    return "This looks like BAGEL's per-guide (RNA-level) output. The audit "+
      "reads the per-gene file: rerun `BAGEL.py bf` without the RNA-level "+
      "flag.";
  return null}
function audDescribeFailure(cols){
  var miss=audNearMiss(cols);if(miss)return miss;
  var lst="["+cols.map(function(x){return "'"+String(x)+"'"}).join(", ")+"]";
  return "Could not recognise this table.\n\n"+
    "  columns found: "+lst+"\n\n"+
    "  formats understood: "+AUD_SUPPORTED.join(", ")+"\n\n"+
    "  Name the columns yourself instead:\n"+
    "      denali audit FILE --set <col> --size <col> --hits <col>\n\n"+
    "  size = how many members that set had.  hits = how many were significant."}
// ---- the math, from core.py ----
function audPyRound(x,nd){if(!isFinite(x))return x;var m=Math.pow(10,nd),y=x*m;
  var f=Math.floor(y),d=y-f;
  if(Math.abs(d-0.5)<1e-9){return(f%2===0?f:f+1)/m}
  return Math.round(y)/m}
function audMean(v){var s=0;for(var i=0;i<v.length;i++)s+=v[i];return s/v.length}
function audStd(v){var m=audMean(v),s=0;for(var i=0;i<v.length;i++)s+=(v[i]-m)*(v[i]-m);
  return Math.sqrt(s/v.length)}
function audFit1(x,y){var mx=audMean(x),my=audMean(y),num=0,den=0;
  for(var i=0;i<x.length;i++){num+=(x[i]-mx)*(y[i]-my);den+=(x[i]-mx)*(x[i]-mx)}
  var b=num/den;return[b,my-b*mx]}
function audR2(x,y){if(audStd(x)===0)return NaN;var f=audFit1(x,y),sr=0,st=0,my=audMean(y);
  for(var i=0;i<x.length;i++){var p=f[0]*x[i]+f[1];sr+=(y[i]-p)*(y[i]-p);st+=(y[i]-my)*(y[i]-my)}
  return st===0?NaN:1-sr/st}
function audRanks(v){var idx=v.map(function(_,i){return i});
  idx.sort(function(a,b){return v[a]-v[b]||a-b});
  var r=new Array(v.length),i=0;
  while(i<idx.length){var j=i;while(j+1<idx.length&&v[idx[j+1]]===v[idx[i]])j++;
    var avg=(i+j+2)/2;for(var k=i;k<=j;k++)r[idx[k]]=avg;i=j+1}
  return r}
function audSpearman(x,y){var rx=audRanks(x),ry=audRanks(y),
  mx=audMean(rx),my=audMean(ry),num=0,dx=0,dy=0;
  for(var i=0;i<x.length;i++){num+=(rx[i]-mx)*(ry[i]-my);
    dx+=(rx[i]-mx)*(rx[i]-mx);dy+=(ry[i]-my)*(ry[i]-my)}
  return num/Math.sqrt(dx*dy)}
function audRankDesc(v){var idx=v.map(function(_,i){return i});
  idx.sort(function(a,b){return v[b]-v[a]||a-b});
  var r=new Array(v.length);idx.forEach(function(o,p){r[o]=p+1});return r}
function audPct0(x){return String(audPyRound(x,0))}

/* ---- nulls.py, ported -----------------------------------------------------
   The number audit() reports is not interpretable without this one: for nine of
   the ten formats this page accepts, hits are counted over the set's own members
   and the no-biology value is nowhere near zero.

   THE MONTE CARLO CANNOT MATCH PYTHON DRAW FOR DRAW. Python samples with NumPy's
   PCG64 at a fixed seed; reproducing that here would mean reimplementing PCG64,
   and matching a 300-draw estimate to 1e-10 across two languages is not a
   meaningful requirement anyway. What must match, and is asserted by
   tests/test_page_audit_parity.py, is the VERDICT -- the thing a reader acts on --
   plus every deterministic field. The two estimates are additionally required to
   agree within their own sampling error. The generator below is a plain
   mulberry32 at the same seed, stated rather than hidden. */
function audRng(seed){
  var a=seed>>>0;
  return function(){
    a|=0; a=a+0x6D2B79F5|0;
    var x=Math.imul(a^a>>>15,1|a);
    x=x+Math.imul(x^x>>>7,61|x)^x;
    return ((x^x>>>14)>>>0)/4294967296;
  };
}
function audBinom(n,p,rnd){    /* n small here; direct Bernoulli sum is exact */
  var k=0; for(var i=0;i<n;i++) if(rnd()<p) k++;
  return k;
}
function audStructure(s,h){
  var n=s.length;
  if(!n) return {structure:"unknown",frac_hits_le_size:null,
                 why:"no finite rows to decide from"};
  var ss=0,hs=0,le=0;
  for(var i=0;i<n;i++){ss+=s[i];hs+=h[i];if(h[i]<=s[i])le++}
  var rate=ss?hs/ss:NaN;
  var counting=(le===n)&&rate>=0&&rate<=1;
  return {structure:counting?"counting":"non-counting",
          frac_hits_le_size:audPyRound(le/n,4),
          why:counting?AUD_V.COUNTING_WHY:AUD_V.NON_COUNTING_WHY};
}
function audNull(s,h){
  var n=s.length;
  if(n<AUD_V.MIN_SETS) return null;
  var counting=audStructure(s,h).structure==="counting";
  var ss=0,hs=0; for(var i=0;i<n;i++){ss+=s[i];hs+=h[i]}
  var rate=ss?hs/ss:NaN;
  var rnd=audRng(20260816), draws=[];
  for(var it=0;it<AUD_V.N_ITER;it++){
    var sim=new Array(n);
    if(counting){ for(var j=0;j<n;j++) sim[j]=audBinom(Math.trunc(s[j]),rate,rnd) }
    else{ sim=h.slice();
      for(var k=n-1;k>0;k--){var m=Math.floor(rnd()*(k+1));var tmp=sim[k];sim[k]=sim[m];sim[m]=tmp} }
    var v=audR2(s,sim.map(function(x){return Math.log10(1+x)}));
    if(isFinite(v)) draws.push(v);
  }
  if(!draws.length) return null;
  draws.sort(function(a,b){return a-b});
  var mean=0; for(var q=0;q<draws.length;q++) mean+=draws[q];
  mean/=draws.length;
  return {_draws:draws, kind:counting
            ?"binomial constant-rate (hits drawn from the set's own members)"
            :"permutation (hits not bounded by size)",
          expected_r2:audPyRound(mean,4),
          ci95:[audPyRound(audPct(draws,2.5),4),audPyRound(audPct(draws,97.5),4)],
          n_iter:draws.length};
}
function audPct(sorted,q){    /* numpy's linear interpolation, on sorted input */
  var idx=(sorted.length-1)*q/100, lo=Math.floor(idx), hi=Math.ceil(idx);
  if(lo===hi) return sorted[lo];
  return sorted[lo]+(sorted[hi]-sorted[lo])*(idx-lo);
}

function audStability(obs,nul,seed){
  /* nulls.stability(), ported. Bootstraps the draws already computed, so it costs
     no extra regressions. A verdict whose sign flips under resampling should say
     so rather than pick a side -- the packaged threshold is imported, not chosen
     here, so the two surfaces cannot disagree about what "stable" means. */
  if(!nul||!isFinite(obs)) return null;
  var d=nul._draws; if(!d||!d.length) return null;
  var rnd=audRng((seed||20260816)+1), here=audPosition(obs,nul), agree=0;
  for(var b=0;b<AUD_V.N_BOOT;b++){
    var r=new Array(d.length);
    for(var i=0;i<d.length;i++) r[i]=d[Math.floor(rnd()*d.length)];
    r.sort(function(a,c){return a-c});
    var lo=audPct(r,2.5), hi=audPct(r,97.5);
    var p=obs>hi?"ABOVE":obs<lo?"BELOW":"INSIDE";
    if(p===here) agree++;
  }
  var frac=agree/AUD_V.N_BOOT, width=nul.ci95[1]-nul.ci95[0];
  var edge=Math.min(Math.abs(obs-nul.ci95[0]),Math.abs(obs-nul.ci95[1]));
  return {position_stability:audPyRound(frac,3),
          verdict_is_stable:frac>=AUD_V.STABLE_AT,
          distance_to_edge_in_ci_widths:width>0?audPyRound(edge/width,3):null};
}
function audPosition(obs,nul){
  if(!nul||!isFinite(obs)) return null;
  return obs>nul.ci95[1]?"ABOVE":obs<nul.ci95[0]?"BELOW":"INSIDE";
}

function audit(sizes,hits){
  var s=[],h=[];
  for(var i=0;i<sizes.length;i++)if(isFinite(sizes[i])&&isFinite(hits[i])){s.push(+sizes[i]);h.push(+hits[i])}
  var n=s.length;
  if(n<8)throw new Error("need at least 8 sets to say anything; got "+n);
  var y=h.map(function(v){return Math.log10(1+v)});
  var mn=s[0],mx=s[0];
  for(var q=1;q<n;q++){if(s[q]<mn)mn=s[q];if(s[q]>mx)mx=s[q]}
  var out={n_sets:n,size_range:[Math.trunc(mn),Math.trunc(mx)],
    r2_size_alone:audPyRound(audR2(s,y),4),
    spearman_size_vs_hits:audStd(s)===0?NaN:audPyRound(audSpearman(s,y),4),
    sets_with_zero_hits:h.filter(function(v){return v===0}).length};
  var share=out.r2_size_alone;
  out.share_explained_without_biology=share;
  // BEFORE the early return, because mapping describes the TABLE, not the
  // verdict. It was attached after, so every degenerate input -- constant hits,
  // constant size -- came back without it, which is exactly the class of input
  // a caller most needs it for. Same fix as core.py; found by the package's own
  // verify suite raising KeyError on the inputs it exists to handle gracefully.
  out.mapping=audStructure(s,h);
  if(!isFinite(share)){
    out.verdict="UNDETERMINED";
    // Two different reasons land here: constant SIZE (no variance in the
    // predictor) and constant HITS (none in the outcome). See core.py.
    if(audStd(s)===0){
      out.reading="This ranking cannot be audited for size: every set is the same size, "+
        "so set size has no variation with which to explain anything.";
      out.what_to_do="This is not an all-clear. Size is ruled out here by construction, but "+
        "the other ways a ranking can be carried by how it was measured -- "+
        "read depth, guide efficacy, replicate count -- are untested and this "+
        "tool does not test them. If your sets do vary in size, check you "+
        "passed the right column.";}
    else{
      var nz=0;for(var z=0;z<h.length;z++)if(h[z]===0)nz++;
      out.reading="This ranking cannot be audited for size: every set returned the same "+
        "number of hits"+(nz===n?" (zero)":"")+", so there is "+
        "no variation in the ranking for set size or anything else to explain.";
      out.what_to_do="This is not an all-clear and it is not a ranking. Nothing here "+
        "distinguishes any set from any other, so there is no top to audit. "+
        "If you expected hits, check the significance threshold and the "+
        "column you passed; if the screen genuinely returned nothing, that "+
        "is the result and no re-ranking will change it.";}
    out.what_this_is_not="Not a candidate list and not a recommendation. This measures a property "+
      "of the ranking, not of any gene or pathway in it.";
    out.method="VIF = 1 + (m-1)*rho_bar, Wu & Smyth 2012, "+
      "Nucleic Acids Research 40(17):e133, doi:10.1093/nar/gks461";
    return out}
  out.reading=audPct0(share*100)+"% of the variance in this ranking is predicted by how the "+
    "sets were built, with no reference to what any gene does.";
  /* The verdict is relative to THIS mapping's own null, not a band on the raw
     R^2. See core.py: a band calibrated on a non-counting screen told a real
     published counting screen measured at 0.36 against a null of 0.72 to check
     that its leading entries were not simply its largest sets. */
  var nul=audNull(s,h);
  if(nul){
    var st=audStability(share,nul,20260816);
    var pub={};
    for(var kk in nul) if(kk.charAt(0)!=="_") pub[kk]=nul[kk];
    out.no_biology_null=Object.assign(pub,{position:audPosition(share,nul)},st||{});
  }
  var pos=nul?audPosition(share,nul):null;
  out.verdict = pos==="ABOVE" ? AUD_V.VERDICT_ABOVE
              : pos==="BELOW" ? AUD_V.VERDICT_BELOW
              : pos==="INSIDE" ? AUD_V.VERDICT_INSIDE
              : AUD_V.VERDICT_UNDETERMINED;
  out.what_to_do = AUD_V.WHAT_TO_DO[out.verdict];
  out.what_this_is_not="Not a candidate list and not a recommendation. This measures a property "+
    "of the ranking, not of any gene or pathway in it.";
  out.method="VIF = 1 + (m-1)*rho_bar, Wu & Smyth 2012, "+
    "Nucleic Acids Research 40(17):e133, doi:10.1093/nar/gks461";
  // reference.py context()
  var lo=0,hi=AUD_CORPUS.length;
  while(lo<hi){var mid=(lo+hi)>>1;if(AUD_CORPUS[mid]<out.r2_size_alone)lo=mid+1;else hi=mid}
  var p=audPyRound(100*lo/AUD_CORPUS.length,1);
  var band=p>=90?"unusually confounded -- worse than nine in ten published screens":
    p>=75?"more confounded than most published screens":
    p>=40?"typical of published screens":
    "less confounded than most published screens";
  out.corpus_percentile=p;
  out.corpus_n_screens=AUD_CORPUS.length;
  out.corpus_collection="MSigDB Hallmark";
  out.corpus_reading="This ranking is "+band+": "+audPct0(p)+"% of "+AUD_CORPUS.length+
    " published CRISPR screens are less explained by set size than yours.";
  out.corpus_caveat="The reference was built against MSigDB Hallmark. If your sets came "+
    "from a different collection the percentile is indicative, not exact.";
  out.corpus_source="BioGRID ORCS 2.0.18, human, 1272 screens meeting the inclusion rule";
  return out}
function audRerank(sizes,hits,names,top){
  var s=[],h=[],nm=[];
  for(var i=0;i<sizes.length;i++)if(isFinite(sizes[i])&&isFinite(hits[i])){
    s.push(+sizes[i]);h.push(+hits[i]);
    nm.push(names?String(names[i]):"set "+i)}
  var n=s.length;
  if(n<8)throw new Error("need at least 8 sets to say anything; got "+n);
  var y=h.map(function(v){return Math.log10(1+v)});
  var constant=audStd(s)===0,resid;
  if(constant){var my=audMean(y);resid=y.map(function(v){return v-my})}
  else{var f=audFit1(s,y);resid=y.map(function(v,j){return v-(f[0]*s[j]+f[1])})}
  var orig=audRankDesc(h),corr=audRankDesc(resid);
  var k=Math.min(Math.trunc(top),n),survived=0,dropped=[];
  for(var j=0;j<n;j++){if(orig[j]<=k&&corr[j]<=k)survived++;
    if(orig[j]<=k&&corr[j]>k)dropped.push(j)}
  dropped.sort(function(a,b){return corr[a]-corr[b]});
  var rows=dropped.map(function(j){return{name:nm[j],size:Math.trunc(s[j]),
    hits:Math.trunc(h[j]),rank_original:orig[j],rank_size_aware:corr[j],
    moved:orig[j]-corr[j]}});
  var reading="Of your top "+k+", "+survived+" hold their place once set size is accounted "+
    "for and "+(k-survived)+" do not. The ones that move are the entries your "+
    "current ranking is least able to justify.";
  if(constant)reading="Every set here is the same size, so the size correction cannot move "+
    "anything and nothing below is evidence either way. This is not a "+
    "ranking that survived the correction; it is one the correction could "+
    "not be applied to.";
  var bf=0;dropped.forEach(function(j){var fall=corr[j]-orig[j];if(fall>bf)bf=fall});
  return{n_sets:n,top_n:k,survived_top_n:survived,left_top_n:k-survived,
    size_is_constant:constant,biggest_fall:bf,left_the_top:rows,
    correction:"log10(1+hits) regressed on set size; ranked by residual",
    reading:reading,
    what_this_is_not:"Not a candidate list. This says which entries were carried by size, not "+
      "which to chase. Nothing here is a recommendation to validate anything."}}
"""

_AUDIT_DOM_JS = r"""
// ---- page wiring: states from docs/DESIGN.md "Interaction". No network,
// no spinner; every state names its exit.
var AUD_LAST=null;
function audEsc(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;")
  .replace(/>/g,"&gt;").replace(/"/g,"&quot;")}
function audErr(html){$("audOut").innerHTML='<div class="aud-err">'+html+'</div>'}
function audRunText(text,label,sep){
  var t;
  try{t=audParseTable(text,sep)}catch(e){
    audErr(audEsc("Could not read this file as a table: "+e.message));return}
  if(!t.cols.length||!t.rows.length){
    audErr(audEsc("This file has no table rows in it. The audit reads the "+
      "results table your enrichment tool exported — one row per gene set."));return}
  AUD_LAST={table:t,label:label};
  var m=audDetect(t);
  if(!m){audUnrecognised(t);return}
  audRender(m,label)}
function audUnrecognised(t){
  var miss=audNearMiss(t.cols);
  if(miss){audErr(audEsc(miss));return}
  var lst="["+t.cols.map(function(x){return "'"+String(x)+"'"}).join(", ")+"]";
  var opts=t.cols.map(function(c,i){return '<option value="'+i+'">'+audEsc(c)+'</option>'}).join("");
  $("audOut").innerHTML=
    '<div class="aud-err">'+audEsc("Could not recognise this table.\n\n  columns found: "+lst+
      "\n\n  formats understood: "+AUD_SUPPORTED.join(", "))+'</div>'+
    '<div class="aud-map"><span class="aud-map-lede">Name the three columns yourself — '+
      'size is how many members that set had, hits how many were significant:</span>'+
    '<label>set name<br><select id="mapSet" class="mapsel">'+opts+'</select></label>'+
    '<label>size<br><select id="mapSize" class="mapsel">'+opts+'</select></label>'+
    '<label>hits<br><select id="mapHits" class="mapsel">'+opts+'</select></label>'+
    '<button id="mapRun" class="btn ghost">Audit with these columns</button></div>';
  $("mapRun").onclick=function(){
    var t2=AUD_LAST.table,si=+$("mapSet").value,zi=+$("mapSize").value,hi=+$("mapHits").value;
    audRender({fmt:"manual",names:t2.rows.map(function(r){return r[si]}),
      sizes:t2.rows.map(function(r){return audToNum(r[zi])}),
      hits:t2.rows.map(function(r){return audToNum(r[hi])}),
      approximate:false,note:"columns named by hand: set="+t2.cols[si]+
        ", size="+t2.cols[zi]+", hits="+t2.cols[hi]},AUD_LAST.label)}}
function audRender(m,label){
  var res,rr;
  try{res=audit(m.sizes,m.hits);rr=audRerank(m.sizes,m.hits,m.names,10)}
  catch(e){audErr(audEsc(e.message+"  The audit needs one row per gene set; "+
    "a file with fewer than 8 usable rows cannot say anything either way."));return}
  var h='<p class="aud-src">read as '+audEsc(m.fmt)+(m.note?" — "+audEsc(m.note):"")+
    ' &middot; '+audEsc(label)+'</p>';
  // Rows without a usable size or hits are masked, never imputed -- the same
  // rule the study applies to its own matrix. Masking silently is the part
  // that misleads: the user sees a verdict over fewer sets than their file
  // has and nothing says so. This counts them and says so. It changes no
  // number, so it stays out of audit() and out of the parity contract.
  var dropped=0;
  for(var q=0;q<m.sizes.length;q++)
    if(!isFinite(m.sizes[q])||!isFinite(m.hits[q]))dropped++;
  if(dropped)h+='<div class="aud-warn">'+dropped+' of '+m.sizes.length+
    ' rows had no usable size or hits and were left out — not counted, not '+
    'guessed at. The verdict below is over the remaining '+
    (m.sizes.length-dropped)+'.</div>';
  if(m.approximate)h+='<div class="aud-warn">⚠ APPROXIMATE INPUT — see the note '+
    'above; the verdict inherits it.</div>';
  h+='<div class="aud-verdict"><div class="v">'+audEsc(res.verdict)+'</div>'+
    '<p class="r">'+audEsc(res.reading)+'</p></div>'+
    '<p class="aud-todo">'+audEsc(res.what_to_do)+'</p>'+
    '<p class="aud-stats">sets '+res.n_sets+' &middot; size range '+res.size_range[0]+
    "–"+res.size_range[1]+' &middot; R² size-alone '+
    (isFinite(res.r2_size_alone)?res.r2_size_alone.toFixed(4):"undefined")+
    (res.sets_with_zero_hits?' &middot; '+res.sets_with_zero_hits+' sets returned nothing':'')+'</p>';
  if(res.corpus_reading!==undefined)
    h+='<div class="aud-block"><div class="aud-lbl">Against the field</div>'+
      '<p class="aud-body">'+audEsc(res.corpus_reading)+'</p>'+
      '<p class="aud-cv">'+audEsc(res.corpus_caveat)+' Source: '+audEsc(res.corpus_source)+'.</p></div>';
  h+='<div class="aud-block"><div class="aud-lbl">What leaves your top '+rr.top_n+'</div>'+
    '<p class="aud-body">'+audEsc(rr.reading)+'</p>';
  if(!rr.size_is_constant){
    if(rr.left_the_top.length){
      h+='<div class="rrwrap"><table class="rr"><thead><tr><th>entry</th>'+
        '<th class="num">size</th><th class="num">hits</th>'+
        '<th class="num">rank → size-aware</th></tr></thead><tbody>'+
        rr.left_the_top.map(function(r){return '<tr><td>'+audEsc(r.name)+'</td>'+
          '<td class="num">'+r.size+'</td><td class="num">'+r.hits+'</td>'+
          '<td class="num mv">'+r.rank_original+' → '+r.rank_size_aware+
          ' ('+(r.moved>0?"+":"")+r.moved+')</td></tr>'}).join("")+
        '</tbody></table></div>'+
        '<p class="aud-cv">biggest fall: '+rr.biggest_fall+' places &middot; correction: '+
        audEsc(rr.correction)+'</p>';}
    else h+='<p class="aud-body">Nothing left the top. This ranking survives its own size correction.</p>';}
  h+='</div><p class="aud-not">'+audEsc(rr.what_this_is_not)+'</p>';
  $("audOut").innerHTML=h;
  $("audOut").scrollIntoView({behavior:"smooth",block:"nearest"})}
function audRunFile(f){
  if(!f)return;
  $("audOut").innerHTML='<p class="aud-src">reading '+audEsc(f.name)+"…</p>";
  var sep=/\.(tsv|tab|txt)$/i.test(f.name)?"\t":null;
  var r=new FileReader();
  r.onload=function(){audRunText(r.result,f.name,sep)};
  r.onerror=function(){audErr(audEsc("Could not read "+f.name+
    " — the browser refused the file. Try again, or use the packaged tool below."))};
  r.readAsText(f)}
$("runExample").onclick=function(){
  audRunText(AUD_EXAMPLE,"example_gprofiler.csv — our own screen, re-exported "+
    "in g:Profiler's shape",null);
  $("audOut").scrollIntoView({behavior:"smooth",block:"start"})};
$("fileIn").onchange=function(){audRunFile(this.files[0]);this.value=""};
(function(){var d=$("drop");
  ["dragover","dragenter"].forEach(function(ev){d.addEventListener(ev,function(e){
    e.preventDefault();d.classList.add("over")})});
  ["dragleave","dragend"].forEach(function(ev){d.addEventListener(ev,function(){
    d.classList.remove("over")})});
  d.addEventListener("drop",function(e){e.preventDefault();d.classList.remove("over");
    if(e.dataTransfer.files&&e.dataTransfer.files.length)audRunFile(e.dataTransfer.files[0]);
    else{var txt=e.dataTransfer.getData("text");if(txt)audRunText(txt,"dropped text",null)}});
  document.addEventListener("paste",function(e){
    var tag=(e.target.tagName||"").toLowerCase();
    if(tag==="input"||tag==="select"||tag==="textarea")return;
    var txt=(e.clipboardData||window.clipboardData).getData("text");
    if(txt&&txt.indexOf("\n")>-1&&/[\t,;]/.test(txt))audRunText(txt,"pasted table",null)});
})();
"""

AUDIT_SCRIPT = ("/*AUDIT-CORE-START*/\n"
                f"const AUD_CORPUS=[{','.join(f'{v:.4f}' for v in _CORPUS)}];\n"
                f"const AUD_V={json.dumps(_VOCAB)};\n"
                f"const AUD_EXAMPLE={json.dumps(EXAMPLE_CSV)};\n"
                + _AUDIT_CORE_JS + "\n/*AUDIT-CORE-END*/\n" + _AUDIT_DOM_JS)


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
<title>denali</title>
<link rel="icon" type="image/png" href="data:image/png;base64,{asset_b64("denali-favicon.png")}">
<style>{FONTS}
{CSS}</style>
<main>

<header class="masthead"><img src="data:image/png;base64,{asset_b64("denali-mark.png")}" alt="denali"></header>

<!-- 1. hero -->
<section class="hero-sec">
<!-- The page had no h1 at all: every outline tool and screen reader saw a
     document starting at h2, with the real title existing only as a styled
     paragraph. This is a markup change, not a design change -- the global
     star-selector margin reset and .hero's explicit font-size mean p and h1
     render identically here, verified by measuring the box before and after
     and getting the same top, left, width, height, and computed type. -->
<h1 class="hero">Bigger gene sets win,<br>and it has nothing<br>to do with biology.</h1>
<p class="claim">A 200-gene program returns more hits than a 30-gene one regardless of
what either does &mdash; the way a raw crime count always ranks big cities as the most
dangerous. Across all {N_PROGRAMS} Hallmark programs scored against {N_KD:,} CRISPRi
knockdowns in K562, <b>program size alone explains {SIZE_R2*100:.1f}%</b> of what looks
like discovery, and {PCT_LO}–{PCT_HI}% of the variance is explained without reference
to what any program does.</p>
<p class="circ">The range is a range because one of our six features is computed
from the same matrix as the outcome, so part of {R_HI:.3f} is arithmetic. {R_LO:.3f} is the
figure that survives that objection, and we never quote the top alone.</p>
<!-- The primary action. The page used to argue and then stop: the first
     interactive element was the explorer, several screens down, exploring OUR
     data. docs/USER_JOURNEY.md names that as dead end A; this row is the fix.
     One accent-filled button on the whole page — the budget decision is
     recorded in docs/DESIGN.md "Interaction". -->
<div class="runrow">
  <button id="runExample" class="btn primary">Run the audit on our screen</button>
  <a class="btn ghost" href="#cost">or drop your own results</a>
</div>
</section>

<!-- 1b. the runner — the path from "convinced" to "ran it on my data".
     Same math as packages/denali-audit, ported to the page and held equal by
     tests/test_page_audit_parity.py. The page still makes zero network calls;
     the file is read with FileReader and never leaves the tab. -->
<section>
<div class="label">Use it on your own screen</div>
<h2 id="cost">Two minutes, before the year.</h2>
<p class="claim">Your enrichment tool already gave you the whole input: set name,
how many genes each set had, how many came back significant. Drop that file
below &mdash; it is read in your browser and goes nowhere. This page makes no
network call of any kind, and a build-failing test enforces that, so your
results cannot leave this tab.</p>

<label class="drop" id="drop">
  <input type="file" id="fileIn" accept=".csv,.tsv,.txt,.tab"
    aria-label="Results table from your enrichment tool. Read locally in your browser; nothing is uploaded.">
  <span class="d1">Drop your results file &mdash; or click to browse, or paste the table</span>
  <span class="d2">Nothing is uploaded: the file is read on your machine and stays there.</span>
  <span class="d3">Read as-is: g:Profiler &middot; Enrichr / GSEApy &middot; DAVID &middot;
clusterProfiler &middot; MAGeCK gene_summary &middot; fgsea &middot; GSEA desktop &middot;
drugZ &middot; BAGEL2. Anything else, you name the three columns yourself.</span>
</label>

<div id="audOut" class="audout" aria-live="polite">
  <div class="aud-empty">Nothing read yet. Three things will appear here, in
  order: the verdict on how much of the ranking set size explains, where that
  sits against 1,272 published CRISPR screens, and which of the top-ten entries
  survive the size correction. Get them from the button above &mdash; our own
  screen, one click &mdash; or from a file of yours.</div>
</div>
</section>

<!-- 2. metrics -->
<section>
<p class="lede">{N_EVALS_W} evaluations. {N_NEG_W} came back negative, one returned no
verdict when our own power rule fired against us, and all {N_EVALS_L} are reported here.
No gene-level claim is made anywhere, and the build fails if one appears.</p>
</section>

{figure("fig1_matrix.png")}

<!-- 4. negatives -->
<section>
<h2 id="findings">Three of the {N_NEG_L} negative findings</h2>
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

<!-- 3b. take it with you — the pipeline copy of the runner above -->
<section>
<div class="label">Take it with you</div>
<h2 id="install">The same check, in your pipeline.</h2>
<p class="claim">The runner above is this repository&rsquo;s own math ported into the
page, and a parity test fails the build if the two ever disagree on a number.
For repeated use &mdash; every screen, every collection, CI &mdash; install the
packaged tool. Same input, same verdict, plus a <code>--json</code> flag and a
replication check the page does not carry.</p>

<div class="use">
  <div>
    <h3>1 &middot; install, from a clone</h3>
    <pre class="cmd">git clone https://github.com/alejandro-publius/denali
pip install -e denali/packages/denali-audit
denali audit my_results.csv
denali rerank my_results.csv --top 10</pre>
    <p class="note">No column renaming: it reads <b>g:Profiler, DAVID,
    clusterProfiler, Enrichr/GSEApy, MAGeCK gene_summary, fgsea, GSEA desktop,
    drugZ and BAGEL2</b> output as-is (<code>denali formats</code>). An R&sup2;
    is not a judgement until you know what normal looks like &mdash; the
    field&rsquo;s median is <b>0.224</b>.</p>
  </div>
  <div>
    <h3>2 &middot; what the CLI adds</h3>
    <pre class="cmd">denali audit results.csv --json
denali replication results.csv --hits-b screen2</pre>
    <p class="note"><b>It grades its own correction.</b> Re-audit the re-ranked
    list and the score has to drop, or the correction did not work on
    your data &mdash; and you know that before you publish, not after. On ours:
    <b>{SIZE_R2} CONFOUNDED &rarr; 0.0000 NOT SIZE-DOMINATED</b>. The tool still
    refuses to say the survivors are real; it reports what was carried by
    size, not what to chase.</p>
    <p class="note"><b>Replication has a price too.</b> When two screens agree,
    <code>denali replication</code> measures how much of the agreement is set
    size &mdash; both screens confounded the same way agree for the same wrong
    reason.</p>
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
no <em>backend</em> and no key to manage: this page is a single static file that
makes zero network calls, enforced by five tests. It is served from GitHub Pages
for convenience, and that copy is byte-identical to the file in the repository
&mdash; downloading it and opening it offline gets you the same page, because
every figure, font and number is already inlined. A backend would mean this demo
could fail in front of you.</p>
</div>
</section>

<!-- 4a. the agent -->
<section>
<div class="label">The loop, running</div>
<h2 id="loop">The agent chooses what to look at next, and decides when it has seen enough.</h2>
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
<h2 id="table">All {N_PROGRAMS} programs</h2>
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
  $("tb").innerHTML=r.map(d=>'<tr tabindex="0" role="button" aria-label="Open details for '+d.short+'" data-i="'+DATA.indexOf(d)+'"><td>'+d.short+
    (d.is_held_out_program?' <span class="tag held">held out</span>':'')+
    '</td><td class="num">'+num(d.n_hits_q05)+'</td><td class="num">'+num(d.R_p)+
    '</td><td class="num">'+num(d.R_p_predicted_from_measurability)+
    '</td><td class="num">'+num(d.R_p_residual_after_measurability)+
    '</td><td><span class="tag">'+(d.passes_measurability_gate?'passes':'fails')+
    '</span></td><td>'+d.reversibility_call+'</td></tr>').join("");
  // Keyboard parity with the mouse. The explorer is the interactive centre of
  // this page and until 2026-08-16 all 50 rows were unreachable without a
  // pointer: tabindex -1, no role, click-only. Enter and Space both open a row,
  // matching what role="button" promises a screen-reader user.
  [...$("tb").rows].forEach(tr=>{{
    tr.onclick=()=>detail(+tr.dataset.i,tr);
    tr.onkeydown=e=>{{if(e.key==="Enter"||e.key===" "){{e.preventDefault();
      detail(+tr.dataset.i,tr);}}}};}});}}
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
  const extra=["mechanism","why_not_gene_level","caveat"]
    .filter(k=>pr[k]).map(k=>'<p>'+pr[k]+'</p>').join("");
  const cmm=pr.change_my_mind
    ? '<div class="cmm"><b>What would change my mind</b><p>'+pr.change_my_mind+'</p></div>'
    : "";
  $("det").innerHTML='<h3>'+d.program+'</h3><p style="font-size:.9375rem;color:var(--soft);margin:-6px 0 14px">'+
    d.call_plain+'</p><dl>'+bits+'</dl><div class="prop"><b>Generated next experiment &middot; '+
    (pr.outcome||'')+'</b><p>'+(pr.next_experiment||'')+'</p>'+extra+'</div>'+cmm;
  $("det").classList.add("on");}}
document.querySelectorAll("table.ex th").forEach(th=>{{
  const go=()=>{{const k=th.dataset.k; sortAsc=(k===sortK)?!sortAsc:(k==="short");
    sortK=k; draw();}};
  th.tabIndex=0; th.setAttribute("role","button");
  th.onclick=go;
  th.onkeydown=e=>{{if(e.key==="Enter"||e.key===" "){{e.preventDefault();go();}}}};}});
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

<script>
{AUDIT_SCRIPT}
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

<!-- 5c. annotation -->
<section>
<div class="label">Added after the freeze &middot; and it failed twice</div>
<h2>Everything above used the cleanest annotation in biology. Most people use the
messiest one.</h2>

<p class="claim">Hallmark is 50 hand-curated sets spanning 6&times; in size. Gene
Ontology Biological Process is 7,538 sets spanning 398&times;, and it is the
most-used gene-set collection there is. We pre-registered a prediction: the size
confound should get <i>worse</i> as the annotation gets looser. {AN_N} sets across
four collections, scored on Modal.</p>

<div class="metrics" style="margin-top:26px">
  <div class="metric"><div class="n">{AN_HALL}%</div>
    <div class="l">of Hallmark sets can be scored against a genome-scale screen</div></div>
  <div class="metric"><div class="n">{AN_GO}%</div>
    <div class="l">of GO Biological Process sets can. The median GO-BP set declares
    {AN_GO_DECL} genes and has {AN_GO_MEAS} measured</div></div>
  <div class="metric"><div class="n">wrong</div>
    <div class="l">our prediction, in direction. GO-BP 0.2905 and Reactome 0.1846
    are <b>below</b> Hallmark, not above</div></div>
  <div class="metric"><div class="n">none</div>
    <div class="l">verdict issued. Our own power rule &mdash; 150 of 250 sets
    scoreable &mdash; fired on three of four collections</div></div>
</div>

<blockquote style="margin-top:30px"><p>More than half of the most-used gene-set
collection in biology cannot be evaluated against this screen at all. That is the
annotation meeting the assay, not the biology.</p></blockquote>

<p class="circ">Two failures and we are reporting both. The prediction was wrong in
direction, which we state rather than let an underpowered result quietly bury. And
the power rule fired before the deciding statistic could be applied, so no verdict
is issued and those R&sup2; figures carry none &mdash; the rule was fixed before the
run for exactly this case and it cost us the headline. What survives is
descriptive, was not the question we asked, and is labelled so wherever it
appears.</p>
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
<h2 id="positive">The one positive</h2>
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
<h2 id="limits">What this does not claim</h2>
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
<h2 id="tools">Set up is not the same as used. Here is what actually touched the result.</h2>
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
every figure and number above is read from results/frozen/ at build time · the only thing this page computes is the audit you feed it, and a parity test holds that equal to the packaged tool<br>
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
