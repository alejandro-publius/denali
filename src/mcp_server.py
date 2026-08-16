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

from src.answers import HELDOUT_WARNING, SCOPE, refuse, unscored
from src.next_experiment import propose

# Anchored to this file, NOT to the caller's cwd. An MCP client launches the
# server from wherever it happens to be, so a relative path here meant a
# stranger wiring this into their agent got FileNotFoundError on
# results/frozen/heldout_evaluation.json. Found by starting the server from
# /tmp the way a client actually would.
FROZEN = Path(__file__).resolve().parents[1] / "results" / "frozen"
# `mcp` is an optional dependency. The server ships as a tool for agents; the study
# reproduces without it. Importing FastMCP at module scope meant a clone that had not
# installed one extra package could not even IMPORT this file -- which aborted the whole
# invariant suite, because the suite imports this module to check the refusal paths.
# Every check above that import already passed and none of them were reported.
try:
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("denali")
except ModuleNotFoundError:                                  # pragma: no cover
    class _Unserved:
        """Keeps the tool functions importable and callable without `mcp` present."""
        @staticmethod
        def tool(*_a, **_k):
            return lambda fn: fn

        @staticmethod
        def run():
            raise SystemExit("pip install mcp to serve this; the study reproduces "
                             "without it and every tool function is importable now.")
    mcp = _Unserved()

_S = pd.read_csv(FROZEN / "program_summary.csv")
_P = json.loads((FROZEN / "predictor.json").read_text())
_H = pd.read_csv(FROZEN / "heldout.csv")


@mcp.tool()
def reversibility(program: str) -> dict:
    """Reversibility of a gene program in the K562 genome-scale CRISPRi screen.

    Returns a measured result if the program is in the frozen 50-program matrix,
    otherwise a prediction with uncertainty. Always returns the generated
    next-experiment proposal and the scope limit.

    Args:
        program: MSigDB program name, e.g. HALLMARK_CHOLESTEROL_HOMEOSTASIS
    """
    blocked = refuse(program)
    if blocked is not None:
        return blocked

    # Case-insensitive, matching the refusals. A companion fix made `refuse()`
    # case-insensitive and left the LOOKUP exact, which is the worse half of the
    # asymmetry: a lowercase program name returned UNSCORED, i.e. a confident
    # wrong answer ("not in the frozen matrix") rather than a refusal. Agents
    # normalise case; MSigDB names are conventionally upper.
    _q = (program or "").strip()
    row = _S[_S.program.str.upper() == _q.upper()]
    if not row.empty:
        r = row.iloc[0]
        program = r.program          # answer under the canonical name
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
            "warning": HELDOUT_WARNING,
            "scope_limit": SCOPE,
        }

    return unscored(program, _P["residual_sd"])


@mcp.tool()
def provenance() -> dict:
    """Provenance, controls and the honest limits of this dataset."""
    return json.loads((FROZEN / "provenance.json").read_text())


if __name__ == "__main__":
    mcp.run()
