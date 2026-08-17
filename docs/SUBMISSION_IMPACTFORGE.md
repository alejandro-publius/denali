# denali — technical writeup

> **Written from scratch, 2026-08-16.** A drafted version of this file was
> referenced in the handoff but is not present in the repository, so this is
> not that draft. Every number below is carried from `results/` and enforced by
> the invariant suite; if a figure here disagrees with the repo, the repo is
> right and this file is stale.

**Repo:** https://github.com/alejandro-publius/denali · **Live:** https://alejandro-publius.github.io/denali/
**Install:** `pip install -e packages/denali-audit` → `denali audit my_results.csv`

---

## The problem

A gene-set enrichment table is the output that decides what a lab does next. You
run a screen, you ask which pathways came back enriched, you get a ranked list,
and you pick from the top. Validating one entry on that list costs roughly a
year and six figures.

**The ranking is substantially an artifact of how the gene sets were drawn.** A
200-gene set returns more hits than a 30-gene set regardless of what either does
— the way a raw crime count always ranks big cities as the most dangerous. The
mechanism is not subtle and it is not new: Wu & Smyth described the variance
inflation behind it in 2012 (CAMERA, `doi:10.1093/nar/gks461`). What was missing
was a number for what it costs you on a real screen, and a way to check your own.

On a published genome-scale CRISPRi Perturb-seq screen (Replogle et al., K562,
9,837 knockdowns × 50 MSigDB Hallmark programs), **set size alone explains 46.5%
of the variance** in which programs look reversible, and a six-feature model
that never looks at what a program *does* explains **56–75%**.

That is not a claim about one screen. Run on seven other groups' published
supplementary tables — CRISPR knockout, CRISPRi/a, single-cell CRISPRa, organoid,
primary human T cell, bulk RNA-seq — **36–88% of each ranking** is explained by
set construction alone. Across **1,272 published screens** from BioGRID ORCS the
field's median is **0.224**.

## What it does

`denali audit` takes the table your analysis already produced and returns three
things:

1. **A verdict** — `CONFOUNDED`, `PARTIALLY CONFOUNDED`, or `NOT SIZE-DOMINATED`.
2. **A percentile** against those 1,272 screens. An R² is not a judgement until
   you know what normal looks like. On our own screen it reports *"worse than
   nine in ten published screens"* — the tool says that about us.
3. **A correction.** `denali rerank` applies it and shows what leaves your top N.

**On our own screen, three of the top ten hold and seven do not.**
`HALLMARK_MYC_TARGETS_V1` — the largest set in the collection at 194 measured
members, ranked first, most hits — **falls to twenty-fourth**. It is the single
most demonstrable thing this project owns, and it is a demotion of our own
headline entry rather than someone else's.

It refuses to go further. The output says so in as many words: *"Not a candidate
list. This says which entries were carried by size, not which to chase."* A tool
that turned a confound estimate into a shortlist would be committing the error it
exists to detect.

Six formats are auto-detected — g:Profiler, DAVID, clusterProfiler,
Enrichr/GSEApy, fgsea, GSEA desktop — because the reason a check like this never
gets run is that it asks you to reshape your data first.

## The stack

Deliberately boring where it touches a number.

| Layer | Choice | Why |
|---|---|---|
| Statistics | Mann–Whitney signed-z, Benjamini–Hochberg FDR, OLS | No neural model anywhere in the scoring path. Every quantitative claim is owned by deterministic code. |
| Runtime | Python 3.12.0, **exact** pins (numpy 2.5.2, pandas 3.0.5, scipy 1.18.0, h5py 3.16.0, statsmodels 0.14.6) | Not floors. numpy 2.x and pandas 3.x both changed default behaviour that moves results. |
| Package | `packages/denali-audit`, deps `numpy>=1.26, pandas>=2.1.1, scipy>=1.11` | Loose on purpose — the tool must install next to whatever a stranger already has. The *study* is pinned; the *tool* is portable. The floors are **tested**, not declared: the full suite runs green at exactly those versions, three majors below what the study pins. |
| Distribution | Static page with every asset inlined; MCP server; Streamlit view | The page makes **zero network calls** and renders offline from one file. |
| Compute | Modal for the 50-program sweep across 10 containers | Reproduces the frozen numbers rather than producing them — deliberately not a `make all` step, and a test asserts that. |
| Verification | The invariant suite + the cross-surface suite, CI on every push, plus the packaged tool's own tests | The suite **counts itself** and the README states that count in three places; all fail the build on disagreement. Exact totals deliberately not repeated here — a number restated in prose is a number that goes stale, which this file did. |

