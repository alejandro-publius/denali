# Gate C1 — pre-registration

Written BEFORE any program-specific statistic was computed. Only global,
program-agnostic properties of the two files were inspected first (shape, dtype,
value encoding, extent of non-finite values) — these were needed to know the
UNITS in which a threshold can be stated, and they carry no information about
any individual program.

## Substrate (verified by download, this session)

| File | md5 (matches figshare) | shape (perturbations x genes) |
|---|---|---|
| `data/raw/K562_gwps_normalized_bulk_01.h5ad` | `a3dfaa94ea8724217f5ecb1e14a5f0c8` | 11,258 x 8,248 |
| `data/raw/rpe1_normalized_bulk_01.h5ad` | `6f1e7d6a09e2f869759e3c4526b7f171` | 2,679 x 8,749 |

Encoding: `X` is a perturbation-EFFECT matrix (≈50% negative, median ≈0), not an
absolute expression matrix. `var/mean` holds per-gene absolute expression level.
Non-finite cells: 0.0074% (K562), 0.0011% (RPE1) — masked, not imputed.

## Gene sets — MSigDB v2026.1.Hs (human symbols)

Hallmark (`h.all.v2026.1.Hs.symbols.gmt`, 50 sets) was searched for all four
programs. It contains sets for interferon and (partially) proteostasis. It
contains **NO senescence set and NO integrated-stress-response set.** Substitutes
are drawn from the same release, named explicitly, and labelled as substitutes.
Each program is evaluated on a PRIMARY set; SECONDARY sets are scored too so the
verdict does not hinge on one arbitrary set choice.

| Program | Hallmark status | PRIMARY set | SECONDARY set(s) |
|---|---|---|---|
| P1 Integrated stress response | **ABSENT** | `GOBP_INTEGRATED_STRESS_RESPONSE_SIGNALING` (54) | `REACTOME_PERK_REGULATES_GENE_EXPRESSION` (32); `REACTOME_ATF4_ACTIVATES_GENES_IN_RESPONSE_TO_ENDOPLASMIC_RETICULUM_STRESS` (27) |
| P2 Senescence | **ABSENT** | `REACTOME_CELLULAR_SENESCENCE` (197) | `GOBP_CELLULAR_SENESCENCE` (109); `REACTOME_SENESCENCE_ASSOCIATED_SECRETORY_PHENOTYPE_SASP` (111) |
| P3 Interferon response | **PRESENT** | `HALLMARK_INTERFERON_ALPHA_RESPONSE` (97) | `HALLMARK_INTERFERON_GAMMA_RESPONSE` (200) |
| P4 Proteostasis | **PARTIAL** (UPR arm only) | `HALLMARK_UNFOLDED_PROTEIN_RESPONSE` (113) | `REACTOME_PROTEIN_FOLDING` (98); `GOBP_PROTEASOMAL_PROTEIN_CATABOLIC_PROCESS` (671) |

## Criterion 1 — MEASURABILITY (three sub-tests, both cell lines)

Statistics, fixed now:

- **1a Presence** — fraction of PRIMARY-set member symbols found in the file's
  `var` gene_name index.
- **1b Expression vs background** — median `var/mean` over present members vs
  median `var/mean` over all measured genes. One-sided Mann-Whitney U
  (members > background).
- **1c Variance across perturbations** — per-gene standard deviation of `X` down
  the perturbation axis (non-finite masked), median over present members vs
  median over all measured genes. One-sided Mann-Whitney U (members > background).

Thresholds, fixed now:

- **1a PASS** iff fraction present >= 0.50 AND absolute count present >= 25.
  Rationale: the measured space is ~8.2-8.7k genes, so a random set recovers
  ~40%; 0.50 requires the program to be no worse than mildly depleted, and 25
  members is the floor for a stable program score.
- **1b PASS** iff median ratio (members/background) >= 1.0 AND p < 0.05.
- **1c PASS** iff median ratio (members/background) >= 1.0 AND p < 0.05.
- **CRITERION 1 PASS** iff 1a AND 1b AND 1c pass in **BOTH** K562 and RPE1.

Rationale for 1c being decisive: if a program's genes do not move across 11,258
knockdowns, then no knockdown reverses it, and the reversal map is undefined for
that program regardless of biology.

## Criterion 2 — CELL-INTRINSIC

Judgement, stated with reasoning, on whether the program is cell-autonomous or
requires tissue architecture / multiple cell types / paracrine signalling.
FAIL if the program's definition depends on cells the substrate does not contain.

## Criterion 3 — ANCHOR

A named, PUBLIC, PATIENT-LEVEL dataset in which the program could later be
connected to human disease. Availability must be confirmed by a live request
this session. Claiming availability from memory is a FAIL.

## Standing rules

- No threshold is revised after seeing a result.
- A program failing any criterion is reported FAIL. It is not rescued.
- The gate does not pick a program; it reports which are eligible.
