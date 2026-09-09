# Run it at the enrichment step, from R

The audit is useful in the ten seconds after an enrichment finishes and nearly
useless a week later, once the top of the list is already in a slide. Every
other surface here asks the analyst to stop, export, and go somewhere else — so
for an R user running clusterProfiler, the check effectively does not exist.

```r
source("integrations/denali.R")
ego <- clusterProfiler::enrichGO(genes, OrgDb = org.Hs.eg.db, ont = "BP")

denali_audit(ego)      # verdict, R², percentile against 1,272 screens
denali_rerank(ego)     # which of your top entries size was carrying
denali_report(ego)     # both, printed verdict-first
```

It takes an `enrichResult` directly — `BgRatio` and `Count` are what the audit
reads, so nothing is renamed. **It is a thin shell over the CLI and deliberately
not a reimplementation**: an R port would be exactly the drift `core.py` warns
about. `tests/test_r_integration.py` runs the R file and the Python package over
the same bytes and fails if any value differs, the same discipline the browser
port is held to. Mutation-tested — drop one row inside the R function and four
checks go red.

**Where that guarantee does and does not hold.** It holds on any machine with R,
and `make test` runs it. **It does not hold in CI**, which does not install R, so
the suite hits its `Rscript is absent` branch and exits 0 having tested nothing.
Until CI installs R, this integration is guarded by whoever runs the suite
locally and not by the build — which is a weaker promise than the browser port's,
and stated here rather than left to be discovered from a green badge.
