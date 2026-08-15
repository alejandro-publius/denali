# Next

**Blocked on a user decision: which candidate.** See `RESELECTION_CANDIDATES.md`
for the full chains, verified datasets, scorecard and risks.

---

## If Candidate 1 (recommended) — the reversal map

**Do not write analysis code until the gate passes.**

### Step 0 — name the program

Pick a **cell-intrinsic** disease-associated transcriptional program. Plausible:
integrated stress response, senescence, interferon response, proteostasis
collapse. **Not** a tissue-specific program — K562 is leukaemia and RPE1 is
retinal epithelium, and forcing lung or liver biology onto them repeats
Candidate 2's error.

### Step 1 — the gate (pre-register it, then run it)

1. **Measurability.** Are the program's genes expressed and *variable* across
   perturbations in `K562_gwps_normalized_bulk_01.h5ad` and
   `rpe1_normalized_bulk_01.h5ad`? A program at background is untestable.
2. **Cell-intrinsic.** Is the program defined by cell-autonomous biology rather
   than tissue architecture or cell-cell composition?
3. **Anchor.** Does an independent patient-level dataset exist to connect the
   result back to human disease later?

**If any fails, the candidate dies at the gate.** Do not build around it.

### Step 2 — only after the gate

```
score all ~9,866 knockdowns for opposition to the program   (K562)
  → replicate the top hits in RPE1 (different cell type, independent screen)
  → DepMap control: is reversal real regulation, or is the gene simply essential
    and the cell dying?
  → named gene + ranked reversal map
```

### Downloads (verified, ~470 MB for the core)

```bash
mkdir -p data/raw
# Replogle genome-scale Perturb-seq pseudobulk, CC BY 4.0
#   figshare article 20029387 -> K562_gwps_normalized_bulk_01.h5ad  (375 MB)
#                                rpe1_normalized_bulk_01.h5ad        ( 95 MB)
# DepMap 24Q4 Public, CC BY 4.0
#   figshare article 27993248 -> CRISPRGeneEffect.csv, Model.csv
# Resolve download_url via:
#   curl -sL "https://api.figshare.com/v2/articles/<id>" | python -c "..."
# NOTE: figshare returns 403 on HEAD but 206 on ranged GET. Use GET.
```

## If Candidate 2 or 3

Both are fully specified in `RESELECTION_CANDIDATES.md` with verified data and
their own risks. Candidate 2's difficulty is lineage confounding; Candidate 3's
is that it is closer to a methods observation than a disease discovery.

## Standing prohibitions

- **No agents or subagents without explicit authorisation**, and any authorised
  agent must be told not to spawn children.
- No UI, Figma, frontend or demo animation.
- No novelty/prior-art sweep beyond the targeted check already done.
- **Do not resurrect** FigContract, RETRIAL, RescueMap/ENOUGH, or the ILD gradient
  project.
- Do not read `docs/archive/` unless historical context is explicitly requested.
