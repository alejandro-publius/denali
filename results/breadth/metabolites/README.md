# Breadth domain (b): metabolite sets

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
No threshold, mapping, stratum or sweep point below was declared in advance. Every
number here is descriptive. This does not revise anything in `results/frozen/`.

**Unit of inference is the distribution.** No pathway, compound, metabolite or
metabolite class is named as a finding, as confounded, or as a candidate anywhere in
these outputs. Set identifiers in `sets_standardized.csv` are deliberately replaced
by salted opaque tokens (`set_<10 hex>`, SHA-256 with a fixed salt) so that no row
can be read as a statement about a specific pathway. The recipe below regenerates
the un-anonymised join for anyone who wants to check the arithmetic.

No clinical, wet-lab or therapeutic recommendation is made or implied.

---

## Files

| file | what it is |
|---|---|
| `metabolite_audit.json` | every `audit()` call: n, size range, R2, Spearman, zero-hit count, verdict, corpus percentile; plus both `audit_replication()` arms and the two detection-threshold sweeps |
| `sets_standardized.csv` | the standardized long table — one row per (mapping, set): `mapping, family, set_token, size, hits`. 4,678 rows across 51 audit calls |
| `analyze.py` | the script that produced both. Imports `denali_audit` unmodified; no maths is reimplemented here |

---

## Provenance (all fetched 2026-08-16, HTTP 200, byte counts verified before parsing)

| source | URL | bytes | sha256 (first 16) |
|---|---|---|---|
| KEGG human pathway list | `https://rest.kegg.jp/list/pathway/hsa` | 22,117 | `345290b203a665fa` |
| KEGG pathway→compound | `https://rest.kegg.jp/link/compound/pathway` | 490,375 | `8d2be4ce10a86b46` |
| SMPDB metabolite membership | `https://smpdb.ca/downloads/smpdb_metabolites.csv.zip` | 166,931,160 | `0fb3d4c23325b064` |
| Metabolomics Workbench study index | `https://www.metabolomicsworkbench.org/rest/study/study_id/ST/summary` | 2,604,844 | `f45ad9bc2f914f90` |
| RefMet full dump | `https://www.metabolomicsworkbench.org/rest/refmet/all` | 43,783,846 | `eab61cc098578837` |
| MW per-study metabolite lists | `.../rest/study/study_id/<ID>/metabolites` × 500 sampled human studies | 22 MB total | — |

Counts as parsed:
- KEGG: 372 human pathways listed; 464 reference maps carry compound links; **305 human
  pathways have ≥1 compound**. KEGG only publishes compound membership at the `map`
  (reference) level, so `hsaNNNNN` was joined to `mapNNNNN` by ID.
- SMPDB zip: 48,687 per-pathway CSVs, file dates 2018-09 (this is the current published
  download; the membership data is 2018-vintage). Subject counts: Metabolic 27,875,
  Disease 20,247, Drug Action 397, Protein 76, Drug Metabolism 64, Signaling 10,
  Physiological 5.
- MW: 4,479 studies indexed, **1,815 human**; 500 sampled (seed 20260816); 384 returned a
  non-empty metabolite table; **358 resolved at least one metabolite to a structure**.
- RefMet: 208,024 rows, of which **35,489 carry an InChIKey**. The remainder are lipid
  species names with no structure record and are unusable for a structure join.

**Attempted and blocked:** `https://hmdb.ca/system/downloads/current/serum_metabolites.zip`
returned **HTTP 403**. The "detected/quantified in blood" HMDB list — the most direct
platform-coverage list — was therefore not available, and the measured list had to be
rebuilt from Metabolomics Workbench instead. This is disclosed because it changes what
"measurable" means here (see Assumption 4).

**Not obtained:** no published metabolomics enrichment table with per-set
`Total / Hits / Raw p` columns was located and downloaded. **Every mapping in this
directory is therefore a COVERAGE mapping, not a differential-abundance one.** See
"What this is not" below.

---

## What "size" and "hits" mean here

- `size` = the number of metabolites the set declares. Construction quantity, taken
  verbatim from the source database.
- `hits` = the number of those declared members that a real human metabolomics
  experiment actually detected. **This is annotation/platform COVERAGE, not
  significance.** It is the same shape of question denali already asked of GO-BP:
  how much of a set-level result is fixed before any biology enters.

No per-set hit count was invented. Where a mapping could not produce one, the row is
absent rather than filled in.

---

## Set collections

