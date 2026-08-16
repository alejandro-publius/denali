# Breadth probe (a) — REGION SETS (ChIP-seq / genomic interval enrichment)

> ### ⚠ Read `../README.md` first — this arm's R² does not clear its own null
>
> This file was written before the no-biology baseline was computed. Adversarial review
> of it, and `../null_baselines.py`, established that where `hits` are drawn from the
> set's own members (`hits ≤ size`), a large size-alone R² is **expected under pure
> counting** — so the values below are **not** by themselves evidence of a confound.
> Every number here reproduces exactly and the provenance survived checking; it is the
> interpretation that is superseded. The synthesis, the correct null per mapping, and
> what survives are in [`../README.md`](../README.md).


**POST-HOC AND EXPLORATORY. Nothing in this directory was pre-registered.**
The unit of inference is the *distribution*. No individual experiment, antigen, cell
type, factor or genomic region is named as a finding, as confounded, or as a candidate,
and nothing here is a clinical, wet-lab or therapeutic recommendation.

Run date: 2026-08-16 (UTC).

---

## The question

Region-set enrichment has the same shape as gene-set enrichment: many sets, wildly
varying member counts, an overlap statistic. Does the size confound appear?

## Prior art — READ THIS BEFORE READING THE NUMBERS

This confound is **not** an unknown in this field. It is one of the field's founding
methodological results, and the correction is standard practice in the good tools:

- **GREAT** (McLean et al., *Nat Biotechnol* 2010) exists *because* the naive
  gene-based hypergeometric test is biased by regulatory-domain size — genes in gene
  deserts win simply because deserts are large. GREAT replaces it with a binomial test
  over genomic space that explicitly accounts for regulatory-domain size, and ranks by
  that binomial p-value by default. `rGREAT` (Gu & Hübschmann, *Bioinformatics* 2023)
  carries this into R/Bioconductor.
- **ChIP-Enrich** (Welch et al., *NAR* 2014) and **Broad-Enrich** (*Bioinformatics*
  2014) empirically model the gene-locus-length → peak-presence relationship, precisely
  because Fisher's exact test on peak/gene overlap has inflated type-I error and biased
  ranking when locus length varies.
- **LOLA** (Sheffield & Bock, *Bioinformatics* 2016) makes the *region universe* a
  first-class, user-specified argument — the background of regions that could in
  principle have been in the query — which is the size-control lever in that framework.
- **regioneR** / **GenomicRanges** permutation nulls and **`bedtools fisher`** give
  size- and length-preserving randomisation as the standard non-parametric answer.

So: **the gap is not that the field lacks a correction.** The gap this probe can speak
to is narrower and empirical — *how much size structure is still sitting in the overlap
tables that a widely used public web tool hands to users, and in the ranking those users
then read.* If you take one thing from this directory, take the prior art, not the R².

## Data provenance (exact)

Everything came from the ChIP-Atlas public object store, `https://chip-atlas.dbcls.jp/data/`
(S3/MinIO-compatible, anonymous listing).

| what | how | verified |
|---|---|---|
| `https://chip-atlas.dbcls.jp/data/metadata/experimentList.tab` | HEAD only → `HTTP 200`, `Content-Length: 344,939,718`, `Last-Modified: Wed, 01 Oct 2025`. Byte-range `0-400000` pulled (`HTTP 206`, 400,001 B) → `head_expList.tab`, used only to read the schema. | yes |
| bucket key listing, prefix `enrichment-analysis/` | 3 paginated `?max-keys=1000` listings → 3,000 keys → `bucket_keys.json`; 574 job folders carrying a `.result.tsv` | yes |
| 188 job config JSONs (folders with a non-trivial uploaded `bedAFile_*.bed`) | `raw/json/*.json`, 752 KB total, 1 of 189 returned HTTP 000 and was dropped | yes |
| **94** of those with `typeA == "bed"` (a genuine genomic-region-set query) → their `*.result.tsv` | `raw/tsv/*.tsv`, **107 MB**, every file byte-count-checked against the size the bucket listing declared (94/94 exact). 7 of the 94 are **0 bytes on the server** — those jobs produced no output — and are excluded. | yes |

