# denali — most of what looks like biology in a genome-scale perturbation screen is not biology

**re:AGENT 2026 · Track A · `github.com/alejandro-publius/denali`**

---

## Finding

> ### Between **56% and 75%** of the variance in which biological programs *appear* reversible in a genome-scale CRISPRi screen is explained by how the programs were defined — chiefly their size — not by their biology.
>
> The range is not hedging. It is the honest interval: **0.561** using only
> features independent of the outcome matrix, **0.751** including
> member co-expression coherence, which is derived from the same matrix as the
> outcome and is therefore partly circular. Both are reported; the
> pre-registered decision used the six-feature model, as written before the sweep.

**Mechanism, one line: bigger programs with more co-moving members return more
hits regardless of what they do — program size alone explains 46.5%.**

We swept **all 50 programs** in MSigDB Hallmark against **9,837 CRISPRi
knockdowns** in K562 (9.2 min). We pre-registered, before running anything, that
if a measurability model explained ≥60% of the variance we would report
*"K562 reversibility is mostly measurability"* as the finding rather than as a
failure. Adjusted R² came back at **0.751**. The pre-registered branch fired.

### Second finding — the obvious filter is wrong 20 of 50 times

We built the measurability gate anyone would build: enough members present,
expressed above background, variable above background. Across 50 programs:

| | |
|---|---:|
| Programs failing the gate that **still produce hits** | **20 / 50** |
| Programs passing the gate that produce **zero** hits | **1 / 50** |
| **Held-out** program failing the gate yet ranking **11/50** with 773 hits | **1** |

The held-out program (`HALLMARK_CHOLESTEROL_HOMEOSTASIS`, `expr_ratio` 0.92)
fails the gate and still ranks 11th of 50. **Our own filter would have discarded
our best result** — which we only found by scoring every program rather than the
ones the filter approved.

### Third finding — a clean negative: essentiality is not the driver

At program level, `essentiality_density` is **flat: standardised coefficient
−0.021, p = 0.90.** Essentiality dominates individual top-hit lists — the top 50
knockdowns for any program are ~4× enriched for essential genes — but it does
**not** predict whether a program looks reversible at all. Those are different
questions and the field routinely conflates them.

---

## Method

```
program (a named gene list)
  → score all 9,837 knockdowns for opposition to it   (rank-based, Mann-Whitney)
  → R_p = log10(1 + hits at q<0.05, BH within program)
  → regress R_p on six measurability features across all 50 programs
```

Primary statistic is nonparametric; cosine similarity and mean effect size are
reported alongside, and the composite is an average of three ranks. No single
number is optimised — the Arc Virtual Cell Challenge winner was ranked on average
rank across seven metrics, and pseudobulk plus classical features beat pure
neural approaches there.

Thresholds and the held-out program list were committed before the corresponding
results existed; see `docs/PRIOR_WORK.md`. That is a methods note, not the
argument. What validates this work is below.

---

## How we know the output is right, by standards outside our own reasoning

**1. We ran a held-out evaluation and it failed, and we report it.** Ten programs
from a different collection, never scored until the model was finished:
underpowered and inconclusive by a rule set in advance, balanced accuracy 0.4375,
worse than chance, zero true positives. **A system that only reports its
successes has no external standard by definition.** We did not refit.

**2. Seven controls, all reported, four of them failing.** A pre-committed
nonsense program of 41 random genes returns zero hits against 517 and 773 for the
real programs. Canonical regulators are recovered on one program and not on the
other — that second one is our null. Guide-pair concordance is −0.019. Top-50
essentiality enrichment is 4.09×.

**3. DepMap is an independent screen we did not run.** Every row is joined to it
and tiered by it, separating "this knockout moves the program" from "this
knockout kills the cell." It is a different assay, different labs, different
readout.

**4. Pre-registered thresholds fired against us.** The rule declaring the
held-out inconclusive — fewer than 8 of 10 programs passing the measurability
gate — was written before any held-out number was visible. It fired.

**5. We audited our own documents adversarially and published what we found.**
Four numeric inconsistencies and one scope violation, all fixed, all recorded in
`LIMITATIONS.md` §7 along with two mid-run crashes and a statistics bug in our
own code.

---

## Controls

