# Repo map

**[`docs/README.md`](README.md) is the documentation index**, ordered by what you came to check.


| Path | Contents |
|---|---|
| `results/frozen/` | 🔒 **The frozen interface.** Matrix, program summary, predictor, held-out, controls, provenance. Everything downstream reads only this |
| `results/sensitivity/` | Post-freeze checks, explicitly not pre-registered |
| `results/figures/` | Four figures + `CAPTIONS.md`, the single source of caption wording |
| `results/prior_work/` | Pre-event ILD evidence — the positive control returning 481–6,532 genes. Not reproducible here |
| `results/discovery/` | Intermediate scoring outputs |
| `results/corpus/` | 1,272 published CRISPR screens from BioGRID ORCS — the distribution a verdict is a percentile against |
| `results/breadth/` | Post-hoc, exploratory. The unmodified `audit()` on three domains that are **not** gene sets — regions, metabolites, microbiome — plus `null_baselines.py`. Reported because it found a boundary condition on the tool, not a fourth confirmation. See scope limit 6 |
| `audits/external/` | The audit run unchanged on seven **other people's** published screens — standardized inputs, provenance and rerun command per entry |
| `benchmarks/tasks/` | Three BenchFlow tasks other agents are scored on. `denali-size-carried` derives its ground truth from the shipped `rerank()` rather than a hand-typed key |
| `benchmarks/challenge/` | A public self-scoring challenge: does your method beat the size-only baseline at predicting a second cell line? Our own `rerank` is entered as a contestant and places fourth of four on top-10 overlap |
| `packages/denali-audit/` | The packaged CLI a stranger installs. `core.py` is `src/`'s maths vendored verbatim; a test requires it to return 0.4649 on the frozen data. |
| `src/` | Pipeline modules, run as `python -m src.<module>` |
| `tests/` | Invariants over the frozen interface |
| `docs/` | Report, limitations, method rules, origins, prior work, data dictionary, pre-registrations |
| `data/genesets/` | MSigDB v2026.1.Hs, committed |
| `data/raw/` | git-ignored substrate — see above |
| `index.html` | The static page. Self-contained, built from frozen numbers |
| `audit.html` | **Run the tool on your own file, in the browser.** The package's own source, executed by CPython in WebAssembly — not a JavaScript restatement of it. Nothing is uploaded |
| `web/` | `build_audit_page.py` inlines the package into `audit.html`; `shoot.py` re-shoots the README images from the current pages |
| `app.py` | Streamlit view of the same frozen data |
