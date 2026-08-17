# Pre-registration — the size-only challenge

**Committed before the evaluation set was built and before any entrant, including
ours, was scored.** The rule below is the rule. If a later commit changes it, the
change is appended underneath with its reason, never edited in place — the same
discipline `docs/MATRIX_PREREG.md` carries for the study.

---

## The question

Does a gene-set ranking method beat **set size alone** at predicting which gene
sets will look hit-rich in an independently screened second cell line?

Arc Institute's Virtual Cell Challenge 2025 reported that perturbation models are
"not yet consistently outperforming naive baselines across all metrics." This
challenge makes the naive baseline in *our* corner of that problem — set size —
into something a stranger can run their own method against, offline, in ten
minutes, with no account and no server.

## The split rule

**The split is by screen, not by gene set.**

- **Input half, published:** the K562 arm. For each of the 50 MSigDB Hallmark
  programs, `size` (genes measured, `n_present_k562`) and `hits`
  (`n_hits_q05_k562`). Written to `data/k562_input.csv` in the plain
  `set,size,hits` form that `denali_audit.adapters.detect()` already reads.
- **Scoring half, withheld from the input file:** the RPE1 arm's
  `n_hits_q05_rpe1` for the same 50 programs. The scorer reads it at scoring time
  from `results/concordance/paired_programs.csv`.

Both halves come from `results/concordance/paired_programs.csv`, frozen. RPE1 is a
different cell line screened independently — it is a held-out *experiment*, not a
held-out slice of the same numbers.

### Why the split is not over gene sets

The obvious alternative — hold out 25 of the 50 programs — was rejected before
being run, on a stated ground: with n = 25 the sampling noise of a Spearman
correlation is larger than the differences between the methods being compared.
Section "Deciding quantity" below records the bootstrap that has to hold for this
choice to be right, and the scorer recomputes it every run. If it fails, the
design is wrong and this file is where that gets recorded.

### Why hit counts are not recomputed

`results/frozen/matrix.csv` cannot regenerate `n_hits_q05` and must not be used to
try. The frozen counts are computed at the **perturbation** level, one test per
guide, before a `groupby(targets).max()` collapses the matrix to one row per gene.
Recomputing Benjamini-Hochberg from the collapsed matrix tests fewer hypotheses on
a max-selected statistic and returns different counts — measured at +4, +2, +2, 0
on the first four programs, in both directions across all 50. Every hit count in
this challenge is read from the frozen files as an integer. None is re-derived.

## The metric

For a submission that assigns a score to each program, higher meaning
ranked-higher:

1. **Spearman** ρ between the submitted ranking and the true RPE1 hit ranking,
   using `denali_audit.core._spearman` — the shipped rank correlation, which is
   scipy-free and is the same function that produced the study's published 0.6633.
2. **Top-10 overlap**: of the 10 programs the submission ranks highest, how many
   are in RPE1's true top 10.
3. **The headline is the delta**: submitted ρ minus the size-only baseline's ρ.
   A positive delta means the method beat set size. Zero or negative means it did
   not, and that is a legitimate and publishable result.

The permanent baseline row is **rank by `size` alone**. It never leaves the board.

## Deciding quantity

Registered in advance, and checked by the scorer on every run:

- **The permutation null.** Shuffle the true RPE1 hit counts across programs 10,000
  times and rescore the size-only baseline. The baseline is a baseline worth
  beating only if its real ρ sits outside that null. If it does not, the challenge
  is measuring nothing and the board says so instead of reporting deltas.
- **The set-level split bootstrap.** Resample 25 of the 50 programs 10,000 times
  and report the standard deviation of the size-only ρ. This is the number that
  justifies splitting by screen rather than by set.
- **Scope limit 6.** The evaluation set must not be a mapping where `hits` are
  counted over the set's own members, because there a large R² is arithmetic
  rather than a confound. The 50 Hallmark programs are safe: `hits` counts
  knockdowns that moved the program (up to 5,707) and `size` counts genes measured
  in the program (up to 194), so `hits` is not bounded by `size` and the two are
  not counted over the same members. The scorer asserts `max(hits) > max(size)` and
  refuses to score if that ever stops being true.

## What this challenge does not ask

It does not ask which gene sets to chase. A ranking that predicts the second
screen well is a ranking that reproduces, and reproducing is not the same as being
real — both screens can be confounded the same way and agree for the same wrong
reason. That is this project's own evaluation 6 and it is the reason the top of
this board is not an endorsement of anything.

No gene is named in this challenge and none should be named in a submission. The
unit throughout is the gene set.

## Prior art, stated plainly

The idea of scoring an enrichment ranking against a size or degree null is not
ours. **EGAD** has shipped node-degree AUROC as a built-in null since 2017
([doi:10.1093/bioinformatics/btw695](https://doi.org/10.1093/bioinformatics/btw695));
**Crow et al., PNAS 2019** did the cross-dataset version. What is ours is running
it as a public challenge with the baseline as a permanent, unremovable row, and
entering our own method as a contestant that can lose.
