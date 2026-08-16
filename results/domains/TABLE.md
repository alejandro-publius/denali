# Track C — one recipe, six domains

Pre-registered in `docs/DOMAINS_PREREG.md` (`6d40a079…`, commit `a2776f7`), correction 1 at `8d2296a`. Every number below was computed by the per-domain module named in the last column and is assembled here, not recomputed.

| domain | sets | size range | R² size alone (raw) | R² (log) | verdict | percentile vs 1,272 CRISPR screens | top-10 survive |
|---|---:|---|---:|---:|---|---:|---:|
| 1 · gene sets (CRISPR screens) | 50 per screen | varies by screen | 0.1918 | 0.2244 | reference distribution | 50.0 | — |
| 6 · yeast genetic interaction | 117 | 7–1377 | 0.3567 | 0.6806 | PARTIALLY CONFOUNDED | 96.1 | 5 |
| 2 · region sets | 300 | 15–84580 | 0.6480 | 0.8931 | CONFOUNDED | 99.6 | 0 |
| 3 · metabolite sets (boundary condition) | 91 | 3–8 | 0.3305 | 0.2991 | PARTIALLY CONFOUNDED | 81.8 | 10 |
| 4 · protein sets | 1277 | 5–399 | 0.3706 | 0.4305 | PARTIALLY CONFOUNDED | 89.2 | 1 |
| 5 · microbiome functions | 5 cohorts | 5–570 | 0.6333 | 0.4463 | CONFOUNDED (4/5 cohorts) | 89.7 | 1 |

## Notes, one per row

- **1 · gene sets (CRISPR screens)** — Pre-event work, cited not recomputed. This IS the reference distribution the other rows are placed against, so its percentile is 50 by construction. `results/corpus/corpus_audit.json`
- **6 · yeast genetic interaction** — The best-annotated organism in biology. Registered expectation was 'at or above the corpus 25th percentile'. `results/domains/yeast.json`
- **2 · region sets** — No gene identifiers anywhere. Size is peaks called; 5638.7x size range. `results/domains/regions.json`
- **3 · metabolite sets (boundary condition)** — Sets are 3-8 members. HEADLINE IS THE POST-HOC STRICT-HIT VARIANT: the registered BH q<0.05 rule made 86% of metabolites hits, so hits = rate x size by identity (R^2 0.9126, printed here and not used). `results/domains/metabolite.json`
- **4 · protein sets** — HEADLINE IS THE REGISTERED VARIANT: the pre-registered hit-fraction guard fired at 75% and required it (degenerate primary R^2 0.6969, printed here and not used). `results/domains/protein.json`
- **5 · microbiome functions** — DEVIATION (correction 1): sets = pathways, members = the species carrying them. 6 of 11 cohorts return NO significant stratum and are UNSCOREABLE, not scored as clean. `results/domains/microbiome.json`

## The pre-registered claim

**(a) IT IS ARITHMETIC — the confound appears in domains that share no biology**

- rows with a defensible number: 6/6 (threshold ≥ 4)
- of those, reaching the tool's PARTIAL line (raw R² ≥ 0.20): 5 (threshold ≥ 3)
- non-gene domains reaching CONFOUNDED (raw R² ≥ 0.40): 2 (threshold ≥ 1)

Thresholds were fixed before any domain substrate was downloaded and are not revised here.

**What this table does not say.** Driving a size correlation to zero would not prove a ranking correct, and a high R² here does not mean any particular set is wrong. The unit of inference is the distribution, and no individual set, experiment, cohort or trait is named as a finding.

