# Does subset size decide the AI leaderboard?

**Pre-registered** in `docs/BENCHMARKS_PREREG.md` (`9b825d87…`, commit
`a2776f7`), written and hashed **before any benchmark data was downloaded**.
Post-deadline extension work. The eleven closed evaluations are not revised;
`results/frozen/` is untouched. All numbers: `results/benchmarks/mmlu.json`.

---

## The negative first, because it is the result

**Benchmarks are not confounded by subset size, and set-level genomics is.
The entire difference is one division.**

We expected this and wrote the expectation down in advance, which is the only
reason it counts as a finding rather than a rationalisation. The
pre-registration says, before any download:

> We expect normalisation to defeat the mechanical confound … If that is what
> comes back, the finding is **"benchmarks got this right and set-level
> genomics didn't — normalisation by set size is the entire difference"** —
> and that is the reportable result, not a failure of the arm.

That is what came back.

## What was measured

Every model in the archived HuggingFace Open LLM Leaderboard with a complete
57-subject MMLU vector: **5,452 models**. No model was excluded after any score
was seen; the panel rule was fixed in advance. MMLU subject sizes run from 100
to 1,534 items — a **15.3×** spread.

**The gate, before any result was read.** Item counts were recovered
independently from each model's own reported standard error,
`n = acc(1−acc)/se² + 1`, and compared against the dataset's test-split sizes.
They agree on **57 of 57 subjects, maximum disagreement 0.0**. A benchmark
whose reported sizes and reported errors disagreed would not be a substrate
worth auditing.

## The four questions, in the order they were registered

| | question | answer | verdict |
|---|---|---|---|
| **A1** | does subset size predict a per-subject **rate**? | ρ = **0.12** | RATE LAYER CLEAN |
| **A2** | does it predict the **count**? | median R² = **0.598** | CONFOUNDED, 100% of the panel |
| **A3** | does re-weighting move the **leaderboard**? | τ = 0.955, top-10 unchanged | criterion FIRED — see below |
| **A4** | how much of two benchmarks' **agreement** is shared weighting? | **0.9%** | AGREEMENT IS CAPABILITY |

**A1 — the rate layer is clean.** Subject size barely predicts subject
accuracy (ρ = 0.12, R² on log-size = 0.004). Item difficulty does not
meaningfully covary with how many items a subject has. This was the outcome
that could have gone the other way and did not.

**A2 — the count layer is confounded, exactly as hard as genomics.** Run
denali's packaged audit verbatim on `(subject, n_items, n_correct)` and the
median size-alone R² is **0.598** — higher than denali's own headline 0.465,
with **100%** of the 5,452 models returning CONFOUNDED. The arithmetic is
present in AI benchmarks in full force. Dividing by item count is the only
thing standing between a leaderboard and the failure mode that dominates
set-level genomics.

**And that number is entirely mechanical — we measured the floor rather than
asserting it.** Replace each model with a hypothetical one scoring *its own
mean accuracy on every subject*: no capability variation whatsoever, so any
size dependence left is arithmetic and nothing else. That null scores
**0.807**. Real models score **0.598** — **below** the arithmetic floor, for
**99.9%** of the panel. Genuine variation in subject difficulty *adds*
variance that size cannot explain, which pushes the observed value down.

So A2 says nothing bad about any benchmark. It measures how strong the
arithmetic is when nothing is normalising it, which is the number that makes
the genomics comparison legible.

**A4 — two benchmarks agree because models differ in capability.** Across the
324 models scored on both MMLU and BIG-Bench Hard, agreement is ρ = 0.841
item-weighted and 0.833 equal-subtask: **0.9%** of the agreement is
attributable to shared weighting structure. Compare denali's own
cross-screen concordance arm, where **26%** of the apparent replication
between two CRISPR screens was set size. Benchmarks agree for the right
reason.

## A3 fired, and we are reporting how it fired

The registered criterion for "construction moves the leaderboard" was: top-5
membership changes by ≥ 1 model, **or** ≥ 10% of the panel moves ≥ 3 ranks.
Both tripped. **The verdict stands as registered — a criterion is never
revised after seeing data.** What follows is labelled post-hoc, and it is the
honest reading.

**The top-5 change is a tie.** The model that enters the top five under
equal-subject weighting is separated from the one it displaces by
**0.000071** — which is **exactly one item out of 14,042**. That is not a
reordering; that is a coin flip resolved differently by two aggregations.

**The rank-move threshold was calibrated blind to panel density.** With 5,452
densely packed models, three ranks is 0.06% of the panel. The median model
moves 39 places — **0.7% of the leaderboard**. Kendall τ is 0.955 and the
**top ten does not change at all**.

So the registered criterion fired on two artifacts of scale, and the
substantive answer to "does benchmark construction move the leaderboard" is:
**barely**.

## Why it barely moves, which is the interesting part

The confound's *input* is large. Item-weighted averaging gives the biggest
subject **15.3× the weight** of the smallest; the five largest subjects are
8.8% of the subjects but **31.1% of the items**; the total-variation distance
between the two weightings is **0.276**. Switching aggregation shifts scores
by 0.8 accuracy points on average and up to 2.8.

The *output* is suppressed by two independent mechanisms:

1. **Normalisation.** Accuracy is a rate, so a big subject does not
   mechanically collect more credit — the thing that makes a big gene set
   collect more hits.
2. **Correlated ability.** Mean cross-subject correlation of model accuracy
   across the panel is **0.87**, with 75.7% of subject pairs above 0.8. A
   model good at one subject is good at the others, so re-weighting subjects
   cannot reorder models much.

Set-level genomics has **neither** protection. Hit counts are counts, not
rates; and gene-set membership induces no comparable across-set correlation
of "ability". That is why the same arithmetic that is inert here is dominant
there.

## What this does not say

- Not that any benchmark is well-designed, or that any leaderboard position
  is deserved. It measures one specific confound and finds it controlled.
- Not that MMLU's construction is balanced — it is not; the weight spread is
  15×. The finding is that the imbalance does not propagate to rankings.
- Not a claim about any model, lab or leaderboard entry. **No model is named
  anywhere in this arm.** The unit of inference is the distribution over
  5,452 models.
- The panel is one archived leaderboard's models on one benchmark family,
  scored by one harness. A2's near-mechanical firing should not be quoted as
  "benchmarks are 60% confounded" — it is the count layer, which nobody ranks
  on.

## Reproduce

```bash
# both artifacts are public, no auth
GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 \
  https://huggingface.co/datasets/open-llm-leaderboard-old/results \
  data/raw/mmlu_v1_results
GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 \
  https://huggingface.co/datasets/open-llm-leaderboard/results \
  data/raw/mmlu_v2_results
.venv/bin/python -m src.benchmarks_audit      # writes results/benchmarks/
```

Subject sizes are committed at `data/benchmarks/mmlu_subject_sizes.json` with
their source URL. Where a model has several result files the most recent by
filename timestamp is used — an implementation decision fixed before any value
was computed, recorded in the module docstring.
