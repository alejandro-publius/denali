"""SKELETON ONLY — proteostasis (UPR) reversal map. NOT YET IMPLEMENTED.

    .venv/bin/python -m src.reversal_score --help

Every function below raises NotImplementedError on purpose. This file exists so
that Build I starts from fixed interfaces rather than from a blank editor. It
was written the night before and **has never been run against data**.

Do not implement scoring here before the Build I block. Do not let a UI import
this module and run it live — the demo reads frozen tables only.


ENVIRONMENT LANDMINES — all measured on this machine, do not rediscover them
---------------------------------------------------------------------------
* Default `python3` is **3.9** and will not work. Use `.venv/bin/python`
  (3.12.0). Confirmed working 2026-08-14.
* Python `urllib`'s SSL chain is **intercepted** on this machine and returns
  well-formed garbage with exit code 0. **Use `curl` for every network call.**
* **figshare returns HTTP 403 on HEAD but 206 on ranged GET.** Never conclude a
  file is unavailable from a HEAD request. Resolve real download URLs through
  `https://api.figshare.com/v2/articles/<id>`.
* **`PAPERCLIP_API_KEY` is NOT set.** Pipeline step 1 (cited gene set) is
  blocked until it is. Fallback is defined in `docs/HACKATHON_PLAN.md`: ship the
  gate's `HALLMARK_UNFOLDED_PROTEIN_RESPONSE` (113 genes, committed under
  `data/genesets/`) and label it explicitly as uncited.


SUBSTRATE FACTS ESTABLISHED BY THE GATE (docs/GATE_C1_RESULTS.md, commit 280c626)
---------------------------------------------------------------------------------
* `X` is a perturbation-EFFECT matrix, ~50% negative, median ~0. It is NOT
  absolute expression. Absolute per-gene expression is in `var/mean`.
* Non-finite entries exist: 0.0074% of K562 (73 gene columns), 0.0011% of RPE1
  (2 columns). **Mask them. Do not impute.**
* K562: 11,258 rows -> 9,823 unique target genes. RPE1: 2,679 rows -> 2,383.
* **Only 2,381 / 9,823 = 24.2% of K562 targets exist in RPE1**, and that subset
  is the *essential-gene* subset, not a random sample. This is partial
  replication with a non-random denominator. Never label it independent
  replication of the map.
* The gate passed the **UPR / protein-folding arm only**. The broad
  `GOBP_PROTEASOMAL_PROTEIN_CATABOLIC_PROCESS` set FAILED the variance test.
  Keep every claim scoped to the UPR.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

K562 = Path("data/raw/K562_gwps_normalized_bulk_01.h5ad")
RPE1 = Path("data/raw/rpe1_normalized_bulk_01.h5ad")
DEPMAP_EFFECT = Path("data/raw/CRISPRGeneEffect.csv")
DEPMAP_MODEL = Path("data/raw/Model.csv")
HALLMARK = Path("data/genesets/h.all.v2026.1.Hs.symbols.gmt")

PROGRAM_SET = "HALLMARK_UNFOLDED_PROTEIN_RESPONSE"

# Pre-declared so a threshold cannot be chosen after seeing the ranking.
# TODO(Build I): fix these BEFORE the first score is computed, and record them
# in a hashed pre-registration exactly as the gate did.
ESSENTIALITY_FLAG_THRESHOLD = None  # DepMap Chronos gene effect below which a
#                                     hit is flagged as "scores because it kills"
N_REPORTED = None                   # size of the "next four" table


@dataclass(frozen=True)
class ProgramGene:
    """One member of the proteostasis program, with its evidence."""
    symbol: str
    citation: str | None      # None => uncited fallback path was used
    source: str               # "paperclip" | "msigdb_hallmark_fallback"


@dataclass(frozen=True)
class ReversalHit:
    """One knockdown, scored against the program."""
    target: str
    reversal_score: float
    k562_rank: int
    rpe1_rank: int | None     # None => NOT COVERED (see 24.2% denominator)
    depmap_avana: float | None
    depmap_ky: float | None
    essentiality_flagged: bool


# --- step 1 -----------------------------------------------------------------
def build_program(use_paperclip: bool = True) -> list[ProgramGene]:
    """Pipeline step 1. Cited proteostasis gene set, one citation per gene.

    If PAPERCLIP_API_KEY is unset, fall back to PROGRAM_SET from HALLMARK and
    mark every gene source='msigdb_hallmark_fallback', citation=None. The
    fallback must be visible in the UI, not silently substituted.
    """
    raise NotImplementedError("Build I")


# --- step 2 -----------------------------------------------------------------
def score_k562(program: list[ProgramGene]) -> list[ReversalHit]:
    """Pipeline step 2. Score all ~9,823 knockdowns for opposition to program.

    Pseudobulk + classical statistics. No neural model in this path -- the
    co-host's own challenge found pseudobulk + classical features beat pure
    neural approaches (docs/WINNING_PATTERNS.md section 7).

    Report SEVERAL metrics, not one headline number. Mask non-finite entries.
    """
    raise NotImplementedError("Build I")


# --- step 3 -----------------------------------------------------------------
def replicate_rpe1(hits: list[ReversalHit]) -> list[ReversalHit]:
    """Pipeline step 3. Fill rpe1_rank, or leave None where not covered.

    MUST return the coverage denominator alongside the ranks so the UI can print
    "2,381 / 9,823 = 24.2%, essential-gene subset" on screen.
    """
    raise NotImplementedError("Build II")


# --- step 4 -----------------------------------------------------------------
def filter_essentiality(hits: list[ReversalHit]) -> list[ReversalHit]:
    """Pipeline step 4. DepMap 24Q4, Broad Avana AND Sanger KY.

    Flag any hit that only scores because the cell is dying. Do NOT drop flagged
    hits -- the demo must show at least one gene the filter killed.
    """
    raise NotImplementedError("Build II")


# --- step 9 -----------------------------------------------------------------
def export_frozen_tables(hits: list[ReversalHit], out: Path) -> None:
    """Freeze results to disk. The MCP server and Streamlit page read ONLY this.

    Nothing downstream recomputes. The demo is a view over frozen tables.
    """
    raise NotImplementedError("Build III")


def main() -> int:
    raise SystemExit(
        "SKELETON ONLY -- scoring is not implemented and must not run tonight.\n"
        "See docs/HACKATHON_PLAN.md. Build I starts 1:00 PM."
    )


if __name__ == "__main__":
    raise SystemExit(main())
