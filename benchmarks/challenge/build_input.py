"""Write the published input half of the challenge from the frozen paired table.

Deterministic and re-runnable: `python benchmarks/challenge/build_input.py` must
leave `data/k562_input.csv` byte-identical or the split rule has moved.

Every value here is copied as an integer from results/concordance/paired_programs.csv.
Nothing is recomputed. See PREREG.md, "Why hit counts are not recomputed".
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PAIRED = ROOT / "results" / "concordance" / "paired_programs.csv"
OUT = HERE / "data" / "k562_input.csv"
EXAMPLE = HERE / "data" / "example_submission.csv"


def main() -> int:
    p = pd.read_csv(PAIRED)
    out = pd.DataFrame({
        "set": p["program"],
        "size": p["n_present_k562"].astype(int),
        "hits": p["n_hits_q05_k562"].astype(int),
    }).sort_values("set", kind="stable").reset_index(drop=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(out.to_csv(index=False))
    print(f"wrote {OUT.relative_to(ROOT)}  {len(out)} sets, "
          f"size {out['size'].min()}-{out['size'].max()}, "
          f"hits {out['hits'].min()}-{out['hits'].max()}")

    # A worked example, so a stranger can score something within a minute of cloning.
    # It is a HALF correction -- it subtracts half as much of the size term as
    # `denali rerank` does -- chosen because it is one line long and because where it
    # lands relative to the full correction is worth knowing.
    import numpy as np
    y = np.log10(1.0 + out["hits"].to_numpy(dtype=float))
    ls = np.log10(out["size"].to_numpy(dtype=float))
    ex = pd.DataFrame({"set": out["set"], "score": (y - 0.5 * ls).round(6)})
    EXAMPLE.write_text(ex.to_csv(index=False))
    print(f"wrote {EXAMPLE.relative_to(ROOT)}  example submission, {len(ex)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
