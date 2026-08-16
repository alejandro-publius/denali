# Breadth domain (c): microbiome functional sets

> ### ⚠ Read `../README.md` first — this arm's R² does not clear its own null
>
> This file was written before the no-biology baseline was computed. Adversarial review
> of it, and `../null_baselines.py`, established that where `hits` are drawn from the
> set's own members (`hits ≤ size`), a large size-alone R² is **expected under pure
> counting** — so the values below are **not** by themselves evidence of a confound.
> Every number here reproduces exactly and the provenance survived checking; it is the
> interpretation that is superseded. The synthesis, the correct null per mapping, and
> what survives are in [`../README.md`](../README.md).


**POST-HOC. EXPLORATORY. NOT PRE-REGISTERED.** Nothing here was specified before the data
were seen. Every mapping below was chosen after inspecting what the data could support.

**Unit of inference is the DISTRIBUTION.** No pathway, reaction, species or taxon is named
anywhere in this directory's prose as a finding, as confounded, or as a candidate. The
per-pathway tables carry identifiers only so the numbers are reproducible.

**No clinical, wet-lab or therapeutic recommendation is made or implied.**

---

## Headline

The answer depends entirely on which construction quantity you call "set size", and the two
candidate definitions in this domain are **negatively correlated with each other**
(Spearman -0.23, log-log Pearson -0.21).

| size definition | R2 size alone (pooled) | percentile vs denali CRISPR corpus (n=1,272) | verdict |
|---|---|---|---|
| reactions per MetaCyc pathway (curated definition) | **0.0014 - 0.0130** | **0.3rd - 1.2th** | NOT SIZE-DOMINATED |
| species-stratified instances actually measured | **0.7844** (FDR<0.10) / 0.7514 (nominal) | **98.8th** / 98.0th | CONFOUNDED |

Concordance arm, 21 cohort pairs, size = members measured, hits = differential-abundance
count: **median 53.5% of cross-cohort agreement is set size** (IQR 40.9 - 64.0).
denali's own comparable CRISPR number is 26%. The evaluation-6 finding reproduces in a
second field and is roughly twice as large.

Under the reaction-count size definition the same concordance arm returns ~0% (median
-1.6% to +1.6% across the three mappings), i.e. cross-cohort agreement in *detection* has
essentially nothing to do with how many reactions a pathway declares.

---

## Data provenance

### Set sizes
- URL: `https://raw.githubusercontent.com/biobakery/humann/master/humann/data/utility_DEMO/metacyc_pathways_structured_filtered_v24_subreactions`
- Fetched 2026-08-16, `curl --max-time 120`, **HTTP 200, 180,357 bytes** (matches the ~180 KB
  expected), MD5 `c6ad3784f8dee2dfba3dfada21404357`, 987 non-empty lines, no truncation.
- Local copy: `metacyc_pathways_structured_filtered_v24_subreactions`
- Parsed by `parse_sizes.py` -> `pathway_sizes.tsv`.

**How reactions were counted.** Each line is `PATHWAY_ID \t <structure>`. The structure is a
whitespace-token expression over reaction IDs and the operators `(`, `)`, `,`, `+`. A leading
`-` on a token encodes reaction *direction* (reverse), not a distinct reaction, so it was
stripped before counting. **size = number of unique reaction IDs per pathway** (the
defensible choice). Counting reaction *slots* instead (duplicates retained) gives an
identical answer: 0 of 987 pathways differ, so this parsing choice does not drive anything.

Size distribution (n = 987): min 4, p10 4, p25 6, **median 8**, p75 12, p90 19, max 268,
mean 11.0. **Fold range 67.0x** - the brief's 67x claim is confirmed exactly, against
Hallmark's ~6x.

