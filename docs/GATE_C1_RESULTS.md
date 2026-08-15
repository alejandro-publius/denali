> ⚠ **SUPERSEDED COUNT.** The figure ~9,866 knockdowns below was a
> planning-stage approximation. The operative count for every reported
> result is **9,837**. See the appended note in `docs/MATRIX_PREREG.md`.

# Gate C1 — Candidate 1 (reversal map) measurability gate. RESULTS.

**Run 2026-08-15.** This is the gate pre-registered in `NEXT.md`, not the project.
No pipeline code was written; no program was chosen.

> **VERDICT: 1 of 4 programs passes all three criteria — P4 proteostasis (UPR
> arm). The other three fail, each for a different and non-rescuable reason.**
>
> **The gate does not select a program. That decision is the user's.**

---

## 1. Substrate — downloaded and integrity-checked this session

figshare article `20029387`, "Replogle et al. 2022 processed Perturb-seq
datasets", DOI `10.25452/figshare.plus.20029387.v1`, **CC BY 4.0**.
Retrieved by ranged GET (`HTTP 206`); HDF5 magic `\x89HDF\r\n\x1a\n` confirmed
on both before download.

| File | bytes | md5 (matches figshare manifest) | shape |
|---|---:|---|---|
| `data/raw/K562_gwps_normalized_bulk_01.h5ad` | 374,587,922 | `a3dfaa94ea8724217f5ecb1e14a5f0c8` ✓ | 11,258 × 8,248 |
| `data/raw/rpe1_normalized_bulk_01.h5ad` | 95,350,546 | `6f1e7d6a09e2f869759e3c4526b7f171` ✓ | 2,679 × 8,749 |

**Encoding, established before any threshold was set.** `X` is a
perturbation-**effect** matrix (≈50% of entries negative, median ≈0), *not*
absolute expression. Per-gene absolute expression lives in `var/mean`.
Non-finite entries: 0.0074% (K562, 73 gene columns), 0.0011% (RPE1, 2 columns) —
**masked, not imputed**.

### Three substrate facts that correct or extend the planning docs

1. **The measured gene space is ~8.2–8.7k genes, not the transcriptome.** A
   random gene set recovers only ~40% coverage by construction. Every coverage
   number below must be read against that ceiling.
2. **`~9,866 knockdowns` is confirmed.** Parsed 9,823 unique target genes in
   K562 from 11,258 rows (649 multi-transcript rows unparsed; including them
   reaches ~9,866). The docs' previously-UNVERIFIED figure is now **VERIFIED**.
3. ⚠ **RPE1 is not genome-scale.** It carries **2,383** unique targets — the
   essential-gene subset — of which 99.9% are also in K562. **Only 24.2% of K562
   perturbations can be tested in RPE1 at all.** This is a hard ceiling on
   Candidate 1's independent-validation step and was not previously recorded.
   *This is reported as context; it is NOT one of the three pre-registered
   criteria and was NOT used to pass or fail any program.*

## 2. Gene sets — MSigDB v2026.1.Hs, exact identifiers

Source: `https://data.broadinstitute.org/gsea-msigdb/msigdb/release/2026.1.Hs/`.
Hallmark file `h.all.v2026.1.Hs.symbols.gmt`, sha256 `eecaf6da…`, 50 sets.

**All 50 Hallmark sets were enumerated and searched.** Hallmark does not contain
a senescence set or an integrated-stress-response set. It was therefore not
possible to satisfy "Hallmark for all four" as specified. Substitutes are drawn
from the same release, named in full, and **labelled as substitutes** rather than
silently swapped.

