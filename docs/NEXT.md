> ⚠ **STALE KNOCKDOWN COUNT below.** The operative figure for every reported
> result is **9,837**. See the appended note in `docs/MATRIX_PREREG.md` for why
> 9,823 and 9,866 also appear in this repo.

# Next

**Candidate 1 (reversal map) is SELECTED. Its gate has PASSED.**
Program: **proteostasis, UPR arm.** Decided by the user 2026-08-15.

Full gate record: `GATE_C1_RESULTS.md` (results), `GATE_C1_PREREGISTRATION.md`
(thresholds, hashed before any value was computed), commit `280c626`.

The other three candidate programs — integrated stress response, senescence,
interferon response — **FAILED the gate and are not revisited.**

Execution plan and schedule: **`HACKATHON_PLAN.md`.**
Cold-start resume: **`MORNING_HANDOFF.md`.**

---

## The program

**Proteostasis, UPR arm.** Primary gene set
`HALLMARK_UNFOLDED_PROTEIN_RESPONSE` (MSigDB v2026.1.Hs, 113 genes).

Gate performance: 83–88% of members measured in both cell lines; expression
2.25× / 1.96× background; variance across perturbations 1.05× / 1.27× background;
all p ≤ 4.4e-06. Cell-intrinsic (ER folding, chaperones, ERAD, UPS are strictly
intracellular). Anchor: **GSE24080, multiple myeloma, n=559**.

⚠ **Scope limit, from the gate itself.** The broad
`GOBP_PROTEASOMAL_PROTEIN_CATABOLIC_PROCESS` set **failed** the variance test
(R = 1.00–1.02, n.s.). The pass is specific to the **UPR / protein-folding arm**,
not to proteostasis writ large. Every downstream claim must be scoped to the UPR.

## The chain

```
proteostasis (UPR) program, one citation per gene
  → score all ~9,823 K562 CRISPRi knockdowns for opposition to the program
  → RPE1 replication arm, coverage denominator stated on screen
  → DepMap essentiality filter (Avana + KY): is reversal regulation, or death?
  → ranked reversal map, PATHWAY-LEVEL claims only (see SCOPE_STATEMENT.md)
```

## Substrate on disk

| File | Status |
|---|---|
| `data/raw/K562_gwps_normalized_bulk_01.h5ad` | ✅ downloaded, md5 verified, 11,258 × 8,248 |
| `data/raw/rpe1_normalized_bulk_01.h5ad` | ✅ downloaded, md5 verified, 2,679 × 8,749 |
| `data/genesets/*.v2026.1.Hs.symbols.gmt` | ✅ committed |
| DepMap 24Q4 `CRISPRGeneEffect.csv`, `Model.csv` | see `MORNING_HANDOFF.md` |

⚠ **RPE1 is not genome-scale.** 2,383 unique targets vs K562's 9,823 — **only
24.2% of K562 perturbations are testable there**, and that quarter is the
*essential-gene* subset, not a random sample. The replication arm is **partial
replication with a stated, non-random denominator** — never call it independent
replication of the map.

---

## Standing prohibitions

### LIFTED, 2026-08-15 — demo layer only

> **The no-UI / no-frontend / no-Figma prohibition is LIFTED for the demo layer
> only.** Frontend is authorised, to be built **Sunday morning over precomputed,
> frozen tables** — never before the science lands. A UI that runs analysis live,
> or that is built ahead of the result it displays, remains prohibited.
>
> This supersedes `CLAUDE.md` §9 for the demo layer only. Everything else in
> §9 stands.

### Still in force

- **No agents or subagents without explicit authorisation**, and any authorised
  agent must be told not to spawn children.
- **No broad prior-art or novelty sweeps** beyond the targeted checks already done.
- **Do not resurrect** FigContract, RETRIAL, RescueMap/ENOUGH, or the ILD
  gradient project.
- Do not redefine a kill criterion after seeing data.
- Computational and high-level only: no wet-lab protocols, no dosing, no
  clinical or therapeutic recommendations.

---

## Pre-publication note

This repository begins at the first commit of the project itself. Earlier
exploratory work is not carried over; what remains useful from it is rewritten in
`docs/ORIGINS.md` and `docs/METHOD_RULES.md`. No personal identifiers appear in
this history.
