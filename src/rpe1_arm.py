"""RPE1 arm — does the size effect reproduce in a second cell line?

PRE-REGISTERED. Thresholds fixed in docs/RPE1_PREREG.md (sha256 ae62feda…,
committed at f509baa) BEFORE this file existed or any RPE1 value was computed.

    size-alone R2 >= 0.25 and positive slope  -> reproduces
    0.10 <= R2 < 0.25                         -> inconclusive
    R2 < 0.10 or negative slope               -> does not reproduce
    fewer than 35 of 50 scoreable             -> UNDERPOWERED, no verdict

Scoped as a generalisation test and NOT a replication: RPE1 covers 24.3% of
K562's targets and that quarter is disproportionately essential genes -- our own
rpe1_coverage_collision control, which FAILS.

Uses the byte-frozen scorer unmodified. Only the substrate path differs, set on
the module object rather than by editing the file, because its sha256 is asserted
elsewhere. Writes results/rpe1/ ONLY; results/frozen/ is not touched.

    .venv/bin/python -m src.rpe1_arm
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import norm, spearmanr
from statsmodels.stats.multitest import multipletests

from src import score_k562 as SC
from src import sweep as SW

RPE1 = Path("data/raw/rpe1_normalized_bulk_01.h5ad")
FROZEN = Path("results/frozen")
OUT = Path("results/rpe1")

PREREG_SHA = "ae62fedaab26a2fadb9b555547cb2ab2cfeb6cb6f3cbbbd76bb63f14efef0df7"
SCORER_SHA = "2abfdc6f730d786180e37f73e2951c303c5a7b42caa27dc3394c74c323d7bbfa"

R2_REPRODUCES = 0.25
R2_FLOOR = 0.10
MIN_SCOREABLE = 35


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    # The scorer must be the frozen one. If it is not, the arm is void -- the
    # pre-registration says we abandon rather than edit.
    actual = _sha(Path("src/score_k562.py"))
    if actual != SCORER_SHA:
        raise SystemExit(f"scorer hash {actual[:16]} != frozen {SCORER_SHA[:16]}; "
                         "the pre-registration forbids editing it. Arm abandoned.")
    pre = _sha(Path("docs/RPE1_PREREG.md"))
    if pre != PREREG_SHA:
        raise SystemExit(f"pre-registration changed ({pre[:16]}). Thresholds may "
                         "not be revised after the fact. Arm abandoned.")

    # Point the frozen scorer at RPE1 without touching the file.
    SC.K562 = RPE1
    X, symbols, pert, targets = SC.load_k562()
    with h5py.File(RPE1, "r") as f:
        expr_all = f["var/mean"][:].astype(float)
    sd_all = np.nanstd(X, axis=0)

    dm = pd.read_csv("data/raw/CRISPRGeneEffect.csv", index_col=0)
    dm.columns = [c.split(" (")[0] for c in dm.columns]
    ess = dm.mean(axis=0)

    sets = SW.hallmark()
    n_targets = len({t for t in targets if t})
    print(f"RPE1 substrate: X {X.shape} | {n_targets:,} unique targets | "
          f"{len(sets)} programs")

    rows = []
    for i, (name, program) in enumerate(sorted(sets.items()), 1):
        u_z, cos, delta, n_present = SC.score(X, symbols, program)
        p = 2 * norm.sf(np.abs(u_z))
        ok = np.isfinite(p)
        q = np.full_like(p, np.nan)
        if ok.sum():
            q[ok] = multipletests(p[ok], method="fdr_bh")[1]
        n_hits = int(np.nansum(q < SW.ALPHA))
        feats = SW.features(program, symbols, expr_all, sd_all, X, ess)
        rows.append({"program": name, **feats, "n_hits_q05": n_hits,
                     "R_p": round(float(np.log10(1 + n_hits)), 4),
                     "scoreable": bool(n_present >= 2 and np.isfinite(u_z).any())})
        if i % 10 == 0:
            print(f"  {i}/50 …")

    S = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    S.to_csv(OUT / "program_summary_rpe1.csv", index=False)

    d = S[S.scoreable & S.n_present.notna() & (S.n_present > 0)]
    n_scoreable = int(len(d))

    res = {
        "preregistration": {"file": "docs/RPE1_PREREG.md", "sha256": PREREG_SHA,
                            "committed": "f509baa",
                            "committed_before_this_ran": True},
        "scorer_sha256": SCORER_SHA, "scorer_unmodified": True,
        "substrate": "rpe1_normalized_bulk_01.h5ad",
        "n_unique_targets": n_targets,
        "n_programs": int(len(S)),
        "n_scoreable": n_scoreable,
        "n_zero_hit_programs": int((S.n_hits_q05 == 0).sum()),
    }

    if n_scoreable < MIN_SCOREABLE:
        res.update(verdict="UNDERPOWERED AND INCONCLUSIVE",
                   reason=f"only {n_scoreable} of {len(S)} scoreable, "
                          f"pre-registered floor is {MIN_SCOREABLE}")
    else:
        fit = sm.OLS(d.R_p, sm.add_constant(d.n_present)).fit()
        r2 = float(fit.rsquared)
        slope = float(fit.params.iloc[1])
        if r2 >= R2_REPRODUCES and slope > 0:
            verdict, claim = "REPRODUCES", "(a)"
        elif r2 < R2_FLOOR or slope <= 0:
            verdict, claim = "DOES NOT REPRODUCE", "(b)"
        else:
            verdict, claim = "INCONCLUSIVE", "neither"
        res.update({
            "size_alone_r2": round(r2, 4),
            "slope": round(slope, 6),
            "slope_p": float(f"{fit.pvalues.iloc[1]:.4g}"),
            "k562_size_alone_r2_for_reference": json.loads(
                (Path("results/sensitivity/stripped_model.json")).read_text()
            )["set_size_alone"]["r2"],
            "verdict": verdict, "claim_supported": claim,
        })
        # descriptive only, no threshold, as pre-registered
        K = pd.read_csv(FROZEN / "program_summary.csv")[["program", "R_p"]]
        m = K.merge(d[["program", "R_p"]], on="program", suffixes=("_k562", "_rpe1"))
        rho, pv = spearmanr(m.R_p_k562, m.R_p_rpe1)
        res["secondary_descriptive"] = {
            "spearman_k562_vs_rpe1_R_p": round(float(rho), 4),
            "p": float(f"{pv:.4g}"), "n_programs": int(len(m)),
            "note": "Descriptive only. No threshold was set for this and none is "
                    "applied after the fact.",
        }

    res["scope"] = (
        "NOT a replication. RPE1 covers 24.3% of K562's knockdown targets and "
        "that subset is disproportionately essential genes -- see the "
        "rpe1_coverage_collision control in results/frozen/controls.csv, which "
        "FAILS at 94.1% vs 11.3% coverage. This arm tests whether the structure "
        "holds in a second cell line, nothing more.")
    res["does_not_revise"] = "the pre-registered K562 primary in results/frozen/"

    (OUT / "rpe1_evaluation.json").write_text(json.dumps(res, indent=2) + "\n")

    print("\n" + "=" * 68)
    print(f"scoreable            : {n_scoreable}/50 "
          f"(pre-registered floor {MIN_SCOREABLE})")
    if "size_alone_r2" in res:
        print(f"size-alone R2 (RPE1) : {res['size_alone_r2']}   "
              f"slope {res['slope']:+.5f}  p={res['slope_p']}")
        print(f"  K562 reference     : {res['k562_size_alone_r2_for_reference']}")
        print(f"thresholds           : >={R2_REPRODUCES} reproduces, "
              f"<{R2_FLOOR} does not")
    print(f"VERDICT              : {res['verdict']}")
    print("=" * 68)
    print(f"wrote {OUT}/")


if __name__ == "__main__":
    main()
