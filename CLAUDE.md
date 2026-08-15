# CLAUDE.md — operational contract

## 1. What this project is

**ACTIVE: Candidate 1, the Perturb-seq reversal map. Program: proteostasis, UPR
arm.** Selected 2026-08-15 after the pre-registered gate passed 3/3
(`docs/GATE_C1_RESULTS.md`, commit `280c626`). Hackathon Track A, "Build an AI
Scientist."

The standing shape:

```
real public data → real computational result → INDEPENDENT external validation
  → mechanistic / perturbational follow-up → durable scientific artifact
  → inspectable product LAST
```

**The data decides. Agents do not.**

## 2. Current phase

**Building.** Pipeline and schedule: `docs/HACKATHON_PLAN.md`. Cold-start
resume: `docs/MORNING_HANDOFF.md`.

⚠ The gate passed the **UPR / protein-folding arm only** — the broad proteasomal
set failed its variance test. Keep every claim scoped to the UPR.

## 3. Read these, in this order

1. `docs/MORNING_HANDOFF.md` — **START HERE.** Zero-explanation resume: the four
   results, every hash and seal, the partial-visibility disclosure, and explicit
   DONE / ABANDONED / NOT STARTED lists.
2. `REPORT.md` — the two-page finding
3. `docs/DEMO.md` — the spoken script and the ranked adversarial answers
4. `docs/LIMITATIONS.md` — first-class; read before defending anything
5. `docs/DATA_DICTIONARY.md` — every frozen column in plain English

Reference: `docs/MATRIX_PREREG.md` (`d3e24b77…`), `docs/SCOPE_STATEMENT.md`,
`results/figures/CAPTIONS.md`. Anything else is in `docs/archive/`.

**ANALYSIS IS CLOSED.** No sweeps, no refits, no new features, no gene-level
claims. Communication and hardening only.

## 4. Data locations

| Path | Contents |
|---|---|
| `src/` | reusable analysis modules, run as `.venv/bin/python -m src.<module>` |
| `tests/` | invariant smoke tests |
| `data/genesets/` | MSigDB v2026.1.Hs GMTs, committed |
| `data/raw/` | git-ignored substrate — see `docs/MORNING_HANDOFF.md` §5 |
| `results/`, `figures/` | ILD nulls (retired) + `results/qc/gate_c1_criterion1.json` |

Active substrate on disk: `K562_gwps_normalized_bulk_01.h5ad` (11,258 × 8,248)
and `rpe1_normalized_bulk_01.h5ad` (2,679 × 8,749), both md5-verified.
`data/raw/natri_lung_ild.h5ad` (4.55 GB) belongs to the **retired** ILD project
and can be deleted to reclaim the space.

⚠ figshare returns **403 on HEAD but 206 on ranged GET** — use GET.
⚠ Replogle `X` is a perturbation-**effect** matrix, not absolute expression;
absolute expression is `var/mean`. Non-finite entries exist — mask, do not impute.

## 5. Non-negotiable scientific rules

- **Donors are the unit of inference, not cells.** 471,905 cells are 119 people.
  Never compute a p-value with cells as replicates.
- **Never infer a diagnosis from expression.** Labels come from authoritative
  metadata only.
- **Check study/batch/site/platform confounding before interpreting biology.**
- **Report effect sizes, not just p-values. Save full results, not just
  significant rows.**
- **External data decides.** A model may propose; it may never self-certify.
  Deterministic/statistical code owns every quantitative claim.
- **Never pool biologically distinct quantities because their units look alike.**
- **Preserve negative results. Kill weak hypotheses; do not rescue them
  rhetorically.** Do not redefine a criterion after seeing the data.
- **Distinguish association from mechanism.** Perturbation evidence outranks
  literature plausibility.
- **Abstention is legitimate.** Prefer "not established" to unsupported
  certainty.

## 6. Archive behaviour

`docs/archive/` contains **superseded work**: FigContract, RETRIAL, RescueMap /
ENOUGH, project selection, Paperclip scouting, Proto/Track C, old architecture
and demo specs.

> **Do not read, summarise, or use `docs/archive/` to influence current
> reasoning unless the user explicitly asks for historical context.**

Its durable lessons are already distilled into `LESSONS_LEARNED.md`,
`WINNING_PATTERNS.md` and `TRANSLATIONAL_CONTEXT.md`. Read those instead.

## 7. Agent behaviour

- **Do not spawn agents or subagents unless explicitly authorised.**
- Any authorised agent must itself be told **not to spawn children**. Measured
  2026-08-12: one unconstrained agent spawned ~7 unplanned descendants. A single
  `Agent` call is not a bounded unit of spend.
- Verification agents are read-only; the main context reconciles their output so
  parallel agents cannot invent conflicting ontologies.

## 8. Reproducibility

Every number in `docs/` must be regenerable by a command recorded beside it.
Default `python3` on this machine is 3.9 and will not work — use the venv.

```bash
cd /Users/alexvintera/figure-contract
.venv/bin/python -m src.atlas_census          # metadata census
.venv/bin/python -m src.atlas_confound        # donor-level confounding audit
.venv/bin/python -m src.pseudobulk "<cell type>"
.venv/bin/python -m src.paired_de  "<cell type>"
.venv/bin/python -m src.figures
```

Environment note: Python `urllib`'s SSL chain is intercepted on this machine.
**Use `curl` for reachability checks.**

## 9. Build order

**UI prohibition LIFTED 2026-08-15 — demo layer only.** Frontend is authorised,
built **Sunday morning over frozen precomputed tables**, never before the science
lands. A UI that runs analysis live, or that is built ahead of the result it
displays, remains prohibited.

Still deferred: no novelty screen, and **do not touch the anchor cohort
(GSE24080)** until the K562 → RPE1 → DepMap chain produces a ranked result.

## 10. Safety and scope

Computational and high-level only. No wet-lab protocols, no biological
sequences, no dosing, no clinical or therapeutic recommendations.
