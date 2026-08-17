"""Do published enrichment rankings clear their own no-biology null?

Pre-registered in docs/EXPANSION_PREREG.md, sha256 179167e58bb9e332, committed at
1010d4d BEFORE this ran.

WHY THIS EXISTS. results/breadth/README.md reports that the 1,272-screen corpus
arm has counting structure (hits <= size) and that on a 250-screen sample the
observed R^2 sits BELOW its own binomial null in 94% of screens. That claim
decides how `denali floor` should be read -- and it has no committed artifact.
The raw ORCS substrate is gitignored and absent, so it cannot be reproduced here
and is not estimated.

What CAN be run exactly is the same proposition on the seven real published
screens whose per-set tables are committed in audits/external/. Same question,
same null function, data a stranger can check.

    .venv/bin/python -m src.external_nulls

Writes results/external_nulls/external_nulls.json. Never writes results/frozen/.
Names no gene, gene set, publication or author as a finding.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "packages" / "denali-audit"))
sys.path.insert(0, str(ROOT / "results" / "breadth"))

from denali_audit import adapters                      # noqa: E402
from denali_audit.core import MIN_SETS                 # noqa: E402
from null_baselines import null_baseline               # noqa: E402

EXTERNAL = ROOT / "audits" / "external"
OUTDIR = ROOT / "results" / "external_nulls"


def main() -> int:
    rows = {}
    for d in sorted(p for p in EXTERNAL.iterdir() if p.is_dir()):
        f = d / "std.csv"
        if not f.exists():
            rows[d.name] = {"status": "NO std.csv"}
            continue
        df = pd.read_csv(f)
        m = adapters.detect(df)
        if m is None:
            rows[d.name] = {"status": "NOT PARSED", "reason": "no adapter matched"}
            continue
        size = pd.to_numeric(m.size, errors="coerce")
        hits = pd.to_numeric(m.hits, errors="coerce")
        ok = size.notna() & hits.notna()
        size, hits = size[ok].to_numpy(float), hits[ok].to_numpy(float)
        if len(size) < MIN_SETS:
            rows[d.name] = {"status": f"TOO FEW SETS ({len(size)} < {MIN_SETS})"}
            continue
        r = null_baseline(size, hits)
        lo, hi = r["null_ci95"]
        # Pre-registered rule: clears the null iff observed exceeds the UPPER bound
        # of the null's 95% interval. Fixed in EXPANSION_PREREG.md section 4 before
        # any of these values existed.
        r["clears_null"] = bool(r["observed_r2"] > hi)
        r["null_ci95_upper"] = hi
        r["status"] = "SCORED"
        rows[d.name] = r

    scored = {k: v for k, v in rows.items() if v.get("status") == "SCORED"}
    n_clear = sum(v["clears_null"] for v in scored.values())
    n = len(scored)
    counting = sum(v.get("has_counting_structure", False) for v in scored.values())

    if n_clear >= 5:
        verdict = ("CLEARS -- the breadth arm's corpus reading does not generalise to "
                   "these screens and `denali floor`'s wording is defensible as written")
    elif n_clear <= 3:
        verdict = ("DOES NOT CLEAR -- the instruction `denali floor` prints is a defect "
                   "for counting-structure mappings and becomes a scope limit today")
    else:
        verdict = ("INDETERMINATE at this n -- reported as indeterminate and not rounded "
                   "toward either conclusion")

    out = {
        "arm": "external screens vs their own no-biology null",
        "status": "POST-HOC arm, pre-registered before running",
        "prereg": "docs/EXPANSION_PREREG.md sha256 179167e58bb9e332, committed 1010d4d",
        "null_function": "results/breadth/null_baselines.py::null_baseline, unmodified",
        "n_screens_scored": n,
        "n_with_counting_structure": counting,
        "n_clearing_their_null": n_clear,
        "decision_rule": "clears iff observed_r2 > upper bound of the null's 95% interval",
        "verdict": verdict,
        "what_this_does_not_show": (
            "Nothing about the 1,272-screen corpus, whose per-set tables are not "
            "committed and were not estimated. Seven screens cannot settle a claim made "
            "about 1,272. This corroborates or fails to corroborate the breadth reading "
            "on data that can actually be run."),
        "scope": (
            "A property of each mapping, not of any experiment, ranking, publication or "
            "author. No gene or gene set is named. No screen is called bad."),
        "screens": rows,
    }
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / "external_nulls.json").write_text(json.dumps(out, indent=2) + "\n")

    print(f"\n  {n} screens scored, {counting} with counting structure\n")
    print(f"  {'screen':22s} {'n':>5s} {'obs R2':>8s} {'null':>8s} {'null hi':>8s} {'clears':>7s}")
    print("  " + "-" * 64)
    for k, v in rows.items():
        if v.get("status") != "SCORED":
            print(f"  {k:22s} {v['status']}")
            continue
        print(f"  {k:22s} {v['n_sets']:5d} {v['observed_r2']:8.4f} "
              f"{v['null_mean_r2']:8.4f} {v['null_ci95_upper']:8.4f} "
              f"{'YES' if v['clears_null'] else 'no':>7s}")
    print(f"\n  {n_clear} of {n} clear their own null")
    print(f"  {verdict}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
