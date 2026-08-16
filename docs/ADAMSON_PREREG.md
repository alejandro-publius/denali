# Adamson 2016 arm — pre-registration

**Written and committed before any Adamson value was computed.** Same protocol as
`docs/MATRIX_PREREG.md`, `docs/RPE1_PREREG.md` and `docs/ANNOTATION_PREREG.md`:
no threshold below was chosen after seeing a value, and the commit that
introduces this file precedes the commit that introduces any Adamson result or
any code that produces one.

At the time of writing, the substrate had been downloaded but **not opened** —
not its `obs` keys, not its perturbation labels, not its gene list. Every
construction rule below is therefore specified in terms of what the file must
contain rather than what it was observed to contain, and the resolved values
(control label, gene count, dropped perturbations) are recorded in the output
artifact so the mapping from this document to the run is auditable.

---

## The question, and why this arm exists

This project published a design failure in its own words:

> K562 is unstressed, so the unfolded protein response was never switched on.
> The gate we built tested whether a program was **measurable**; it should have
> tested whether it was **engaged**.

That is a confession without a test attached. Everything denali measured was
measured in a screen where the flagship program was, by our own account, never
switched on. The obvious objection — that our headline is an artifact of
scoring programs that were dormant — has never been answered with data.

Adamson et al. 2016 (Cell, doi:10.1016/j.cell.2016.11.048) is a Perturb-seq
screen of the unfolded protein response in **the same cell line, K562**, built
around a targeted UPR library. If our finding survives in a screen where the
program is engaged, the confound is structural. If it collapses, our headline
was partly an artifact of dormancy and we narrow it.

**Substrate.** scPerturb-harmonised GEO GSE90546 / GSM2406681, Zenodo record
13350497, file `AdamsonWeissman2016_GSM2406681_10X010.h5ad`, 471,286,951 bytes.

## Scope, stated before the result exists

**This is not a replication of the K562 genome-scale result and we will not call
it one.** Adamson is a **targeted UPR library of ~115 perturbations**, not a
genome-scale screen of 9,837 knockdowns. The libraries differ in size by roughly
two orders of magnitude and in design by intent: one is unbiased, the other is
deliberately enriched for regulators of the very program under test. A targeted
library is the *worst* possible substrate for a claim about unbiased screens and
the *best* available substrate for a claim about engagement. We are using it only
for the second.

Wherever this arm's result is stated, the 115-perturbation targeted-library
scope is stated with it. Not in a footnote.

## The premise is itself falsifiable — precondition P0

The entire arm rests on "in Adamson the UPR is engaged." We are not going to
assume that because a paper title says so. It is checked first, and the check can
fail.

**P0 (engagement).** Let `U` = the members of `HALLMARK_UNFOLDED_PROTEIN_RESPONSE`
measured in this substrate. Compute the mean absolute perturbation effect across
`U`, pooled over all retained perturbations. Compare against a null of **1,000
random gene sets matched to `U` on both size and mean-expression decile**, drawn
from the measured genes. Engagement is established if the observed statistic
exceeds the **99th percentile** of that null (one-sided, p < 0.01).

Expression-decile matching is part of the rule, not a refinement added later:
UPR genes are on average more highly expressed, and an unmatched null would
declare engagement for that reason alone.

**If P0 fails, no verdict is issued on (a) or (b).** The arm reports
**PREMISE NOT ESTABLISHED**, which is a reportable outcome and is itself
informative — it would mean this file does not contain the stressed condition
the design assumes.

## Primary claim

**(a)** The size confound persists under engagement. Set size alone explains a
substantial share of the variance in `R_p` across the 50 Hallmark programs scored
in Adamson, with positive slope — i.e. the mechanism denali identified is
structural and is not an artifact of having scored dormant programs.

## Alternative claim

**(b)** It does not persist. The size effect is materially weaker or absent when
the program is engaged. This would mean denali's K562 headline is at least partly
an artifact of measuring programs that were never switched on, and **we would
narrow the headline and say so in the README rather than in an appendix.**

## The deciding statistic, fixed now

`R²` of `R_p` on `n_present` alone (ordinary least squares, one predictor),
computed over the Hallmark programs scoreable in Adamson.

`R_p = log10(1 + hits at q < 0.05)`, Benjamini–Hochberg corrected **within
program** over the perturbations with a finite score. Gate constants are the
committed ones and are not re-tuned here: `MIN_FRAC = 0.50`, `MIN_N = 25`,
`ALPHA = 0.05`.

The statistic is produced by the **byte-frozen scorer**
`src/score_k562.py` (sha256 `2abfdc6f…`). Its `score()` function is **imported and
called unmodified**; the file is not edited. Per the RPE1 constraint, if the
statistic required modification to run here, this arm would be abandoned rather
than the scorer changed.