**SMPDB curated metabolic pathways — n = 98, sizes 4–73 (18.25×), median 24.**
(Sizes are counted as distinct InChIKey skeleton blocks, so a pathway listing the same
skeleton twice under two stereo forms counts it once; the raw member-row count tops out
at 74.)
SMPDB's "Metabolic" subject contains 27,875 entries, but ~99.6% are combinatorially
auto-generated lipid-species templates (the same skeleton re-emitted once per acyl-chain
combination). Those are near-duplicate clones and would have made the collection look
far larger than it is. They were removed by dropping any pathway whose name contains a
parenthetical with a digit; 98 curated pathways remain. **This filter is a judgement
call and is the single most contestable step in the join** — a reviewer should poke it
first. Keeping the clones would inflate n from 98 to ~27,875 with essentially 15 distinct
size values, which is not a real sample.

**KEGG human pathways — n = 216 after excluding global/superpathway maps and pathways
with <5 compounds; sizes 5–148 (29.6×).** Excluded global maps: `hsa01100, 01110, 01120,
01200, 01210, 01212, 01220, 01230, 01232, 01240, 01250, 01310, 01320`. One variant (`B3`)
retains all 305 with no exclusions, to show what those maps do to the fit.

Both collections sit far below Hallmark's 32–200. That is the point of this domain.

---

## Assumptions (a reviewer should attack these in order)

1. **The MW study metabolite table = "detected".** Metabolomics Workbench lists the
   metabolites a study reported. Absence from that table is treated as not-detected. It
   could equally mean not-targeted, not-reported, or filtered before submission.
2. **Structure join is on the InChIKey skeleton block (first 14 characters).** Full-key
   matching would drop stereochemistry and protonation-state mismatches that are the
   same compound in practice; skeleton matching over-merges stereoisomers. Skeleton
   matching was chosen, and it is a choice that inflates hits slightly.
3. **MW metabolite → RefMet name → InChIKey is a two-hop resolution.** Only 35,489 of
   208,024 RefMet rows carry an InChIKey, so any study metabolite whose RefMet name has
   no structure record is silently dropped. 358 of 384 non-empty studies survived. The
   resulting union is **6,443 distinct InChIKey blocks**.
4. **"Measurable" here means "measured somewhere in a 358-study human convenience
   sample", not "on a defined analytical platform".** The HMDB blood list that would
   have given a platform-anchored answer returned 403. The union is therefore biased
   toward whatever MW depositors happened to study.
5. **KEGG compound → structure runs through SMPDB.** SMPDB supplies only 1,310
   KEGG-ID↔InChIKey pairs. A KEGG compound with no SMPDB crosswalk entry **can never
   score a hit**, so every KEGG mapping is a *floor*, not an unbiased estimate. The
   `B2` variant makes this explicit by auditing that crosswalk coverage on its own.
6. **SMPDB membership includes ubiquitous cofactors** (ATP, NAD, water-adjacent
   species). Those are trivially "detected", which is exactly why the saturated
   variants behave the way they do.
7. **Set members overlap between pathways in both collections.** No adjustment was
   made; the overlap is part of what is being measured, disclosed rather than removed.
8. **SMPDB membership is 2018-vintage; MW detection is 2026-vintage.** A metabolite
   catalogued in 2018 and a platform coverage snapshot from 2026 are not contemporaneous.

---

## Results

