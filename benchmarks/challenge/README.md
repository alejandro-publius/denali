# Does your gene-set method beat set size?

A public, self-scoring challenge. Clone, run one command, get a number. No account,
no server, no key, no network, and no 470 MB download.

```
python benchmarks/challenge/scorer/score.py benchmarks/challenge/data/example_submission.csv
```

The current standings are in [`board.md`](board.md), and the rule that built the
evaluation set was [pre-registered and committed before the split](PREREG.md).

---

## Why this exists

Arc Institute ran the Virtual Cell Challenge in 2025 — 5,000+ registrants, 114
countries, 1,200+ teams, 300+ final submissions — and
[reported](https://arcinstitute.org/news/virtual-cell-challenge-2025-wrap-up) that
perturbation prediction models are "not yet consistently outperforming naive
baselines across all metrics," with the winners combining deep learning and
classical statistical features.

That is the field's flagship benchmark saying it cannot reliably beat the naive
baseline. This project measures one specific naive baseline — **set size** — and
until now shipped it as a diagnosis rather than as something you could run your own
method against. This challenge is the baseline, packaged as a contest.

## The question

You get one screen. Rank its gene sets. The scorer asks whether your ranking
predicts an **independently screened second cell line** better than ranking by set
size does.

- **Input, published:** [`data/k562_input.csv`](data/k562_input.csv) — 50 MSigDB
  Hallmark programs from the K562 arm, as `set,size,hits`. That is the plain form
  `denali_audit.adapters.detect()` already reads, alongside g:Profiler, DAVID,
  clusterProfiler, Enrichr, MAGeCK, fgsea, GSEA desktop, drugZ and BAGEL2 exports.
- **Truth, withheld from the input file:** the RPE1 arm's hit counts for the same
  50 programs. The scorer derives it at scoring time from
  `results/concordance/paired_programs.csv`. There is no answer-key file and no
  number is typed into the scorer.
- **Baseline, permanent:** rank by `size`. It never leaves the board.

## Submitting

One CSV with a `set` column and a `score` column, one row per gene set, higher
score meaning ranked higher; any other columns are ignored, so you can submit your
tool's own output table with a single column appended, and the rows may be in any
order. Put it in [`entries/`](entries/) and open a pull request — the pull request
is the submission mechanism. The scorer reruns every file in `entries/` on every
run and regenerates `board.md`, so a row that cannot be reproduced from its own
file does not survive.

## Where our own method places: fourth of four, and then first

**`denali rerank` is entered as a contestant and on the headline board it loses.**
Its size-aware residual scores a Spearman delta of **+0.0113** over the baseline —
indistinguishable from simply ranking by size — and on top-10 overlap it scores
**0.40 against the baseline's 0.60**, which is a loss, not a narrow win. The naive
"reuse the hit count you already have" entry beats both at 0.6633 and 0.80. The
worked example in `data/`, a *half*-strength correction, scores 0.6466 and 0.80, so
correcting all the way costs most of the cross-screen signal while correcting
halfway costs almost none of it.

Then there is a second table, and it inverts the first.

The board's target is RPE1's **raw** hit ranking, and that ranking is itself
size-confounded — the study measures size explaining R² 0.214 in RPE1. So a
predictor with size stripped out is scored against a target that still contains
size. Two explanations produce the first table and nothing in it separates them:
either size predicts RPE1 because the confound replicates and the metric is
contaminated, or the residual discarded real biology along with size and the
correction is simply too aggressive.

Removing size from **both** sides decides it. Against the size-removed target, the
naive hit count that won the first table falls to +0.2193 and stops being
distinguishable from chance (permutation p = 0.12); the size-only baseline goes
*negative*; and the correction is the only entrant that clears its own permutation
null, at **+0.4972, p = 0.0002**.

**Which method wins is decided by whether the target is size-corrected.** That is
this project's thesis occurring inside this project's own challenge, and it is the
result on the page — not the first table, and not the second, but the fact that
they disagree.

Two limits on how far that goes, because the flattering reading is available here
and it is not the supported one. It rules out the possibility that the correction
destroys everything: there is reproducible non-size agreement between two
independently screened cell lines. It does **not** establish that the residual is
biology — both sides of that comparison are corrected the same way, so they can
still agree for the same wrong reason, which is evaluation 6 pointed back at us.
And the first table's loss stands on its own terms: if what you want is to predict
the next screen, applying the full correction costs you, and that cost is real,
ours, and printed at the same size as everything else.

## Scope, and the one mapping this challenge refuses

**Scope limit 6 applies here and the scorer enforces it in code.** Where `hits` are
counted over the set's own members — which is what classical overlap enrichment
does, so `hits ≤ size` — regressing a count on the number of trials that produced it
recovers the trial count, and a large R² there is *arithmetic rather than a
confound*. A challenge built on that mapping would hand the size baseline a win it
did not earn.

The 50 Hallmark programs are not that mapping: `hits` counts knockdowns that moved
the program (up to 5,707) and `size` counts genes measured in the program (up to
194), so `hits` is not bounded by `size`.
`scorer/score.py::guard_scope_limit_6` asserts this and refuses to score if it ever
stops being true; `verifier/test_scorer.py` mutates it on purpose to prove the guard
fires.

The seven published screens in [`../../audits/external/`](../../audits/external/)
**do** trip scope limit 6 — they are overlap enrichment where `hits ≤ size`. They
are kept in the repository as format examples and are deliberately **not** part of
this evaluation set. If you want to see the adapters read a real supplementary
table, use those; if you want a score, use `data/k562_input.csv`.

## What this challenge is not

It does not ask which gene sets to chase, and a submission that reads as a
candidate list has inverted it. Ranking well means reproducing across two screens,
and two screens confounded the same way agree for the same wrong reason.

No gene is named here and none should be named in a submission. The unit throughout
is the gene set.

## The answers are in this repository, and that is stated rather than hidden

An offline, no-account, no-server challenge cannot hide its key: whatever the
scorer can compute, an entrant can compute. Pretending otherwise would be exactly
the unearned assurance this project exists to flag. The design makes cheating
pointless instead of impossible — the prize is a row in a markdown table, next to a
description of the method that earned it.

## Prior art

The idea of scoring an enrichment ranking against a size or degree null is not
ours. **EGAD** has shipped node-degree AUROC as a built-in null since 2017
([doi:10.1093/bioinformatics/btw695](https://doi.org/10.1093/bioinformatics/btw695));
**Crow et al., PNAS 2019** did the cross-dataset version. Running it as a public
challenge, with the baseline as a permanent row and the authors entered as a
contestant that loses, is the part that is ours.

## Verifying

```
python benchmarks/challenge/verifier/test_scorer.py    # 20 checks, incl. mutated guards
python benchmarks/challenge/build_input.py             # must leave data/ byte-identical
docker build -f benchmarks/challenge/environment/Dockerfile .
```

The verifier checks that the scorer discriminates rather than rubber-stamping: a
constant score, a missing set, a duplicate set, a non-numeric score, an infinite
score, wrong column names, unknown set names, malformed CSV, an empty file and a
missing file are each rejected; the oracle scores exactly 1.0000; and the baseline
and naive entries are required to reproduce the study's own published 0.60 and
0.6633.
