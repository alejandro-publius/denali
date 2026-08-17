"""Run `denali verify` against denali's own claims before pointing it at anyone.

A verification product from a group that has not verified itself is an assertion.
This runs the shipped `verify()` over this project's own published headline and
over the seven external screens already in the repository, and writes whatever
comes back.

    .venv/bin/python -m src.self_verify

Writes results/verify/self_verification.json. Never writes results/frozen/.
Names no gene, gene set, publication or author as a finding. Calls no study
wrong, and the external screens are included because their tables are committed
here, not because anything about them is in question.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "packages" / "denali-audit"))

from denali_audit import adapters                       # noqa: E402
from denali_audit.verify import verify                  # noqa: E402

OUTDIR = ROOT / "results" / "verify"
FROZEN = ROOT / "results" / "frozen" / "program_summary.csv"
EXTERNAL = ROOT / "audits" / "external"


def _row(name, size, hits, claim, claimed=None, source=None):
    r = verify(size, hits, claim=claim, claimed_size_share=claimed, source=source,
               command=f"denali verify {source}")
    f = r.get("floor", {})
    n = (f.get("no_biology_null") or {})
    return {
        "name": name,
        "status": r["status"],
        "r2_size_alone": f.get("r2_size_alone"),
        "null_expected_r2": n.get("expected_r2"),
        "null_ci95": n.get("ci95"),
        "mapping": (f.get("mapping") or {}).get("structure"),
        "verdict_is_stable": n.get("verdict_is_stable"),
        "n_not_verifiable": len(r["not_verifiable"]),
        "full": r,
    }


def main() -> int:
    rows = []

    # 1. Our own published headline, verified with the tool we are selling.
    s = pd.read_csv(FROZEN)
    rows.append(_row(
        "denali's own screen (the published 0.4649)",
        s["n_present"], s["n_hits_q05"],
        claim=("Set size alone explains 46.5% of the variance in this screen's "
               "gene-set hit ranking."),
        claimed=0.4649,
        source="results/frozen/program_summary.csv"))

    # 2. The seven external screens whose tables are committed here.
    for d in sorted(p for p in EXTERNAL.iterdir() if p.is_dir()):
        f = d / "std.csv"
        if not f.exists():
            continue
        m = adapters.detect(pd.read_csv(f))
        if m is None:
            rows.append({"name": d.name, "status": "NOT PARSED"})
            continue
        rows.append(_row(
            f"external: {d.name}",
            pd.to_numeric(m.size, errors="coerce"),
            pd.to_numeric(m.hits, errors="coerce"),
            claim=None,
            source=str(f.relative_to(ROOT))))

    scored = [r for r in rows if r.get("r2_size_alone") is not None]
    distinguishable = [r for r in scored
                       if r["status"].startswith("DISTINGUISHABLE")]
    counting = [r for r in scored if r["mapping"] == "counting"]

    out = {
        "arm": "self-verification — denali's own claims, checked with denali's own tool",
        "status": "POST-HOC. Not pre-registered. Reports whatever came back.",
        "n_checked": len(scored),
        "n_distinguishable_from_their_own_null": len(distinguishable),
        "n_with_counting_structure": len(counting),
        "the_uncomfortable_part": (
            "Our own screen is the only one here that clears its null, and that is "
            "NOT evidence that our screen is better science. It is a structural "
            "property of the mapping: our hits count perturbations over ~9,800 "
            "knockdowns, so set size gets no arithmetic head start and the null "
            "sits near zero. The seven external screens are classical overlap "
            "enrichment, where hits are counted over each set's own members and the "
            "no-biology value is large by construction. We are comparing our own "
            "data against an easier baseline than theirs, and a reader should "
            "discount the contrast accordingly. Reported because a verification "
            "tool that flatters its author is worth nothing."),
        "what_this_does_not_show": (
            "Nothing about the quality, correctness or reliability of any study "
            "whose table appears here. A ranking indistinguishable from its own "
            "null is not a wrong result; it is a ranking this particular measure "
            "cannot resolve. No study is named as a finding and none is criticised."),
        "scope": (
            "Collection-level only. No gene, gene set, publication or author is "
            "named as a finding. No clinical or wet-lab claim follows."),
        "rows": rows,
    }
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / "self_verification.json").write_text(json.dumps(out, indent=2) + "\n")

    print(f"\n  {len(scored)} rankings checked with the shipped verify()\n")
    print(f"  {'ranking':46s} {'mapping':13s} {'R2':>7s} {'null':>7s}  status")
    print("  " + "-" * 100)
    for r in rows:
        if r.get("r2_size_alone") is None:
            print(f"  {r['name']:46s} {r['status']}")
            continue
        print(f"  {r['name']:46s} {r['mapping']:13s} {r['r2_size_alone']:7.4f} "
              f"{r['null_expected_r2']:7.4f}  {r['status']}")
    print(f"\n  {len(distinguishable)} of {len(scored)} distinguishable from their own null")
    print(f"  {len(counting)} of {len(scored)} have counting structure\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
