# Morning handoff — 2026-08-15

**For a cold session. Read this file and `HACKATHON_PLAN.md`. Nothing else is
required to resume.**

| | |
|---|---|
| Check-in | **08:30 AM** |
| Build I | **1:00 PM** |
| Submission | **Sunday 10:45 AM** |
| Real build time | ~10 hours |

---

## 1. The decision, already made

**Track A — "Build an AI Scientist." Candidate 1, the reversal map.
Program: proteostasis, UPR arm.**

Selected by the user 2026-08-14 after the gate passed. **Do not reopen this.**
The other three programs — integrated stress response, senescence, interferon
response — failed the gate and are **not revisited**.

⚠ **Scope limit that came from the gate itself:** the pass covers the **UPR /
protein-folding arm only**. The broad `GOBP_PROTEASOMAL_PROTEIN_CATABOLIC_PROCESS`
set FAILED the variance test (R = 1.00–1.02, n.s.). Keep every claim scoped to
the UPR; do not let it drift into "proteostasis" generally.

## 2. The commit

**`280c62617fd02804380df400cfebb6d969b5345f`** (`280c626`)
— *"Gate C1 PASSES for proteostasis (UPR); three of four programs FAIL"*

| Artifact | sha256 |
|---|---|
| `docs/GATE_C1_PREREGISTRATION.md` | `d7d90e41332a7c70cf7a5b2d2678ceb9be85d153e0185be2f110e0e3f448d915` |
| `src/gate_c1.py` | `f543b22efe075d034575e105f7a1e5aa31616b4280e302053e7a3967aacb7c55` |

This commit is the provenance claim: thresholds were hashed **before** any
program-specific value was computed, and the commit timestamp proves the
pre-registration precedes the results. `src/gate_c1.py` is committed
byte-identical to the version that produced the numbers, so its hash verifies —
it therefore still carries an absolute scratchpad `GMT_DIR`. **Repoint `GMT_DIR`
to `data/genesets/` before re-running**, and note that doing so changes the hash.

Gate outcome: **P4 proteostasis (UPR) PASS 3/3.** P1 ISR, P2 senescence,
P3 interferon all FAIL. Full numbers: `docs/GATE_C1_RESULTS.md`.

## 3. The three answers from last night

### a) What the 24.2% is a ceiling on

- **Numerator: 2,381** — unique gene targets perturbed in **both** K562 and RPE1.
- **Denominator: 9,823** — unique gene targets perturbed in K562.
- **2,381 / 9,823 = 24.2%.**

It is a ceiling on **how much of the K562 ranked map can be looked up in RPE1 at
all** — the *addressable* fraction, before any question of whether replication
succeeds. The other 7,442 knockdowns have no RPE1 measurement: they can neither
replicate nor fail, they are simply absent. It is **not** a ceiling on the
replication rate among covered genes.

### b) Is the RPE1 arm independent replication?

**No. It is partial replication with a stated — and non-random — denominator.**

Within its coverage it *is* genuinely independent: different cell type (retinal
pigment epithelium vs CML blast), separately screened, separate experiment. Two
things stop it being replication of the map:

1. Coverage is 24.2% — three of every four hits are unaddressable.
2. **RPE1's 2,383 targets are the essential-gene subset** (99.9% ⊂ K562's set).
   Essential genes are exactly those whose knockdown has large fitness and
   transcriptional consequences, so the covered quarter is enriched for
   strong-effect genes. Replication measured inside it runs systematically
   optimistic versus a random 24.2% sample.

⚠ **Consequence for the pipeline:** the genes RPE1 can replicate are
disproportionately the genes step 4's essentiality filter exists to flag. The
replication arm and the toxicity filter contend over the same subset. Expect
this and report it rather than discovering it on stage.

**On-screen label, every time an RPE1 rank appears:**
`RPE1 rank — or NOT COVERED (2,381/9,823 = 24.2%, essential-gene subset)`

### c) The anchors, by disease

| Accession | Disease | n |
|---|---|---:|
| GSE112680 | Amyotrophic lateral sclerosis (whole blood) | 376 |
| GTEx v10 | **Not a disease** — normal-tissue ageing, postmortem donors | 980 |
| GSE65391 | Paediatric systemic lupus erythematosus (longitudinal + clinical) | 996 |
| **GSE24080** | **Multiple myeloma** (MAQC-II) | **559** |

**Best fit: GSE24080, multiple myeloma.** Myeloma plasma cells carry an extreme
immunoglobulin folding and secretory load, making them constitutively
UPR-dependent — and proteasome inhibition being standard of care is the clinical
demonstration that proteostasis is the operative axis. Runner-up is ALS
(proteostasis collapse is central to the pathology) but GSE112680 is **whole
blood** while the pathology is in motor neurons, so the tissue is wrong for a
UPR readout.

All four anchors were confirmed by live API call, not from memory.

## 4. Open risks — say these before a judge does

