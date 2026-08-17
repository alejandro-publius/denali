"""Evaluation 13 — is a screen's no-biology floor predictable from its design?

Pre-registered in docs/FLOOR_LAW_PREREG.md. The model, the four predictors, the
cross-validation scheme, the three claim branches and their thresholds, the
permutation control and the falsification condition were all fixed there before
this file computed anything.

THE QUESTION. `results/breadth/` established that the no-biology value of an
audit R^2 is not zero and depends on how `hits` was defined -- scope limit 6.
This asks the narrower question that the 1,272-screen corpus can actually
answer: within one mapping structure, can the floor be predicted from how the
screen was built, before any biology is consulted?

WHY IT MATTERS EITHER WAY. If it can, the floor is a property of design rather
than of findings, and an enrichment result should be reported next to its
expected floor. If it cannot, that is the eighth negative result in this project
and is published as one.

    .venv/bin/python -m src.floor_law

Reads results/corpus/corpus_per_screen.csv. Writes results/floor_law/ only.
Never writes results/frozen/.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "results" / "corpus" / "corpus_per_screen.csv"
OUT = ROOT / "results" / "floor_law"

# --- FIXED IN THE PRE-REGISTRATION. Do not edit after seeing a value. --------
SEED = 20260817
N_FOLDS = 5
N_PERM = 1000
CLAIM_A = 0.50          # at or above: the floor is largely a design artifact
CLAIM_B_FLOOR = 0.20
PREDICTORS = ("log10_n_hits", "log10_n_measured", "n_sets_used", "hit_rate")
# -----------------------------------------------------------------------------


def design_matrix(d: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """The four design predictors, and nothing that knows any biology."""
    X = np.column_stack([
        np.log10(d.n_hits.to_numpy(float)),
        np.log10(d.n_measured.to_numpy(float)),
        d.n_sets_used.to_numpy(float),
        d.n_hits.to_numpy(float) / d.n_measured.to_numpy(float),
    ])
    y = d.r2_size_alone.to_numpy(float)
    # Folds by PUBLICATION, not by screen. One publication contributes 340 of
    # the 1,272 screens; a random split would put it on both sides of every
    # fold and score memorisation as prediction.
    groups = d.source_id.astype(str).to_numpy()
    return X, y, groups


def _fit(X, y):
    A = np.column_stack([np.ones(len(X)), X])
    beta, *_ = np.linalg.lstsq(A, y, rcond=None)
    return beta


def _predict(beta, X):
    return np.column_stack([np.ones(len(X)), X]) @ beta


def grouped_cv_r2(X, y, groups, seed=SEED, n_folds=N_FOLDS) -> tuple[float, np.ndarray]:
    """Cross-validated R^2 with whole publications held out together."""
    rng = np.random.default_rng(seed)
    uniq = np.unique(groups)
    rng.shuffle(uniq)
    assign = {g: i % n_folds for i, g in enumerate(uniq)}
    fold = np.array([assign[g] for g in groups])
    pred = np.empty_like(y)
    for k in range(n_folds):
        tr, te = fold != k, fold == k
        if te.sum() == 0 or tr.sum() < len(PREDICTORS) + 2:
            pred[te] = y[tr].mean() if tr.sum() else y.mean()
            continue
        pred[te] = _predict(_fit(X[tr], y[tr]), X[te])
    ss_res = float(((y - pred) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    return (1.0 - ss_res / ss_tot), pred


def main() -> int:
    d = pd.read_csv(CORPUS)
    X, y, groups = design_matrix(d)
    q, pred = grouped_cv_r2(X, y, groups)

    # Permutation control: shuffle the outcome, refit, and see what the same
    # pipeline scores on noise. Without this a positive Q is not interpretable.
    rng = np.random.default_rng(SEED)
    null = np.array([grouped_cv_r2(X, rng.permutation(y), groups, seed=SEED)[0]
                     for _ in range(N_PERM)])
    p95 = float(np.percentile(null, 95))
    clears = bool(q > p95)

    beta = _fit(X, y)
    coefs = {name: round(float(b), 6)
             for name, b in zip(("intercept",) + PREDICTORS, beta)}

    # Single-predictor cross-validated R^2, so "hit_rate dominates" is a
    # measured statement rather than an impression. Pre-registered as EXPECTED,
    # which is why confirming it is not reported as a discovery.
    solo = {}
    for i, name in enumerate(PREDICTORS):
        solo[name] = round(grouped_cv_r2(X[:, [i]], y, groups)[0], 4)

    if not clears:
        verdict = ("NOTHING CLAIMED — the model did not clear its own "
                   "permutation null")
    elif q >= CLAIM_A:
        verdict = "CLAIM (a) — the floor is largely a design artifact"
    elif q >= CLAIM_B_FLOOR:
        verdict = "CLAIM (b) — partially predictable"
    else:
        verdict = "CLAIM (c) — it does not generalise"

    out = {
        "arm": "evaluation 13 — is the no-biology floor predictable from design?",
        "prereg": ("docs/FLOOR_LAW_PREREG.md, sealed before this model was fitted. "
                   "Post-hoc with respect to the corpus, which already existed; "
                   "pre-registered with respect to this model, which did not."),
        "n_screens": int(len(d)),
        "n_publications": int(pd.Series(groups).nunique()),
        "predictors": list(PREDICTORS),
        "cv": {"scheme": "5-fold, grouped by publication so no publication "
                         "appears in both train and test", "seed": SEED},
        "cv_r2": round(float(q), 4),
        "permutation_null": {
            "n": N_PERM, "p95_of_cv_r2": round(p95, 4),
            "clears_null": clears,
            "why": ("A cross-validated R^2 is only interpretable against what "
                    "the same pipeline scores on a shuffled outcome."),
        },
        "verdict": verdict,
        "coefficients_full_fit": coefs,
        "single_predictor_cv_r2": solo,
        "expected_before_fitting": (
            "hit_rate was pre-registered as the expected dominant predictor, "
            "because the corpus is entirely in the counting regime where the "
            "floor is partly arithmetic. Confirming it is not a discovery."),
        "what_this_does_not_show": (
            "Nothing about mapping structures other than counting: every screen "
            "here counts hits over each set's own members, so mapping structure "
            "is constant and cannot be a predictor. The breadth arm's "
            "cross-domain question stays open and this arm does not close it. "
            "Nothing about whether any individual screen is good — a predictable "
            "floor is not a criticism of the screen that has one."),
        "scope": ("Writes results/floor_law/ only, never results/frozen/. No "
                  "gene, gene set or publication is named."),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "floor_law.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({k: out[k] for k in
                      ("n_screens", "n_publications", "cv_r2",
                       "permutation_null", "verdict", "single_predictor_cv_r2",
                       "coefficients_full_fit")}, indent=2))
    print(f"\nwrote {(OUT / 'floor_law.json').relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