### Abundance / hits
- Source: local read-only repository `~/Documents/GitHub/crc-metagenomics`,
  `data/raw/pathway_chunks/*.csv` - **7 per-cohort HUMAnN pathway-abundance matrices**
  exported from curatedMetagenomicData (snapshot `2021-03-31`, per
  `scripts/export_data.R` / `scripts/export_data_stratified.R` in that repo).
  Contrary to the task brief, raw pathway abundance matrices **are** present there; they are
  simply not obvious because the files carry no sample-ID column.
- Files and byte counts read: FengQ_2015.csv (14,301,994 B, 154 samples), ThomasAM_2018a.csv
  (6,478,871 B, 80), ThomasAM_2018b.csv (5,865,181 B, 60), ThomasAM_2019_c.csv (7,936,617 B,
  80), VogtmannE_2016.csv (9,113,405 B, 104), YuJ_2015.csv (12,621,542 B, 128),
  ZellerG_2014.csv (14,715,097 B, 156). **762 samples total.**
- Each matrix is samples x features; features are community-level pathways
  (`PWY-xxxx: name`) plus species-stratified instances (`PWY-xxxx: name|g__X.s__Y`),
  6,000 - 21,000 columns per cohort.
- Nothing was written to that repository and no git command was run there.

**The join hazard, and how it was closed.** The chunk files have no sample-ID column, so
condition labels (CRC / control) could not be attached by position - the sibling merged file
`pathway_unstratified_full.csv` contains 1,604 rows from 11 cohorts, and a naive positional
alignment to the 762 chunk rows is **wrong** (verified and rejected in `verify_align.py`:
the row-order hypothesis fails for 6 of 7 cohorts). Sample IDs were instead recovered by
exact-value fingerprint: for each cohort, each chunk row was hashed on 60 shared
unstratified pathway columns and matched against the sample-ID-bearing merged file
restricted to that cohort. Result (`id_match_diagnostic.json`): **7/7 cohorts, 762/762 rows
matched, 762 distinct sample IDs, 0 collisions**, over 453-517 shared columns. This is a
verified join, not an assumption.

Cohort composition after the join (samples; CRC / control): 154 (46/61), 80 (29/24),
60 (32/28), 80 (40/40), 104 (52/52), 128 (74/54), 156 (53/61). Remaining samples in each
cohort are adenoma, which was excluded from every differential test.

---

## Mappings run (all of them, not just the flattering one)

Set of results in `standardized_table.tsv` (42 variants), `table_sensitivity.tsv`
(24 threshold/cut combinations), `audit_output_combined.json`.

### Arm 1 - size = reactions per MetaCyc pathway

- **A - DETECTION mapping.** hits = number of samples in which the community-level pathway
  has non-zero abundance. *Label: this is a detection estimand, not a differential-abundance
  hit count.* Pooled n=491, R2 = 0.0014. Per cohort n=413-471, R2 = 0.0007-0.0037.
- **B - RECOVERED-CONTRIBUTOR mapping.** hits = number of distinct species-stratified
  instances of the pathway observed with non-zero abundance. Pooled n=405, R2 = 0.0076-0.0080.
  Per cohort n=343-377, R2 = 0.0051-0.0140.
- **C - DIFFERENTIAL-ABUNDANCE mapping.** hits = number of species-stratified instances
  significant at BH-FDR < 0.10, Mann-Whitney CRC vs control. Pooled n=324, R2 = 0.0117.
  Per cohort: 3 of 7 usable (R2 = 0.0092-0.0167); **4 of 7 returned zero significant
  instances anywhere in the cohort**, which makes the audit degenerate (no variance in hits)
  and is reported as "no defensible number", not as "not confounded".

Every non-degenerate variant in this arm sits between the **0.2nd and 1.7th percentile** of
the CRISPR corpus. Spearman is weakly **negative** in B and C (-0.09 to -0.26): larger
curated pathways return *fewer* recovered members, not more.

### Arm 2 - size = species-stratified instances actually measured

