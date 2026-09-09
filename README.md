# denali 🏔

**A genome-scale CRISPRi screen, read back to ask what it can and cannot discover — and the answer is mostly an artifact of how the programs are defined, not their biology.**

[![CI](https://github.com/alejandro-publius/denali/actions/workflows/ci.yml/badge.svg)](https://github.com/alejandro-publius/denali/actions/workflows/ci.yml)
[![tests](https://img.shields.io/badge/tests-556-brightgreen.svg)](tests/test_frozen_invariants.py)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](.python-version)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Jump to:** [Findings](#findings) · [Architecture](docs/ARCHITECTURE.md) · [MCP server](#mcp-server--denali-as-a-tool-for-ai-agents) · [Reproduce it](#reproduce-it) · [Scope limits](#scope-limits) · [In plain language](#in-plain-language) · [How to check this project](#how-to-check-this-project) · [full docs index](docs/README.md)

A genetic screen hands a lab a ranked list of thousands of hits, and validating the top of it costs a year and six figures. **denali is the check you run before that decision.** It takes the table your gene-set analysis already produced and tells you how much of your ranking is explained by *how the sets were built* rather than by any biology.

```bash
pip install -e packages/denali-audit
denali audit my_results.csv
denali rerank my_results.csv --top 10
```

No column renaming. It reads **ten formats** as-is — g:Profiler, DAVID, clusterProfiler, Enrichr/GSEApy, MAGeCK `gene_summary`, fgsea, GSEA desktop, drugZ, BAGEL2 and this project's own output; `denali formats` lists them. Four of the ten report no per-set hit count, so the tool stands one in and **prints an APPROXIMATE flag above the verdict** rather than hiding the substitution. The reason any of this matters is that a check which asks you to reshape your data first is a check nobody runs.

**Not run the screen yet?** [**Plan a screen**](https://alejandro-publius.github.io/denali/screen.html) is the same instrument arriving at stage one instead of stage ten — eleven stages, what each decides, what goes wrong at it in your words, and a plain statement at the seven stages where denali has nothing to offer. It holds a pre-registration you write before you have data and shows it back to you beside your results. Nothing uploads; it lives in your browser.

**No Python at all?** [**Drop a CSV on the web version**](https://alejandro-publius.github.io/denali/audit.html). It runs this same package in your browser through WebAssembly — same code, same numbers — so there is no server and your file is never uploaded.

What comes back is a verdict, a percentile against **1,272 published screens**, and a correction:

```
MORE SIZE-CARRIED THAN ITS OWN NULL: 46% of the variance in this ranking is
predicted by how the sets were built, with no reference to what any gene does.

AGAINST THE FIELD
This ranking is unusually confounded — worse than nine in ten published
screens: 90% of 1272 published CRISPR screens are less explained by set
size than yours.
```

An R² is not a judgement until you know what normal looks like. The field's median is **0.224** and that output is denali's own screen at **0.465** — the tool says it about us.

**One caveat we would rather state than have found.** Those two numbers are not computed the same way: the corpus median fits log size, the audit fits raw size. On a like-for-like raw predictor the field's median is **0.192**, which makes our screen look *more* unusual rather than less, so the comparison is not flattering us — but it is a comparison across transforms and the percentile is indicative rather than exact. `docs/CORPUS.md` carries the sensitivity; the tool's own output says the reference is indicative too.

Then `denali rerank` applies the correction and shows you what leaves the top of your list. **On our own screen, three of the top ten hold and seven do not** — see [what the tool does to our own headline](#what-the-tool-does-to-our-own-result).

---

**Why trust it?** Because the study underneath it is the same check, run on our own data and then on everyone else's, and reported when it came back against us.

We scored all **50 MSigDB Hallmark gene programs** against **9,837 CRISPRi knockdowns** in K562 and asked which programs are *reversible* — which have many knockdowns that measurably move them. Then we asked the question underneath it: how much of that is biology at all. **Between 56% and 75% of the variance in apparent reversibility is explained by a model that never looks at what a program does.** It is a range and not a point because one of our six features is computed from the same matrix as the outcome, so part of the upper figure is arithmetic rather than discovery; **0.561** is the number that survives that objection and we never quote the top alone. The mechanism is size — bigger programs with more co-moving members return more hits regardless of their function, and **program size alone explains 46.5%**.

**And on seven other people's screens.** We ran the identical command on the published supplementary tables of seven external studies — CRISPR knockout, CRISPRi/a, single-cell CRISPRa, organoid, primary-T-cell, and bulk RNA-seq — and **36–88% of each ranking is explained by set construction alone.** Every input, provenance, and rerun command is in [`audits/external/`](audits/external/README.md); each number was verified against the source document and re-derived against this repo's own `src/audit_screen.py`. One study comes back only partially confounded and one candidate table was refused for having no true hit count — the auditor discriminates rather than flagging everything. The confound is not ours; it is the field's, and it is arithmetic.

**And fourteen times against ourselves.** Ten of fourteen evaluations came back negative, one returned no verdict when our own power rule fired, and all fourteen are reported below. The headline was also recomputed by [a second implementation that never read the first](docs/INDEPENDENT_RECOMPUTE.md).

**New to CRISPR screens?** [Start with the plain-language section](#in-plain-language) — no jargon, and it explains why any of this matters before the method does.

**Evaluating this?** Four questions are answered with file paths at [**How to check this project**](#how-to-check-this-project), at the bottom. If you have two minutes rather than ten: the [findings table](#findings) is fourteen rows and ten of them say NEGATIVE; the [loop](docs/LOOP.md) is where the agent chooses and halts; and `grep -n 'HALLMARK_\|REACTOME_' src/next_experiment.py` returns nothing, which is our central claim stated as something you can falsify in one command rather than something you have to believe.

**Read it at [alejandro-publius.github.io/denali](https://alejandro-publius.github.io/denali/).** The hosted copy is byte-identical to `index.html` in this repository and, like it, makes **zero network calls** — GitHub Pages serves the file, nothing fetches anything. So if the venue wifi dies, clone the repo and double-click `index.html`: same page, no server, no network. Everything in it is injected from `results/frozen/` at build time. A Streamlit view of the same frozen data lives in `app.py` (`streamlit run app.py`); both read `results/frozen/` and neither recomputes.

![Running the audit on your own screen, and re-auditing after the fix](docs/img/use-it.png)

*What a user does: audit the ranking they already have and see where it sits against 1,272 published screens, then `denali rerank` to see what leaves the top ten. Or connect the frozen matrix to their agent — no API key, no backend.*

## What the tool does to our own result

`denali rerank` applies the correction the audit names and shows what leaves the
top of the list. Run on **our own screen**, the one this whole repository is
about:

```bash
# build the input from this repo's own frozen results, then rerank it
python -c "import pandas as pd; d=pd.read_csv('results/frozen/program_summary.csv'); \
  d[['program','n_present','n_hits_q05']].rename(columns={'program':'set','n_present':'size','n_hits_q05':'hits'}) \
  .to_csv('our_screen.csv', index=False)"
denali rerank our_screen.csv --top 10
```

> Of your top 10, **3 hold their place** once set size is accounted for and
> **7 do not**. The ones that move are the entries your current ranking is least
> able to justify.

| entry | size | hits | rank → size-aware | |
|---|--:|--:|:--:|--:|
| `HALLMARK_MYC_TARGETS_V1` | 194 | 5,707 | **1 → 24** | −23 |
| `HALLMARK_OXIDATIVE_PHOSPHORYLATION` | 193 | 3,321 | 4 → 26 | −22 |
| `HALLMARK_E2F_TARGETS` | 190 | 5,668 | 2 → 21 | −19 |
| `HALLMARK_MTORC1_SIGNALING` | 176 | 1,706 | 9 → 27 | −18 |
| `HALLMARK_G2M_CHECKPOINT` | 182 | 5,229 | 3 → 19 | −16 |
| `HALLMARK_MITOTIC_SPINDLE` | 158 | 1,754 | 8 → 20 | −12 |
| `HALLMARK_HEME_METABOLISM` | 133 | 2,428 | 7 → 12 | −5 |

**Our number one falls to twenty-fourth.** `MYC_TARGETS_V1` is the largest set
in the collection at 194 measured members, it returned the most hits, and once
you ask how many hits a set that size returns *anyway*, it is unremarkable.

**The three that hold are not thereby real.** They are the three this ranking
is not obviously unable to justify, which is a weaker statement and the only one
the data supports. The tool says the same thing in its own output and we are not
going to say more than it does.

Note what the tool refuses to do here. It does not tell you the three survivors
are real, and it does not hand back a shorter list to go chase. Its own output
says so: *"Not a candidate list. This says which entries were carried by size,
not which to chase."* The correction is `log10(1+hits)` regressed on set size,
ranked by residual — stated in the output, so you can disagree with it.

We put our own screen through this rather than a borrowed example on purpose. A
tool that demotes its author's top hit by twenty-three places is a stronger
argument than any paragraph about why you should trust it.

## What we chose, and why

Stated up front because every one of these is attackable, and a reader should not
have to infer that we picked well.

1. **MSigDB Hallmark, not our own gene sets.** This is the field's own curated
   standard, so the size critique cannot be dismissed as an artifact of how *we*
   drew the boundaries — the sets were drawn by someone else, for other purposes,
   before we existed. Hallmark also spans a 6× size range (32 to 200 declared members), which is what makes the size effect visible at all. A collection of
   uniformly-sized sets would have hidden it.

2. **K562, because the screen exists.** Replogle et al. published a genome-scale
   CRISPRi Perturb-seq screen covering 9,837 knockdowns; nothing at that scale was
   going to be generated here. The cost is real and we state it rather than bury
   it: K562 is an unstressed leukemia line, and our own first program failed its
   known-regulator control for exactly that reason.

3. **Fourteen evaluations, ten of them negative.** Where an evaluation was
   pre-registered, the alternative claim was named before any value was computed,
   so a null was a publishable outcome rather than a failure. Ten came back
   negative, one returned no verdict at all because our own power rule fired, and
   two came back positive — one of which is a control, and it is labelled a
   control because that is what it is.

4. **Program level, never gene level.** Guide-pair concordance is −0.019: two
   independent reagents against the same gene disagree. That forbids any
   single-gene claim in this dataset, including a flattering one, and it is
   enforced by a test that fails the build rather than by our good intentions.

**What we deliberately did not attempt.** No structural or sequence-design claim,
because the concordance figure above forbids the gene-level claim one would have
to rest on. No candidate list and no ranked "top programs" table, because that is
the nomination the pre-registration refuses to make. No second cell line: RPE1 was
available and we checked it, but it covers only 24.3% of K562's targets and that
quarter is disproportionately the essential-gene subset — a control we ran and
published as a **FAIL** (94.1% vs 11.3% coverage, essential vs non-essential).
Running it anyway and calling it replication would have been the easiest available
overstatement.

## Findings

Fourteen evaluations. Ten negative, one with no verdict because our own power rule fired. All fourteen are reported. The eighth leaves our own data entirely: it asks the same question of two published clinical CRISPR off-target datasets. The eleventh leaves the data altogether and asks the literature.

| # | Evaluation | Result | Verdict |
|---|---|---|---|
| 1 | Is apparent reversibility biology? | adj R² **0.561–0.751** from measurability alone; program size alone 0.465 | **NEGATIVE** — pre-registered branch (b) fired |
| 2 | Does the obvious quality filter work? | **20 of 50** programs fail the gate and produce hits anyway; only **1** passes and produces nothing | **NEGATIVE** — the filter would have discarded our own best result |
| 3 | Does the predictor generalise? | **1 of 10** held-out programs measurable → underpowered and inconclusive; balanced accuracy **0.4375**, **zero** true positives | **NEGATIVE** — not refit |
| 4 | Does the ranking work at all? | Master regulator at rank 2/11,258; **11 of 17** canonical pathway members in the extreme 10%, p = 7.0×10⁻⁸, correct sign at both tails | **POSITIVE** — a control, not a discovery |
| 5 | Does the size effect hold in a second cell line? | RPE1, independently screened: size alone **R² 0.276**, slope **+0.0116**, p = 1.1×10⁻⁴, 49 of 50 scoreable | **POSITIVE** — pre-registered at ≥0.25, and it cleared by 0.026 |
| 6 | When two screens agree, is that biology? | Raw cross-screen agreement ρ **+0.663**; after removing set size, **+0.493**. **26% of the apparent replication is set size.** Size alone predicts **6 of the top 10** programs in the second screen | **NEGATIVE** — post-freeze, not pre-registered |
| 7 | Does the confound worsen in the annotations biologists actually use? | **UNDERPOWERED on 3 of 4 collections** — the pre-registered power rule fired before the deciding statistic could be applied. Descriptive, not pre-registered: **98% of Hallmark sets are scoreable against a genome-scale screen; 46% of GO Biological Process sets are** | **NO VERDICT** — and our prediction was wrong in direction |
| 8 | Does the same confound run in clinical CRISPR off-target nomination? | Two published datasets, neither ours. **CHANGE-seq vs GUIDE-seq**, 56 paired guides, 202,043 nominated sites: across seven swept read thresholds, **17.6–33.9% (median 31.2%)** of biochemical–cellular agreement is explained by **search yield**, not the guide. **85.2%** of nominated sites sit at 5–6 mismatches. **CRISPRme**, 14 therapeutic guides: **44.1%** of top-ranked sites score best on an alt allele, but only **12.4%** are absent from the reference | **NEGATIVE** — post-hoc, thresholds swept |
| 9 | Does the confound survive when the program is actually switched on? | Adamson 2016 UPR Perturb-seq, **pre-registered before the substrate was opened**. Engagement established first: mean effect **0.0551** vs a size- and expression-matched null's 99th percentile **0.0487**, p = 0.001. Then size alone explains **R² 0.269**, slope **+0.0072**, p = 1.2×10⁻⁴, **50 of 50** scoreable | **NEGATIVE** — pre-registered claim (a): the confound **persists under engagement** |
| 10 | Does our headline describe the field, or just our screen? | **1,272** published screens (BioGRID ORCS) from **187** publications: median size-alone R² **0.224**, mean 0.253; **9.6%** of screens reach our 0.465 — but **26.7%** of *publications* do, because one publication is 26.7% of the corpus; the gradient across hit-list-size bins (0.056 → 0.184 → 0.226 → 0.263) is monotonic | **NEGATIVE** — post-hoc, not pre-registered. Our screen is above the field's 90th percentile by screen but only its **73rd by publication**, and quoting 46.5% as typical would overstate the field ~2× |
| 11 | Does the field say so? | Of the **187** publications behind those screens, **111** resolved to full text in PubMed Central and **4** — **3.6%** — mention gene-set size anywhere; 14.4% use competitive-test machinery. Positive control: all three enrichment-methods papers fire, so the low rate is a rate and not a dead query | **POSITIVE** — pre-registered branch (b) fired (`docs/LITERATURE_PREREG.md`, sha256 `165d91a2…`, sealed at `b0c5e35` before the run). Arm is post-freeze. Measures **mention, not understanding**, over a **59.4%** open-access denominator |
| 12 | Does the field say so — when a model reads the papers instead of a regex? | Two models read all **111** publications. **13.5–16.2%** adjusted for set size or measured it, against the regex's 18.0%. Of the **15** that acted, **10** matched none of the thirteen patterns; of the **20** the regex called positive, **13** did nothing | **NEGATIVE** — for the regex, not the field: the two methods agree on 5 papers out of a union of 25, so the close headline shares are two errors nearly cancelling |
| 13 | Can a screen's no-biology floor be predicted from how it was built? | Four design-only predictors over all **1,272** corpus screens, five folds grouped by publication: cross-validated R² **0.0935** against a permutation p95 of **0.0007** | **NEGATIVE** — pre-registered claim (c) fired at a 0.20 floor; a floor cannot be guessed from design and has to be computed per screen |
| 14 | Does the verdict depend on who called the hits? | Same screen, same **49** programs, same size column — only the rule turning scores into hits changed. All four **threshold** rules return **MORE SIZE-CARRIED THAN ITS OWN NULL** (R² **0.4530–0.5631**); all three **quantile / top-N** rules return **UNDETERMINED**. The tool goes from naming set construction the ranking's dominant feature to refusing to answer, and said nothing about the convention that decided it | **NEGATIVE** — pre-registered claim (b) fired ([`docs/HIT_RULE_PREREG.md`](docs/HIT_RULE_PREREG.md), sealed before any value). A scope limit on the instrument, and it surfaced a live defect in the shipped package |

**Evaluation 8 leaves our data and the finding survives.** The confound this project found in gene sets is not about gene sets. In a CRISPR off-target list the analogue of set size is **search yield** — how many candidate sites the mismatch budget nominated — and it carries roughly the same share of apparent cross-assay agreement as set size carries of our cross-screen agreement: **31.2% median against our 26%.** Same direction, modestly stronger, and we do not say dramatically. Two things are disclosed rather than buried. First, the *other* regression — search yield against the **biochemical** hit count — returns R² **0.83–1.00** and exactly **1.0000** at the two lowest thresholds, because a nominated site with ≥1 read is a hit by construction; that number is an identity, not a finding, and it is the one this arm would have overstated itself with. Second, on CRISPRme: that variants create off-target sites is **the CRISPRme paper's own finding**, not ours, and the 44.1% figure means a variant makes the site a *better* match — the stricter reading, sites absent from the reference entirely, is **12.4%**. We conflated those two while building this arm; quoting the first while describing the second overstates the effect roughly threefold. The denominator is the top 1,000 by CFD per guide, a ranked shortlist, not the genome. **No guide is named safe or unsafe** — the gene-level refusal, applied where the ranking has a patient at the end of it. → [`docs/OFFTARGET.md`](docs/OFFTARGET.md), `src/offtarget_audit.py`

**Evaluation 10 ran our audit on the field itself, and our own headline came back atypical.** BioGRID ORCS 2.0.18 ships 1,952 curated human CRISPR screens from 418 publications with an explicit HIT column; 1,272 meet the inclusion rule. The median published screen shows size-alone R² **0.224** — our 0.465 sits above the field's 90th percentile, so quoting it as if it described screens generally would overstate the field by roughly 2×. The two numbers are **not the same estimand** (different unit, outcome and predictor — the comparison table is in `docs/CORPUS.md`), a smaller field median does not falsify ours, and an independent execution of the same idea landed near 0.10 and could not be reconciled, so neither number is "the field's value." Post-hoc, not pre-registered, names no screen and no publication. See `docs/CORPUS.md` and `results/corpus/`.

**Evaluation 7 failed twice and we are reporting both.** We predicted the size confound would get *worse* in looser collections. It did not: GO-BP 0.2905 and Reactome 0.1846, both **below** Hallmark's 0.4649 — the opposite direction. And separately, the pre-registered rule (150 of 250 sets must be scoreable) fired on three of four collections, so strictly no verdict is issued at all and the R² values above carry none. What survives is descriptive and was not the question we asked: **more than half of GO Biological Process — the most-used gene-set collection in biology — cannot be evaluated against this screen, because the median GO-BP set declares 20 genes and has 8 measured in this screen.** 793 sets across four collections, scored on Modal in 522 s. **The comparator is Hallmark's size-alone R², 0.4649**, computed over all 50 frozen programs; the arm's own Hallmark row reads 0.4464 because one set (`HALLMARK_PANCREAS_BETA_CELLS`, 9 members) fails a stricter scoreability gate here than in the original sweep — a sample-size difference of 0.0186, not drift, reconciled in the artifact. GO-BP and Reactome sit below Hallmark under **both** figures, so the direction claim is unaffected either way. The 0.4649 bar itself comes from `results/sensitivity/stripped_model.json`, which is **post-freeze and not pre-registered** — disclosed rather than dressed up, and it reproduces from the frozen matrix in one line.

**Evaluation 6 is the one to remember.** "It replicated in a second cell line" is the strongest evidence most hit lists ever get. We measured what that evidence is worth: **you can predict 6 of the top 10 programs in an independent screen using nothing but how many genes are in each set.** Both screens are confounded the same way, so agreeing for the same wrong reason looks exactly like agreeing for the right one. Post-freeze and not pre-registered, and labelled so — prompted by our own landscape review noticing we had no right to claim a number here. `src/audit_screen.py --hits-b` runs this on anyone's paired screens.

**On evaluation 5, the margin is thin and we are not going to pretend otherwise.** The pre-registered bar was R² ≥ 0.25 and the result is 0.2758 — it clears by 0.026. It is a genuine pre-registered positive, the threshold was fixed and hashed before the sweep ran ([`docs/RPE1_PREREG.md`](docs/RPE1_PREREG.md), sha256 `ae62feda…`, committed at `f509baa`), and the same byte-frozen scorer was used unmodified. But a bar cleared by that little would have been missed by a slightly noisier screen, and **this is a generalisation test, not a replication**: RPE1 covers 24.3% of K562's targets and that quarter is disproportionately essential genes — our own `rpe1_coverage_collision` control, which **FAILS** at 94.1% vs 11.3%. What it supports is that the size effect is a property of set-level statistics rather than of K562 alone. It does not make the K562 number more precise, and it does not revise the frozen primary.

Also measured: essentiality density is flat at program level, coefficient **−0.021**, p = 0.90. It dominates individual hit lists and predicts nothing about whether a program is reversible.

## Features

- **An agent that chooses its own next step and halts on its own** — it picks which program to read by a stated policy, updates a running estimate, emits a next experiment, and stops when the estimate stops moving. Change the policy or the halt rule and it visits different programs and stops elsewhere. On halting it reports that stopping early **overstated its own answer by 0.081**, and names the gap
- **A next experiment that changes when the results change** — zero hits proposes raising statistical power and re-running; a strong result proposes pathway-level validation in a second cell type. No branch tests a program name
- **A packaged CLI anyone can install** — `pip install -e packages/denali-audit` puts `denali` on PATH with six subcommands: `audit` (verdict + corpus percentile), `rerank` (apply the correction, see what leaves your top N), `baseline` (what does a size-only predictor score on your evaluation?), `floor` (the published no-biology floor for any screen in the atlas), `replication` (two screens agreed — how much of that is set size?) and `formats` (the ten tool outputs read without renaming a column, four of them flagged approximate on the verdict itself). `core.py` is this repository's own maths vendored verbatim, and a test requires it to return exactly **0.4649** on the frozen research data, so the tool and the paper cannot drift apart
- **The check runs on other people's screens, and here it is doing so** — `src/audit_screen.py` takes any gene-set results table and reports the same estimate; validated against synthetic screens with known answers, and it reproduces our own figure exactly. [`audits/external/`](audits/external/README.md) is the same command run unchanged on the published supplementary tables of **seven studies we did not run and did not choose** — CRISPR-KO, CRISPRi/a, single-cell CRISPRa, organoid, primary T cell and bulk RNA-seq — where **36–88%** of each ranking is explained by set construction alone. One comes back only partially confounded and one candidate table was refused for having no true hit count, so the auditor discriminates rather than flagging everything
- **Genome-scale sweep** — every one of 9,837 knockdown targets scored against all 50 Hallmark programs, 491,850 cells; the full matrix ships in the repo rather than a filtered top-N
- **Rank-based reversal statistic** — Mann–Whitney of program-member effects against the rest of the transcriptome, per perturbation, with cosine similarity and mean effect size reported alongside so no single number carries the claim
- **Pre-registered thresholds, hashed before any value was computed** — the primary claim, the alternative claim, the statistic deciding between them, and the conditions for reporting neither, all fixed in advance
- **Held-out evaluation scored only after the predictor was frozen** — the model is serialised and hashed (`610f2a75…`), the hash verified at load time, and the ten programs opened only afterwards; a mismatch aborts
- **DepMap essentiality filter** — every row joined to Chronos gene effect across 1,178 lines and tiered by it, separating "this knockout moves the program" from "this knockout kills the cell"
- **Seven controls with published outcomes, four of them failing** — a pre-committed nonsense program returns zero hits against 517 and 773; guide-pair concordance is −0.019; top-50 essentiality enrichment is 4.09×. The failures are kept, not dropped
- **Literature layer with per-gene provenance and a measured retrieval audit** — 113 genes, one citation each via Paperclip, then a blind 20-gene probe that found **19 of 20 returning the same unrelated paper**; we report the audit, not the layer
- **Scope guard that fails the build** — the test suite scans the rendered page and the captions for any gene symbol within 260 characters of verdict language, so "no novel gene is named" is enforced by code rather than by memory
- **Static page with every number injected from frozen files** — 49 values pass through a `V()` helper that records each source; a number that cannot be traced does not render
- **Client-side program explorer** — all 50 programs sortable and filterable, one toggle isolating the 20 that fail the gate and produce hits anyway, held-out programs tagged, and a generated next-experiment proposal per program; embedded as JSON, zero network calls
- **MCP server** exposing the matrix to agents, whose unscored branch reports the predictor's own failure verbatim
- **The loop is drawn and falsifiable** — [`docs/LOOP.md`](docs/LOOP.md) shows the measure → model → gate → propose → audit cycle, names the file behind each stage, and publishes the one-line grep that would prove the claim false
- **Deterministic reproduction in ten steps** — `make all` from a clean clone reproduces every file in `results/` byte-identical, figures included, in 12 m 05 s; re-verified after the night's merges with an empty diff

## MCP server — denali as a tool for AI agents

```bash
.venv/bin/python -m src.mcp_server
```

Six tools in two halves. `reversibility` and `provenance` are lookups into our
frozen result — they read `results/frozen/` only, never recompute, never score.
`audit` and `rerank` are the packaged tool itself, imported from
`packages/denali-audit` and run on **the caller's own data**: an agent passes its
own set sizes and hit counts, or just a path to whatever its enrichment tool
already wrote, and gets back the same check we ran on ourselves. Nothing about
denali's screen enters those two answers. Until they existed this server was a
database of our findings; an agent could ask what we found and could not run the
check on anything of its own.

**The two halves are deliberately asymmetric, and that is the design.** This
server will apply a correction to your ranking and it will not nominate anything
from ours. Ask it which program to chase and it refuses — citing the 0.4375
balanced accuracy its own predictor scored on held-out data. Applying a
correction is a statement about a ranking that already exists; nominating is a
claim about what is true, and the predictor that would have to back that claim
failed its own evaluation. A tool that handed you a candidate list on that
evidence would be committing the error this project exists to measure.

Wiring this into a client's config, and the full six-tool reference table, is in [`docs/MCP_SERVER.md`](docs/MCP_SERVER.md).

## Reproduce it

Python 3.12.0. Every number in `results/frozen/` and every figure is reproducible — seeds are fixed and inputs are checksummed.

```bash
make setup     # venv + pinned dependencies (needs `uv`: https://docs.astral.sh/uv/)
make data      # prints the one manual step, below
make all       # ten steps, ~13 min, ends by running the invariants
make page      # rebuild index.html from the frozen numbers
```

### The one manual step — 470 MB substrate

Not in git. ⚠ **figshare returns 403 on HEAD but 206 on ranged GET** — use GET.

```bash
mkdir -p data/raw
curl -sL -o data/raw/K562_gwps_normalized_bulk_01.h5ad https://ndownloader.figshare.com/files/35773217
curl -sL -o data/raw/rpe1_normalized_bulk_01.h5ad       https://ndownloader.figshare.com/files/35775512
curl -sL -o data/raw/CRISPRGeneEffect.csv               https://ndownloader.figshare.com/files/51064667
curl -sL -o data/raw/Model.csv                          https://ndownloader.figshare.com/files/51065297
```

| File | md5 |
|---|---|
| `K562_gwps_normalized_bulk_01.h5ad` | `a3dfaa94ea8724217f5ecb1e14a5f0c8` |
| `rpe1_normalized_bulk_01.h5ad` | `6f1e7d6a09e2f869759e3c4526b7f171` |
| `CRISPRGeneEffect.csv` | `6edf7ade09b9b34199210b559d4745d3` |
| `Model.csv` | `675210d17675f3517b0ce39a3c274f16` |

**A fresh clone reproduces every file in `results/` byte-identical.** Clone at any commit, run `make all`, and all four of these are empty:

```bash
git status --short          # nothing untracked or modified
git diff --stat             # nothing changed
git status --short results/ # in particular, no result moved
git diff --stat results/frozen/
```

Last measured at **`f1ecd25`**: `make all` exited 0, all four surfaces empty, **64** files under `results/` actually rewritten by the run rather than left untouched, and the clone's own suite green at **384/384** plus **10/10** cross-surface. The four figures are included — they are regenerated, not skipped.

**This claim is dated on purpose.** Earlier versions of this paragraph tried to carry a measurement forward by arguing that no code had changed since, in sentences like *"the three commits after it match nothing under `src/`"*. Those sentences went stale within hours and shipped a checkable command that returned the opposite of the claim beside it — 27 commits and six `src/` files by the time anyone looked. A reproducibility section that hands a skeptic a self-refuting command is worse than one that says nothing. So: the commit is named, the reader re-runs it if they care whether it still holds, and no argument is made about commits that had not been written when this was measured.

**Three earlier runs found real defects, and none of them was in a reported number.**

1. A `wall_clock_min` field was being written into a frozen artifact, which makes byte-comparison across machines impossible by construction. Runtime is now printed and never stored.
2. FIG 4 drew its lines in set-iteration order, and because Python salts string hashing per process the same picture serialised to different bytes each run — three `PYTHONHASHSEED` values gave three MD5s before the fix and one after.
3. A run failed at the final invariant step and the failure was real: a fresh clone counted 350 assertions against a badge claiming 351, because the Adamson provenance guard shelled out to `git show` on a commit a rebase had erased, so it **silently skipped** wherever that object was missing — including CI, whose shallow checkout meant the guard had never once run there. It is now content-addressed against the sha256 the amendment itself cites and needs no history.

**And twice a reproduction *looked* verified and was not**, which is worth more than the passes. Once the substrate had been moved off the machine, so `make check` failed with `MISSING substrate` and the run printed an empty diff having executed nothing — an empty diff from a run that never happened is indistinguishable from a pass. Once the result was measured at a commit and then quietly assumed to hold at `HEAD`, after `src/build_page.py` — which `make all` invokes — had changed underneath it. Both were caught by asking *what did this actually execute*, which is the same question the skipped-guard failures answer.

An earlier run of this check had two diffs, and both were defects rather than noise. A `wall_clock_min` field was being written into a frozen artifact, which makes byte-comparison across machines impossible by construction; runtime is now printed and never stored. FIG 4 drew its lines in set-iteration order, and because Python salts string hashing per process the same picture serialised to different bytes each run — three `PYTHONHASHSEED` values gave three MD5s before the fix and one after. Neither was a scientific value, and neither should have been in a file we ask people to diff.

`make all` deliberately does **not** re-run the two live-API steps (`make retrieval`). Those indexes change, so their outputs are committed as dated observations from 2026-08-15. The instability of retrieval is the finding, not a defect.

The headline was also rebuilt from scratch by a second implementation that never read the first — see [`docs/INDEPENDENT_RECOMPUTE.md`](docs/INDEPENDENT_RECOMPUTE.md). Three further defects a reproduction check found along the way, none of them touching a reported number, are in [`docs/REPRODUCE_HISTORY.md`](docs/REPRODUCE_HISTORY.md).

## Tests

`tests/test_frozen_invariants.py` — **556 assertions**, run by `make test` and at the end of `make all`, so a mismatch fails the reproduction loudly rather than producing a confidently wrong page. It covers the matrix shape, both ends of the adj R² range, the post-freeze split, all four gate counts, the held-out balanced accuracy and zero true positives, the underpowered flag, the refit flag, both essentiality coefficients, guide-pair concordance, the control verdict counts, and the predictor hash. Every headline number in `REPORT.md`, `index.html` and `CAPTIONS.md` is traced back to a frozen file with a matching value, not to prose.

Two guards exist because each caught a real defect. The **compile guard** parses every file under `src/` and `tests/` before anything else — added after a shipped module was found not to compile. The **scope guard** builds a gene-symbol universe from the Hallmark GMT and fails the build if any symbol appears within 260 characters of verdict language in the rendered page or the captions, with an allowance for "recovered known answer" and "positive control"; it enforces the −0.019 scope limit mechanically. A third set of checks asserts the page makes **no network calls** — no `fetch`, no `XMLHttpRequest`, no external script or stylesheet — so the interactive explorer cannot break unattended.

The suite has caught, in order: a stat bug reporting 5 evidence sources instead of 34, an essentiality coefficient published with the wrong sign, a miscount of failing controls, a stale caption, and a module that did not parse.

## The baseline, as a contest

Arc Institute's Virtual Cell Challenge 2025 — 5,000+ registrants, 1,200+ teams —
[reported](https://arcinstitute.org/news/virtual-cell-challenge-2025-wrap-up) that
perturbation models are "not yet consistently outperforming naive baselines across
all metrics." This repository measures one such naive baseline and shipped it only
as a diagnosis. [`benchmarks/challenge/`](benchmarks/challenge/) makes it something
a stranger can run their own method against: clone, one command, a score, no
account and no download. A pull request is the submission mechanism.

**Our own method loses on it.** `denali rerank`'s size-aware residual beats the
size-only baseline by a Spearman delta of +0.0113 — indistinguishable from ranking
by size — and scores 0.40 on top-10 overlap against the baseline's 0.60, which is a
loss. The naive "reuse the hit count you already have" entry scores 0.6633 and 0.80.
A half-strength correction scores 0.6466 and 0.80, so the cost is not in correcting
but in correcting all the way.

**Then the ordering inverts.** That board scores against RPE1's *raw* hit ranking,
which is itself size-confounded: over these 50 programs, RPE1's own set sizes
explain **R² 0.3090** of it. So a size-corrected predictor is being scored against
a size-contaminated target. Removing size from both sides reverses the result: the
naive hit count falls to +0.2193 and is no longer distinguishable from chance
(permutation p = 0.1214), the size-only baseline goes negative at −0.1755, and the
correction is the only entrant clearing its permutation null at **+0.4972**,
p = 0.0003.

*Three different R² values for "size in RPE1" are correct in this repository and
they answer different questions, which is worth stating because two sessions
confused them.* **0.3090** is RPE1's hits on RPE1's own sizes over the paired 50
— the target confound above, and the only one relevant to the board.
**0.2758** is [evaluation 5](docs/RPE1_PREREG.md), the full RPE1 arm over its 49
scoreable programs. **0.214** is
[`results/concordance/cross_screen.json`](results/concordance/cross_screen.json),
which regresses RPE1 on **K562's** sizes — a cross-screen quantity, not a
property of RPE1 at all.

That inversion was computed twice, by two sessions, from two independent
implementations reading the same frozen `paired_programs.csv`. All four rank
correlations agree to four decimals and the permutation p-values differ in the
third, which is what independent draws look like rather than a copied seed. It
establishes that the arithmetic is right; both runs read the same data, so it does
not independently establish the data.

Which method wins is decided by whether the target is size-corrected. That is this
project's thesis occurring inside this project's own challenge. It rules out the
correction destroying all signal; it does **not** establish that the residual is
biology, since both sides are corrected the same way and can agree for the same
wrong reason — [evaluation 6](results/concordance/) pointed back at us.

## Scope limits

1. **No gene-level result is claimed.** Guide-pair concordance is −0.019; no novel gene is named anywhere, and the build fails if one appears near verdict language.
2. **Not generalisable on our own evidence.** The held-out evaluation was underpowered and inconclusive, and its binary axis failed outright at 0.4375.
3. **One cell line, unstressed.** Everything is K562. Measurable is not the same as engaged, and our gate tested the wrong one.
4. **The attribution is to gene-set construction, not measurement.** A post-freeze check gives 0.152 for measurement-only against 0.697 for construction-only. Better instrumentation would not move the number.
5. **Transcriptional movement is not phenotypic reversal.** Computational only — no wet-lab protocols, no dosing, no clinical or therapeutic recommendation.
6. **A large R² is a confound only where `hits` are not counted over the set's own members.** [`results/breadth/`](results/breadth/README.md) ran the unmodified `audit()` across three domains that are not gene sets and found the boundary. Where `hits ≤ size` because both are counted over the same members — which is what classical overlap enrichment does — regressing a count on the number of trials that produced it recovers the trial count, and a large R² there is **arithmetic rather than a confound**. The no-biology value is not zero and depends entirely on the mapping, so the number is interpretable only against the right null. All three domains returned large R² values and **none survived its own null**; our primary screen is the one that does — 0.4649 against a permutation null of 0.0182. [`results/breadth/null_baselines.py`](results/breadth/null_baselines.py) computes the correct null per mapping. This applies to anyone running this check, including us.

7. **The audit does not apply to a top-N or top-percentile hit list.** Evaluation 14 changed nothing but the rule turning scores into hits, on the same screen and the same 49 programs. All four **threshold** rules (BH q, raw p, effect size) returned a verdict above their own null, R² **0.4530–0.5631**. All three **quantile / top-N** rules returned **UNDETERMINED** — because a rule that fixes how many hits each program gets leaves set size nothing to predict. "Our top 200 hits" is an ordinary way to publish a screen, so this reaches real users, and a clean-looking verdict on such a list is a false reassurance rather than a finding. The power asymmetry has not gone away; it has moved out of the hit count and into the within-program ordering, which `audit()` never reads. [`docs/HIT_RULE.md`](docs/HIT_RULE.md).

How to cite a floor, a percentile, or a size-corrected re-ranking from this tool is in [`docs/CITE_A_FLOOR.md`](docs/CITE_A_FLOOR.md).

## Deeper docs

Everything below was cut from this README to keep it readable, not to bury it. Each file keeps the words it had here.

| | |
|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | The full pipeline diagram, and why the freeze boundary is the load-bearing part |
| [`docs/METHOD.md`](docs/METHOD.md) | The statistic, the regression, the measurability gate, and the rule that fired before any number was seen |
| [`docs/RESEARCH_CHALLENGES.md`](docs/RESEARCH_CHALLENGES.md) | What nearly went wrong: the circular feature, engagement vs. reversibility, the filter that fails 20 of 50, retrieval concentration |
| [`docs/MCP_SERVER.md`](docs/MCP_SERVER.md) | Wiring denali into an agent's client config, and the six-tool reference table |
| [`docs/TOOL_CHAIN.md`](docs/TOOL_CHAIN.md) | Every sponsor tool at the enrichment step, what touched a number and what didn't |
| [`docs/RUNNING_SRC.md`](docs/RUNNING_SRC.md) | The pipeline scripts in `src/`, one at a time, and why they take no flags |
| [`docs/REPRODUCE_HISTORY.md`](docs/REPRODUCE_HISTORY.md) | Three defects a reproduction check found, all in the wiring and none in a reported number |
| [`docs/INDEPENDENT_RECOMPUTE.md`](docs/INDEPENDENT_RECOMPUTE.md) | The headline rebuilt from the method section by code that never read the original |
| [`docs/REPO_MAP.md`](docs/REPO_MAP.md) | What's in every top-level directory |
| [`docs/BASELINE_CLI.md`](docs/BASELINE_CLI.md) | `denali baseline` — the naive baseline as something you can call on your own evaluation |
| [`docs/R_INTEGRATION.md`](docs/R_INTEGRATION.md) | Running the audit from R, directly on a `clusterProfiler` `enrichResult` |
| [`docs/LITERATURE_INFER_RESULTS.md`](docs/LITERATURE_INFER_RESULTS.md) | Two models reading all 111 papers instead of grepping them, and what that changed |
| [`docs/CITE_A_FLOOR.md`](docs/CITE_A_FLOOR.md) | How to cite a floor, a percentile, or a re-ranking from this tool |
| [`docs/CITATIONS.md`](docs/CITATIONS.md) | Every dataset and paper this project rests on, and what it was used for |
| [`docs/RESULTS_PAGE.md`](docs/RESULTS_PAGE.md) | Two more screenshots of the static page and its per-program detail panel |
| [`docs/README.md`](docs/README.md) | The full documentation index — pre-registrations, limitations, everything else |

---

Code MIT ([LICENSE](LICENSE)). Data: Replogle et al. 2022 Perturb-seq and DepMap 24Q4, both CC BY 4.0; MSigDB v2026.1.Hs under its own terms.

# In plain language

*This section assumes no background. Everything above it assumes some.*

## What problem is this?

A CRISPR screen switches off ten thousand genes, one at a time, and measures what happens to the cell after each one. It hands a biologist a ranked list of thousands of "hits." Labs then spend months, and often six figures, chasing the top of that list.

The list is less trustworthy than it looks, for three reasons a newcomer would not guess:

- **Some genes are just load-bearing.** Switch off a gene the cell needs to survive and *everything* changes. Those genes flood the top of any ranking without telling you anything specific.
- **Bigger pathways win automatically.** A pathway with 200 genes returns more hits than one with 30, regardless of what either does — the same way a raw crime count always ranks big cities as the most dangerous.
- **The measurement disagrees with itself.** Two reagents aimed at the *same* gene should give the same answer. In this dataset their agreement is **−0.019** — statistically indistinguishable from noise.

## What did we build?

denali reads a finished screen back and estimates **how much of the apparent signal is explained by how the programs were defined — chiefly their size — rather than biology**, before anyone commits to a candidate.

The answer, on a published genome-scale screen: **between 56% and 75%**. A model that never looks at what a single gene *does* — only at how each pathway was defined, chiefly its size — predicts most of what looks like discovery. Pathway size alone explains **46.5%**.

We also checked the obvious fix. If you filter out poorly-measured pathways, you throw away **20 of 50** pathways that produce real results anyway. The quality filter a careful person would build is wrong 40% of the time.

## Why should anyone care?

Because the expensive mistake in this field is not missing a hit. It is **chasing one that was never there.** A false lead costs a year of a graduate student's life and a grant cycle.

That has a published price. Freedman, Cockburn & Simcoe put the cumulative prevalence of irreproducible preclinical research **above 50%**, costing roughly **US$28 billion a year in the United States alone** ([PLOS Biology 2015](https://doi.org/10.1371/journal.pbio.1002165)). We quote it the way it should be quoted: it aggregates several categories of irreproducibility, not only false leads from screens, and it is contested at the margins — but it is the standard citation and the right order of magnitude. denali does not address all of that. It addresses one mechanism inside it, and it measures how much that mechanism costs on a real screen instead of asserting that it matters.

denali is a cheap check that runs before that decision. It does not find new drug targets and does not claim to. It tells you which parts of your ranking are measurement artifacts, and it proposes a next experiment that **changes when your results change** — if a pathway comes back empty it tells you to raise statistical power and re-run; if it comes back strong it tells you to validate in a second, independently screened cell type.

It is a tool for deciding what *not* to chase. That is unglamorous, and it is where the money goes.

## How do you know we're not fooling ourselves?

This is the part we care most about, so it is built into the code rather than promised in prose.

- **We wrote down what would prove us wrong, hashed it, and committed it before running anything.** The pre-registration is recoverable at a named commit.
- **We held ten pathways back** and only opened them after the model was frozen and hashed. The model **failed** on them — worse than a coin flip, zero true positives. We published that instead of quietly refitting.
- **Ten of our fourteen evaluations came back negative.** All fourteen are reported, including the one that clears its bar by only 0.026.
- **The one positive is a control, not a discovery.** Run unchanged on a pathway it was never tuned for, the ranking puts that pathway's known master switch at **rank 2 of 11,258**. So the machinery works — it just is not finding what people assume it is finding.
- **556 automated checks** fail the build if the words and the data stop agreeing. They have caught us five times, including once when we published a number with the wrong sign.

# How to check this project

Four questions worth asking of any computational result, each answered with the
file that settles it. They began as a hackathon's judging criteria; the event
was not entered, and they turned out to be the right structure for the writeup
anyway, so they stayed.

**1 · Closing the loop.** Ten pathways were named and committed as a held-out set before the code that scores them existed. The predictor was frozen and hashed first; the scorer verifies that hash on load and aborts if it changed. It failed on the held-out set — balanced accuracy **0.4375**, zero true positives — and we reported it. For the second half, hold a pathway fixed and change only its result: the proposed experiment flips from *"validate in a second cell type"* to *"raise power and re-run."* No branch in that code tests a pathway's name.

The loop then ran **eight laps**, each re-entering at MEASURE with a different substrate and the same byte-frozen scorer, and **three of them stopped on a rule fixed before the run rather than a judgement made after it** — two halting outright, one putting an engagement gate in front of its own question so that a null would have had no result to report. **The halts are the evidence.** A loop that only ever continues is not being governed by anything. The last lap turned the audit on its own corpus and found the corpus confounded the same way the field is, which moved our headline from roughly the 90th percentile to the 73rd — the correction leads that writeup because it costs us the number. → `docs/LOOP.md`, `src/next_experiment.py`, `src/score_heldout.py`, `results/frozen/heldout_evaluation.json`

**2 · Inspectability.** Every number on the results page passes through a helper that records the frozen file it came from; **49** values are traced and an untraceable number does not render. The pre-registration is hashed and diffable against what we reported. Four self-found errors are written into the limitations, including one where we blamed a sponsor tool that in fact works.

Prose is held to the data the same way the page is. The findings table in this README is the single source of truth: the suite parses it, and **15 restatements of the count across 7 files** fail the build if any one of them drifts — including the three places this README states its own test count. The failure mode we care about is subtler than a wrong assertion, and we hit it three times: a check that **silently stops running** — gated on data a clean clone does not have, keyed to a commit a rebase erased, matched against markup that had been rewritten. All three passed while testing nothing. They are now content-addressed rather than reference-addressed, and the self-counting badge is what caught them, because a skipped check and a passing check look identical in the output but change the count. → `src/build_page.py`, `tests/test_frozen_invariants.py`, `docs/MATRIX_PREREG.md`, `docs/LIMITATIONS.md` §7

**3 · Validation.** Judged against standards outside our own reasoning: a published Perturb-seq screen, MSigDB pathway definitions, and DepMap gene-fitness data across 1,178 cell lines. The positive control recovers a known master regulator at rank 2 of 11,258, with 11 of 17 canonical members in the extreme 10% (p = 7.0×10⁻⁸) and the correct sign at both tails. Four of seven controls fail and are kept.

The strongest external check is that **the finding is not about us.** The identical command runs on seven other groups' published supplementary tables — CRISPR knockout, CRISPRi/a, single-cell CRISPRa, organoid, primary-T-cell and bulk RNA-seq — and **36–88%** of each ranking is explained by set construction alone; one comes back only partially confounded and one candidate table was refused outright for having no true hit count, so the auditor discriminates rather than flagging everything. Widened to **1,272 published screens**, the field's median size-confound is **0.224** against our **0.465** — which says our headline is atypical in magnitude, and we published that rather than bury it. Three arms take the same confound off our data entirely: a methods audit of published clinical off-target nominations, a screen where the program is actively engaged rather than dormant, and — pre-registered before it ran — an audit of whether the **187 publications behind those screens mention set size at all.** Only **4 of the 111** that are open access do, which is **3.6%**. That arm ships with a positive control that must fire on three enrichment-methods papers, because a 3.6% rate and a dead search are indistinguishable without one, and it is labelled as measuring **mention, not understanding**. → `results/frozen/controls.csv`, `audits/external/`, `docs/CORPUS.md`, `REPORT.md`

**4 · Sponsor tools.** The distinctive use is that we treated one as the **object of measurement** rather than a dependency: Paperclip retrieved literature for 113 genes, we blind-probed 20 of them, and **19 of 20 came back with the same unrelated paper**. That audit is a published figure, and nothing it returned feeds any result. Modal runs the real sweep across containers and reproduces the frozen numbers exactly, so reproduction no longer needs a 470 MB download — the same scorer run elsewhere, which establishes portability and not independent confirmation of the maths. The project also ships *as* a tool: an MCP server whose reply for an unscored pathway volunteers the predictor's own failure, unasked. Every tool's status is tested rather than recalled, and an automated check fails the build if an "unused" claim stops being true. The same tool is also used properly, and both facts are reported: Paperclip runs evaluation 11's audit over 187 publications, so it appears here as an instrument *and* as an object of measurement. BenchFlow carries **three tasks — two on the findings, one on the product** — `denali-gate-trap`, where the naive quality filter scores 0.6981 and the reference solution 0.7413; `denali-confound-estimate`, where an agent must estimate the size confound on seven real published screens whose true values span 0.36–0.88; and `denali-size-carried`, which hands an agent a ranked hit list and scores whether it can identify which of the top ten are carried by set size, graded against the size-aware residual the packaged tool computes. **47 of its 70 entries are size-carried**, so the obvious shortcut is to say so about all of them — and the metric is built so that both constants score exactly 0.5 balanced accuracy and earn exactly zero. That last task is the stronger form of the move: a finding graded is a fact somebody must reproduce, a tool graded is a capability somebody must have. All three were rebuilt and run oracle-to-verifier in their containers, all three grade deterministically in code with no model judging, all three grade other people's agents and no denali result depends on any of them. Revalidating them found that the first task had silently stopped parsing when BenchFlow renamed a config key, which is recorded rather than quietly fixed. → `docs/TOOLS.md`, `docs/LITERATURE.md`, `benchmarks/README.md`, `src/modal_sweep.py`, `src/mcp_server.py`
