# denali

**Between 56% and 75% of the variance in which biological programs *appear*
reversible in a genome-scale CRISPRi screen is measurement quality, not biology —
the range depends on whether a partly-circular feature is included, and we report
both.** The mechanism is size: bigger programs with more co-moving members return
more hits regardless of what they do, and program size alone explains 46.5%. What validates it is
that we ran a held-out evaluation and it **failed** — underpowered, inconclusive,
balanced accuracy 0.4375, worse than chance — and we report that alongside four
controls, an independent DepMap reference, and thresholds that fired against us. **We do not
claim any gene-level result** — guide-pair concordance is −0.019, no novel gene is
named anywhere, and the held-out evaluation came back **underpowered and
inconclusive** with one axis failing outright. To reproduce: `make setup && make data && make all` — about 22 minutes, every
input public and md5-verified, full instructions below. Next
is the experiment the pipeline itself proposes: re-run the identical sweep in
**stressed** K562, which our stated mechanism predicts will move the unfolded
protein response from zero hits to non-zero, and which refutes that mechanism if
it does not.

---

| | |
|---|---|
| **Prior work** | [`docs/PRIOR_WORK.md`](docs/PRIOR_WORK.md) |
| **Full report** | [`REPORT.md`](REPORT.md) |
| **Limitations** | [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md) |
| **Demo script** | [`docs/DEMO.md`](docs/DEMO.md) |
| **Data dictionary** | [`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md) |
| **Frozen outputs** | [`results/frozen/`](results/frozen/) |
| **Pre-registrations** | [`docs/MATRIX_PREREG.md`](docs/MATRIX_PREREG.md) · [`docs/GATE_C1_PREREGISTRATION.md`](docs/GATE_C1_PREREGISTRATION.md) |

## The three findings

1. **56–75% of apparent reversibility is measurement.** Pre-registered: we said
   before running that if a measurability model cleared 60% we would report this
   as the finding, not as a failure. It cleared.
2. **The obvious measurability filter is wrong 20 times out of 50** — and it would
   have discarded our own best result, which fails the gate yet ranks 11/50.
3. **Essentiality is not the driver at program level** — coefficient +0.021,
   p = 0.90. It dominates individual hit lists and predicts nothing about whether
   a program is reversible at all.

---

## Reproduce

**Python 3.12.0.** Every number in `results/frozen/` and every figure is
reproducible bit-for-bit — seeds are fixed and inputs are checksummed.

```bash
make setup     # venv + pinned deps from requirements.txt
make data      # prints the ONE manual step, below
make all       # ~22 min, reproduces everything deterministic
make page      # serve the expo page
```

### The one manual step — 470 MB substrate

Not in git. ⚠ **figshare returns 403 on HEAD but 206 on ranged GET** — use GET.

```bash
mkdir -p data/raw
curl -sL -o data/raw/K562_gwps_normalized_bulk_01.h5ad https://ndownloader.figshare.com/files/35773217
curl -sL -o data/raw/rpe1_normalized_bulk_01.h5ad       https://ndownloader.figshare.com/files/35775512
curl -sL -o data/raw/CRISPRGeneEffect.csv               https://ndownloader.figshare.com/files/51064667
curl -sL -o data/raw/Model.csv                          https://ndownloader.figshare.com/files/51065297
```

| File | md5 |
|---|---|
| `K562_gwps_normalized_bulk_01.h5ad` | `a3dfaa94ea8724217f5ecb1e14a5f0c8` |
| `rpe1_normalized_bulk_01.h5ad` | `6f1e7d6a09e2f869759e3c4526b7f171` |
| `CRISPRGeneEffect.csv` | `6edf7ade09b9b34199210b559d4745d3` |
| `Model.csv` | `675210d17675f3517b0ce39a3c274f16` |

Replogle et al. 2022 Perturb-seq (CC BY 4.0) · DepMap 24Q4 (CC BY 4.0) ·
MSigDB v2026.1.Hs (committed under `data/genesets/`).

### What `make all` does not re-run

**Two live-API steps**: Europe PMC and Paperclip retrieval (`make retrieval`).
Those indexes change, so their outputs — the 34-sources / 50.4% / 19-of-20
retrieval audit — are committed as **dated observations from 2026-08-15** rather
than reproducible numbers. The script that produced them is
`src/probe_retrieval.py` and its raw output is
`results/discovery/probe_retrieval.json`. That instability is the finding, not a
defect.

### Prior work, not reproducible here

`results/prior_work/` holds the pre-event ILD evidence — the positive control
returning **481–6,532 genes at q<0.05** while the pre-registered contrast
returned zero across seven populations. It needs a 4.5 GB atlas not included
here. See `docs/PRIOR_WORK.md`.

## Data

Replogle et al. 2022 genome-scale Perturb-seq (K562, CC BY 4.0) · DepMap 24Q4
(CC BY 4.0) · MSigDB v2026.1.Hs. All md5-verified; checksums in
`results/frozen/provenance.json`.

## Scope

Computational only. No wet-lab protocols, no dosing, no clinical or therapeutic
recommendation. Transcriptional movement is not phenotypic reversal.
