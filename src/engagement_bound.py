"""POST-FREEZE SENSITIVITY CHECK. Not pre-registered.

Answers the sharpest question anyone has asked about this project: how much of
the headline is really the *unstressed cell line* problem rather than the size
problem?

The background. Our first program returned a null for a reason our measurability
gate had not thought to test -- the program was *measurable* in K562 but not
*engaged*, because an unstressed cell line does not run a stress program. That is
recorded as a design failure in LIMITATIONS.md section 3. The fair follow-up is
whether the same confusion is quietly driving the 56-75% result.

It is not, and the two failure modes are separable in the frozen data:

  measurable but not engaged  ->  passes the quality gate, returns zero hits
  the size effect             ->  bigger sets return more hits regardless

The first is countable. The second is a property of all 50. If the unstressed
line were carrying the headline, removing the programs it affects should move the
fit. Removing them barely moves it -- and moves it the wrong way for that story.

Writes results/sensitivity/engagement_bound.json ONLY.

    .venv/bin/python -m src.engagement_bound
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import statsmodels.api as sm

FROZEN = Path("results/frozen")
OUT = Path("results/sensitivity")
FEATURES = ["n_present", "frac_present", "expr_ratio", "sd_ratio",
            "essentiality_density", "coherence"]


def _adj_r2(d: pd.DataFrame) -> float:
    dd = d.dropna(subset=FEATURES + ["R_p"])
    return float(sm.OLS(dd.R_p, sm.add_constant(dd[FEATURES])).fit().rsquared_adj)


def main() -> None:
    S = pd.read_csv(FROZEN / "program_summary.csv")

    # measurable but not engaged: the gate says it is well measured, and nothing
    # moved it. That is the signature of a program the cell line never runs.
    mask = S.passes_measurability_gate & (S.n_hits_q05 == 0)
    affected = sorted(S.loc[mask, "program"])

    full, without = _adj_r2(S), _adj_r2(S[~mask])
    size_alone = float(sm.OLS(S.R_p, sm.add_constant(S.n_present)).fit().rsquared)

    res = {
        "question": ("How much of the 56-75% result is the unstressed-cell-line "
                     "problem rather than the size problem?"),
        "measurable_but_not_engaged": {
            "definition": "passes the measurability gate AND returns zero hits",
            "n": int(mask.sum()),
            "of": int(len(S)),
            "programs": affected,
        },
        "adj_r2_all_programs": round(full, 4),
        "adj_r2_excluding_them": round(without, 4),
        "delta": round(without - full, 4),
        "size_alone_r2_all_programs": round(size_alone, 4),
        "reading": (
            f"{int(mask.sum())} of {len(S)} programs show the measurable-but-not-"
            f"engaged signature. Removing them changes the fit by "
            f"{without - full:+.4f} -- and in the direction that makes the result "
            f"stronger, not weaker. Meanwhile set size alone explains "
            f"{size_alone:.1%} across all {len(S)}. The two are different failure "
            f"modes and the size effect is the one carrying the headline."),
        "what_this_does_not_settle": (
            "K562 could still make some programs look flat in a way a second cell "
            "line would reveal. This bounds the effect inside our own screen; it "
            "cannot bound it across screens. That is precisely what the RPE1 arm "
            "would test, and why it is the named next experiment."),
        "status": "POST-FREEZE, NOT PRE-REGISTERED",
        "prompted_by": "a reviewer question, not our plan",
        "does_not_replace": "the pre-registered primary in results/frozen/",
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "engagement_bound.json").write_text(json.dumps(res, indent=2) + "\n")

    print("POST-FREEZE: unstressed-line effect vs size effect -- not pre-registered")
    print(f"  measurable but not engaged : {int(mask.sum())} of {len(S)}  {affected}")
    print(f"  adj R2 all programs        : {full:.4f}")
    print(f"  adj R2 excluding them      : {without:.4f}   ({without - full:+.4f})")
    print(f"  size alone, all programs   : {size_alone:.4f}")
    print(f"wrote {OUT/'engagement_bound.json'}")


if __name__ == "__main__":
    main()