| Control | Result |
|---|---|
| **Nonsense program** — 41 random genes, seed pre-committed | **0 hits** vs 517 and 773 for real programs. ✅ The method does not manufacture signal. |
| **Known-regulator recovery** (held-out program) | SREBF2 rank 2 of 11,258 scored perturbations (perturbation frame, larger than the 9,837 unique genes because some are targeted twice); 11 of 17 canonical members in the extreme 10%, binomial **p = 7.0×10⁻⁸**; **79% sign-correct** at both tails. ✅ |
| **Known-regulator recovery** (program A) | Not recovered. PERK/IRE1/XBP1 at q≈0.8–1.0. ❌ **This is the null.** |
| **Guide-pair concordance** | **−0.019**, flat at every effect-size cut. ❌ Gene-level calls are not reproducible. |
| **Essentiality-matched null** (program A) | Top-50 4.09× enriched (p<0.001). ❌ for program A. |
| **Essentiality-matched null** (program B) | Top-50 3.32× enriched (p<0.001), but the headline hit is not essential and sits in Tier 1. ⚠️ **CAVEAT**, recorded as such. |
| **RPE1 coverage collision** | 94.1% vs 11.3% coverage, essential vs non-essential. ❌ The replication arm mostly reaches genes the toxicity filter flags. |
| **Held-out ten** | See below. |

### Held-out evaluation — reported as measured, not refit

Ten Reactome programs, selected by public rule (`sha256(name)` rank, no seed, no
hand-picking), not scored until the predictor was finished and frozen.

> **VERDICT: UNDERPOWERED AND INCONCLUSIVE.** Only **1 of 10** held-out programs
> passes the measurability gate. The pre-registration states that below 8 of 10
> this evaluation is inconclusive — that rule fired before we saw the numbers.

Both axes reported anyway, as required:

| Axis | Result | Verdict |
|---|---|---|
| Rank recovery | Spearman ρ = **+0.526**, 95% CI **[−0.101, +0.913]**, p = 0.119 | **PARTIAL** — CI crosses zero |
| Binary recovery | balanced accuracy **0.4375** (tp 0, tn 7, fp 1, fn 2) | **FAILURE** — worse than chance, zero true positives |

### The single clearest illustration of the whole result

`REACTOME_SCAVENGING_OF_HEME_FROM_PLASMA` drew the **highest prediction of all
ten** (R_p 5.26) and returned **0 hits**. It has **one measured member**.

The model predicted strongly *because* the program looked measurable on the
features it could see, and the program returned nothing *because* it was not
measurable at all. **This is the measurability finding reappearing in held-out
data the model had never touched — the failure and the finding are the same
fact.** It is the clearest single example in the project of why we report claim
(b) rather than a reversibility atlas.

**We did not refit.** The pre-registration forbids it and the commit history shows
we didn't.

---

## Figures

All from data measured here. No protein renders, no borrowed model outputs — a
structure on screen would imply a gene-level claim our concordance forbids.
Captions in `results/figures/CAPTIONS.md`, worded identically wherever used.

| | |
|---|---|
| `fig1_matrix.png` | The reversal matrix, 9,837 × 50, held-out program marked |
| `fig2_gate_failure.png` | Gate pass/fail vs hits; the 20-of-50 failure quadrant shaded |
| `fig3_measurability.png` | Program size vs hits, both R² shown as a range |
| `fig4_retrieval.png` | 20 probe genes → sources; 19 converge on one paper |

## Post-freeze sensitivity check, not pre-registered

Run after the hard freeze, prompted by an adversarial self-critique rather than
by the plan. It does not enter `results/frozen/` and does not revise the
pre-registered primary.

**Splitting our six features into measurement vs. gene-set construction:
measurement-only reaches adj R² 0.152; construction-only reaches 0.697.** Set
size alone (0.465) beats all three measurement features combined.

**The pre-registered range 0.561–0.751 stands. The attribution does not.** The
variance is carried by how programs are defined, chiefly their size — not by how
well their genes were measured. Better instrumentation would not change it.

Full record: `results/sensitivity/README.md`.

## A second cell line, and what replication is worth

**RPE1 arm — pre-registered.** Thresholds fixed and hashed (`ae62feda…`,
committed `f509baa`) before the sweep ran. The same byte-frozen scorer, only the
substrate path differs.

| | |
|---|---|
| Size alone, in RPE1 | **R² 0.2758**, slope **+0.0116**, p = 1.1×10⁻⁴ |
| Scoreable | 49 of 50, against a pre-registered floor of 35 |
| Pre-registered bar | ≥ 0.25 → **REPRODUCES**, claim (a) |

