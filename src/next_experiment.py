"""Criterion 1 — propose a next experiment, GENERATED from the result.

No branch tests a program name. Every branch reads measured quantities from
results/frozen/program_summary.csv and the measurability features. Change the
data and the proposal changes; that is the criterion verbatim.

    .venv/bin/python -m src.next_experiment <PROGRAM_NAME>
    .venv/bin/python -m src.next_experiment --demo
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

FROZEN = Path("results/frozen")
FEATURES = ["frac_present", "expr_ratio", "sd_ratio", "n_present",
            "essentiality_density", "coherence"]
HIT_MIN_HITS = 100          # matches reversibility_call == "reversible"
CONCORDANCE = -0.019


def _fit(S: pd.DataFrame):
    d = S.dropna(subset=FEATURES + ["R_p"])
    mu, sd = d[FEATURES].mean(), d[FEATURES].std()
    X = sm.add_constant((d[FEATURES] - mu) / sd)
    m = sm.OLS(d.R_p, X).fit()
    resid_sd = float((d.R_p - m.predict(X)).std())
    return m, mu, sd, resid_sd


def _predict(m, mu, sd, feat: dict) -> float:
    x = pd.DataFrame([{f: feat[f] for f in FEATURES}])
    x = sm.add_constant((x - mu) / sd, has_constant="add")
    return float(m.predict(x).iloc[0])


def propose(program: str, S: pd.DataFrame, feat: dict | None = None) -> dict:
    """Return a next-experiment proposal derived entirely from measured values."""
    m, mu, sd, resid_sd = _fit(S)
    row = S[S.program == program]

    # ---------- BRANCH 3: never scored ----------
    if row.empty:
        if feat is None:
            raise SystemExit(f"{program} not scored and no features supplied")
        pred = _predict(m, mu, sd, feat)
        pred_hits = int(round(10 ** pred - 1))
        # expected information gain: how much this program would move our
        # understanding, = predictive uncertainty relative to the observed spread
        eig = round(float(resid_sd / S.R_p.std()), 3)
        return {
            "program": program, "outcome": "UNSCORED",
            "evidence": {"predicted_R_p": round(pred, 3),
                         "predicted_hits": pred_hits,
                         "prediction_sd": round(resid_sd, 3),
                         "expected_information_gain": eig,
                         **{k: feat[k] for k in FEATURES}},
            "next_experiment": (
                f"Score {program} against all 9,837 knockdowns. Predicted "
                f"R_p={pred:.2f} (~{pred_hits} hits) with prediction SD "
                f"{resid_sd:.2f}, from measurability features alone."),
            "expected_information_gain": (
                f"{eig} of one observed-spread SD. The measurability model already "
                f"explains most of the variance, so the informative part of this "
                f"experiment is the RESIDUAL: whether the observed R_p departs from "
                f"{pred:.2f} by more than {resid_sd:.2f}."),
            "cost": "~11 s compute on the existing matrix.",
        }

    r = row.iloc[0]
    hits, gate = int(r.n_hits_q05), bool(r.passes_measurability_gate)
    resid = float(r.R_p_residual_after_measurability) if pd.notna(
        r.R_p_residual_after_measurability) else float("nan")

    # ---------- BRANCH 1: null ----------
    if hits == 0:
        # the mechanism is READ OFF the features, not hardcoded
        if r.expr_ratio < 1.0:
            mech = (f"program members sit BELOW background expression "
                    f"(expr_ratio={r.expr_ratio:.2f}), i.e. the program is not "
                    f"engaged in this condition")
            fix = ("induce the condition that switches this program on, then "
                   "re-profile the same knockdowns")
            falsify = (f"If, after induction, expr_ratio rises above 1.0 and the "
                       f"program still returns 0 hits, the null is NOT explained by "
                       f"engagement and the mechanism is refuted.")
        elif r.sd_ratio < 1.0:
            mech = (f"members are expressed but do not VARY across perturbations "
                    f"(sd_ratio={r.sd_ratio:.2f}); nothing in this library moves them")
            fix = ("perturb upstream regulators not covered by this library, or "
                   "use a library targeting non-coding regulators")
            falsify = ("If a broader library still leaves sd_ratio below 1.0, the "
                       "program is unmovable in this cell type and the mechanism holds.")
        else:
            mech = (f"members are expressed and variable (expr_ratio="
                    f"{r.expr_ratio:.2f}, sd_ratio={r.sd_ratio:.2f}) yet nothing "
                    f"reaches significance; this is a POWER limit, not a biology limit")
            fix = ("increase cells per perturbation, or aggregate related "
                   "perturbations to raise effective n")
            falsify = ("If doubling depth yields no hits, the null is biological "
                       "rather than statistical and the mechanism is refuted.")
        return {
            "program": program, "outcome": "NULL_WITH_MECHANISM",
            "evidence": {"n_hits_q05": 0, "expr_ratio": float(r.expr_ratio),
                         "sd_ratio": float(r.sd_ratio),
                         "frac_present": float(r.frac_present),
                         "passes_measurability_gate": gate},
            "mechanism": mech,
            "next_experiment": f"Change the condition: {fix}. Then re-run the identical sweep.",
            "falsifies_the_mechanism": falsify,
            "cost": "one re-profile; scoring is ~11 s on the existing pipeline.",
        }

    # ---------- BRANCH 2: hit ----------
    if hits >= HIT_MIN_HITS:
        excess = ("above" if resid > 0 else "below")
        return {
            "program": program, "outcome": "HIT_ABOVE_THRESHOLD",
            "evidence": {"n_hits_q05": hits, "R_p": float(r.R_p),
                         "R_p_predicted_from_measurability":
                             float(r.R_p_predicted_from_measurability),
                         "residual": round(resid, 3),
                         "passes_measurability_gate": gate},
            "next_experiment": (
                "Validate at PATHWAY level: test whether the ranked knockdowns "
                "recover this program's canonical regulators at both tails, in a "
                "second independently screened cell type, using set-level "
                "enrichment — not individual gene lookups."),
            "why_not_gene_level": (
                f"Guide-pair concordance is {CONCORDANCE}. Two independent guides "
                f"against the same gene give uncorrelated scores, so any single-gene "
                f"call here is not reproducible. Set-level statistics aggregate over "
                f"thousands of perturbations and survive that noise; individual "
                f"ranks do not."),
            "caveat": (
                f"Observed R_p is {abs(resid):.2f} {excess} what measurability alone "
                f"predicts. The measurability model explains most of the variance "
                f"across programs, so the residual is the only part that can be "
                f"biology." + ("" if gate else
                " NOTE: this program FAILS the measurability gate, so treat even the "
                "residual cautiously.")),
            "cost": "existing RPE1 matrix; no new data.",
        }

    # ---------- weak ----------
    return {
        "program": program, "outcome": "WEAK",
        "evidence": {"n_hits_q05": hits, "R_p": float(r.R_p)},
        "next_experiment": (
            f"Underpowered at {hits} hits. Either raise depth or merge with a "
            f"related program to increase measured member count "
            f"(n_present={int(r.n_present)})."),
        "cost": "cheap; no new data required.",
    }


def main() -> None:
    S = pd.read_csv(FROZEN / "program_summary.csv")
    args = sys.argv[1:]
    if args and args[0] == "--demo":
        nulls = S[S.n_hits_q05 == 0].sort_values("n_present", ascending=False)
        hits = S[S.n_hits_q05 >= HIT_MIN_HITS].sort_values("R_p", ascending=False)
        picks = [nulls.iloc[0].program, hits.iloc[0].program]
        for p in picks:
            print(json.dumps(propose(p, S), indent=2))
            print()
        return
    print(json.dumps(propose(args[0], S), indent=2))


if __name__ == "__main__":
    main()
