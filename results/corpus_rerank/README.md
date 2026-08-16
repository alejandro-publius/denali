# Does the correction actually move the top of a published screen?

**POST-HOC, exploratory, not pre-registered.** This arm applies the packaged
correction (`denali_audit.core.rerank`, the vendored code path, verbatim) to the
same 1,272 published screens the corpus audit measured, and counts how many of each
screen's top 10 sets keep a top-10 place once set size is regressed out. It was run
to convert the thesis from a property of one screen into a property of the
literature. What it found instead bounds the thesis, and that is the result.

---

## The question

The corpus audit found a median size-alone R² of 0.224 across published screens,
with our own screen above the 90th percentile at 0.4649. An R² is a variance share,
not a decision: what a lab acts on is the top of the list. So: in the median
published screen, how many of the top 10 entries survive a size-aware re-ranking?

## The answer: nine

| | survivors of the top 10 |
|---|---:|
| 10th percentile | 6 |
| 25th percentile | 8 |
| **median** | **9** |
| 75th percentile | 9 |
| 90th percentile | 9 |
| mean | 8.08 |

**No screen loses its entire top 10** (0 of 1,272 at zero survivors), and 65 screens
(5.1%) keep all ten. In the median published screen the size correction displaces
one entry of ten. Our own screen keeps **3 of 10 — only 2.5% of published screens
churn that hard or harder.**

## Read against our own headline, honestly

The flattering reading would have been "the literature's top-10 lists are mostly
size artifacts." The data says the opposite: a median R² of 0.224 is real but is
usually not enough to reorder the top of the list. The confound is widespread; the
*damage to the top 10* is concentrated in a tail of screens — and ours is in that
tail. Three readings, all true at once:

1. For the median published screen, the naive top 10 and the size-aware top 10
   nearly coincide. The correction is cheap insurance there, not a rescue.
2. The screens where the correction bites (3 or fewer of 10 surviving: 2.5% of the
   corpus) cannot be identified without running it. That is what the audit's R² is
   for — the two agree in direction (Spearman between size-alone R² and survivors:
   −0.267): more size-confounded rankings churn more.
3. Our own screen's 46.5% / 3-of-10 is atypical of the literature on both measures
   at once. Quoting either number as though it described published screens in
   general would overstate the field's problem by a wide margin.

## Stratified by hit-list size — and why this table must not be over-read

| hits in screen | n | median survivors | tied top-10 boundary | median R² |
|---|---:|---:|---:|---:|
| 20–100 | 118 | 8 | 96% | 0.056 |
| 100–500 | 166 | 8 | 74% | 0.184 |
| 500–2,000 | 784 | 9 | 23% | 0.226 |
| 2,000+ | 204 | 9 | 24% | 0.263 |

The corpus audit's R² gradient (stronger confound in permissive hit lists) does
**not** reappear as a survivor gradient — if anything, survival is slightly higher
where the R² is higher. These are different quantities: R² is variance across all
50 sets; survival is stability of the top 10 specifically. And the small-hit-list
rows are not evidence of churn: with 20–100 hits, hits-per-set counts tie heavily,
**96% of those screens have a tied hit count at the top-10 boundary**, and the
packaged rerank breaks ties by input order. Their lower medians are substantially
tie mechanics, not biology. Across all screens, 36.3% have a tied boundary; among
untied screens the median is 9, same as the headline.

## The screen is not the independent unit, same as before

1,272 screens come from 187 publications; each publication collapsed to its median
screen first:

| | screen-level | publication-level |
|---|--:|--:|
| n | 1,272 | 187 |
| 10th percentile | 6 | 4.3 |
| 25th percentile | 8 | 5.75 |
| **median** | **9** | **7** |
| 75th percentile | 9 | 8 |
| 90th percentile | 9 | 9 |

The correction moves the median from 9 to 7: the large multi-screen publications
sit at the stable end, and treating screens as independent overstates the
literature's stability. Both numbers are reported and neither is quoted alone.

## The estimand, precisely

