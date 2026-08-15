"""The caveats the callable surface attaches to every answer.

Split out of `src/mcp_server.py` for one reason: the page claims the server
reports its own failure verbatim, and the only way to make that claim checkable
is for both to read the same string object. A copy-paste would drift silently
and the claim would quietly become false.

Every number here is read from `results/frozen/` at import. Nothing is typed in.
stdlib + pandas only, so the page can import this without the MCP dependency.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

FROZEN = Path("results/frozen")

_EVAL = json.loads((FROZEN / "heldout_evaluation.json").read_text())
_PROV = json.loads((FROZEN / "provenance.json").read_text())
_CTRL = pd.read_csv(FROZEN / "controls.csv")

CONCORDANCE = float(_CTRL.loc[_CTRL.control == "guide_pair_concordance", "value"].iloc[0])
R2_LO = _PROV["deciding_statistic"]["adjusted_r2_x_independent_only"]
R2_HI = _PROV["deciding_statistic"]["adjusted_r2_all_six"]
BAL = _EVAL["axis2_balanced_accuracy"]
TP = _EVAL["axis2_confusion"]["tp"]
N_GATE = _EVAL["n_passing_gate"]
N_HELD = _EVAL["n_heldout"]

SCOPE = (f"Pathway-level only. Guide-pair concordance is {CONCORDANCE:+.3f}, so "
         f"gene-level calls are not reproducible and no novel gene is named. "
         f"Between {R2_LO:.0%} and {R2_HI:.0%} of variance in apparent "
         f"reversibility is measurement quality, not biology.")

VALIDATION = (f"FAILED on held-out data: balanced accuracy {BAL:.4f}, worse than "
              f"chance, {TP} true positives. The predictor is reported, not "
              f"endorsed.")

HELDOUT_WARNING = (f"Held-out evaluation was UNDERPOWERED AND INCONCLUSIVE "
                   f"({N_GATE}/{N_HELD} passed the gate). Binary recovery was worse "
                   f"than chance. Treat predictions as unvalidated.")

UNSCORED_NOTE = ("Not in the frozen matrix. Supply measurability features to get a "
                 "prediction, or score it on the existing pipeline.")


def unscored(program: str, residual_sd: float) -> dict:
    """The answer for a program we never scored.

    Lives here rather than inside the server so the page can render the real
    response instead of a transcription of it. The interesting property of this
    branch is that the tool volunteers its own failure before it is asked.
    """
    return {
        "program": program,
        "status": "UNSCORED",
        "note": UNSCORED_NOTE,
        "prediction_uncertainty_sd": residual_sd,
        "predictor_validation": VALIDATION,
        "scope_limit": SCOPE,
    }