1. **Transcriptional reversal is not phenotypic reversal.** The most likely
   attack. A knockdown that moves the UPR signature has not been shown to rescue
   any cellular or disease phenotype. Put this on the slide ourselves.
2. **The top hit may be a known upstream regulator.** Rediscovery is a real
   possibility. If the hit is a canonical UPR regulator, say so plainly and
   frame it as a positive control validating the method — never present a
   rediscovery as a discovery.
3. **Track A is the most crowded track at this event.** Differentiation comes
   from the evidence chain and the honest nulls, not from novelty of concept.
4. **The RPE1 arm is 24.2% partial with a non-random denominator** — second-most
   likely attack if presented as independent replication.
5. **`PAPERCLIP_API_KEY` is not set.** Pipeline step 1 is blocked until it is.
   Fallback: ship `HALLMARK_UNFOLDED_PROTEIN_RESPONSE` (113 genes, committed at
   `data/genesets/h.all.v2026.1.Hs.symbols.gmt`) labelled explicitly as uncited.
6. **Sunday morning is 105 minutes for four items.** If something must be cut,
   cut demo polish — never the clean-clone reproduction check.

## 5. State of the substrate

| Asset | Status |
|---|---|
| `data/raw/K562_gwps_normalized_bulk_01.h5ad` | ✅ 11,258 × 8,248, md5 verified, loads |
| `data/raw/rpe1_normalized_bulk_01.h5ad` | ✅ 2,679 × 8,749, md5 verified, loads |
| `data/genesets/*.v2026.1.Hs.symbols.gmt` | ✅ committed (4 files, MSigDB v2026.1.Hs) |
| `data/raw/CRISPRGeneEffect.csv` (DepMap 24Q4) | ✅ 409 MB, md5 `6edf7ade…` verified, **17,916 genes**, parses |
| `data/raw/Model.csv` (DepMap 24Q4) | ✅ 631 KB, md5 `675210d1…` verified, **2,105 lines × 47 cols**; `OncotreeLineage` (35) and `OncotreePrimaryDisease` (96) both present |
| `AvanaLogfoldChange.csv` (3.4 GB) | ❌ **not downloaded** — decide in Build II |
| `KYLogfoldChange.csv` (1.6 GB) | ❌ **not downloaded** — decide in Build II |
| `src/reversal_score.py` | ✅ skeleton, interfaces stubbed, **never run** |

⚠ Step 4 calls for **both** Broad Avana and Sanger KY. `CRISPRGeneEffect.csv` is
the merged Chronos matrix; the two per-library logfold files are 5 GB combined
and are **not** on disk. Decide early in Build II whether cross-library
adjudication is worth that download, or whether the merged matrix suffices for
the flag. Do not discover this at 6 PM.

### Environment landmines — already measured, do not rediscover

- Default `python3` is **3.9 and will not work**. Use `.venv/bin/python` (3.12.0,
  verified working). No system-python3 invocation exists in the active tree.
- Python `urllib`'s SSL chain is **intercepted** here and returns well-formed
  garbage with exit code 0. **Use `curl` for every network call.**
- **figshare returns 403 on HEAD but 206 on ranged GET.** Never conclude a file
  is missing from a HEAD. Resolve real URLs via
  `https://api.figshare.com/v2/articles/<id>`.
- `X` in the Replogle files is a perturbation-**effect** matrix (~50% negative,
  median ~0), **not** absolute expression. Absolute expression is `var/mean`.
- Non-finite entries exist (0.0074% K562 / 0.0011% RPE1). **Mask, do not impute.**

## 6. First three commands

```bash
cd /Users/alexvintera/figure-contract

# 1. environment + substrate integrity (~10 s)
.venv/bin/python -c "
import anndata as ad
for p in ['data/raw/K562_gwps_normalized_bulk_01.h5ad','data/raw/rpe1_normalized_bulk_01.h5ad']:
    print(p.split('/')[-1], ad.read_h5ad(p, backed='r').shape)
"

# 2. confirm the DepMap fetch landed and is readable
ls -lh data/raw/CRISPRGeneEffect.csv data/raw/Model.csv && \
md5 -q data/raw/CRISPRGeneEffect.csv   # expect 6edf7ade09b9b34199210b559d4745d3
                                       # Model.csv  675210d17675f3517b0ce39a3c274f16

# 3. re-verify the gate still reproduces (repoint GMT_DIR to data/genesets first)
.venv/bin/python src/gate_c1.py | tail -20
```

Then open `docs/HACKATHON_PLAN.md` and start Build I at 1:00 PM.

## 7. Standing prohibitions

**LIFTED for the demo layer only:** no-UI / no-frontend / no-Figma. Frontend is
authorised, **built Sunday morning over frozen precomputed tables, never before
the science lands.** A UI that runs analysis live remains prohibited.

**Still in force:** no agents, no subagents, no broad prior-art sweeps, do not
resurrect FigContract / RETRIAL / RescueMap-ENOUGH / the ILD project, do not read
`docs/archive/`, do not redefine a kill criterion after seeing data.
