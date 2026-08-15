"""MCP server — one tool over the frozen reversal matrix.

Given a program: measured reversibility if we scored it, predicted with
uncertainty if we did not, plus the generated next-experiment proposal.

Reads results/frozen/ only. Never recomputes, never scores.

    .venv/bin/python -m src.mcp_server
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from mcp.server.fastmcp import FastMCP

from src.next_experiment import propose

FROZEN = Path("results/frozen")
mcp = FastMCP("denali")

_S = pd.read_csv(FROZEN / "program_summary.csv")
_P = json.loads((FROZEN / "predictor.json").read_text())
_H = pd.read_csv(FROZEN / "heldout.csv")

SCOPE = ("Pathway-level only. Guide-pair concordance is -0.019, so gene-level "
         "calls are not reproducible and no novel gene is named. Between 56% and "
         "75% of variance in apparent reversibility is measurement quality, not "
         "biology.")


@mcp.tool()
def reversibility(program: str) -> dict:
    """Reversibility of a gene program in the K562 genome-scale CRISPRi screen.

    Returns a measured result if the program is in the frozen 50-program matrix,
    otherwise a prediction with uncertainty. Always returns the generated
    next-experiment proposal and the scope limit.

    Args:
        program: MSigDB program name, e.g. HALLMARK_CHOLESTEROL_HOMEOSTASIS
    """
    row = _S[_S.program == program]
    if not row.empty:
        r = row.iloc[0]
        return {
            "program": program, "status": "MEASURED",
            "rank_of_50": int(r.rank_by_R_p),
            "knockdowns_that_moved_it": int(r.n_hits_q05),
            "call": r.reversibility_call, "call_plain": r.call_plain,
            "passes_measurability_gate": bool(r.passes_measurability_gate),
            "measurability_limited": bool(r.measurability_limited),
            "predicted_from_measurability_alone": float(r.R_p_predicted_from_measurability),
            "residual_that_could_be_biology": float(r.R_p_residual_after_measurability),
            "is_held_out_program": bool(r.is_held_out_program),
            "next_experiment": propose(program, _S),
            "scope_limit": SCOPE,
        }

    h = _H[_H.program == program]
    if not h.empty:
        r = h.iloc[0]
        return {
            "program": program, "status": "HELD_OUT_AND_SCORED",
            "predicted_R_p": float(r.R_p_predicted),
            "observed_R_p": float(r.R_p_observed),
            "knockdowns_that_moved_it": int(r.n_hits_q05),
            "warning": ("Held-out evaluation was UNDERPOWERED AND INCONCLUSIVE "
                        "(1/10 passed the gate). Binary recovery was worse than "
                        "chance. Treat predictions as unvalidated."),
            "scope_limit": SCOPE,
        }

    return {
        "program": program, "status": "UNSCORED",
        "note": ("Not in the frozen matrix. Supply measurability features to get a "
                 "prediction, or score it: ~11 s on the existing pipeline."),
        "prediction_uncertainty_sd": _P["residual_sd"],
        "predictor_validation": ("FAILED on held-out data: balanced accuracy 0.4375, "
                                 "worse than chance, zero true positives. The "
                                 "predictor is reported, not endorsed."),
        "scope_limit": SCOPE,
    }


@mcp.tool()
def provenance() -> dict:
    """Provenance, controls and the honest limits of this dataset."""
    return json.loads((FROZEN / "provenance.json").read_text())


if __name__ == "__main__":
    mcp.run()
