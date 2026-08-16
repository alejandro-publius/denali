# RPE1 arm — pre-registration

**Written and committed before the RPE1 sweep was run.** Same protocol as
`docs/MATRIX_PREREG.md`: no threshold below was chosen after seeing a value, and
the commit that introduces this file precedes the commit that introduces any
RPE1 result.

---

## The question, scoped honestly

Our headline is that most of the variance in apparent reversibility across 50
Hallmark programs is explained by how the gene sets were built — chiefly their
size — rather than by biology. That was measured in **one screen, one cell line**.

The obvious objection is that it might be a property of K562 rather than a
property of screens. Replogle et al. published a second genome-scale CRISPRi
Perturb-seq screen in **RPE1**, a non-cancerous retinal pigment epithelial line,
and it is already in our substrate.

**This is not a replication and we will not call it one.** RPE1 covers **2,386**
unique knockdown targets against K562's 9,837 — **24.3%** — and that quarter is
disproportionately the *essential-gene* subset. We measured that ourselves and
published it as a failing control (`controls.csv`, `rpe1_coverage_collision`,
**FAIL**: 94.1% vs 11.3% coverage for essential vs non-essential genes).

So the question is narrower and it is the one the data can answer:

> **Does the measurability model's structure hold in a second, independently
> screened cell line?**

## Primary claim

**(a)** The relationship between set construction and apparent reversibility
reproduces in RPE1: set size alone explains a substantial share of the variance
in `R_p` across the same 50 Hallmark programs, and the sign of the effect is the
same as in K562.

## Alternative claim

**(b)** It does not reproduce. The size effect is materially weaker or absent in
RPE1, which would mean our K562 finding is at least partly a property of that
screen rather than of set-level statistics in general — and we would say so and
narrow the headline accordingly.

## The deciding statistic, fixed now

`R²` of `R_p` on `n_present` alone (ordinary least squares, one predictor),
computed over the 50 Hallmark programs scored in RPE1 with the **byte-frozen
scorer** `src/score_k562.py` (sha256 `2abfdc6f…`), unmodified — only the substrate
path differs.

`R_p = log10(1 + hits at q<0.05)`, BH-corrected within program. Identical to K562.

| Outcome | Threshold | Verdict |
|---|---|---|
| Claim (a) supported | RPE1 `R²` ≥ **0.25** AND slope positive | The size effect reproduces across cell lines |
| Ambiguous | 0.10 ≤ `R²` < 0.25 | **Report as inconclusive.** Directional but weak. |
| Claim (b) supported | RPE1 `R²` < **0.10** OR slope negative | Does not reproduce; narrow the headline to K562 |

**Why 0.25 and not the K562 figure.** K562's size-alone `R²` is 0.4649. We are
deliberately **not** requiring RPE1 to match it, because RPE1 has a quarter of the
perturbations and therefore less power to resolve hits at all — fewer hits
compresses `R_p` toward zero and mechanically weakens any relationship. Requiring
0.4649 would be setting a threshold we have reason to believe is unfair. 0.25 is
set as "clearly present, allowing for the power penalty," and is fixed before the
number exists.

## Secondary, reported but not deciding

- Spearman ρ between K562 `R_p` and RPE1 `R_p` across the 50 programs. Descriptive
  only — no threshold, because the coverage collision above makes it hard to
  interpret and we are not going to interpret it after the fact.
- The number of RPE1 programs returning zero hits, as a power check.

## What would make us report neither

If fewer than **35 of 50** programs are scoreable in RPE1 (too few measured
members to compute the statistic), the arm is **UNDERPOWERED AND INCONCLUSIVE**
and no verdict is issued — the same rule that fired against us on the held-out
ten, where 1 of 10 passed and we reported it.

## Constraints

1. `results/frozen/` is **not** touched. RPE1 output goes to
   `results/rpe1/` and is a separate artifact.
2. The K562 headline is **not** revised by this arm in either direction. If (a)
   holds, the claim broadens with the coverage caveat attached. If (b) holds, the
   claim narrows to K562. Neither rewrites the pre-registered primary.
3. **No gene-level claim.** Guide-pair concordance forbids it in RPE1 exactly as
   it does in K562.
4. The 24.3% coverage figure and the failing coverage control are stated wherever
   this arm's result is stated. Not in a footnote.
5. The scorer is not modified. If it needs modification to run on RPE1, the arm is
   abandoned rather than the scorer edited — its hash is load-bearing elsewhere.
