# The headline was recomputed by a second implementation that never read the first

`src/independent_recompute.py` reimplements the headline statistic **from the
method section of this README**, not from the code. `src/score_k562.py`,
`src/sweep.py` and `src/freeze_predictor.py` were not read while writing it — a
reimplementation that consulted the original would only prove the original can
be copied. Different machinery at every step where a choice existed:

| step | frozen path | independent path |
|---|---|---|
| Mann–Whitney U | its own byte-frozen scorer | `scipy.stats.mannwhitneyu` |
| BH correction | its own | `statsmodels.stats.multitest.multipletests` |
| regression | its own | `statsmodels.formula.api.ols` |

It reads the raw 470 MB substrate, not `results/frozen/`, and recomputes every
hit count from `X`.

| figure | published | independent | agree |
|---|---:|---:|:--:|
| adj R², all six features | 0.751 | **0.7511** | ✅ |
| adj R², outcome-independent five | 0.561 | **0.5606** | ✅ |
| R², set size alone | 0.4649 | **0.4649** | ✅ |

Per-program agreement across all **50** programs: **Pearson 1.000000**, Spearman
1.000000, largest absolute difference in `R_p` of **0.000049** — which is the
rounding in the stored file, not a disagreement. The hit counts are identical as
integers.

Asserted by the suite to a stated tolerance of 0.01, so a future divergence
fails the build rather than sitting in a JSON nobody opens. The scorer is also
run against synthetic data with a known answer: a planted signal returns hits on
60 of 60 perturbations, a null returns 0 of 60.

**What this does not establish.** That the method is *correct*. Two
implementations of a wrong method agree with each other perfectly. This rules
out implementation error in the frozen scorer; it does not rule out the question
being the wrong one to ask, which is what the fourteen evaluations are for.