It clears by **0.026**. That is thin and we say so: a slightly noisier screen
would have missed it. What it supports is that the size effect is a property of
set-level statistics rather than of K562 alone. It is a **generalisation test,
not a replication** — RPE1 covers 24.3% of K562's targets and that quarter is
disproportionately essential genes, our own `rpe1_coverage_collision` control,
which **FAILS** at 94.1% vs 11.3%.

**Cross-screen concordance — post-freeze, not pre-registered.** Prompted by our
own landscape review noticing we had no right to claim a number here.

| | |
|---|---|
| Raw rank agreement, K562 vs RPE1 | ρ **+0.663**, p = 1.5×10⁻⁷ |
| After removing set size from both | ρ **+0.493**, p = 2.7×10⁻⁴ |
| Share of the agreement that is size | **26%** |
| Top-10 overlap: observed / size alone / chance | **0.8 / 0.6 / 0.2** |

**Six of the top ten programs in an independent cell line are predictable from
set size alone.** "It replicated in a second system" is the strongest evidence
most hit lists ever get; both screens are confounded the same way, so agreeing
for the same wrong reason is indistinguishable from agreeing for the right one
unless someone checks.

Limits: 50 programs, two cell lines, one lab, one assay. A measurement on these
two screens, not a general estimate of cross-screen reproducibility.

## The annotation arm — pre-registered, and it stopped itself

**Evaluation 7. Pre-registered** (`docs/ANNOTATION_PREREG.md`, `ec5edb90…`,
committed `10a82a7` before the run). 793 sets across four collections, same
byte-frozen scorer, seed 20260815.

> **VERDICT: UNDERPOWERED ON 3 OF 4 COLLECTIONS — NO VERDICT ISSUED.** The rule
> — fewer than 150 of 250 sets scoreable — was fixed before the run and fired
> before the deciding statistic could be applied. Claim (a) and claim (b) are
> both unresolved.

| Collection | Scoreable | Size-alone R², **carries no verdict** |
|---|---:|---:|
| Hallmark (the comparator, not a candidate) | 49 / 50 | 0.4464 |
| WikiPathways | 149 / 246 | 0.1017 |
| Reactome | 138 / 248 | 0.1846 |
| GO Biological Process | 115 / 249 | 0.2905 |

**Our predicted direction was wrong, and we state it rather than let an
underpowered result hide it.** We predicted the confound would worsen in looser,
larger collections. Had the arm been powered, the numbers would have supported
the opposite: GO-BP 0.2905 and Reactome 0.1846 both sit **below** Hallmark's
0.4649. Two failures in one arm — the power rule fired *and* the prediction was
backwards — and both are in the result file.

**The Hallmark bar, reconciled.** This arm reports Hallmark at **0.4464** against
a bar of **0.4649**, which reads as our own baseline failing its own bar. It is
not. Same predictor, same statistic, same byte-frozen scorer; the arm applies a
stricter scoreability gate than the original sweep, so one set drops out and 49
are scored instead of 50. Delta **0.0186**, attributable to
`HALLMARK_PANCREAS_BETA_CELLS` (40 declared, 9 present). Both runs agree it
produced nothing — the frozen sweep records it as 0 hits, the arm excludes it as
unscoreable. **Sample size, not drift**, and the direction comparison is
unaffected under either bar. The 0.4649 figure itself is post-freeze and not
pre-registered (`results/sensitivity/stripped_model.json`).

**What survives is descriptive, and it was not the question we asked.**
Scoreability falls monotonically as a collection gets larger and less curated:
**98% of Hallmark sets can be scored against a genome-scale screen; for GO
Biological Process it is 46%.** Across all sampled GO-BP sets the median declares
**20 genes and has 8 measured** in this screen. More than half of the most-used
gene-set collection in biology cannot be evaluated against this screen at all —
a property of the annotation meeting the assay, not of the biology. No threshold
was set for this and none is applied; it carries no verdict either.

Full record: `results/annotation/annotation_evaluation.json`.

## The confound outside our own data — off-target nomination

**Evaluation 8. POST-HOC, NOT PRE-REGISTERED. Thresholds swept, not chosen** —
the same labelling as the cross-screen arm above, for the same reason. Neither
dataset is ours; both are published supplementary tables.

**Arm 1 — CHANGE-seq vs GUIDE-seq.** Lazzarotto et al., *Nat Biotechnol* 2020,
doi:10.1038/s41587-020-0555-7. 202,043 biochemically nominated sites over 110
guides, with a cellular assay on **56 of the same guides**. Two assays, same
guides, different physical principle. The confound is the one this project keeps
finding in different clothes: in our data a set's **size** inflated its hit
count; here a guide's **search yield** does the same job, and it ranges from 20
to 13,499 sites per guide — a **675×** spread. **85.2%** of nominated sites sit
at 5 or 6 mismatches, the permissive tail the mismatch budget creates.

