# Leaderboard — does your method beat set size?

**Every number on this page is written by [`scorer/score.py --board`](scorer/score.py) and none is typed by hand.**
Regenerate with:

```
python benchmarks/challenge/scorer/score.py --board
```

Truth is the held-out RPE1 screen over 50 MSigDB Hallmark programs. `delta` is Spearman minus the size-only baseline's Spearman: **positive means the method beat set size.**

| # | method | Spearman | top-10 | delta vs baseline |
|--:|---|--:|--:|--:|
| 1 | raw K562 hit count | 0.6633 | 0.80 | +0.2082 |
| 2 | hits per gene measured | 0.6599 | 0.70 | +0.2048 |
| 3 | denali rerank residual | 0.4664 | 0.40 | +0.0113 |
| 4 | **size only (baseline)** | 0.4551 | 0.60 | +0.0000 |

The size-only baseline scores rho **0.4551** against a permutation null whose 95th percentile of |rho| is 0.2781 (p = 0.0014), so it is a baseline worth beating rather than a straw man.

Two of these rows are also produced by `src/concordance.py`, written months earlier on a different codepath: the study publishes the raw cross-screen agreement as **0.663** and reports size alone predicting **6 of the top 10**. The scorer's independent implementation returns 0.6633 and 0.60. Same frozen inputs, so this checks the scoring code rather than the data — but it is the check that would have caught this challenge quietly drifting away from the study, and `verifier/test_scorer.py` asserts both.

## The same predictors, scored against a target with size removed from it too

The table above scores against RPE1's **raw** hit ranking, and that ranking is itself size-confounded: over these 50 programs, RPE1's own set sizes explain **R² 0.3090** of it. So a predictor with size stripped out is scored against a target that still contains size. Removing size from both sides inverts the order:

| method | Spearman vs RPE1 residual | permutation p |
|---|--:|--:|
| denali rerank residual | **+0.4972** | 0.0003 |
| hits per gene measured | **+0.2993** | 0.0359 |
| raw K562 hit count | +0.2193 | 0.1214 — not significant |
| size only (baseline) | -0.1755 | 0.2193 — not significant |

**Which method wins is decided by whether the target is size-corrected, and that is the result on this page.** Against the raw target the naive hit count wins outright; against the size-removed target it is no longer distinguishable from chance, while the correction this project ships is the only entrant that clears its permutation null. The board is not measuring one thing well — it is measuring two different things, and the confound decides which.

This second table was recomputed by a separate implementation that did not read this scorer. All four rank correlations agreed to four decimal places; the permutation p-values differed in the third decimal, which is the expected signature of independent draws rather than a copied seed. Both implementations read the same frozen `paired_programs.csv`, so what this establishes is that the arithmetic is right, not that the underlying data is.

Read the limits of that honestly. It rules out the possibility that the correction destroys everything: there is reproducible non-size agreement between two independently screened cell lines, at p = 0.0003. It does **not** establish that the residual is biology. Both sides of that comparison are corrected the same way, so they can still agree for the same wrong reason — which is this project's own evaluation 6, pointed back at this project's own challenge.

## How to enter

Open a pull request adding one CSV to [`entries/`](entries/). No server, no account, no hosting — the pull request **is** the submission mechanism, and the scorer reruns every entry in `entries/` on every run, so a row that cannot be reproduced from its own file does not survive.

## The row that matters

**`denali rerank residual` is this project's own method, entered as a contestant.**
On the first table it places fourth of four on top-10 overlap, below the baseline it is supposed to improve on. That result is not softened anywhere on this page. A benchmark authored by the party it flatters is marketing, so it is scored by the same code as everyone else and both of its results are printed at the same size.

## What a high row is not

Ranking well on the first table means predicting the second screen, and predicting the second screen is not the same as being right. Both screens can be confounded the same way and agree for the same wrong reason — that is this project's own evaluation 6, which found 26% of the cross-screen agreement is set size rather than biology. No row on this board is an endorsement of any gene set, and no gene is named.
