# Which correction should a biologist actually use?

**Pre-registered** in `docs/CORRECTIONS_PREREG.md` (`d58fa082…`, commit
`a2776f7`), written and hashed **before the substrate was downloaded**. Post-
deadline extension work; `results/frozen/` and `results/corpus/` untouched.
All numbers: `results/corrections/summary.json` and `per_screen.csv`.

---

## The question nobody had answered

The literature has proposed fixes for the size confound for fifteen years —
CAMERA's variance inflation (Wu & Smyth 2012, doi:10.1093/nar/gks461),
size-preserving permutation nulls, and the ordinary hypergeometric test that
most enrichment tools actually ship. denali cites CAMERA as the theory it
recovered empirically. **Nobody had measured how much of the size dependence
each correction removes on a large corpus of real screens, or how often one
makes things worse.**

Six corrections, **1,272 published CRISPR screens**, one table.

## The gate, before any correction number was read

The pre-registration required this pipeline to reproduce the committed corpus
arm before it was allowed to report anything. It does, on **1,272 of 1,272
screens**: median size-alone R² **0.2244** against the published 0.224, and
**0.19185** against the published raw-size 0.192. The corrections below are
computed by the same code path that reproduces the published numbers exactly.

## The result

Primary metric: **squared Spearman correlation between the ranked statistic
and set size** — how much size dependence survives the correction. Rank-based
so that corrections emitting incomparable scales can be compared, and so that
denali's own linear residualisation is not handed a win by construction.
Baseline median across the corpus: **0.106**.

| | correction | median reduction in size dependence | screens made worse | verdict |
|---|---|---:|---:|---|
| C1 | ORA hypergeometric — the field's default | 0.574 | 0.7% | **WORKS** |
| C2 | size-preserving permutation null (standardised) | 0.229 | 13.4% | PARTIAL |
| C3 | competitive score test, CAMERA at ρ̄ = 0 | 0.028 | 18.2% | **FAILS** |
| C4 | CAMERA with variance inflation, ρ̄ = 0.01 | 0.616 | 1.5% | **WORKS** |
| C4 | CAMERA with variance inflation, ρ̄ = 0.05 | 0.847 | 1.8% | **WORKS** |
| C5 | denali's own residualisation | **0.857** | **6.3%** | WORKS ON MEDIAN, **UNRELIABLE TAIL** |

Collapsing each publication to its median screen first — the pseudo-replication
correction the corpus arm already applies to itself — moves every reduction up
to the 0.90–0.96 band and does not change the ordering.

## The negative we are obliged to report

The pre-registration committed us in advance: *if denali's own correction
loses to a published method, the report must say the tool should recommend
that method rather than itself.* Here is the honest accounting.

**On the registered primary metric, denali's own residualisation wins** — its
median reduction of 0.857 is the highest in the table, edging CAMERA-VIF at
ρ̄ = 0.05 (0.847). The literal obligation does not fire.

**On reliability, it loses, and we are saying so.** C5 makes **6.3%** of
screens worse — nearly **four times** CAMERA-VIF's 1.8%, for a median gain of
one percentage point. It is the only method in the table that clears the
median bar and fails the tail bar, which is why its verdict reads WORKS ON
MEDIAN, UNRELIABLE TAIL.

**So the recommendation is CAMERA's variance-inflated competitive test, not
ours.** It is nearly as good at the median, three to four times safer in the
tail, and it is the method the literature has been recommending since 2012.
`denali rerank` is a fast diagnostic that usually agrees with it; it is not
the best available correction, and the tool should not present itself as one.

**C3 fails, and it is the same method as C4 without the inflation.** A
competitive score test with ρ̄ = 0 removes almost nothing (median 0.028) and
makes 18.2% of screens worse. Setting ρ̄ to a small positive number turns the
worst method in the table into the best-behaved one. That is Wu & Smyth's
entire 2012 argument, reproduced across a thousand screens that were run
without reference to it: **the inflation term is the correction. The
competitive framing alone is not.**

## The finding a practitioner will care about most

**A correction changes the size dependence far more than it changes who is at
the top of your list — except exactly where it matters.**

Median overlap between the uncorrected top ten and the corrected top ten,
stratified by how confounded the screen was to begin with:

| baseline size dependence | n screens | hypergeometric | CAMERA-VIF ρ̄=0.05 | denali residual |
|---|---:|---:|---:|---:|
| < 0.05 | 122 | 8/10 | 3/10 | 8/10 |
| 0.05 – 0.10 | 427 | 9/10 | 9/10 | 9/10 |
| 0.10 – 0.20 | 518 | 9/10 | 9/10 | 9/10 |
| **> 0.20** | **205** | **7/10** | **3/10** | **6/10** |

In the typical screen the top ten barely moves, because Hallmark hit counts
are small integers with heavy ties and the same sets stay on top. In the
**most confounded fifth of the corpus, applying CAMERA-VIF replaces seven of
your top ten**. If you are going to check one thing before committing a year
to a hit list, check whether your screen is in that stratum.

## What this cannot tell you

**Driving the size correlation to zero proves size-decoupling, not
correctness.** A correction that deleted all biology would score perfectly on
every metric in this document. There is no ground truth in this corpus and we
are not going to pretend otherwise: nothing here says any correction produces
*right* answers, only how much size dependence survives it.

Other limits, stated because they bound the table:

- **ρ̄ is assumed, not measured.** Inter-gene correlations cannot be computed
  from ORCS hit tables, so C4 uses fixed ρ̄ = 0.01 and 0.05. This is the arm's
  main limitation and it was declared in the pre-registration, not discovered
  afterwards. The gap between those two values (0.616 → 0.847) shows how much
  the assumption carries.
- **C3/C4 read `SCORE.1`**, whose meaning differs across screens; that
  heterogeneity is part of why the uninflated test performs badly.
- **GOseq and SetRank are N/A**, declared in advance: GOseq corrects a per-gene
  covariate (transcript length), SetRank corrects inter-set overlap. Neither
  targets set size, and neither was quietly dropped after the fact.
- **The screen is not the independent unit.** Every distribution above is also
  reported publication-collapsed in the JSON, and neither is quoted alone.
- Hallmark only, 50 sets per screen. Reactome or GO-BP would widen the size
  range considerably.

## Reproduce

```bash
mkdir -p data/raw/orcs && cd data/raw/orcs
curl -sL --http1.1 -A 'Mozilla/5.0' -o orcs_human.tar.gz \
  'https://downloads.thebiogrid.org/Download/BioGRID-ORCS/Latest-Release/BIOGRID-ORCS-ALL-homo_sapiens-LATEST.screens.tar.gz'
tar tzf orcs_human.tar.gz | wc -l     # must be 1953; expect 752,653,348 bytes
tar xzf orcs_human.tar.gz && cd ../../..
.venv/bin/python -m src.corrections_audit
```

⚠ Over HTTP/2 curl truncates this file and exits 92 — use `--http1.1`. A
truncated tarball parses fine and produces wrong numbers silently.

**Scope.** Collection-level statistics only. No screen, publication or gene
set is named as a finding; the unit of inference is the distribution.