`head_expList.tab` schema, worked out empirically from the first rows (columns are
unlabelled in the file): 1 experiment accession (SRX/DRX/ERX) · 2 genome assembly ·
3 antigen class · 4 antigen · 5 cell-type class · 6 cell type · 7 cell-type description ·
8 processing log `reads,%mapped,%duplicates,n_peaks` · 9 title · 10+ `key=value`
sample attributes. **This file alone gives peak counts and no overlap statistic — i.e.
size with no hits, and therefore NO DEFENSIBLE NUMBER on its own.** It is not the basis
of any R² below. The enrichment result TSVs are.

`*.result.tsv` schema — column labels were **read off the `<th title=...>` tooltips in
the sibling `*.result.html`**, not guessed:

| col | label | meaning |
|---|---|---|
| 1 | ID | experiment accession |
| 2 | Experiment type | antigen class |
| 3 | Feature | antigen |
| 4–5 | Cell class / Cell | cell annotation |
| 6 | **Num of peaks** | "Number of peaks called for the accession ID at column 1" |
| 7 | **Overlaps / Dataset A** | `x/N` — x entries of the user's query set overlapped, N = query-set size (constant down the file) |
| 8 | Overlaps / Dataset B | `y/M` — same against the control set |
| 9 | Log10 P-val | Fisher exact, col 7 vs col 8 |
| 10 | Log10 Q-val | Benjamini–Hochberg |
| 11 | Fold Enrichment | ratio of the col-7 rate to the col-8 rate |

## The mapping onto the audit contract

    set   = one ChIP-seq / ATAC-seq / Bisulfite-seq experiment (an antigen in a cell type)
    size  = col 6, the number of peaks that experiment called   <- construction quantity
    hits  = col 7 numerator, query regions that experiment recovered  <- result quantity

Both numbers are **read from the file**. Neither is invented.

`audit()` is run **once per user job** (one job = one query region set evaluated against
the whole ChIP-Atlas experiment universe), giving a *distribution* of R² over jobs
rather than a single headline.

### Assumptions, stated so a reviewer can poke them

1. **Orientation.** The brief's natural mapping wanted `hits` = "how many of that
   experiment's peaks overlap the query". ChIP-Atlas reports the transpose: how many of
   the **query's** regions were hit. Both are honest per-set result quantities and both
   are bounded above by the peak count, so both carry the same construction-quantity
   exposure — but they are **not the same number**, and this audit is run on the one the
   file actually contains. This is the single largest thing to poke.
2. **`hits` saturates at the query-set size N** (median N = 736 regions). A very large
   peak set can hit all N and go no higher. That *compresses* the size–hits relationship
   at the top, so it biases R² **down**, not up.
3. Each job's sets share one query set, one genome and one peak-calling threshold, so
   within a job the sets are commensurable. Across jobs they are not, which is why
   nothing is pooled.
4. Jobs are user-submitted and self-selected. This is a convenience sample of ~90 real
   analyses out of the 574 jobs whose output happened to be listed in the first 3,000
   bucket keys — not a random sample of the field.
5. Rows are deduplicated on experiment accession within a job; only `[SDE]RX\d+` IDs
   are kept.
6. Five jobs returned **every set at zero hits** (query BED overlapped nothing at all —
   almost certainly an assembly or chromosome-naming mismatch upstream). The hit vector
   is constant, R² is undefined, `audit()` returns `nan`, **and its verdict field then
   falls through to `NOT SIZE-DOMINATED`, which would be a false clean bill of health.**
   They are split out and excluded from every M1 statistic.

## Mappings run (all of them, not just the flattering one)

| id | mapping | n jobs | median R² | verdict spread |
|---|---|---|---|---|
| **M1** | size = peak count, hits = query regions recovered | 82 | **0.4035** (IQR 0.282–0.499; range 0.0001–0.779) | 41 CONFOUNDED / 25 PARTIAL / 16 NOT |
| **M2** | size = peak count, hits = overlap with the job's **control** set (68/86 of which are randomised regions, `typeB = "rnd"` — no biology in them at all) | 86 | **0.5845** (0.591 on the randomised-only subset) | 65 CONFOUNDED / 14 PARTIAL / 7 NOT |
| **M3** | descriptive only, **not** `audit()` output: Spearman of peak count vs the statistics a user actually ranks on | 82 | ρ(size, log Q) = **−0.61** (IQR −0.76…−0.40); ρ(size, fold enrichment) = **+0.31** (IQR 0.03…0.46) | — |
| **M-null** | `experimentList.tab` alone: peak counts, no overlap statistic | — | **NO DEFENSIBLE NUMBER** | size with no hits; not attempted |

