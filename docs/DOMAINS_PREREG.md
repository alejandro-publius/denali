# Domains arm (Track C) — pre-registration

**Written and committed before any domain substrate was downloaded and before
any value was computed.** No threshold or construction below was chosen after
seeing a value.

**Post-deadline extension work.** Closed evaluations unrevised;
`results/frozen/` untouched; outputs to `results/domains/` on a branch.

---

## The question, scoped honestly

If the size confound is arithmetic and not biology, it must appear wherever a
score is aggregated over sets of varying size — in domains that share no
biology with CRISPR screens, and in the best-annotated corners of biology
where "sloppy curation" cannot be the excuse. Six domains, one recipe, one
table. **A row that does not support a defensible number says "no defensible
number here" — all six rows are reported or none.**

## The recipe, identical per domain

Build a real (set, size m, hits k) table from public data — a construction a
practitioner in that field would actually produce, not a simulation. Then:

1. `r2_size_alone` from `core.audit` verbatim (raw-size predictor), with its
   verdict line (CONFOUNDED ≥ 0.40 / PARTIAL ≥ 0.20).
2. The log-size variant (the corpus transform), used ONLY for percentile
   placement against the committed 1,272-screen distribution
   (`results/corpus/corpus_per_screen.csv`, `r2_size_alone` column) — same
   transform against same transform, never mixed.
3. `core.rerank` top-10 survival: how many of the top 10 by raw hits hold
   once size is removed.

Minimum 8 usable sets (the tool's own MIN_SETS); a set is usable with ≥ 5
measured members, EXCEPT domain 3 where sets are 5–40 members by construction
and the floor is ≥ 3 (deviation fixed now, because it is the boundary
condition the domain exists to probe).

## The six constructions, fixed now

**1 · Gene sets (have it).** The committed corpus arm: median per-screen
size-alone R² 0.224 across 1,272 screens (log-size). No new computation; the
row cites `results/corpus/` and sits at its own 50th percentile by
construction. Pre-event work, labelled as such.

**6 · Yeast genetic interaction — RUN FIRST.** Costanzo 2016 global genetic
interaction network (data files from thecellmap.org; ~17 MB single GET) + SGD
GO Slim (`go_slim_mapping.tab`, single GET). Gene-level statistic: number of
significant negative genetic interactions per gene at the study's published
intermediate stringency (|ε| > 0.08, p < 0.05, or the file's own encoding of
that stringency — whichever the file provides is recorded). Hit rule: top 10%
of genes by that count (sensitivity: 5% and 20%, reported alongside). Sets:
GO Slim biological-process terms (sensitivity: component, function), size =
annotated genes among measured genes. This is the best-annotated organism in
biology: if the confound holds here, it cannot be blamed on sloppy curation.
**Pre-registered expectation:** the log-size R² falls at or above the corpus
25th percentile (0.186). Alternative: below the 10th percentile (0.103) —
which would mean annotation quality DOES rescue set-level inference, the
strongest objection to this project stands, and we report exactly that.

**2 · Region sets.** ChIP-Atlas enrichment analysis: query = NHGRI-EBI GWAS
Catalog genome-wide significant SNPs for the trait with the most catalog
associations (deterministic, capability-blind rule), against ChIP-Atlas TF
peak sets; size = peaks per experiment (result table or experimentList.tab),
hits = overlapping query regions per experiment. If the service cannot be
driven programmatically in-session: "no defensible number here."

**3 · Metabolite sets — the boundary condition.** Public MetaboAnalyst
example dataset `human_cachexia.csv` (77 urine samples, cachexic vs control;
single GET, no auth). Per-metabolite Welch t-test on log-transformed
concentrations, BH q < 0.05 → hit (the field's default workflow). Sets: SMPDB
pathway metabolite sets (bulk CSV download) mapped by compound name/HMDB ID;
size = mappable measured metabolites per set. Tests whether the confound
survives when sets are 5–40 members.

**4 · Protein sets.** A public tumor/normal proteomic abundance matrix from
CPTAC via a no-auth GET (attempt order fixed: LinkedOmics CPTAC COAD, then
BRCA, then the PDC public API). Welch t per protein, BH q < 0.05 → hit; if
the hit fraction falls outside [1%, 60%], the top-10%-by-|t| variant is also
reported. Sets: Reactome via `UniProt2Reactome.txt` (single GET), human,
size = measured mapped proteins per pathway.

**5 · Microbiome functions.** HUMAnN MetaCyc pathway abundances from
curatedMetagenomicData for colorectal-cancer cohorts (the multi-cohort
domain). Per cohort: Welch t-test per pathway, CRC vs control, on relative
abundances; BH q < 0.05 → that pathway is a "hit" in that cohort. The
set-shaped table is then: sets = MetaCyc superpathway/ontology-class
groupings of pathways, size = member pathways measured in the cohort, hits =
member pathways significant. If ≥ 2 cohorts are obtainable,
`audit_replication` gives the concordance arm: how much of cross-cohort
agreement is set size. Access order fixed: local R with
curatedMetagenomicData if present, else any public flat-file mirror, else
"no defensible number here."

## The deciding claim, fixed now

**Primary claim (a) — "it is arithmetic":** at least 4 of the 6 rows yield a
defensible number AND at least 3 of those reach the tool's PARTIAL line
(size-alone R² ≥ 0.20, raw-size predictor) AND at least one non-gene domain
reaches CONFOUNDED (≥ 0.40).

**Alternative claim (b):** fewer than 3 defensible rows reach 0.20 — the
confound does not travel beyond gene sets at the strength claimed, the
"arithmetic not biology" framing is falsified at this breadth, and that is
the reported headline.

**Yeast sub-claim, decided by its own thresholds above,** reported in the
same table regardless of (a)/(b).

## What would make us report neither

Fewer than 4 of 6 rows defensible → no (a)/(b) verdict; the table is still
published with every row labelled, because "we could not get the data" is a
different statement from "the effect is absent," and conflating them is how
fields fool themselves.

## Constraints

1. No individual set, experiment, cohort, trait, or publication is named as a
   finding. Distributions and counts only.
2. Every construction above that involves OUR choice of hit rule is a
   *published-style default*, stated in the table caption; sensitivity
   variants are reported next to the primary, never instead of it.
3. `results/frozen/`, `results/corpus/` untouched. Outputs to
   `results/domains/`.
4. Post-hoc additions (any domain 7, any alternative hit rule beyond the
   registered sensitivities) are labelled POST-HOC.
