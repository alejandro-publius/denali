# reversal-map

**Between 56% and 75% of the variance in which biological programs *appear*
reversible in a genome-scale CRISPRi screen is measurement quality, not biology —
the range depends on whether a partly-circular feature is included, and we report
both.** The mechanism is size: bigger programs with more co-moving members return
more hits regardless of what they do, and program size alone explains 47%. Two
things were sealed in git before the work that validates them — the held-out
program at commit `9ad74a7`, twenty-one minutes before the scoring code existed,
and the predictor at `d902803`, before the held-out set was opened. **We do not
claim any gene-level result** — guide-pair concordance is −0.019, no novel gene is
named anywhere, and the held-out evaluation came back **underpowered and
inconclusive** with one axis failing outright. To reproduce: clone, run
`.venv/bin/python -m src.sweep` (9.2 min, 50 programs × 9,837 knockdowns), then
`src.freeze_matrix`, `src.freeze_predictor`, `src.score_heldout` in that order —
every input is public and md5-verified in `results/frozen/provenance.json`. Next
is the experiment the pipeline itself proposes: re-run the identical sweep in
**stressed** K562, which our stated mechanism predicts will move the unfolded
protein response from zero hits to non-zero, and which refutes that mechanism if
it does not.

---

| | |
|---|---|
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
   have discarded our own sealed program, which fails the gate yet ranks 11/50.
3. **Essentiality is not the driver at program level** — coefficient +0.021,
   p = 0.90. It dominates individual hit lists and predicts nothing about whether
   a program is reversible at all.

## Data

Replogle et al. 2022 genome-scale Perturb-seq (K562, CC BY 4.0) · DepMap 24Q4
(CC BY 4.0) · MSigDB v2026.1.Hs. All md5-verified; checksums in
`results/frozen/provenance.json`.

## Scope

Computational only. No wet-lab protocols, no dosing, no clinical or therapeutic
recommendation. Transcriptional movement is not phenotypic reversal.