| Outcome | Threshold | Verdict |
|---|---|---|
| Claim (a) supported | Adamson `R²` ≥ **0.25** AND slope positive | The confound persists under engagement; it is structural |
| Ambiguous | 0.10 ≤ `R²` < 0.25 | **Report as inconclusive.** Directional but weak. |
| Claim (b) supported | Adamson `R²` < **0.10** OR slope negative | Does not persist; narrow the K562 headline toward dormancy |

**Why 0.25 and not K562's 0.4649.** Same reasoning as the RPE1 arm, and more
forcefully. Adamson has ~115 perturbations against K562's 9,837. `R_p` is a
count-derived quantity and its ceiling here is `log10(1 + 115) ≈ 2.06` against
K562's observed range. Fewer perturbations compresses `R_p` toward zero and
mechanically weakens any relationship with set size. Requiring 0.4649 would be
setting a bar we already have reason to believe is unfair, which is a way of
guaranteeing the answer we might prefer. 0.25 is "clearly present, allowing for
the power penalty," fixed before the number exists, and identical to the bar the
RPE1 arm cleared by 0.026.

## Substrate construction — pre-specified, and NOT part of the frozen scorer

This is the one place the arm genuinely differs from RPE1, and it is disclosed
rather than buried. The frozen scorer consumes a **perturbation-effect matrix**
(rows = perturbations, columns = genes). Replogle's substrate ships in that form.
Adamson ships as **sparse single-cell counts**, so an effect matrix has to be
built. That construction is new code, it is not covered by the scorer's hash, and
it is a real degree of freedom. It is therefore fixed here, in advance:

1. Retain genes detected (non-zero) in **≥ 1%** of cells.
2. Normalise each cell to **10,000** counts, then `log1p`.
3. Identify control cells by the substrate's own non-targeting/control label in
   `obs.perturbation`. The resolved label is recorded verbatim in the output.
4. Pseudobulk: per perturbation, the **mean** across its cells. A perturbation
   with fewer than **25 cells** is dropped, and the dropped set is recorded.
5. Effect matrix `X` = pseudobulk(perturbation) − pseudobulk(control), controls
   excluded from the rows.
6. Non-finite entries are **masked, never imputed** (`docs/METHOD_RULES.md`).
7. `X` and the gene symbols are passed to the unmodified `score()`.

No step above is conditional on a result. If the substrate cannot satisfy a step
— for example if no control label exists — the arm is reported as
**NOT RUNNABLE** rather than the step being relaxed.

## What would make us report neither

Any of the following fires **before** (a)/(b) is considered, and each was fixed
before the substrate was opened:

- **P0 fails** → `PREMISE NOT ESTABLISHED`, no verdict.
- **P1** Fewer than **35 of 50** programs are scoreable → `UNDERPOWERED AND
  INCONCLUSIVE`, no verdict. Same rule that fired against us on the held-out ten,
  where 1 of 10 passed and we reported it.
- **P2** Fewer than **15 of 50** scoreable programs return at least one hit at
  q < 0.05 → `UNDERPOWERED AND INCONCLUSIVE`, no verdict. A regression fitted to
  a column that is almost entirely zero is not a measurement, and with ~115
  perturbations this is a live possibility rather than a formality.

An underpowered or null outcome is a reportable result. It is not a failure and
it will not be quietly re-run with a different threshold.

## Secondary, reported but not deciding

- Spearman ρ between K562 `R_p` and Adamson `R_p` across the programs scoreable
  in both. Descriptive only, no threshold — the library designs differ too much
  to interpret it, and we are not going to interpret it after the fact.
- The number of Adamson programs returning zero hits, as a power check.
- `n_present` in Adamson vs K562 per program, as a measurability check.

## Constraints

1. `results/frozen/` is **not** touched. Output goes to `results/adamson/` and is
   a separate artifact.
2. The K562 headline is **not** revised by this arm in either direction without
   the disclosure attached. If (a) holds, the claim broadens with the
   targeted-library caveat. If (b) holds, the claim narrows. Neither rewrites the
   pre-registered primary.
3. **No gene-level claim.** Guide-pair concordance is −0.019 in K562 and forbids
   per-gene calls here exactly as it does there. No novel gene is named.
4. The scorer is not modified. Its hash is load-bearing elsewhere.
5. The targeted-library scope and the fact that the pseudobulk construction is
   **not** covered by the scorer's hash are stated wherever the result is stated.
6. No wet-lab, dosing, clinical or therapeutic claim. Transcriptional movement is
   not phenotypic reversal.
