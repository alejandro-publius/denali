"""Evaluation 14 — does denali's verdict depend on who called the hits?

Pre-registered in docs/HIT_RULE_PREREG.md, sha256 8e39c426..., sealed at f4b3f8d
BEFORE any value below was computed.

THE QUESTION. `denali audit` reads a size column and a hit column and reports what
share of a ranking set construction explains. It has never asked where the hit
column came from. Every hit count in this project came from one convention -- a
two-sided normal p-value on the reversal statistic, BH-corrected within program,
cut at q < 0.05 -- fixed in src/sweep.py before the sweep and never varied.

The mechanism this project attributes the confound to is statistical power: a
program with more measured members yields a more precise rank statistic, so more
of its perturbations clear a fixed threshold. That is a property of THRESHOLDING.
A rule that takes the top q% or the top N per set cannot express it in the hit
count at all, because the count is then set by the rule rather than by the data.

So this holds the screen completely fixed, varies only the hit rule, and asks the
shipped audit() what it would tell a caller.

WHAT THIS IS NOT. Not a claim that any convention is wrong; thresholding and
quantile-cutting are both standard. Not a revision of anything: see the substrate
gap below, which means no number here is comparable to the published 0.4649.

    .venv/bin/python -m src.hit_rule_audit

Reads results/frozen/matrix.csv and results/frozen/program_summary.csv, read-only.
Writes results/hit_rule/ only. NEVER writes results/frozen/.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm
from statsmodels.stats.multitest import multipletests

from denali_audit.core import audit

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / "results" / "frozen"
OUT = ROOT / "results" / "hit_rule"

# --- FIXED IN THE PRE-REGISTRATION. Do not edit after seeing a value. --------
ALPHA = 0.05
UZ_CUT = 2.0
QUANTILES = {"R5": 0.02, "R6": 0.10}
TOP_N = 200
RANGE_LIMIT = 0.20        # verdict identical but R2 spread wider than this: report both
PUBLISHED_R2 = 0.4649     # for the disclosed-gap comparison ONLY, never as a target
GAP_LIMIT = 0.10          # R1 further than this from published: absolute values are
#                           substrate-specific and must be labelled so everywhere
# -----------------------------------------------------------------------------

RULES = [
    ("R1", "BH q < 0.05 within program (the published convention)", "threshold"),
    ("R2", "uncorrected two-sided p < 0.05", "threshold"),
    ("R3", "Bonferroni p < 0.05/n within program", "threshold"),
    ("R4", "fixed effect size |u_z| >= 2.0, no correction", "threshold"),
    ("R5", "top 2% of genes per program", "quantile"),
    ("R6", "top 10% of genes per program", "quantile"),
    ("R7", f"top {TOP_N} genes per program", "fixed count"),
]


def call_hits(u: np.ndarray, rule: str) -> int:
    """Hits for one program under one rule. `u` is already masked to finite."""
    n = u.size
    if rule == "R1":
        p = 2 * norm.sf(np.abs(u))
        return int((multipletests(p, method="fdr_bh")[1] < ALPHA).sum())
    if rule == "R2":
        return int((2 * norm.sf(np.abs(u)) < ALPHA).sum())
    if rule == "R3":
        return int((2 * norm.sf(np.abs(u)) < ALPHA / n).sum())
    if rule == "R4":
        return int((np.abs(u) >= UZ_CUT).sum())
    if rule in QUANTILES:
        # Signed and one-sided, in the project's own direction: positive u_z means
        # the knockdown pushed the program down. A quantile rule has no threshold
        # to be two-sided about.
        k = int(np.ceil(QUANTILES[rule] * n))
        return int(min(k, n))
    if rule == "R7":
        return int(min(TOP_N, n))
    raise ValueError(rule)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    mat = pd.read_csv(FROZEN / "matrix.csv").set_index("target_gene")
    summ = pd.read_csv(FROZEN / "program_summary.csv").set_index("program")

    # A program whose column is entirely non-finite cannot be scored under ANY
    # rule -- there is nothing to threshold and nothing to rank. Excluded rather
    # than imputed (CLAUDE.md: mask, never impute), and the exclusion is counted
    # in the artifact rather than silently shrinking the denominator. The first
    # run of this arm died on ZeroDivisionError inside multipletests for exactly
    # this column, which is the honest way to find out.
    candidates = [c for c in mat.columns if c in summ.index]
    programs, excluded = [], []
    for c in candidates:
        (programs if np.isfinite(mat[c].to_numpy(dtype=float)).any()
         else excluded).append(c)
    sizes = [float(summ.loc[p, "n_present"]) for p in programs]

    per_rule, per_program = {}, []
    for rid, label, family in RULES:
        hits = []
        for p in programs:
            u = mat[p].to_numpy(dtype=float)
            u = u[np.isfinite(u)]           # MASK, never impute
            h = call_hits(u, rid)
            hits.append(h)
            per_program.append({"rule": rid, "program": p, "n_present": summ.loc[p, "n_present"],
                                "n_finite": int(u.size), "hits": h})
        a = audit(sizes=sizes, hits=hits)   # the SHIPPED function, imported
        arr = np.asarray(hits, dtype=float)
        r2 = float(a["r2_size_alone"])
        constant = bool(arr.min() == arr.max())
        per_rule[rid] = {
            "rule": label,
            "family": family,
            "r2_size_alone": None if not np.isfinite(r2) else round(r2, 4),
            "verdict": a["verdict"],
            # A finite R^2 on a CONSTANT hit column is the signature of the
            # core.py defect this arm surfaced: ss_tot is only mathematically
            # zero, so the `ss_tot == 0` refusal is bypassed and a garbage
            # negative share is reported as an all-clear. Recorded per rule so
            # this artifact says which behaviour it observed, and so the arm's
            # verdict can be checked to be the same before and after the fix.
            "constant_hits_but_finite_r2": bool(constant and np.isfinite(r2)),
            "hits_min": int(arr.min()),
            "hits_max": int(arr.max()),
            "hits_median": float(np.median(arr)),
            "hits_constant": bool(arr.min() == arr.max()),
            "hits_cv": (round(float(arr.std() / arr.mean()), 4)
                        if arr.mean() else None),
        }
        shown = per_rule[rid]["r2_size_alone"]
        print(f"  {rid}  {family:11s}  R2={'  undef' if shown is None else f'{shown:.4f}'}  "
              f"{a['verdict']:20s}  hits {int(arr.min())}-{int(arr.max())}")

    verdicts = {v["verdict"] for v in per_rule.values()}
    # Spread over the THRESHOLD family only. The quantile rules' R^2 is either
    # undefined (correct) or garbage (the defect above); including it would make
    # the spread a statement about a bug rather than about the rules, and would
    # change the moment core.py is fixed. The comparison the question needs is
    # among rules where the quantity is defined.
    r2s = [v["r2_size_alone"] for v in per_rule.values()
           if v["family"] == "threshold" and v["r2_size_alone"] is not None]
    spread = round(max(r2s) - min(r2s), 4)
    gap = round(abs(per_rule["R1"]["r2_size_alone"] - PUBLISHED_R2), 4)

    if len(verdicts) > 1:
        verdict = ("CLAIM (b) — the verdict is in part a function of the caller's "
                   "hit-calling convention. This is a scope limit and the tool must "
                   "say so on its own output.")
    elif spread > RANGE_LIMIT:
        verdict = ("CLAIM (c) — the verdict is robust across rules but the estimate "
                   f"is not: R2 spans {spread:.4f}. Report the range, not a point.")
    else:
        verdict = ("CLAIM (a) — the verdict is robust to hit-calling. The concern "
                   "this arm was built to test was unfounded.")

    out = {
        "arm": "evaluation 14 — does the verdict depend on who called the hits?",
        "prereg": ("docs/HIT_RULE_PREREG.md, sha256 8e39c4261ec5d2e68b27d1484a9db32e"
                   "b34b4ba39b2fae9138de68bd4df50170, sealed at f4b3f8d before any "
                   "value here was computed."),
        "substrate": {
            "file": "results/frozen/matrix.csv",
            "n_programs": len(programs),
            "n_programs_excluded_all_non_finite": len(excluded),
            "why_excluded": ("a column with no finite u_z cannot be thresholded or "
                             "ranked under any rule; excluded, not imputed, and "
                             "counted here rather than silently dropped"),
            "n_genes": int(mat.shape[0]),
            "sizes_from": "results/frozen/program_summary.csv n_present, identical "
                          "across all rules — only the hit column moves",
            "non_finite": "masked, never imputed",
        },
        "DISCLOSED SUBSTRATE GAP": (
            "matrix.csv is NOT the vector the published hit counts were computed on. "
            "src/sweep.py counts hits over all 11,258 perturbation rows and only then "
            "collapses to 9,837 unique target genes by each gene's MAXIMUM u_z. So no "
            "threshold rule recomputed here can reproduce n_hits_q05: fewer rows, an "
            "upward-shifted distribution, and a different BH denominator. The 470 MB "
            "substrate that would allow the uncollapsed comparison is gitignored and "
            "absent. EVERY absolute R2 in this file is substrate-specific and is NOT "
            "comparable to the published 0.4649. This arm is entitled only to the "
            "comparison ACROSS rules on one substrate, which is the comparison the "
            "question needs. Written into the pre-registration before it could be "
            "discovered."),
        "r1_vs_published": {
            "r1_here": per_rule["R1"]["r2_size_alone"],
            "published_headline": PUBLISHED_R2,
            "absolute_gap": gap,
            "gap_limit": GAP_LIMIT,
            "exceeds_limit": bool(gap > GAP_LIMIT),
            "why": "expected and pre-registered; see DISCLOSED SUBSTRATE GAP",
        },
        "rules": per_rule,
        "verdict": verdict,
        "distinct_verdicts": sorted(verdicts),
        "r2_spread_within_threshold_family": spread,
        "DEFECT THIS ARM SURFACED IN THE SHIPPED TOOL": {
            "what": ("audit() returns a false all-clear -- verdict NOT SIZE-DOMINATED "
                     "plus a large negative R2 -- when the hit column is constant at "
                     "most values."),
            "why": ("core.py _r2() guards the degenerate case with `ss_tot == 0`, an "
                    "exact float test on a quantity that is only MATHEMATICALLY zero. "
                    "Elementwise log10 of the same integer is not always bit-identical, "
                    "so ss_tot lands at ~9.7e-30, the guard does not fire, and "
                    "audit()'s `if not np.isfinite(share)` refusal is bypassed."),
            "measured": ("constant hits of 0, 1, 2, 10, 50, 100, 500 and 1000 refuse "
                         "correctly (ss_tot exactly 0.0); 5, 197, 200 and 984 return a "
                         "finite negative R2 and an all-clear. Whether the tool refuses "
                         "depends on the representability of log10(1+k) for the "
                         "caller's own hit count."),
            "why_it_survived": ("the refusal branch was added 2026-08-16 after dropping "
                                "an all-zero-hits table into the page runner. k=0 is one "
                                "of the values where the exact test accidentally works, "
                                "so the fix was verified on the single input that cannot "
                                "expose it and generalised to 'constant hits'."),
            "who_hits_it": ("any top-N hit list -- 'our top 200 hits' is an ordinary way "
                            "to publish a screen -- any quantile hit definition, and "
                            "screen-level inputs where every set returns the same count."),
            "reported_to": "the session holding packages/denali-audit/ at the time; not "
                           "fixed here, because that file was dirty in a shared checkout "
                           "and a dirty file is not mine to edit.",
            "arm_verdict_is_unaffected": ("with the defect the quantile rules read "
                                          "NOT SIZE-DOMINATED; once fixed they read "
                                          "UNDETERMINED. Both differ from the threshold "
                                          "family's CONFOUNDED, so claim (b) fires either "
                                          "way and this arm's conclusion does not depend "
                                          "on the bug."),
        },
        "THE READING THIS ARM FORBIDS": (
            "R5, R6 and R7 fix the hit count per program by construction, so their "
            "hit column is constant and their R2 is near zero or undetermined. That "
            "is NOT evidence that such rankings are unconfounded. It is evidence "
            "that this diagnostic CANNOT SEE the power difference under a rule that "
            "fixes the count. The underlying asymmetry -- larger programs yield more "
            "precise statistics -- is untouched by the choice of hit rule; a quantile "
            "rule only moves it out of the hit count and into the within-program "
            "ordering, which audit() never reads. A near-zero R2 under R5-R7 is the "
            "diagnostic going blind, never the ranking coming back clean. Fixed in "
            "the pre-registration so the framing could not be chosen afterwards."),
        "what_this_is_not": (
            "Not a claim that any hit-calling convention is wrong -- thresholding and "
            "quantile-cutting are both standard and both defensible. Not a revision "
            "of the published headline, which this arm cannot reach. Not a claim "
            "about any gene, gene set or publication, none of which is named."),
        "scope": ("One screen, 50 sets. Establishes that the rules differ or do not "
                  "on a real screen; not how they compare in general."),
    }
    (OUT / "hit_rule.json").write_text(json.dumps(out, indent=2) + "\n")
    pd.DataFrame(per_program).to_csv(OUT / "per_program_hits.csv", index=False)

    print(f"\n{verdict}")
    print(f"distinct verdicts: {sorted(verdicts)}")
    print(f"R2 spread within the threshold family: {spread}")
    print(f"R1 here {per_rule['R1']['r2_size_alone']} vs published {PUBLISHED_R2} "
          f"— gap {gap} (expected; see the disclosed substrate gap)")
    print(f"\nwrote {OUT}/hit_rule.json and per_program_hits.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