| Program | Hallmark status | PRIMARY set (scored) | SECONDARY sets (also scored) |
|---|---|---|---|
| P1 Integrated stress response | **ABSENT** | `GOBP_INTEGRATED_STRESS_RESPONSE_SIGNALING` (54) | `REACTOME_PERK_REGULATES_GENE_EXPRESSION` (32); `REACTOME_ATF4_ACTIVATES_GENES_IN_RESPONSE_TO_ENDOPLASMIC_RETICULUM_STRESS` (27) |
| P2 Senescence | **ABSENT** | `REACTOME_CELLULAR_SENESCENCE` (197) | `GOBP_CELLULAR_SENESCENCE` (109); `REACTOME_SENESCENCE_ASSOCIATED_SECRETORY_PHENOTYPE_SASP` (111) |
| P3 Interferon response | **PRESENT** | `HALLMARK_INTERFERON_ALPHA_RESPONSE` (97) | `HALLMARK_INTERFERON_GAMMA_RESPONSE` (200) |
| P4 Proteostasis | **PARTIAL** — UPR arm only | `HALLMARK_UNFOLDED_PROTEIN_RESPONSE` (113) | `REACTOME_PROTEIN_FOLDING` (98); `GOBP_PROTEASOMAL_PROTEIN_CATABOLIC_PROCESS` (671) |

Secondary sets exist so no verdict rests on one arbitrary set choice.

## 3. Pre-registration

Thresholds were fixed and hashed **before any program-specific value was
computed**; only global, program-agnostic file properties (shape, dtype, value
encoding, non-finite extent) were inspected first, because they determine the
*units* a threshold can be stated in.

Pre-registration sha256 **`d7d90e41332a7c70cf7a5b2d2678ceb9be85d153e0185be2f110e0e3f448d915`**.

- **1a Presence** — PASS iff ≥50% of PRIMARY members found in `var` **and** ≥25 present.
- **1b Expression vs background** — median `var/mean` of members vs all measured
  genes. PASS iff ratio ≥1.0 **and** one-sided Mann–Whitney p<0.05.
- **1c Variance across perturbations** — per-gene SD of `X` down the perturbation
  axis, members vs background. PASS iff ratio ≥1.0 **and** one-sided MWU p<0.05.
- **Criterion 1 PASS** iff 1a ∧ 1b ∧ 1c in **both** K562 and RPE1.

1c is the decisive one: *if a program's genes do not move across 11,258
knockdowns, no knockdown reverses it, and the reversal map is undefined for that
program regardless of the biology.*

No threshold was revised after seeing a result.

## 4. Criterion 1 — measurability, full numbers

`R` = median(members)/median(background). `p` = one-sided Mann–Whitney.
Bold = PRIMARY set.

