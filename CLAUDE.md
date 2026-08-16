# CLAUDE.md — operational contract  ·  denali

## What this is

A measurement of what a genome-scale CRISPRi screen can and cannot discover.
All 50 MSigDB Hallmark gene programs scored against 9,837 knockdowns in K562,
measurability-gated, pre-registered.

**Nine evaluations. Six negative. All nine reported.**

**ANALYSIS IS CLOSED.** No new sweeps, no refits, no new features, no
gene-level claims. Communication and hardening only.

## Read in this order

1. `docs/MORNING_HANDOFF.md` — zero-explanation resume: results, hashes,
   disclosures, and DONE / ABANDONED / NOT STARTED
2. `REPORT.md` — the two-page finding
3. `docs/LIMITATIONS.md` — read before defending anything; §0 is a collapse we found ourselves
4. `docs/DEMO.md` — the spoken script and the ranked adversarial answers
5. `docs/PRIOR_WORK.md` — what came before, marked pre-event
6. `docs/ORIGINS.md` — why the project is built this way, and what died to get here
7. `docs/METHOD_RULES.md` — the rules this code obeys
8. `docs/DATA_DICTIONARY.md` — every frozen column in plain English

Reference: `docs/MATRIX_PREREG.md`, `docs/SCOPE_STATEMENT.md`,
`results/figures/CAPTIONS.md`.

## Non-negotiable

- **Pathway-level claims only. No novel gene is named anywhere.** Guide-pair
  concordance is −0.019; per-gene calls are not reproducible.
- **Never revise a pre-registration after seeing a value.** Append a correction
  below the original instead.
- **Preserve negatives.** They are the result here, not a shortfall.
- **External data decides.** Deterministic code owns every quantitative claim.
- **Figures come from our own data.** A protein render would imply a gene-level
  claim we have forbidden.
- **Do not spawn agents or subagents** without explicit authorisation.
- **No claims about how fast this was built.**

## Layout

| Path | Contents |
|---|---|
| `results/frozen/` | the frozen interface — everything downstream reads only this |
| `results/sensitivity/` | post-freeze checks, explicitly not pre-registered |
| `results/figures/` | four figures + `CAPTIONS.md`, the single source of caption wording |
| `src/` | run as `.venv/bin/python -m src.<module>` |
| `app.py` | expo page, `.venv/bin/streamlit run app.py` |
| `data/genesets/` | MSigDB v2026.1.Hs, committed |
| `data/raw/` | git-ignored; re-fetch instructions in `docs/MORNING_HANDOFF.md` §8 |

## Environment

Default `python3` is 3.9 and will not work — use `.venv/bin/python` (3.12).
The venv has **no pip**; install with `uv pip install --python .venv/bin/python`.
`urllib`'s SSL chain is intercepted here — use `curl`.
figshare returns 403 on HEAD but 206 on ranged GET.
Replogle `X` is a perturbation-**effect** matrix, not expression; absolute
expression is `var/mean`. Non-finite entries exist — **mask, never impute**.

## Scope

Computational only. No wet-lab protocols, no dosing, no clinical or therapeutic
recommendation. Transcriptional movement is not phenotypic reversal.