The ranking corrected here is the **naive hits-per-set ordering** — the same
construction the corpus audit's R² measures — not any publication's own enrichment
ranking, which ORCS does not carry. Survivorship of a p-value-ranked list is a
different, unmeasured quantity. The rerank residualises **raw** set size (the
packaged tool's correction, vendored from the concordance arm); the corpus audit's
headline R² uses **log** size. Neither substitutes for the other.

## What would make this wrong

- **Tie handling.** 36.3% of screens have a tied top-10 boundary and the packaged
  rerank resolves ties by input order. The untied-only median (9) matches the
  headline, so the headline stands, but per-stratum numbers in the small-hit-list
  bins should not be quoted at all.
- **Top-10 is one choice.** Pre-fixed here before running (it is the number of
  candidates this project's own framing uses), but a top-3 or top-50 version could
  read differently. Not run, deliberately: choosing the cutoff after seeing data
  is the failure mode this repository exists to prevent.
- **Hallmark only, 50 sets.** With 50 sets, a random reshuffle would keep 2 of 10
  by chance; 9 is far from that floor, but collections with more sets (Reactome,
  GO-BP) have more room to churn and were not run.
- **Pseudo-replication, quantified above.** Screen-level 9 vs publication-level 7;
  anyone quoting the 9 without the 7 is quoting the flattering half.
- **Selection into ORCS.** Curated screens are not a random sample of screens run.

## Sanity gates (both passed before anything was written)

1. **Join gate**: the audited set matches the corpus audit's committed per-screen
   table row-for-row (1,272 screens), and the size-alone R² recomputed here equals
   the committed value for every screen (max |ΔR²| = 0.0).
2. **Own-screen gate**: our own screen, read through the same packaged adapters,
   lands above the corpus 90th percentile on size-alone R² (0.4649 ≥ 0.4548),
   matching the corpus audit, and its rerank reproduces the published 3-of-10.

## Reproduce it

```bash
mkdir -p data/raw/orcs && cd data/raw/orcs
curl -sL --http1.1 -A 'Mozilla/5.0' -o orcs_human.tar.gz \
  'https://downloads.thebiogrid.org/Download/BioGRID-ORCS/Release-Archive/BIOGRID-ORCS-2.0.18/BIOGRID-ORCS-ALL-homo_sapiens-2.0.18.screens.tar.gz'
# 752,653,348 bytes; the server ignores Range requests, so a truncated transfer
# must be restarted, not resumed. tar tzf must count 1953.
tar xzf orcs_human.tar.gz && cd ../../..
.venv/bin/python -m src.corpus_rerank   # writes results/corpus_rerank/
```

The URL pins release 2.0.18 rather than Latest-Release: the join gate asserts
row-for-row identity with the corpus audit's committed table, which a newer ORCS
release would break by construction.

`data/raw/` is gitignored. The outputs here are committed, and the invariant suite
recomputes the median, the zero/all-ten counts, all four strata and the
publication-level median from the per-screen table on every build.
`results/frozen/` is untouched by this arm.

## The same arm, run as distributed compute

`src/modal_corpus_rerank.py` fans this arm across Modal containers. Every screen
is independent of every other, so this is the one embarrassingly-parallel
workload in the project — and it is genuinely the same arm, not a cloud
reimplementation: the per-screen function `src.corpus_rerank.screen_row` is
imported verbatim and calls the packaged `denali_audit.core.rerank`.

```bash
modal run src/modal_corpus_rerank.py            # 1,952 files, 32 containers
```

| | |
|---|---|
| Containers | **32** |
| Wall clock | **62 s** for all 1,952 files (1,272 audited, 680 excluded, 0 unparseable) |
| Join gate, against evaluation 10 | 1,272 screens row-for-row, max \|ΔR²\| = **0.0** |
| Own-screen gate | R² **0.4649** vs corpus p90 **0.4548**, survivors **3 of 10** |
| Agreement gate, against the local run | **1,272 of 1,272 screens identical** |
| Median survivors | **9**, mean **8.08** — the same distribution |

The third gate is the one worth having. A distributed run that quietly disagreed
with the single-process run would be the most dangerous output this repository
could produce, so the per-screen survivor counts are compared row-for-row and a
single disagreement is a non-zero exit. It writes `modal_agreement.json` and
`modal_per_screen.csv` and never touches `corpus_rerank.json`: the local arm owns
that file, this one reproduces it and reports whether it agreed. Like
`src/modal_sweep.py`, it is deliberately **not** a `make all` step, and the
invariant suite asserts that for both.

**Two things this run found that a laptop would not have.** The substrate is
**uploaded** to a Modal Volume rather than downloaded in the container, because
BioGRID truncated the in-container fetch at `IncompleteRead(1036550 bytes read)`
and ignores `Range` headers, so a resumable download is not available — the same
family of truncation `docs/CORPUS.md` records for curl over HTTP/2. And the first
run left that truncated archive cached in the Volume, where a status check that
only asked *does the archive exist* would have skipped the upload forever. The
archive's sha256 is now verified in the container on every run and a wrong hash
drops the cache and re-uploads, because a cache that can be poisoned by a failed
write has to be able to notice.

**Source.** BioGRID ORCS 2.0.18, human, MIT licence. Oughtred R et al., *Protein
Science* 2021;30(1):187–200, doi:10.1002/pro.3978. Gene sets: MSigDB Hallmark
v2026.1.Hs, 50 sets.

**Scope.** Collection-level and screen-level statistics only. No screen is named,
no publication is criticised, no gene set is named as a finding, and nothing here
nominates a candidate: the count measures a property of each ranking, not of
anything in it. The unit of inference is the distribution.
