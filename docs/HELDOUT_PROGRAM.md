# Held-out program — SEALED until Section 9

**Written 2026-08-15, BEFORE any scoring of the primary program.**

> **DO NOT LOOK AT THIS PROGRAM'S RESULTS UNTIL THE PRIMARY PIPELINE IS FROZEN.**
> Nothing in the pipeline may be tuned, thresholded, filtered or re-specified
> after this program's numbers are seen. If it fails, **that is the finding.**

## Why this file exists

Kexin Huang is judging. Biomni's central claim is **zero-shot generalization to
unseen tasks with no task-specific tuning.** A result on a program the pipeline
was built against is not evidence of that. This file is the unseen task.

## The held-out program

**`HALLMARK_CHOLESTEROL_HOMEOSTASIS`** — MSigDB v2026.1.Hs, committed at
`data/genesets/h.all.v2026.1.Hs.symbols.gmt`.

**Why this one, decided blind:**

- **Different biology from the primary.** Not a stress response, not a
  proteostasis sibling. SREBP-driven sterol metabolism. If the pipeline only
  works on stress programs, this exposes it.
- **Cell-intrinsic** by the same standard the gate applied: sterol sensing,
  synthesis and uptake are cell-autonomous, requiring no tissue architecture.
- **Has a human patient-level anchor** if it survives: familial
  hypercholesterolemia / statin-response cohorts.
- **Chosen without looking at its data.** Its coverage, expression and variance
  in K562/RPE1 have deliberately **NOT** been computed. It has not been run
  through the Gate C1 script. It may well fail measurability — that outcome is
  reportable and will be reported.

## Pre-committed run conditions

The Section 9 run uses the pipeline **exactly as frozen after Section 7**:

- same scoring statistic (rank-based nonparametric primary, cosine reported alongside)
- same RPE1 handling and denominator reporting
- same DepMap essentiality filter and threshold
- same output tiers
- **no re-tuning, no threshold change, no gene-set swap, no "the program needed X"**

If the held-out program returns nothing, the reported result is that the
pipeline did not generalize to it.

## Pre-committed nonsense control (Section 7)

So the negative control cannot be cherry-picked, its draw is fixed here in
advance:

- **41 genes**, sampled uniformly without replacement from the measured `var`
  gene space of `K562_gwps_normalized_bulk_01.h5ad`
- **`numpy.random.default_rng(20260815)`**
- Sampled at run time from that seed. Not curated, not inspected, not redrawn.
  **If the nonsense program produces a surviving hit, that is reported as a
  failure of the method, not discarded as a fluke.**

## Pre-committed guide-pair consistency control

738 genes in the K562 file carry **separate `P1` and `P2` rows** (independent
sgRNA constructs against the same target); 8,866 are already collapsed to
`P1P2`. The 738 are a reagent-level internal-consistency check: the two rows for
one gene should receive concordant reversal scores. Reported as a control, **not**
as a replication arm — 738/9,823 = 7.5% coverage, and both rows share cell line,
batch and library.
