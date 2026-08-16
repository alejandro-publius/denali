# Benchmarks arm (Track A) — pre-registration

**Written and committed before any benchmark data was downloaded or any value
computed.** Same protocol as `docs/MATRIX_PREREG.md` and `docs/RPE1_PREREG.md`:
no threshold below was chosen after seeing a value, and the commit that
introduces this file precedes the commit that introduces any benchmark result.

**Post-deadline extension work.** The eleven closed evaluations are not revised
by anything here, in either direction. `results/frozen/` is not touched.
Everything this arm produces goes to `results/benchmarks/` on a branch.

---

## The question, scoped honestly

denali's claim is that set-level rankings are dominated by how the sets were
built — chiefly their size — rather than by what the sets mean. If that is
arithmetic and not biology, it must appear wherever a score is aggregated over
sets of varying size. An LLM benchmark is exactly that: MMLU is 57 subject
subsets whose test sizes span roughly 100 to 1,534 items, and a leaderboard
position is an aggregate over them.

**The disanalogy, stated before anything runs.** Gene-set hit counts are
COUNTS: a bigger set mechanically collects more hits. Benchmark subject scores
are RATES: accuracy is already normalised by item count. The mechanical
count-confound therefore cannot appear in the rate layer *by construction*.
What CAN appear:

1. **In the count layer** (items-correct per subject), the arithmetic confound
   should reappear in full — which locates exactly where normalisation is doing
   its work.
2. **In the rate layer**, only a *construction correlation* can survive: if
   item difficulty covaries with subject size, size predicts accuracy even
   after normalisation.
3. **In the aggregate**, size still enters through *weighting*: an
   item-weighted (micro) average weights each subject by its size, an
   equal-subject (macro) average does not. If rankings differ between the two,
   leaderboard position is partly an artifact of how many items each subject
   happens to have.

## Pre-registered expectation (required, and falsifiable)

We expect **normalisation to defeat the mechanical confound**: the count layer
confounded (A2 fires ≥ 0.40), the rate layer weak (A1 below 0.5), and the
leaderboard largely robust to re-weighting (A3 lands at or near "robust").
If that is what comes back, the finding is: **"benchmarks got this right and
set-level genomics didn't — normalisation by set size is the entire
difference"** — and that is the reportable result, not a failure of the arm.
The alternative — rankings move materially under re-weighting — would be the
bigger claim, and we are writing down now that we consider it less likely.

## Data, fixed before download

- **Primary substrate:** per-subject MMLU accuracies (57 subjects) for a panel
  of models, from a public bulk artifact requiring no authentication (the
  HuggingFace Open LLM Leaderboard per-subject results, or an equivalent
  public lm-evaluation-harness result set).
- **Panel rule (fixed to prevent cherry-picking):** every model in the bulk
  artifact with a complete 57-subject vector is included. No model is excluded
  after any score is seen. Models are never named as findings; the unit of
  inference is the distribution over the panel.
- **Subject sizes** are constants of the MMLU test set, taken from the dataset
  itself, not from any model's output.
- **Secondary substrate (A4 only):** per-subtask results for two benchmarks on
  the same panel (target: BBH subtasks and MMLU-Pro categories from the Open
  LLM Leaderboard v2 artifacts; MMLU vs BBH acceptable).

## The deciding statistics, fixed now

**A1 — does size predict the RATE?** Spearman ρ between subject size
(n_items) and per-subject accuracy averaged across the panel, n = 57 subjects.
OLS R² of the same on log10(n_items) reported alongside. Per-model ρ
distribution reported descriptively (models share subject difficulty, so the
subject is the independent unit, not the model).

| Outcome | Threshold | Verdict |
|---|---|---|
| Construction correlation strong | \|ρ\| ≥ 0.50 | Size predicts difficulty; the rate layer is NOT clean |
| Present but moderate | 0.25 ≤ \|ρ\| < 0.50 | Reported as measured, no strong claim |
| Rate layer clean | \|ρ\| < 0.25 | Normalisation left no exploitable size signal |

**A2 — the COUNT layer.** For each model, `denali audit` verbatim
(`packages/denali-audit`, `core.audit`) on (subject, n_items, n_correct) with
n_correct = round(accuracy × n_items). Deciding statistic: median
`r2_size_alone` across the panel.

| Outcome | Threshold | Verdict |
|---|---|---|
| Arithmetic confound present in count layer | median ≥ 0.40 (the tool's own CONFOUNDED line) | The identical arithmetic is present; normalisation is what stands between leaderboards and the genomics failure mode |
| Not present | median < 0.40 | The analogy fails even at the count layer; report and stop extrapolating |

A2 firing is *expected and partially mechanical*; it is reported as the
mechanism being located, never as a scandal about any benchmark.

**A3 — THE REAL ONE: does weighting move the leaderboard?** For every model:
micro score = Σ correct / Σ items; macro score = mean of 57 subject accuracies.
Rank the panel both ways.

Deciding statistics: (i) Kendall τ between the two rankings; (ii) share of
models whose rank moves ≥ 3 positions; (iii) top-5 membership change; (iv) max
absolute rank move.

| Outcome | Threshold | Verdict |
|---|---|---|
| Construction moves the leaderboard | top-5 membership changes by ≥ 1 model OR ≥ 10% of the panel moves ≥ 3 ranks | Leaderboard position is partly an artifact of benchmark construction |
| Robust | top-5 unchanged AND < 5% move ≥ 3 ranks AND τ ≥ 0.98 | Benchmarks' normalisation + weighting practice survives the audit |
| Between | anything else | PARTIAL; report the four numbers, claim neither headline |

**A4 — cross-benchmark agreement (evaluation-6 analog).** ρ_micro = Spearman
across models between benchmark-1 micro score and benchmark-2 micro score;
ρ_macro = the same after re-aggregating both benchmarks equal-subtask. Share
of agreement attributable to weighting = 1 − ρ_macro/ρ_micro, defined only if
ρ_micro ≥ 0.30 (guard fixed now; below it the share is meaningless and is not
reported).

| Outcome | Threshold | Verdict |
|---|---|---|
| Weighting structure inflates agreement | share ≥ 0.25 | A quarter or more of "two benchmarks agree" is shared construction |
| Agreement is capability | share < 0.10 | The clean case; benchmarks agree for the right reason |
| Between | 0.10–0.25 | Reported as measured |

## What would make us report neither

- Fewer than **20 models** with complete 57-subject vectors obtainable from a
  public artifact → A1–A3 issue **no verdict** (DATA UNOBTAINABLE is the
  reported outcome, not a workaround).
- No public per-subtask artifact for a second benchmark on the same panel →
  A4 is reported as **"no defensible number here."**
- We do not swap in a different construction after seeing that the registered
  one is inconvenient. Any post-hoc analysis is labelled POST-HOC.

## Constraints

1. No model, lab, or leaderboard entry is named as a finding. Distributions
   only.
2. `results/frozen/` untouched; outputs to `results/benchmarks/`.
3. The closed evaluations are not renumbered or revised.
4. Accuracy values are taken as published in the artifact; we do not re-run
   any model.