| Program | Set | Cell | present/declared | frac | 1a | expr R | expr p | 1b | SD R | SD p | 1c |
|---|---|---|---:|---:|:--:|---:|---:|:--:|---:|---:|:--:|
| **P1** | **GOBP_INTEGRATED_STRESS_RESPONSE_SIGNALING** | K562 | 39/54 | .722 | ✅ | 1.29 | 1.3e-01 | ❌ | 1.02 | 1.9e-01 | ❌ |
| **P1** | **GOBP_INTEGRATED_STRESS_RESPONSE_SIGNALING** | RPE1 | 39/54 | .722 | ✅ | 1.37 | 1.8e-02 | ✅ | 1.08 | 8.1e-02 | ❌ |
| P1 | REACTOME_PERK_REGULATES_GENE_EXPRESSION | K562 | 26/32 | .812 | ✅ | 1.80 | 1.4e-04 | ✅ | 1.03 | 3.0e-02 | ✅ |
| P1 | REACTOME_PERK_REGULATES_GENE_EXPRESSION | RPE1 | 28/32 | .875 | ✅ | 1.31 | 5.3e-02 | ❌ | 1.18 | 1.1e-02 | ✅ |
| P1 | REACTOME_ATF4_ACTIVATES_GENES… | K562 | 22/27 | .815 | ❌ | 1.72 | 3.8e-03 | ✅ | 1.02 | 1.4e-01 | ❌ |
| P1 | REACTOME_ATF4_ACTIVATES_GENES… | RPE1 | 24/27 | .889 | ❌ | 1.20 | 2.8e-01 | ❌ | 1.02 | 5.0e-02 | ❌ |
| **P2** | **REACTOME_CELLULAR_SENESCENCE** | K562 | 102/197 | .518 | ✅ | 1.33 | 1.1e-02 | ✅ | 1.00 | 5.1e-01 | ❌ |
| **P2** | **REACTOME_CELLULAR_SENESCENCE** | RPE1 | 112/197 | .569 | ✅ | 1.06 | 1.0e-01 | ❌ | 0.96 | 7.9e-01 | ❌ |
| P2 | GOBP_CELLULAR_SENESCENCE | K562 | 60/109 | .550 | ✅ | 1.14 | 2.2e-01 | ❌ | 0.99 | 9.1e-01 | ❌ |
| P2 | GOBP_CELLULAR_SENESCENCE | RPE1 | 70/109 | .642 | ✅ | 1.13 | 6.1e-02 | ❌ | 1.02 | 1.7e-01 | ❌ |
| P2 | REACTOME_…SASP | K562 | 38/111 | .342 | ❌ | 1.68 | 2.4e-03 | ✅ | 1.01 | 1.1e-01 | ❌ |
| P2 | REACTOME_…SASP | RPE1 | 45/111 | .405 | ❌ | 1.81 | 2.1e-03 | ✅ | 1.02 | 7.7e-02 | ❌ |
| **P3** | **HALLMARK_INTERFERON_ALPHA_RESPONSE** | K562 | 40/97 | .412 | ❌ | **0.88** | 5.3e-01 | ❌ | 1.06 | 8.7e-04 | ✅ |
| **P3** | **HALLMARK_INTERFERON_ALPHA_RESPONSE** | RPE1 | 53/97 | .546 | ✅ | **0.76** | 9.9e-01 | ❌ | 1.02 | 3.6e-01 | ❌ |
| P3 | HALLMARK_INTERFERON_GAMMA_RESPONSE | K562 | 74/200 | .370 | ❌ | **0.86** | 6.5e-01 | ❌ | 1.06 | 3.2e-06 | ✅ |
| P3 | HALLMARK_INTERFERON_GAMMA_RESPONSE | RPE1 | 90/200 | .450 | ❌ | **0.88** | 6.9e-01 | ❌ | 1.12 | 2.8e-03 | ✅ |
| **P4** | **HALLMARK_UNFOLDED_PROTEIN_RESPONSE** | K562 | 94/113 | **.832** | ✅ | **2.25** | 4.0e-09 | ✅ | 1.05 | 4.4e-06 | ✅ |
| **P4** | **HALLMARK_UNFOLDED_PROTEIN_RESPONSE** | RPE1 | 99/113 | **.876** | ✅ | **1.96** | 6.4e-08 | ✅ | **1.27** | 2.4e-10 | ✅ |
| P4 | REACTOME_PROTEIN_FOLDING | K562 | 64/98 | .653 | ✅ | 1.69 | 1.5e-03 | ✅ | 1.02 | 3.2e-03 | ✅ |
| P4 | REACTOME_PROTEIN_FOLDING | RPE1 | 65/98 | .663 | ✅ | 2.15 | 1.8e-08 | ✅ | 1.07 | 1.1e-03 | ✅ |
| P4 | GOBP_PROTEASOMAL_PROTEIN_CATABOLIC_PROCESS | K562 | 442/671 | .659 | ✅ | 1.22 | 4.0e-04 | ✅ | 1.00 | 4.0e-01 | ❌ |
| P4 | GOBP_PROTEASOMAL_PROTEIN_CATABOLIC_PROCESS | RPE1 | 465/671 | .693 | ✅ | 1.21 | 1.4e-03 | ✅ | 1.02 | 7.0e-02 | ❌ |

**Reading the failures.**

- **P1 ISR** fails on **1c variance** — its genes are present (72%) and expressed,
  but they barely move across 11,258 knockdowns (R = 1.02–1.08, n.s.). The
  narrower PERK sub-arm *does* pass 1c in both lines, so the ISR is not uniformly
  dead — but the pre-registered primary set fails, and the primary is what counts.
- **P2 senescence** fails on **1c in every set and both lines** (R = 0.96–1.02,
  all n.s.). This is the cleanest failure in the table: senescence genes are no
  more responsive to genetic perturbation than an average gene.
- **P3 interferon** fails on **1b, and in the informative direction**: ISG
  expression is **below** background (R = 0.76–0.88) in both lines. Unstimulated
  cultured cells contain no interferon, so the program is off. Its genes *do*
  vary (1c passes in 3 of 4), but variance around an unexpressed baseline is not
  a testable program.
