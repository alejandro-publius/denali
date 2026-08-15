# Matrix pre-registration

**Written and committed BEFORE any program beyond A and B was scored.**
Same protocol as `GATE_C1_PREREGISTRATION.md`. No value below was chosen after
seeing a result, and **no threshold here may be revised after seeing one.**

---

## 0. What has and has not been run

**Already scored, before this document:** `HALLMARK_UNFOLDED_PROTEIN_RESPONSE`
(program A) and `HALLMARK_CHOLESTEROL_HOMEOSTASIS` (program B, sealed
`9ad74a7`). Both remain in the Tier 1 sweep; **neither is held out**, and the
predictor in Tier 3 will be fit including them. This is disclosed because they
are not naive rows.

**Not run:** every other Hallmark program, every Reactome program, all features,
the predictor, and the held-out evaluation.

**Timing benchmark only** (no program-level result inspected): 9.6 s/program,
0.5 s matrix load, 0.74 GB RAM.

## 1. The unit and the statistic

**Reversibility statistic**, per program *p*:

> **R_p = log10(1 + number of perturbations at q < 0.05, BH-corrected WITHIN program p)**

Within-program BH, not matrix-wide. Fixed now so the correction scope cannot be
chosen later to suit the answer.

**Measurability features**, all computable **without scoring** — from the gene
set, the expression matrix and DepMap alone:

| # | Feature | Source |
|---|---|---|
| M1 | `frac_present` — fraction of members in the measured space | Gate C1 §1a |
| M2 | `expr_ratio` — median member expression ÷ background | Gate C1 §1b |
| M3 | `sd_ratio` — median member SD across perturbations ÷ background | Gate C1 §1c |
| M4 | `n_present` — members measured (absolute size) | gene set ∩ `var` |
| M5 | `essentiality_density` — fraction of members DepMap-essential | `CRISPRGeneEffect.csv` |
| M6 | `coherence` — mean pairwise correlation among member genes across perturbations | `X` |

## 2. (a) PRIMARY CLAIM — reversibility is program-intrinsic

> Programs differ in reversibility for reasons **not** reducible to how well
> their genes are measured. After conditioning on M1–M6, substantial variance in
> R_p remains unexplained, and the reversible/null split reflects biology.

## 3. (b) ALTERNATIVE CLAIM — measurability dominates

> **"K562 reversibility is mostly measurability."** Whether a program returns
> hits is largely determined by how many of its genes are measured, how highly
> they are expressed, and how much they vary — not by the program's biology. The
> deliverable becomes **a quantified limit on what genome-scale perturbation
> screens can discover in a resting cell line.**

**This is not a failure and will not be presented as one.** If it is what the
data says, it is the more useful result and it is what we report.

## 4. (c) THE DECIDING STATISTIC AND THRESHOLD

Ordinary least squares of **R_p on M1–M6** across the 50 Hallmark programs.
Decision on **adjusted R²**:

| Adjusted R² | Verdict |
|---|---|
| **≥ 0.60** | Report **(b)** — measurability dominates |
| **≤ 0.30** | Report **(a)** — reversibility is program-intrinsic |
| **0.30 < R² < 0.60** | **Report both.** Mixed result, state the number, make **no dominance claim either way.** |

Reported alongside, never in place of: per-feature standardised coefficients
with 95% bootstrap CIs (1,000 resamples), and the R² of each feature alone.

## 5. (d) WHAT MAKES US REPORT NEITHER

Any one of these and we report the diagnostic, not a claim:

1. **Fewer than 20 of 50 programs pass the Gate C1 measurability criteria** — too
   little dynamic range to model.
2. **R_p is degenerate** — more than 45 of 50 programs share an identical value
   (all zero, or all saturated).
3. **The nonsense control produces any perturbation at q < 0.05.** Pre-committed
   seed 20260815. If random genes yield hits, the method is broken and nothing
   downstream is interpretable.
4. **n_effective < 20 programs** entering the OLS after gating — 6 features on
   fewer than 20 points is not a model.

## 6. (e) HELD-OUT SET — SEALED

**Selection rule, blind and deterministic. No seed, no hand-picking, fully
re-derivable by anyone:**

> From `data/genesets/c2.cp.reactome.v2026.1.Hs.symbols.gmt`, keep sets with
> **30 ≤ n_genes ≤ 200** (the Hallmark size range — this controls the most
> obvious collection confound). Rank by **sha256(set_name)** hex digest
> ascending. **Take the first 10.**

Eligible pool: **694 of 1,839** Reactome sets.