| | |
|---|---|
| Share of biochemical–cellular agreement explained by search yield, 7 read thresholds | **17.6% – 33.9%**, median **31.2%** |
| R² of search yield against **cellular** hit count | 0.36 – 0.55 |
| Our own cross-screen figure, for comparison | **26%** |

Same direction, modestly stronger. **Not dramatically so, and we do not say
dramatically.** The objection to it: 56 paired guides, one lab, two assays, and
the cellular assay detects far fewer sites by construction, so the agreement
estimate is noisy. No threshold is privileged, which is why all seven are
reported rather than the best one.

**A tautology this arm refused to report.** Regressing search yield on the
**biochemical** hit count gives R² **0.83 – 1.00**, and exactly **1.0000** at the
two lowest thresholds. That is an identity, not a finding — every nominated site
has at least one read, so at those rules the hit count *is* the yield. The
reported figure is the cellular direction, the only one that can carry
information. The tautological number is kept in the output because it is the one
this arm would have overstated itself with.

**Arm 2 — CRISPRme.** Cancellieri et al., *Nat Genet* 2022,
doi:10.1038/s41588-022-01257-y. Top 1,000 sites by CFD for each of 14 therapeutic
guides. **Not a discovery** — that variants create off-target sites is the
CRISPRme paper's own finding, and recovering it only confirms the pipeline reads
the data correctly.

| Quantity | n / 14,000 | Share | Per guide |
|---|--:|--:|---|
| Best alignment comes from an **alt allele** | 6,179 | **44.1%** | 40.1% – 52.1% |
| Site is **absent from the reference** | 1,737 | **12.4%** | 8.5% – 20.2% |

These are not the same statement, and **quoting 44.1% while describing the second
overstates the effect roughly threefold.** We made exactly that error while
building the arm; it is recorded rather than quietly corrected. The denominator
is also not the genome — it is a shortlist already ranked by predicted activity.

**Scope.** No guide is named safe or unsafe and none is ranked. These are
properties of how off-target lists are **constructed**, not verdicts on any
guide — the same rule that stops `src/audit_screen.py` naming a gene set, applied
to a domain with a patient at the end of it. This arm does not revise the
pre-registered K562 primary.

Full record: `results/offtarget/offtarget_evaluation.json`, `docs/OFFTARGET.md`.

## Does the confound survive when the program is actually switched on?

**Evaluation 9. Pre-registered** (`docs/ADAMSON_PREREG.md`, `b83e7308…`, committed
`7a98d4d` before the substrate was opened). The standing objection to everything
above is that K562 is unstressed, so the UPR was never engaged and a null is
unsurprising. Adamson 2016 is a targeted UPR Perturb-seq library, which makes it
the one substrate where engagement can be established rather than assumed.

**Engagement first, as a gate.** Against 1,000 null gene sets matched on set size
and control-expression decile, the observed mean absolute effect is **0.0551**
against a null 99th percentile of **0.0487** (null mean 0.0422), empirical
**p = 0.001**. The program is engaged. Only then was the size question asked.

| | |
|---|---|
| Size alone, in Adamson | **R² 0.2685**, p = 1.2×10⁻⁴ |
| Scoreable | **50 of 50**; 39 return at least one hit, 11 return none |
| Verdict | **PERSISTS UNDER ENGAGEMENT** — claim (a) |
| K562 reference | 0.4649 |

**Amendment 1, appended rather than rewritten.** The original pre-registration did
not say which construct was the control. That was resolved by a rule about
construct identity — `(mod)` and `_pBA`, pooled, 7,293 cells — written into an
amendment appended *below* the original text, with **no threshold changed**: P0,
P1, P2 and the R² bands are untouched and the original is diffable at `7a98d4d`.
Because the control definition was the one real degree of freedom, the arm
reports what the other choices would have given: **0.2398** and **0.2699** for the
two single controls, against 0.2685 pooled. The definition did not manufacture
the result.

**The honest scope limit, stated by the arm itself.** This is **not a
replication**. Adamson is a targeted library of 103 retained perturbations
deliberately enriched for regulators of the program under test, against K562's
9,837 genome-scale knockdowns. It is the worst available substrate for a claim
about unbiased screens and the best available one for a claim about engagement,
and it is used only for the second. The single-cell → perturbation-effect
construction is **new code and is not covered by the frozen scorer's hash** — the
arm says so rather than implying the whole pipeline was byte-frozen.