## What was hard

**Four guards passed while testing nothing.** One was gated on data a clean clone
does not have. One was keyed to a commit a rebase had erased. One matched markup
that had been rewritten. One was the counter itself, carrying a hand-maintained
offset so checks added below it were silently uncounted. All four passed —
because a skipped check and a passing check look identical in the output. They
are now content-addressed rather than reference-addressed, and the mechanism that
caught two of them is the suite counting itself: a skipped check still changes
the total.

**Twice a reproduction looked verified and was not.** Once the 470 MB substrate
had been moved off the machine, so `make check` failed and the run printed an
empty diff having executed nothing — an empty diff from a run that never happened
is indistinguishable from a pass. Once a result measured at one commit was
assumed to hold at `HEAD` after `src/build_page.py`, which `make all` invokes, had
changed underneath it.

**A question broke the headline and we kept the question.** Three of the six
"measurability" features are properties of the gene *set*, not of our measurement.
Split apart: measurement features alone give adjusted R² **0.152**;
set-construction features alone give **0.697**. Set size by itself beats all three
measurement features combined, three times over. The number stood; the word
*measurement* did not.

**Our own quality filter was wrong 20 times out of 50.** We built the gate anyone
would build, then checked it against all 50 programs rather than only the ones it
approved. Twenty fail it and produce hits anyway; exactly one passes and produces
nothing. The held-out program fails our own filter and ranks 11th of 50 with 773
hits. We would have discarded our best result.

**Guide-pair concordance came back at −0.019** — two independent reagents against
the same gene disagree — which forbids gene-level claims outright. So the project
names **no novel gene anywhere**, and that is enforced by a test rather than by
good intentions.

**The MCP server worked from exactly one directory: the one we always demonstrated
it from.** It resolved `results/frozen/` against the caller's working directory,
so every real client would have gotten `FileNotFoundError`. Found by starting it
from `/tmp` the way a stranger's client does.

## What keeps the tool and the study honest

`packages/denali-audit/core.py` is the study's own maths vendored verbatim, not a
reimplementation. **A test runs the packaged `audit()` against the frozen research
data and requires exactly `0.4649`** — the published headline. If the tool and the
paper ever disagree, CI fails rather than the README continuing to cite a number
the shipped code no longer produces.

Separately, the headline was **recomputed by a second implementation written from
the README's method section**, without reading the original scoring code, using
scipy's Mann–Whitney and statsmodels' BH and OLS in place of the frozen path's
own. Agreement: **Pearson 1.000000** across all 50 programs, hit counts identical
as integers, all three published figures reproduced. That rules out
implementation error in the frozen scorer. It does **not** establish that the
method is correct — two implementations of a wrong method agree with each other
perfectly, and that limit is stated wherever the result appears.

## What it does not claim

- **No experiment was run.** The loop closes against data, not against a cell.
- **The predictor failed its held-out test** — balanced accuracy 0.4375, worse
  than chance, zero true positives — and was not refit. Reported as a failure.
- **One cell line, unstimulated.** K562 has no ER stress, which is why our own
  first program failed its known-regulator control.
- **Thirteen evaluations, seven negative**, one with no verdict because our own
  pre-registered power rule fired. All thirteen are reported, including the one
  that found our headline atypical of the field and cost us the number.