| # | Held-out program | n | sha256 prefix |
|---:|---|---:|---|
| 1 | `REACTOME_GASTRULATION` | 119 | `0134dbac04ef` |
| 2 | `REACTOME_EPH_EPHRIN_SIGNALING` | 92 | `0244ef512b0e` |
| 3 | `REACTOME_FORMATION_OF_THE_CORNIFIED_ENVELOPE` | 129 | `02999b2da9e7` |
| 4 | `REACTOME_SCAVENGING_OF_HEME_FROM_PLASMA` | 69 | `02bce73cf66e` |
| 5 | `REACTOME_RET_SIGNALING` | 40 | `03704aa87b12` |
| 6 | `REACTOME_REGULATION_OF_LIPID_METABOLISM_BY_PPARALPHA` | 118 | `039c743e5c6b` |
| 7 | `REACTOME_G_PROTEIN_MEDIATED_EVENTS` | 54 | `0473c3892e06` |
| 8 | `REACTOME_TRIGLYCERIDE_METABOLISM` | 38 | `04c3c0ebac13` |
| 9 | `REACTOME_MEIOSIS` | 120 | `051dda6e3043` |
| 10 | `REACTOME_REGULATION_OF_PYRUVATE_METABOLISM` | 33 | `053a84d8de03` |

**These 10 are NOT scored until the Tier 3 model is frozen and committed.**
Held out from a *different collection* than the training set, so this tests
generalisation across curation style as well as across programs — a harder test,
and one we may fail.

**Program B (`HALLMARK_CHOLESTEROL_HOMEOSTASIS`) remains separately sealed at
`9ad74a7` as the original single-program held-out.** It is in the Tier 1 training
set and is **not** part of this 10.

### Held-out evaluation metric, fixed now

**Spearman ρ between predicted and observed R_p across the 10 held-out programs**,
with a **1,000-resample bootstrap CI**.

⚠ **Pre-registered power limitation.** At n=10, ρ = 0.5 corresponds to p ≈ 0.14.
**We will report the point estimate and CI and will make no significance claim**
on the held-out set. Anyone reading ρ as a significant result is misreading it,
and we say so first.

## 6f. (f) WHAT COUNTS AS SUCCESS AND WHAT COUNTS AS FAILURE

Fixed now, before the sweep. Two independent axes; **both are reported whatever
they say.**

### Axis 1 — rank recovery (primary)

Spearman ρ between predicted and observed R_p across the 10 held-out programs:

| ρ | Verdict |
|---|---|
| **≥ 0.60** | **SUCCESS.** The predictor generalises to unseen programs from an unseen collection. |
| **0.30 – 0.60** | **PARTIAL.** Reported as a weak, directional effect with the CI. No generalisation claim. |
| **< 0.30** | **FAILURE.** Reported as failure to generalise, in those words. |
| **< 0** | **FAILURE, inverted.** Reported as such, not as "near zero". |

### Axis 2 — binary reversible/null recovery (secondary)

Each held-out program is predicted reversible or null by the frozen Tier 3 model,
then compared to its measured call. **Balanced accuracy** across the 10:

| Balanced accuracy | Verdict |
|---|---|
| **≥ 0.75** | SUCCESS |
| 0.55 – 0.75 | PARTIAL |
| **< 0.55** | FAILURE — no better than guessing at n=10 |

### Binding conditions

- **Both axes are reported.** Reporting only the more flattering one is
  prohibited.
- **A failure is a result, not a retry.** If either axis fails we report it and
  do **not** refit, re-feature, re-threshold, or re-draw the held-out set.
- The **n=10 CI will be shown next to every number**, so "SUCCESS" is always read
  against its own imprecision.
- If **fewer than 8 of the 10** held-out programs pass the Gate C1 measurability
  criteria, the held-out evaluation is reported as **UNDERPOWERED AND
  INCONCLUSIVE** rather than as success or failure.

## 7. Standing rules

- Tier 1 must call the **byte-identical committed scoring function**
  `src/score_k562.py`, sha256 `2abfdc6f730d786180e37f73e2951c303c5a7b42caa27dc3394c74c323d7bbfa`.
  **If the statistic changes, program B's seal is void.**
- Held-out rows are not scored, inspected, or plotted before the Tier 3 model is
  frozen and pushed.
- **Pathway-level claims only. No novel gene is named anywhere.** Guide-pair
  concordance is −0.019 (`SCOPE_STATEMENT.md`).
- Any tier that will not finish by its checkpoint is **stopped and reported**,
  not half-built.
- Tier 4 results arrive after the 6:30 PM hard freeze and therefore **cannot
  enter `results/frozen/`**; they may only be reported verbally or as an appendix.
