# Handoff — text for surfaces I do not own

Written by the session that built [`benchmarks/challenge/`](challenge/). Everything
below is **exact text to place**, not a suggestion to rewrite. I did not edit
`README.md`, `docs/`, `results/`, `packages/`, `src/`, `tests/` or `web/`.

---

## 1. For `README.md` — one row in the repository-layout table

Place after the `benchmarks/tasks/` row:

```markdown
| `benchmarks/challenge/` | A public self-scoring challenge: does your method beat the size-only baseline at predicting a second cell line? Our own `rerank` is entered as a contestant and places fourth of four on top-10 overlap |
```

## 2. For `README.md` — a short section

Suggested placement: immediately after the benchmarks section, before Scope limits.

```markdown
### The baseline, as a contest

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
which is itself size-confounded (size explains R² 0.214 in RPE1), so a
size-corrected predictor is being scored against a size-contaminated target.
Removing size from both sides reverses the result: the naive hit count falls to
+0.2193 and is no longer distinguishable from chance (permutation p = 0.12), the
size-only baseline goes negative, and the correction is the only entrant clearing
its permutation null at +0.4972, p = 0.0002.

Which method wins is decided by whether the target is size-corrected. That is this
project's thesis occurring inside this project's own challenge. It rules out the
correction destroying all signal; it does **not** establish that the residual is
biology, since both sides are corrected the same way and can agree for the same
wrong reason — [evaluation 6](results/concordance/) pointed back at us.
```

## 3. For `docs/DATA_DICTIONARY.md` — a trap that is currently undocumented

`results/frozen/matrix.csv` **cannot regenerate** `n_hits_q05`, and nothing
currently says so. The two live at different levels of aggregation:
`n_hits_q05` is counted at the **perturbation** level, one test per guide, while
`matrix.csv` is written afterwards from `groupby(targets).max()`, one row per gene.
Recomputing Benjamini-Hochberg from the collapsed matrix tests fewer hypotheses on
a max-selected statistic and returns different counts — measured at +4, +2, +2, 0 on
the first four programs, and in both directions across all 50 (Spearman between the
two is 0.9979, so the *ranking* survives and only the counts move).

Suggested line for the `matrix.csv` section:

```markdown
> **Do not recompute `n_hits_q05` from this file.** These are gene-level scores,
> collapsed from the perturbation level by `groupby(targets).max()`. The frozen hit
> counts were computed *before* that collapse, one test per guide, so a
> Benjamini-Hochberg pass over this matrix corrects for fewer tests on a
> max-selected statistic and returns different counts. Read `n_hits_q05` from
> `program_summary.csv`.
```

Credit where due: the mechanism was identified by the session working the
annotation arm, not by me — I had the discrepancy and the wrong hypothesis
(self-membership exclusion, which the ANGIOGENESIS 0-vs-0 case already refuted).

## 4. Nothing else

No number in `results/`, `docs/` or `README.md` needs to change because of this
work. The challenge derives every figure it prints from
`results/concordance/paired_programs.csv` and the packaged functions, and its two
cross-checks are that the baseline reproduces the study's published size-alone
top-10 of **0.60** and the naive entry reproduces the published cross-screen
Spearman of **0.6633**. Both are asserted in
`benchmarks/challenge/verifier/test_scorer.py`, so if a future change moves either,
that verifier goes red rather than the challenge silently drifting from the study.

## 5. One thing I could not do, for whoever picks this up

The evaluation set is 50 gene sets on two screens, because that is the only
exactly-frozen paired data in the repository. `results/corpus/` has 1,272 published
screens but commits **per-screen summaries only** — the per-set tables live in
`data/raw/orcs/`, which is git-ignored and absent, so a stranger cloning the
repository could not rebuild them and the challenge would fail its own
under-ten-minutes requirement. A 25-of-50 set-level split was rejected in the
pre-registration for a measured reason: bootstrapped, it carries SD 0.1814 on the
baseline Spearman alone, which is larger than three of the four gaps on the board.

If the ORCS per-set tables are ever committed in a reduced form, the same scorer
takes them unchanged — it reads through `denali_audit.adapters.detect()` — and the
evaluation set could go from 50 sets on 2 screens to thousands on 1,272. That is
the single highest-value extension and it is blocked only on data availability.
