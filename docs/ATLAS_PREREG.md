# Pre-registration — the no-biology floor atlas

**Sealed before any floor was computed for any source beyond BioGRID ORCS.**
The existing 1,272-screen corpus predates this document and is not covered by
it; this governs every source ADDED to the atlas from here.

## What an atlas is, and why the rule has to come first

`results/corpus/` is 1,272 published human CRISPR screens with a no-biology
floor each. An atlas is that, for every public perturbation dataset legally
reachable, **computed by identical code**. The identical-code part is the whole
value: a floor that means one thing in ORCS and another in Tahoe is not a
reference, it is two numbers with the same name.

The inclusion rule is written here before any new value exists because that is
the only reason anyone believes the corpus number today, and because an atlas
whose membership rule was chosen after seeing which sources looked good would
be a marketing artifact.

## Inclusion rule — fixed

A dataset enters the atlas when **all** of the following hold. These are the
existing corpus rule, restated so a second source is held to the first source's
bar rather than to a new one:

1. **Shape without authorship.** The source yields, per screen, a table of gene
   sets with *members measured* and *members significant*, **without this
   project running a new enrichment analysis**. Where we would have to author
   the differential-expression step or the enrichment step ourselves, the
   resulting floor would be a property of our pipeline, not of the published
   screen — and the atlas would be measuring itself. Such a source is
   **rejected**, not adapted.
2. **≥ 20 hits** and **≥ 10,000 genes measured** in the screen.
3. **≥ 8 usable sets**, where a set is usable with **≥ 5 measured members**.
4. **Scored against MSigDB Hallmark v2026.1.Hs**, the same 50 sets, so the
   floor is comparable across sources.
5. **Licence verified from a primary source read at survey time**, recorded in
   `results/atlas/source_survey.json` with the URL. A licence taken from memory,
   from a secondary summary, or from this project's own earlier prose does not
   count.

## Redistribution rule — fixed

- **Derived statistics only.** Floors, the counts they were computed from, and
  the identifiers needed for attribution.
- Where a licence permits redistribution of derived statistics, they ship in
  `denali_audit/atlas.py`.
- **Where a licence forbids or does not clearly permit it, the floor is computed
  and the number published, and the source data is not redistributed.** Never
  redistribute data whose terms were not read.
- Descriptive curation authored by the source (cell line, phenotype, library) is
  not shipped inside the package even where permitted; it stays in the research
  repository.

## Method version

A floor is `R² of log10(1 + hits per set) on log10(set size)`, across the
Hallmark sets within one screen. `ATLAS_VERSION` in `denali_audit/atlas.py` is
bumped only when that definition changes. Adding screens under an unchanged rule
does not bump it — the content hash of the per-screen table distinguishes those,
and the content hash is what a citation pins.

## Modal

The existing discipline is unchanged and binding: **Modal verifies, it does not
author.** If a Modal run and a local run disagree on any screen, both numbers go
in `docs/LIMITATIONS.md`. The disagreement is not reconciled quietly and the
convenient one is not chosen.

## What would falsify the atlas's usefulness

Stated in advance. If floors turn out to be **effectively constant across
sources and assay types** — say an interquartile range below 0.05 — then the
atlas is an expensive way to publish one number, and it should say so and stop.
The corpus already argues against that (p10 0.103, p90 0.455 within ORCS alone),
but across sources it has never been tested and could come back flat.

---

# RESULT — the survey, and what it says about growth

Recorded 2026-08-17. Six candidate source families were surveyed, each by one
agent and then **adversarially re-checked by a second agent instructed to refute
it**. Three of the six had a claim overturned by that second pass. Full records,
including every licence URL actually opened, are in
`results/atlas/source_survey.json`.

| source | licence (verified) | fits rule 1? | verdict |
|---|---|---|---|
| **BioGRID ORCS 2.0.18** | **MIT** — read verbatim from `LICENSE.txt`, HTTP 200 | yes | already in: 1,272 of 1,952 |
| **Tahoe-100M** (pseudobulk DE) | **CC0 1.0** — read in full from the HF `LICENSE.md` | **yes** | **build next** — 65,218 DE contrasts |
| DepMap 24Q4 | CC BY 4.0 — verified on the Figshare deposit | **no** (refuted) | needs an enrichment step we would author |
| Paperclip supplementary tables | per-article, mixed | **no** (refuted) | 0 computable from the index alone |
| GEO + ArrayExpress | no blanket licence | **no** (refuted) | 0 of 199 supplementary files were enrichment tables |
| Arc Virtual Cell Atlas (excl. Tahoe) | CC0 1.0 | no | single-cell matrices, no hit lists |

## The licence correction that matters

The brief this work was done from stated BioGRID ORCS as **CC BY 4.0**. It is
**MIT**, and the repository's README was already right. Verified this session by
fetching `LICENSE.txt` from the BioGRID download host directly and reading the
grant, which is explicitly extended to the data files. **The source wins over
the brief**, and the brief was wrong. Nothing in the repository needed changing;
this is recorded so the next person does not re-derive it.

## Did the atlas grow? No, and this is why

**It did not.** The atlas is still the 1,272 ORCS screens, and saying that
plainly is worth more than a thin second source.

Three of the five candidate additions fail inclusion rule 1 outright — they
would require this project to author the differential-expression or enrichment
step, which would make the resulting floor a property of our pipeline rather
than of the published screen. That is not a resourcing problem and more time
would not fix it.

The one genuine candidate is **Tahoe-100M's pseudobulk differential-expression
component**: CC0, redistribution of derived statistics permitted, and it fits
the shape without us authoring an enrichment step. Its size is
`4,089,820,780` rows — 62,710 genes × 65,218 contrasts, verified exactly, with
no remainder. Two things blocked it in this session and both are environmental
rather than scientific:

- **Modal is not installed** in this environment, so the fan-out the brief
  specifies has no runner. `modal` does not resolve on PATH and is absent from
  the venv.
- **`data/raw/` is empty.** Every raw substrate is git-ignored, so a source has
  to be re-downloaded before anything can be computed, and the Tahoe DE
  component is a multi-hundred-gigabyte fetch.

So the next step is specified rather than attempted: fetch the Tahoe pseudobulk
DE parquet, map each `(drug, concentration, cell line)` contrast to the
set/size/hits shape at a stated significance threshold, and run the same
`audit()` under the rule above. **A contrast is not a CRISPR screen**, and if
those floors enter the atlas they enter it labelled as a different assay type,
with the distribution reported separately before it is reported pooled.