- **P4 proteostasis** passes on the primary set and on `REACTOME_PROTEIN_FOLDING`.
  ⚠ It **fails 1c on the broad `GOBP_PROTEASOMAL_PROTEIN_CATABOLIC_PROCESS` set**
  (R = 1.00–1.02, n.s.). **The pass is specific to the UPR/folding arm, not to
  proteostasis writ large.** Any downstream claim must be scoped to the UPR.

## 5. Criterion 2 — cell-intrinsic or tissue-dependent

Cell-line provenance verified live this session via Cellosaurus (not from memory):

- **K562** `CVCL_0004` — blast-phase CML, BCR-ABL1 positive.
  **`TP53` homozygous frameshift p.Gln136fs\*13** (c.406_407insC).
- **hTERT-RPE1** `CVCL_4388` — retinal pigment epithelial cell (`CL_0002586`),
  retina (`UBERON_0001782`), **telomerase-immortalized by TERT transfection**.

| Program | Verdict | Reasoning |
|---|:--:|---|
| P1 ISR | **PASS** | Four sensor kinases (PERK/GCN2/PKR/HRI) → eIF2α → ATF4. Entirely within one cell; no paracrine or architectural requirement. |
| P2 Senescence | **FAIL** | Two problems, both structural. (a) The SASP arm is *definitionally* secretory — its meaning is paracrine action on neighbouring and immune cells that a monoculture does not contain. (b) The arrest arm is disabled in both substrates by construction: senescence arrest is p53-dependent and **K562 is TP53-frameshift homozygous**, while **RPE1 is hTERT-immortalized**, which bypasses replicative senescence. The substrate cannot express the program even in principle. |
| P3 Interferon | **PASS** (mechanism) | JAK–STAT signalling and ISG induction are cell-autonomous. ⚠ But the circuit requires an exogenous ligand that unstimulated culture does not supply — which is exactly what criterion 1b measured. Intrinsic in mechanism, not engaged in this substrate. |
| P4 Proteostasis | **PASS** | ER folding load, HSP chaperones, ERAD and the ubiquitin–proteasome system are strictly intracellular and constitutively active in any proliferating cell. No tissue architecture required. |

## 6. Criterion 3 — independent patient-level anchor

Every anchor below was confirmed by a **live request this session**. Sample
counts are as returned by the API, not recalled.

| Program | Anchor | Verified | Patient-level content |
|---|---|---|---|
| P1 ISR | **GSE112680** | NCBI eutils esummary, `n_samples=376`, *Homo sapiens* | Whole-blood transcriptome in amyotrophic lateral sclerosis; ISR is a prominent axis in ALS/FTD |
| P2 Senescence | **GTEx v10** | `gtexportal.org/api/v2/dataset/subject`, **980 subjects**, age bracket + sex + Hardy scale returned | Donor-level ageing contrast across tissues; expression matrices open |
| P3 Interferon | **GSE65391** | NCBI eutils esummary, `n_samples=996`, *Homo sapiens* | Longitudinal paediatric SLE **with clinical parameters** — the canonical human interferon-signature cohort |
| P4 Proteostasis | **GSE24080** | NCBI eutils esummary, `n_samples=559`, *Homo sapiens* | MAQC-II multiple myeloma — the canonical proteostasis-stressed human disease (proteasome inhibition is standard of care) |

All four programs pass criterion 3. Anchor availability was **not** the
discriminating criterion.

---

## 7. THE GATE TABLE

