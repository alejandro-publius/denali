# How far does the finding travel?

**POST-HOC, exploratory, not pre-registered.** This exists to test our own headline
against the published literature rather than to confirm it, and the answer is that
our number is at the edge of the distribution rather than the middle of it.

---

## The question we had no right to leave open

We measured, on one screen, that program size alone explains **46.5%** of apparent
reversibility. The obvious objection is that we picked a screen where that happens to
be true. Until now the only answer we had was a second cell line and a second
annotation collection — both still our own analysis, on data we chose.

BioGRID ORCS 2.0.18 ships **1,952 curated human CRISPR screens from 418 publications**,
each with an explicit `HIT = YES/NO` column. That is the field as actually practised,
assembled by someone else, and each screen reduces to exactly the set/size/hits table
`src/audit_screen.py` already consumes. So the audit can run on all of it.

## The result

**1,272 screens** met the inclusion rule below. Their size-alone R² distribution:

| | R² |
|---|---|
| 10th percentile | 0.103 |
| 25th percentile | 0.186 |
| **median** | **0.224** |
| 75th percentile | 0.269 |
| 90th percentile | 0.455 |
| mean | 0.253 |

**Only 9.6% of published screens reach our 0.465.** A third (33.6%) clear 0.25.

The effect grows with the size of the hit list:

| hits in screen | n | median R² |
|---|---:|---:|
| 20–100 | 118 | 0.056 |
| 100–500 | 166 | 0.184 |
| 500–2,000 | 784 | 0.226 |
| 2,000+ | 204 | 0.263 |

That gradient is monotonic and it is the part we did not expect. The confound is
weakest in the small, selective hit lists and strongest in the permissive ones — which
is the opposite of reassuring, because a permissive hit list is what a genome-scale
screen usually produces and what a lab usually mines.

## Read against our own headline, honestly

**The median published screen is at 0.224, not 0.465.** Our screen sits above the 90th
percentile of the field. Three readings, and we are not going to pick the flattering
one for you:

1. Our number is real but atypical, and quoting 46.5% as though it describes screens
   in general would overstate it by roughly a factor of two.
2. The estimands are not identical (below), so the two numbers are not strictly
   comparable and the gap is partly definitional.
3. The confound is present across the literature — a median of 0.224 means that in a
   typical published screen, roughly a fifth of the ranking is predicted by set size
   with no reference to biology. That is smaller than ours and still large.

All three are true at once. What we will not say is that the corpus confirms 46.5%.

## The estimands are not the same, and conflating them would be the error this project exists to catch

| | denali's 0.465 | this corpus number |
|---|---|---|
| unit | 50 Hallmark programs | Hallmark sets, per screen |
| outcome | `R_p = log10(1 + hits at q<0.05)` over 9,837 perturbations | `log10(1 + members that were hits)` |
| predictor | `n_present`, untransformed | `log10(set members measured in that screen)` |
| scope | one deeply-sampled Perturb-seq screen | 1,272 screens of every design |

A smaller number here does not falsify ours. It bounds how far ours travels, which is
a different and more useful thing.

**The predictor transform matters, and we measured how much.** The corpus headline
uses log size; `src/audit_screen.py` uses raw size. Rerunning the corpus with the raw
predictor moves the median from **0.224 to 0.192** (reported in
`results/corpus/corpus_audit.json` as `median_r2_raw_size_predictor`). Neither is
"the" number — the sensitivity is itself part of the result, and it is one reason
independent implementations of this idea should be expected to land in different
places.

## What would make this wrong

- **Heterogeneous hit definitions.** Every publication set its own significance
  threshold, captured in ORCS as `SIGNIFICANCE_CRITERIA`. Hit rates therefore vary by
  orders of magnitude across screens. Stratifying by hit-list size (above) is a partial
  control, not a fix.
- **An independent run of the same idea disagreed.** A separate execution reported a
  median near **0.10** over ~1,673 screens, with non-monotonic strata. We could not
  reconcile the two, and we report ours because it is the one whose code and inclusion
  rules are in this repository and reproducible. The transform sensitivity above is a
  candidate contributor, not a demonstrated reconciliation. **Neither number should be
  quoted as "the field's value."** The qualitative conclusion — our screen is atypical,
  the confound is widespread but weaker elsewhere — survives both.
- **Hallmark only.** Reactome and GO-BP would widen the size range considerably, and
  our own annotation arm suggests that changes the picture. Not run here.
- **Selection into ORCS.** Curated screens are not a random sample of screens run.

## Reproduce it

```bash
mkdir -p data/raw/orcs && cd data/raw/orcs
curl -sL --http1.1 -A 'Mozilla/5.0' -o orcs_human.tar.gz \
  'https://downloads.thebiogrid.org/Download/BioGRID-ORCS/Latest-Release/BIOGRID-ORCS-ALL-homo_sapiens-LATEST.screens.tar.gz'
tar tzf orcs_human.tar.gz | wc -l     # must be 1953
tar xzf orcs_human.tar.gz && cd ../../..
python -m src.corpus_audit            # writes results/corpus/
```

⚠ **Over HTTP/2 curl truncates this file at ~70 MB and exits 92.** Use `--http1.1`.
The integrity check above is not optional — a truncated tarball parses fine and
produces wrong numbers silently. Expect 752,653,348 bytes.

`data/raw/` is gitignored; the substrate is documented here, not committed. The
outputs in `results/corpus/` are committed, and the invariant suite recomputes the
median, the 9.6% figure and all four strata from the per-screen table on every build.
`results/frozen/` is untouched by this arm.

**Inclusion rule, stated in `src/corpus_audit.py` and enforced by an invariant:** a
screen is audited if it reports at least 20 hits, measured at least 10,000 genes, and
yields at least 8 sets with 5 or more measured members. **680 of 1,952 screens fail
that rule** (0 failed to parse), overwhelmingly because they are targeted rather than
genome-scale.

**Source.** BioGRID ORCS 2.0.18, human, MIT licence. Oughtred R et al., *Protein
Science* 2021;30(1):187–200, doi:10.1002/pro.3978. Gene sets: MSigDB Hallmark
v2026.1.Hs, 50 sets.

**Scope.** Collection-level and screen-level statistics only. No screen is named as
confounded, no publication is criticised, and no gene set is named as a finding. The
unit of inference is the distribution, and an invariant scans this document for
screen and publication identifiers the same way the gene-symbol guard scans the page.
