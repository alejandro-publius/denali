"""Freeze the three next-experiment proposals the expo page renders.

The page reads frozen tables and computes nothing, so the loop shown in
`docs/DEMO.md` beat 6 has to exist on disk. This writes it.

One proposal per branch of `src.next_experiment.propose`, chosen by measured
value rather than by name:

  NULL      the zero-hit program with the most measured members
  HIT       the highest-R_p program above the hit threshold
  UNSCORED  the held-out program that drew the HIGHEST prediction

The unscored case carries its observed outcome alongside the prediction, so the
page can show what the agent proposed *and* what actually happened. That row is
the one where the prediction was most wrong.

    .venv/bin/python -m src.freeze_proposals
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.next_experiment import FEATURES, HIT_MIN_HITS, propose

FROZEN = Path("results/frozen")


def main() -> None:
    S = pd.read_csv(FROZEN / "program_summary.csv")
    H = pd.read_csv(FROZEN / "heldout.csv")

    null_p = S[S.n_hits_q05 == 0].nlargest(1, "n_present").iloc[0].program
    hit_p = S[S.n_hits_q05 >= HIT_MIN_HITS].nlargest(1, "R_p").iloc[0].program
    unscored = H.nlargest(1, "R_p_predicted").iloc[0]

    out = {
        "_regenerate": "python -m src.freeze_proposals",
        "_source": "results/frozen/program_summary.csv + heldout.csv",
        "_note": "Generated from measured values only. No branch tests a program name.",
        "null": propose(null_p, S),
        "hit": propose(hit_p, S),
        "unscored": propose(unscored.program, S,
                            feat={k: float(unscored[k]) for k in FEATURES}),
    }
    # what actually happened to the unscored program, for honest side-by-side
    out["unscored"]["observed_outcome"] = {
        "n_hits_q05": int(unscored.n_hits_q05),
        "n_present": int(unscored.n_present),
        "n_declared": int(unscored.n_declared),
        "unscoreable": bool(unscored.unscoreable),
        "verdict": ("The agent's highest-confidence proposal of the ten. "
                    f"{int(unscored.n_present)} of {int(unscored.n_declared)} members "
                    f"measured. It returned {int(unscored.n_hits_q05)} hits."),
    }

    (FROZEN / "proposals.json").write_text(json.dumps(out, indent=2) + "\n")
    print(f"wrote {FROZEN/'proposals.json'}")
    for k in ("null", "hit", "unscored"):
        print(f"  {k:9s} {out[k]['program']:52s} {out[k]['outcome']}")


if __name__ == "__main__":
    main()