M3 is reported because log Q is what the ChIP-Atlas table sorts on by default. Log Q is
negative-is-more-significant, so ρ ≈ −0.61 means experiments that called more peaks
receive more significant Fisher p-values. The **effect-size** column (fold enrichment)
tracks size far less (ρ ≈ +0.31) — that difference is the most actionable thing here.

Stratified by experiment type (a stratum, not a candidate): median M1 R² is lower for
the transcription-factor stratum than for the chromatin-accessibility, histone-mark and
polymerase strata. Reported as a distributional stratification only.

## Where this falls against the denali CRISPR corpus (1,272 screens)

Corpus: p10 0.1026 · p25 0.1862 · **median 0.2244** · p75 0.2689 · p90 0.4548;
only 9.6% of published screens reach denali's own 0.465.

- M1 median **0.4035** → roughly the **86th percentile** of the CRISPR corpus
  (linear interpolation between corpus p75 and p90).
- **79%** of region-set jobs exceed the CRISPR corpus *median*.
- **43%** exceed the corpus *p90*, and **39%** reach or exceed 0.465 — the level only
  9.6% of published CRISPR screens reach.

So the confound is, if anything, **more visible in region-set enrichment than in the
CRISPR corpus** — while being, unlike in the CRISPR corpus, a *named and long-solved*
problem in this field's methods literature. Both halves of that sentence matter.

## Replication arm

`audit_replication()` was run on **496 pairs of distinct user jobs** that share a
genome and a peak threshold (hence an identical set universe and identical `size`
vector, verified elementwise) but submitted different query BEDs — i.e. two independent
"screens" over the same sets. Pairs whose uploaded BED had an identical byte count were
excluded as probable resubmissions of the same query. Median 5,460 paired sets.

- median raw agreement (Spearman) **0.600**
- median agreement after regressing out log size **0.110**
- median **51%** of the apparent agreement is set size (IQR 12%–77%)
- restricted to the 368 pairs where |raw agreement| ≥ 0.20 — the ratio is unstable when
  raw agreement is near zero and can even go negative — the median is **64%**
  (IQR 39%–81%)

Caveat: these are two different queries against one shared experiment universe, not two
independent replicates of one experiment. It measures how much of "the same experiments
come up for both of us" is explained by those experiments simply having more peaks.

## Files

- `audit_regions.json` — the audit output summary (all mappings)
- `per_job_audit.csv` — one row per job: full `audit()` output for M1 and M2, plus M3
- `set_size_hits.csv.gz` — the standardized table, 1,226,499 rows:
  `job, set, size, hits, hits_control, log_q, fold`
- `replication_pairs.csv` — 496 `audit_replication()` outputs
- `build_table.py` — the script; imports `audit`/`audit_replication` unmodified
- `job_configs.json`, `jobs_index.json`, `bucket_keys.json` — provenance indices
- `raw/json/`, `raw/tsv/` — the downloaded source files (byte-verified)
- `head_expList.tab`, `h1.html`, `j1.tsv`, `j1.json` — schema-inspection samples

## Limitations

- Convenience sample of user-submitted jobs; not a random or complete sample.
- The orientation caveat (assumption 1) is not cosmetic — a reviewer should treat M1 as
  "size vs. recovered query regions", not "size vs. peaks overlapping".
- Hit saturation at the query-set size biases R² downward.
- One tool, one database. ChIP-Atlas's Fisher test is *already* a comparison of the
  query rate against a control rate; the residual size structure measured here is
  power, not effect — which is exactly why M3's split between log Q and fold enrichment
  is the useful number.
- Nothing here evaluates GREAT, LOLA, regioneR or ChIP-Enrich outputs. Their corrections
  are cited, not tested. This probe cannot say whether those corrections are sufficient.
- Post-hoc. No pre-registration. No multiple-testing control across the 82 jobs.
