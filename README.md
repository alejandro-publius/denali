# ILD/IPF donor-level program discovery

A biological discovery pipeline in **fibrotic interstitial lung disease**, built
entirely on public data. Discovery in a 119-donor lung single-cell atlas; two
independent external cohorts held in reserve for validation.

**The data decides. Agents do not.**

## Status

**Discovery phase. The first pre-registered contrast returned NULL** and the
project is awaiting a decision on the next route. The pipeline itself is
validated — the positive control returns 6,532 genes at q<0.05 in the same cells.

Read `docs/CURRENT_STATE.md` first.

## The arc

```
public lung single-cell data
  → verify disease/control metadata against authoritative sources
  → donor-aware cell-state / transcriptional-program discovery
  → replicate in an independent 582-lung cohort
  → test in an independent blood/outcome cohort
  → prioritise candidate drivers
  → optional public perturbation evidence for causality
  → novelty check only after replication
  → interface only after the biology survives
```

## Layout

```
CLAUDE.md              operational contract — read first
docs/                  active documentation (12 files, all current)
  archive/             superseded work — do not read unless asked
src/                   analysis modules, run as `python -m src.<module>`
tests/                 invariant smoke tests
data/raw/              4.55 GB atlas (git-ignored, re-downloadable)
data/metadata/         donor table, census, confounding audit
data/processed/        pseudobulk matrices per cell type
results/{discovery,validation,clinical,qc}/
figures/{discovery,validation,final}/
```

## Reproduce

Default `python3` on this machine is 3.9 and will not work — use the venv.

```bash
# fetch the discovery atlas (4.55 GB, ~5 min)
curl -sL -o data/raw/natri_lung_ild.h5ad \
  https://datasets.cellxgene.cziscience.com/c3d9262e-0dc5-4eca-bf20-56e6d96d0306.h5ad

.venv/bin/python -m src.atlas_census                       # metadata census
.venv/bin/python -m src.atlas_confound                     # donor-level confounding
.venv/bin/python -m src.atlas_composition                  # composition analysis
.venv/bin/python -m src.pseudobulk "lung secretory cell"
.venv/bin/python -m src.paired_de  "lung secretory cell"   # the null result
.venv/bin/python -m src.anchor_de  "lung secretory cell"   # the positive control
.venv/bin/python -m src.figures
```

## Data

| Role | Source | Scale |
|---|---|---|
| Discovery | Natri et al. *Nat Genet* 2024, CELLxGENE `07e12576-…` | 471,905 cells, 119 donors |
| Lung validation | GSE47460 (LGRC) | 582 lungs, 160 UIP/IPF, DLCO on 515 |
| Blood validation | GSE28042 | 75 IPF with transplant-free survival |

Accessions, counts and every verified parsing trap: `docs/DATASETS.md`.

## Scope

Computational and high-level only. No wet-lab protocols, no biological
sequences, no dosing, no clinical or therapeutic recommendations.
