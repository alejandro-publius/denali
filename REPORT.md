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

**2. Four controls, all reported, three of them failing.** A pre-committed
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
| **Essentiality-matched null** | Top-50 4.09× enriched (p<0.001). ❌ for program A. |
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