This is denali's exact estimand - members measured vs members significant - applied to the
microbiome's operative unit of testing. A pathway is not tested once; it is tested once per
species that carries it.

- **D - members measured vs FDR<0.10.** Pooled n=324, size range 1-932 (**932x**),
  **R2 = 0.7844, Spearman 0.886, 172 sets with zero hits -> 98.8th percentile, CONFOUNDED.**
  Per cohort: 3 of 7 usable (R2 = 0.7956-0.8315, 98.9th-99.2nd percentile); 4 of 7 degenerate
  at FDR<0.10.
- **D - members measured vs nominal p<0.05.** Pooled R2 = 0.7514 (98.0th). All 7 cohorts
  usable, R2 = 0.7056-0.8316 (97.1st-99.2nd percentile). Nominal, uncorrected - labelled.
- **E - control.** Same hit vector, reaction-count size: R2 = 0.0130 (1.2th percentile).

**Sensitivity** (`table_sensitivity.tsv`): across 4 testability thresholds (strata present in
>=5%, 10%, 25%, 50% of a cohort's samples) x 3 significance cuts (FDR<0.10, FDR<0.20,
nominal p<0.05), members-measured R2 spans **0.737 - 0.822** (12/12 CONFOUNDED) and
reaction-count R2 spans **0.0087 - 0.0264** (12/12 NOT SIZE-DOMINATED). Neither verdict is
an artifact of a threshold choice.

### Concordance arm (`audit_replication`)

All 21 cohort pairs, per mapping. `table_replication_pairs.tsv`, `table_replication_pairs_D.tsv`.

| mapping | size used | pairs | median raw agreement | after removing size | median % that is size |
|---|---|---|---|---|---|
| A detection | reactions | 21 | 0.957 | 0.970 | -1.6% |
| B recovered contributors | reactions | 21 | 0.983 | 0.984 | -0.1% |
| C differential abundance | reactions | 21 | 0.873 | 0.860 | +1.6% |
| **D differential abundance** | **members measured** | 21 (3 finite at FDR<0.10) | 0.873 | 0.504 | **+42.2%** |
| **D differential abundance** | **members measured** | 21 (21 finite, nominal p<0.05) | 0.768 | 0.357 | **+53.5%** (IQR 40.9-64.0) |

denali's own two-CRISPR-screen comparable is 26%.

---

## Assumptions a reviewer will poke

1. **Set-size definition is not unique in this domain, and the choice decides the verdict.**
   The curated reaction count and the number of measured species instances are *negatively*
   correlated (Spearman -0.23). Arm 1 and Arm 2 are not two estimates of one quantity; they
   answer two different questions and both are reported.
2. **Arm 2's "size" is data-dependent.** Members measured is not a pre-declared set size the
   way a CRISPR library's genes-per-set is; it depends on which species were detected in that
   cohort at the chosen prevalence threshold. It therefore partly encodes pathway prevalence,
   which is itself biology. This makes Arm 2 a weaker analogue of the corpus comparison than
   the raw percentile suggests, and it is the single largest caveat here.
3. **hits <= members is mechanically true in Arm 2.** More tests give more significant tests.
   That is exactly the confound the audit exists to quantify and it is the same structure as
   the CRISPR corpus (genes per set vs significant genes per set), so the percentile
   comparison is like-for-like - but the direction of the result is not a surprise, only its
   magnitude is.
4. **Arm 1 mixes units.** Size counts reactions; mappings B and C count species instances.
   A pathway's reaction count does not bound its species count, so B and C are approximate
   under the reaction-size definition. Mapping A (size = reactions, hits = samples detected)
   has the same unit mismatch. This is stated rather than hidden; it is part of why Arm 1's
   near-zero R2 should not be read as "microbiome pathway analysis is clean".
5. **HUMAnN's own construction may already de-confound Arm 1.** Pathway presence in HUMAnN
   is called from the fraction of a pathway's reactions covered (MinPath-style), which is
   size-normalised by design. A near-zero reaction-size R2 is therefore partly a property of
   the tool, not evidence about the biology.