| Program | 1. Measurable in K562 **and** RPE1 | 2. Cell-intrinsic | 3. Patient-level anchor | **Gate** |
|---|:--:|:--:|:--:|:--:|
| **P1 — Integrated stress response** | ❌ **FAIL** (1c: genes do not vary across perturbations, R=1.02–1.08 n.s.) | ✅ PASS | ✅ PASS (GSE112680, n=376) | ❌ **FAIL** |
| **P2 — Senescence** | ❌ **FAIL** (1c: R=0.96–1.02 n.s. in every set, both lines) | ❌ **FAIL** (SASP is paracrine; K562 TP53-null, RPE1 hTERT-immortalized) | ✅ PASS (GTEx v10, n=980) | ❌ **FAIL** |
| **P3 — Interferon response** | ❌ **FAIL** (1b: expression *below* background, R=0.76–0.88) | ✅ PASS (mechanism only; ligand absent) | ✅ PASS (GSE65391, n=996) | ❌ **FAIL** |
| **P4 — Proteostasis (UPR arm)** | ✅ **PASS** (83–88% present; expr 2.25×/1.96×; SD 1.05×/1.27×; all p≤4.4e-06) | ✅ PASS | ✅ PASS (GSE24080, n=559) | ✅ **PASS** |

---

## What this establishes

Of four candidate cell-intrinsic programs, **exactly one — the unfolded-protein-
response arm of proteostasis — is measurable, cell-intrinsic, and anchorable** in
the Candidate 1 substrate. The three failures are independent and mechanistically
interpretable rather than statistical noise: senescence cannot run in either line
by construction, interferon is switched off without ligand, and the ISR's
canonical gene set does not respond to genetic perturbation.

## What this does NOT establish

- **Not** that a reversal map for the UPR would find anything. Criterion 1 tests
  whether the program is *visible*, not whether any knockdown *opposes* it.
- **Not** that proteostasis is the right program for a disease result. It passed a
  measurability gate, which is a floor, not a recommendation.
- **Not** that P4 generalises beyond the UPR/folding arm — the broad proteasomal
  set fails 1c.
- **Not** that RPE1 replication is feasible for an arbitrary hit: **only 24.2% of
  K562 perturbations exist in RPE1**.
- **Not** that any of these programs is disease-relevant in K562/RPE1. Neither
  line is disease tissue; the anchor cohorts exist precisely because that gap is
  unclosed.
- **No program has been selected.** That is the user's decision.

## Reproduce

```bash
cd <repo root>
# substrate (470 MB, CC BY 4.0, ranged GET — figshare 403s on HEAD)
curl -sL -o data/raw/K562_gwps_normalized_bulk_01.h5ad https://ndownloader.figshare.com/files/35773217
curl -sL -o data/raw/rpe1_normalized_bulk_01.h5ad       https://ndownloader.figshare.com/files/35775512
md5 data/raw/K562_gwps_normalized_bulk_01.h5ad   # a3dfaa94ea8724217f5ecb1e14a5f0c8
md5 data/raw/rpe1_normalized_bulk_01.h5ad        # 6f1e7d6a09e2f869759e3c4526b7f171

# gene sets, MSigDB v2026.1.Hs — committed under data/genesets/, or re-fetch:
for f in h.all c2.cp.reactome c5.go.bp c2.cp.wikipathways; do
  curl -sL -O "https://data.broadinstitute.org/gsea-msigdb/msigdb/release/2026.1.Hs/${f}.v2026.1.Hs.symbols.gmt"
done

.venv/bin/python src/gate_c1.py     # writes gate_c1_criterion1.json
```

## Committed artifacts

| Artifact | Path | sha256 |
|---|---|---|
| Pre-registration | `docs/GATE_C1_PREREGISTRATION.md` | `d7d90e41332a7c70cf7a5b2d2678ceb9be85d153e0185be2f110e0e3f448d915` |
| Gate script | `src/gate_c1.py` | `f543b22efe075d034575e105f7a1e5aa31616b4280e302053e7a3967aacb7c55` |
| Raw output | `results/qc/gate_c1_criterion1.json` | — |
| Gene sets | `data/genesets/*.v2026.1.Hs.symbols.gmt` | Hallmark: `eecaf6da…` |

⚠ **`src/gate_c1.py` is committed byte-identical to the version that produced
these numbers**, so its sha256 still verifies against the value cited above and
in the commit message. It therefore still carries the absolute
`GMT_DIR` scratchpad path from the run environment. **To re-run, repoint
`GMT_DIR` to `data/genesets/`** — do not "fix" it in place without noting that
the hash then changes. Preserving the exact artifact that generated the result
was judged more valuable than a cosmetically clean path.
