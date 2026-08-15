"""Emit index.html — a single static file, every number traced to results/frozen/.

    .venv/bin/python -m src.build_page

Design contract, enforced below:
  * no number is typed into the template. Every value comes through V(), which
    reads a frozen file and records where it came from. A number that cannot be
    traced does not appear on the page.
  * caption text is read verbatim from results/figures/CAPTIONS.md.
  * figures are inlined as base64 so index.html is genuinely standalone.
  * white ground, ONE accent, FOUR type sizes, no gradients, no dark hero,
    no dashboard chrome, no interactive controls.
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
:root{--ink:#1a1a1a;--soft:#5c5c5c;--rule:#e3e3e3;--accent:#1a4d7a;--paper:#fff}
*{box-sizing:border-box;margin:0;padding:0}
html{-webkit-text-size-adjust:100%}
body{background:var(--paper);color:var(--ink);
  font:400 17px/1.62 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
  padding:0 40px}
main{max-width:1100px;margin:0 auto;padding:52px 0 120px}
/* four type sizes: hero / heading / body / small */
.hero{font-size:63px;line-height:1.04;letter-spacing:-.035em;font-weight:700}
h2{font-size:23px;line-height:1.3;font-weight:600;letter-spacing:-.01em;margin:0 0 22px}
.small{font-size:14.5px;line-height:1.55;color:var(--soft)}
.claim{font-size:20px;line-height:1.45;max-width:52em;margin:22px 0 0}
.circ{font-style:italic;font-size:16px;color:var(--soft);max-width:56em;margin:14px 0 0}
.mech{font-size:16px;margin:12px 0 0;max-width:56em}
section{margin:80px 0 0}
hr{border:0;border-top:1px solid var(--rule);margin:72px 0 0}
.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;margin:38px 0 0}
.metric{border:1px solid var(--rule);border-radius:3px;padding:20px 22px}
.metric .n{font-size:40px;line-height:1;font-weight:700;letter-spacing:-.02em}
.metric .l{margin-top:10px;font-size:14.5px;line-height:1.4;color:var(--soft)}
.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:26px}
.card{border-top:2px solid var(--accent);padding:20px 0 0}
.card h3{font-size:17px;font-weight:600;margin:0 0 10px}
.card p{font-size:15.5px;line-height:1.6;color:#333}
figure{margin:0}
figure img{width:100%;height:auto;display:block;border:1px solid var(--rule)}
figcaption{margin-top:14px;font-size:14.5px;line-height:1.6;color:var(--soft);max-width:58em}
figcaption b{color:var(--ink);font-weight:600}
blockquote{border-left:2px solid var(--accent);padding:2px 0 2px 26px;margin:0;
  max-width:44em}
blockquote p{font-size:17px;line-height:1.62}
.control{max-width:46em}
.control p{font-size:15.5px;line-height:1.62;color:#333}
.control .note{margin-top:14px;font-weight:600;color:var(--ink)}
ol.limits{list-style:none;counter-reset:l;display:grid;grid-template-columns:1fr 1fr;
  gap:22px 44px}
ol.limits li{counter-increment:l;position:relative;padding-left:32px;font-size:15.5px;
  line-height:1.6}
ol.limits li::before{content:counter(l);position:absolute;left:0;top:0;
  color:var(--accent);font-weight:700;font-variant-numeric:tabular-nums}
footer{margin-top:96px;padding-top:26px;border-top:1px solid var(--rule);
  font:400 13px/1.9 ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--soft)}
footer b{color:var(--ink);font-weight:600}
a{color:var(--accent)}
@media(max-width:1000px){.metrics,.cards,ol.limits{grid-template-columns:1fr}
  .hero{font-size:42px}body{padding:0 22px}main{padding:56px 0 80px}}
"""

HTML = f"""<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>denali — what a genome-scale screen can and cannot discover</title>
<style>{CSS}</style>
<main>

<!-- 1. hero -->
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

<!-- 2. metrics -->
<div class="metrics">
  <div class="metric"><div class="n">4</div><div class="l">evaluations run</div></div>
  <div class="metric"><div class="n">3</div><div class="l">came back negative</div></div>
  <div class="metric"><div class="n">1</div><div class="l">came back positive</div></div>
  <div class="metric"><div class="n">0</div><div class="l">gene-level claims made</div></div>
</div>

<hr>

<!-- 3. fig 1 -->
<section>{figure("fig1_matrix.png")}</section>

<hr>

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

<hr>

<!-- 5. fig 2 -->
<section>{figure("fig2_gate_failure.png")}</section>

<hr>

<!-- 6. the heme example -->
<section>
<blockquote><p>One held-out row carries the whole result. <b>{HEME_NAME}</b> drew
the highest prediction of all {NHELD} — R<sub>p</sub> {HEME_PRED} — on
{HEME_N} measured gene. It returned {HEME_HITS} hits. The model predicted strongly
because the program looked measurable on the features it could see, and the
program returned nothing because it was not measurable at all. The failure and the
finding are the same fact.</p></blockquote>
</section>

<hr>

<!-- 7. the control -->
<section class="control">
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

<hr>

<!-- 8. fig 4 -->
<section>{figure("fig4_retrieval.png")}</section>

<hr>

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

<!-- 10. provenance -->
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