Full record: `results/adamson/adamson_evaluation.json`, `docs/ADAMSON_RESULTS.md`.

## Does our headline describe the field, or just our screen?

**Evaluation 10. POST-HOC, exploratory, not pre-registered.** BioGRID ORCS 2.0.18
ships 1,952 curated human CRISPR screens with an explicit `HIT` column; **1,272**
meet the stated inclusion rule (≥20 hits, ≥10,000 genes measured, ≥8 usable sets;
680 excluded, 0 unparseable).

| Screen-level | R² |
|---|---:|
| p10 / p25 | 0.103 / 0.186 |
| **median** | **0.224** |
| p75 / p90 | 0.269 / 0.455 |
| mean | 0.253 |
| Share reaching our 0.465 | **9.6%** |

**Our screen sits above the field's 90th percentile.** Quoting 46.5% as though it
described screens generally would overstate the field by roughly 2×. The effect
also grows monotonically with hit-list size — **0.056 → 0.184 → 0.226 → 0.263**
across the four bins — which is the uncomfortable direction, because permissive
hit lists are what genome-scale screens produce and what labs mine.

**The arm then audited itself and lost the headline.** The screen is not the
independent unit: those 1,272 screens come from **187 publications**, one
contributes **340 screens (26.7% of the corpus)** and the top five contribute
**58.9%**, while the median publication contributes two. Collapsing each
publication to its median screen first moves the share reaching 0.465 from 9.6%
to **26.7%**, and the median from 0.224 to **0.246** — denali sits above roughly
the 73rd percentile of the literature, not the 90th. The publication-level
distribution is also far wider (0.043–0.654 against 0.103–0.455), so the
tightness of the screen-level distribution was itself an artifact of counting.
**This is the project's own thesis occurring inside the project's own audit**, and
it leads the writeup rather than sitting in a caveats list.

**Two disclosures this arm does not ship without.** First, **0.224 and 0.465 are
not the same estimand** — different unit, outcome and predictor — so a smaller
field median does not falsify ours; it bounds how far ours travels. Second, **an
independent execution of the same idea landed near 0.10 over ~1,673 screens with
non-monotonic strata and could not be reconciled.** We report ours because its
code and inclusion rule are in this repository, and **neither number should be
quoted as "the field's value."** The predictor transform is a known contributor
and is measured, not waved at: the raw-size predictor moves the median to
**0.192**. No screen and no publication is named as confounded.

Full record: `results/corpus/corpus_audit.json`, `docs/CORPUS.md`.

## Limitations

Full document: **`docs/LIMITATIONS.md`**. In brief:

1. **The 0.751 figure is partly mechanical** — coherence derives from the same
   matrix as the outcome. Honest floor 0.561.
2. **−0.019 guide-pair concordance** — no gene-level claim is made anywhere, and
   **no novel gene is named in this project.**
3. **One cell line.** K562, leukemia-derived, unstimulated. Program A's null is
   explained by exactly this: no ER stress, so the UPR was never engaged.
4. **The gate is wrong 20/50 times**, including on our own held-out program.
5. **The evidence layer is a pointer layer.** Our top-cited source for ATF3 was a
   paper about integrating single-cell data across species. 19 of 20 blind-probe
   genes returned the same zebrafish methods paper; one returned a different gene.
6. **Held-out is underpowered** and one axis failed outright.

---

## Next experiment

Generated by the pipeline, not written by us (`src/next_experiment.py`). It reads
measured values and emits a different proposal per outcome — no branch tests a
program name:

- **Null** → the mechanism is read off `expr_ratio`/`sd_ratio`, a condition change
  is proposed, and a falsification condition is stated.
- **Hit** → pathway-level validation only, with the −0.019 reason given.
- **Unscored** → predicted R_p, prediction SD, and expected information gain.

**The single highest-value next experiment this work implies:** re-run the
identical sweep in a **stressed** K562 population.

Be precise about which null this tests. Program A returned **517 hits and ranks
12 of 50** — it is not a quiet program. What failed is the `known_regulator_recovery`
control: the canonical UPR sensors do **not** land at the extremes of the ranking
(`controls.csv`, program_a, FAIL). So the ranking moved, and it did not move the
genes the biology says it should.

Our stated mechanism — no ER stress, so the sensors are never engaged — predicts
that inducing ER stress recovers those sensors at the extremes. If it does not,
the mechanism is refuted and the null is biological rather than conditional.
