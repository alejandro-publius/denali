# Lessons learned

Durable, earned the hard way across several retired directions. The projects that
produced them are archived; these are the parts that still bind.

## Statistics and inference

- **Donors, not cells, are independent patient-level replicates.** 471,905 cells
  are 119 people. A p-value computed with cells as replicates is meaningless and
  will be the first thing a reviewer attacks.
- **Check study / batch / site / platform confounding before interpreting
  biology.** If every case came from one site and every control from another, a
  model learns the site.
- **Report effect sizes, not just p-values. Save complete results, not only
  significant rows.**
- **A sensitivity check run on genes selected by the same test is circular.** It
  measures influence, not replication.
- **Know your test's floor.** The smallest two-sided Wilcoxon signed-rank p at n
  pairs is 2/2ⁿ. At n=14 that is 1.2×10⁻⁴, so after multiple-testing correction
  *no gene can reach significance by that test whatever the biology*.
- **Independent validation is essential**, and validation data is never mixed
  with discovery data.

## Labels and provenance

- **Never infer a diagnosis** — not from expression, not from morphology, not
  from a cohort's overall topic.
- **Verify metadata against authoritative sources.** A curated re-encoding can
  silently lose the most important distinction in a dataset: CELLxGENE's `disease`
  field collapses 39 IPF donors into generic "interstitial lung disease", while
  the authors' own label ships in the same file.
- **Provenance must remain recoverable.** No row without it.
- **"Present in an index" ≠ "extractable evidence."** Records can be returned by
  search while containing nothing to read.

## Measurement ontology

- **Never pool biologically distinct quantities because their units look
  similar.** Residual enzyme activity, fraction of corrected cells, pathway flux,
  biomarker normalisation and clinical response are **different quantities** even
  when all are reported as percentages.
- **Do not manufacture a universal threshold across incomparable measurement
  types.** Quantitative translational claims require an explicit measurement
  ontology and provenance.
- Refusing to compute a statistic across incomparable rows *is* the scientific
  act, not a failure to deliver.

## Epistemics

- **External data decides.** Models may propose; they may never self-certify.
- **Deterministic / statistical code owns every quantitative claim.**
- **Do not benchmark an agent against itself and call it validation.**
- **Distinguish association from mechanism.** Perturbation evidence outranks
  literature plausibility.
- **Preserve negative results.** They are legitimate outputs.
- **Kill weak hypotheses instead of rescuing them rhetorically.** Do not
  progressively weaken a claim to keep a project alive; do not redefine a
  criterion after seeing the data.
- **A bug invalidates every conclusion built on it.** Re-derive; do not patch the
  prose.
- **Expect silent wrong answers in public data infrastructure.** Measured
  instances: an API silently returning only significant results while accepting
  and ignoring the parameters meant to control that; effect sizes silently
  rounded to one decimal place; ragged metadata rows where field *names* vary per
  sample so a positional parse merges two arms; an SSL trust store returning
  well-formed zeros with exit code 0. **Assume this class of failure exists and
  test for it.**

## Process

- **Do not build UI before a real result exists.**
- **Use sponsor tools only where they genuinely improve the science.** A tool
  whose deletion would not change the answer does not belong in the architecture.
- **No recursive subagent spawning unless explicitly authorised.** Measured: one
  unconstrained agent spawned ~7 unplanned descendants. A single agent call is
  not a bounded unit of spend.
- **Archive dead directions rather than letting them influence fresh reasoning.**

## Tooling note — Paperclip / GXL

Archived in full; only these operational facts are worth carrying forward if it
is ever used again:

- It can perform **structured extraction from papers, tables, figures and
  supplements** — the exhaustive worker reaches supplements, which is where
  contradictions with a paper's own main text tend to live.
- **Citation chaining can outperform naive semantic search** on targeted corpora;
  semantic retrieval ranks on abstracts and misses what is only in a
  bibliography.
- **Historical papers may be indexed but not extractable** — scanned back-files
  are metadata-only stubs.
- **Verify API and index freshness before depending on recent literature.**
- **Retrieval tools do not decide numeric scientific claims.**