Corpus yardstick (denali's 1,272 published CRISPR screens):
`p10 0.1026 | p25 0.1862 | median 0.2244 | p75 0.2689 | p90 0.4548`.

### The headline is the spread, not one number

51 audit calls were run. R2 ranges from **0.0003 to 0.7935** on the same underlying
pathway definitions. **The choice of mapping determines the verdict completely.**
Reporting any single one of these as "the" metabolite-set number would be dishonest,
which is why all 51 are in `metabolite_audit.json`.

### The controlling variable is the hit rate, not the domain

Across the 47 non-degenerate variants, Spearman(R2, median hit rate) = **+0.523**.
The mechanism is arithmetic, not biological:

- When the hit rate saturates (median 0.69 in the loosest SMPDB mapping), `hits ≈ 0.69 ×
  size` **by construction**. R2 = 0.79 there is not evidence of a biological confound;
  it is evidence that nearly everything declared was also detected.
- When the hit rate collapses toward 0, the response is mostly zeros (83 of 98 sets had
  zero hits in one single-study variant) and R2 is noise: 0.075.
- At ≥75% detection frequency, **0 compounds qualify** and `audit()` returns an
  undefined R2. Those two rows are labelled `DEGENERATE` in the JSON rather than being
  reported as "NOT SIZE-DOMINATED", which is what the raw NaN comparison would have
  produced.

### THE BOUNDARY CONDITION — the size confound VANISHES in the small-set stratum

This is the result the domain was chosen to test. Same 98 sets, same audit, only the
strictness of "a hit" changes:

| detection threshold | qualifying compounds | all 98 sets: hit rate → R2 | sets <20 members (n=37): hit rate → R2 |
|---|---|---|---|
| ≥1 study | 6,443 | 0.690 → **0.794** CONFOUNDED | 0.667 → **0.434** CONFOUNDED |
| ≥1% of studies | 1,966 | 0.633 → **0.711** CONFOUNDED | 0.667 → **0.336** PARTIAL |
| ≥5% | 558 | 0.460 → **0.566** CONFOUNDED | 0.500 → **0.332** PARTIAL |
| ≥10% | 290 | 0.384 → **0.456** CONFOUNDED | 0.444 → **0.126** NOT SIZE-DOMINATED |
| ≥25% | 63 | 0.099 → **0.244** PARTIAL | 0.111 → **0.0004** NOT SIZE-DOMINATED |
| ≥50% | 8 | 0.000 → **0.250** PARTIAL | 0.000 → **0.0006** NOT SIZE-DOMINATED |
| ≥75% | 0 | DEGENERATE | DEGENERATE |

Read the last two rows: at a defensible detection threshold, the whole collection sits
at R2 ≈ 0.24–0.25 — **almost exactly the published-CRISPR-corpus median (0.2244)** —
while the small-set stratum sits at **R2 ≈ 0.0005, three orders of magnitude below
corpus p10**. The confound in the full collection is carried entirely by the large-set
tail. `audit()` had 37 sets in that stratum, comfortably above the 8-set floor, so this
is not a small-n artefact of the audit itself.

The KEGG collection reproduces the direction on an independent set definition, more
weakly (n = 113 in its <20 stratum): 0.304 → 0.230 → 0.186 → 0.164 → **0.011** across
the same thresholds.

**The confound does not invert. It vanishes.** At small set sizes the size–hits relation
degenerates rather than reversing: absolute counts are so small (a 9-member pathway with
1 hit) that there is almost no variance for size to explain.

### Per-stratum spread, loosest vs strictest mapping

| stratum | n sets | R2 range observed across mappings |
|---|---|---|
| <20 members | 37 (SMPDB) / 113 (KEGG) | 0.0004 – 0.506 |
| 20–40 members | 43 / 51 | 0.006 – 0.384 |
| >40 members | 18 / 52 | 0.0003 – 0.673 |

The >40 stratum has only 18 SMPDB sets — above the 8-set floor but thin, and its R2 is
the least stable number in the table.

### Where this domain falls against the CRISPR corpus

There is no single answer, and saying so is the answer:
- Loosest/saturated coverage mappings: R2 0.57–0.79, **≥p90** (top ~10% of published
  screens). Driven by arithmetic saturation, not biology.
- Mid-strictness mappings: R2 0.22–0.46, **~p50–p90**.
- Strict-detection mappings, and every mid-to-strict small-set stratum: R2 0.0004–0.19,
  **<p10 to ~p25**.

**Best single defensible characterisation:** at the ≥25%-of-studies detection threshold
(the strictest point at which the response is still non-degenerate), the full
98-pathway collection scores **R2 = 0.244, ~corpus median (p50)**, and the <20-member
stratum scores **R2 = 0.0004, far below p10.**

### Replication arm

`audit_replication()` was run twice on the 98 SMPDB sets. Both arms are coverage
replication — two independent detection lists, not two differential-abundance screens.

| arm | n paired sets | raw agreement | after removing size | % of agreement that is size |
|---|---|---|---|---|
| two disjoint random halves of the 358 studies (179 vs 179) | 98 | 0.9903 | 0.9503 | **4.0%** |
| the two single broadest-coverage studies | 98 | 0.7929 | 0.7079 | **10.7%** |

Only 4–11% of the apparent agreement is attributable to set size. This is the *opposite*
of the CRISPR replication picture, and the reason is mundane: coverage lists agree with
each other because the same well-characterised compounds are detectable everywhere,
which is a genuine shared cause and not a size artefact. **Do not read these two rows as
evidence that metabolomics replicates well.** They measure agreement between two
detection lists, which is close to a tautology.

---

## What this is NOT

- **Not a differential-abundance result.** No p-values, no significance, no effect sizes
  entered this analysis. Every "hit" is a detection, not a finding.
- **Not a candidate list**, not a ranking, and not a statement about any pathway.
- **Not pre-registered.** Post-hoc throughout.
- **Not a claim that metabolite-set enrichment is safe.** The clean small-set numbers
  come with hit counts so low (median 2 hits per set overall, median 1 in the <20
  stratum, and 13 of 98 sets at zero) that a real enrichment analysis
  on these sets would be underpowered for a different reason. Absence of a size confound
  at n=9 members and 1 hit is not the same as a trustworthy result.

## Reproduce

```
/tmp/denali-integ-r5rQU4fP/denali/.venv/bin/python analyze.py
```
The script re-reads the cached downloads listed above; re-fetching them will move the
numbers, because the Metabolomics Workbench study index grows.