6. **Detection saturation was checked, not assumed.** 23-47% of pathways are detected in
   100% of a cohort's samples, but 25-36% are detected in under 50%, with 111 distinct hit
   values and full spread 1-154 in the largest cohort. Arm 1's near-zero R2 is not a
   variance-free artifact.
7. **Differential tests are unadjusted Mann-Whitney, CRC vs control, adenoma dropped,**
   within cohort, on relative abundances, no covariate adjustment, no compositional
   transform. A better-specified differential model would change the hit counts; whether it
   changes the size relationship is untested.
8. **MetaCyc version skew.** Sizes come from HUMAnN v3 / MetaCyc v24; the abundances come
   from a curatedMetagenomicData 2021-03-31 snapshot. 324-491 of the ~450-520 observed
   pathway identifiers per cohort joined to the definition file; unjoined identifiers were
   dropped, and a version-skewed drop is not guaranteed to be random with respect to size.
9. **The definition file lives under `utility_DEMO/`.** It is the filtered v24 structured
   file HUMAnN ships, but no independent confirmation was obtained that it is byte-identical
   to the file used in the pipeline that produced the 2021 abundances.
10. **Seven cohorts, one disease, one body site, one tool.** These are not seven independent
    draws from "microbiome studies"; they share a processing pipeline and a curation layer,
    which inflates the concordance arm's raw agreement.

---

## Limitations

- No pre-registration; every mapping was chosen post hoc.
- 4 of 7 cohorts produce zero FDR<0.10 significant stratified features, so the per-cohort
  FDR results rest on 3 cohorts. The nominal-p<0.05 variant covers all 7 but is uncorrected.
- The concordance arm's raw agreements (0.77-0.98) are high partly because all seven cohorts
  were processed identically; a genuinely independent pipeline would likely lower them.
- No true per-reaction result quantity exists in this data. The strict analogue of "how many
  of this set's declared members came back significant" - members = reactions - is **not
  computable** here, because HUMAnN pathway output is not resolved to individual reactions.
  Every hit mapping above substitutes a different member unit and is labelled accordingly.
- The corpus percentiles compare a microbiome number to a CRISPR distribution. They locate
  the number; they do not establish that the two are exchangeable.

---

## Files

| file | contents |
|---|---|
| `metacyc_pathways_structured_filtered_v24_subreactions` | downloaded definition file (180,357 B) |
| `pathway_sizes.tsv` | 987 pathways, unique-reaction and slot counts |
| `parse_sizes.py` | size parser |
| `verify_align.py` | positional-alignment hypothesis, tested and **rejected** |
| `match_ids.py`, `id_match_diagnostic.json` | fingerprint sample-ID recovery, 762/762 |
| `run_audit.py`, `audit_output.json` | Arm 1 (reaction-count size) + concordance |
| `run_audit2.py`, `audit_output_D.json` | Arm 2 (members-measured size) + concordance |
| `run_sensitivity.py`, `table_sensitivity.tsv` | 24 threshold x cut combinations |
| `make_standard_table.py`, `standardized_table.tsv` | 42 variants with corpus percentiles |
| `audit_output_combined.json` | both arms merged |
| `table_A_detection.tsv`, `table_B_species_breadth.tsv`, `table_C_diffabund.tsv`, `table_D_members_measured.tsv` | per-cohort per-pathway size/hit tables |
| `table_replication_pairs.tsv`, `table_replication_pairs_D.tsv` | all 21 pairs x mapping |

Yardstick used throughout: denali CRISPR corpus, `results/corpus/corpus_per_screen.csv`,
n = 1,272 screens, p10 0.1026 / p25 0.1862 / median 0.2244 / p75 0.2689 / p90 0.4548
(re-derived from the file and confirmed identical to the published values).
