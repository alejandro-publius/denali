# CLAUDE.md — operational contract

## 1. What this project is

**Currently BETWEEN PROJECTS.** The ILD/IPF gradient project was retired on
evidence (see `docs/CURRENT_STATE.md`). Three verified candidates are ranked in
`docs/RESELECTION_CANDIDATES.md`; none is started.

The standing shape, whatever is chosen:

```
real public data → real computational result → INDEPENDENT external validation
  → mechanistic / perturbational follow-up → durable scientific artifact
  → inspectable product LAST
```

**The data decides. Agents do not.**

## 2. Current phase

**Reselection complete, awaiting a decision.** Recommended: Candidate 1, the
Perturb-seq reversal map — **gated**. Nothing may be built until the user picks a
candidate and its gate passes. See `docs/NEXT.md`.

## 3. Read these, in this order

1. `docs/CURRENT_STATE.md` — authoritative checkpoint
2. `docs/RESELECTION_CANDIDATES.md` — the three candidates, verified data, scorecard
3. `docs/NEXT.md` — the exact next action and the gate
4. `docs/LESSONS_LEARNED.md` — the rules earned the hard way
5. `docs/WINNING_PATTERNS.md` — active design requirements
6. `docs/TRANSLATIONAL_CONTEXT.md` — the downstream bar, context only

That is the whole active set — six files. Anything else is in `docs/archive/`.

## 4. Data locations

| Path | Contents |
|---|---|
| `src/` | reusable analysis modules, run as `.venv/bin/python -m src.<module>` |
| `tests/` | invariant smoke tests |
| `data/`, `results/`, `figures/` | artifacts of the **retired** ILD project |

`data/raw/` is git-ignored. `data/raw/natri_lung_ild.h5ad` (4.2 GB) belongs to
the retired project and can be deleted to reclaim the space.

Candidate datasets are **not yet downloaded**. Verified accessors are in
`docs/NEXT.md`. ⚠ figshare returns **403 on HEAD but 206 on ranged GET** — use GET.

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

## 9. Do not build yet

No UI, no Figma, no frontend, no demo animation, no novelty screen, no CRISPR /
perturbation analysis, and **do not touch the validation cohorts** until a
replicable discovery signal exists.

## 10. Safety and scope

Computational and high-level only. No wet-lab protocols, no biological
sequences, no dosing, no clinical or therapeutic recommendations.
