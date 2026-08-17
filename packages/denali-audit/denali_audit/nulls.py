"""What would this R^2 be with no biology in it at all?

THE NUMBER `audit()` REPORTS IS NOT INTERPRETABLE WITHOUT THIS ONE, and for most
inputs this package accepts the no-biology value is not zero.

Where `hits` are counted over the set's own members -- so `hits <= size`, which is
what classical overlap enrichment does -- regressing a count on the number of
trials that produced it recovers the trial count. A large R^2 there is arithmetic,
not a confound. Nine of the ten formats `adapters.detect()` recognises have that
structure: g:Profiler, DAVID, clusterProfiler, Enrichr, fgsea, GSEA desktop,
MAGeCK, drugZ and BAGEL2. The tenth is this project's own, whose hits count
perturbations rather than members.

That gap shipped. Until 2026-08-17 `audit()` issued CONFOUNDED / PARTIALLY
CONFOUNDED bands against the raw R^2 with no reference to the null, so a real
published screen measured at 0.36 against a null of 0.72 -- LESS size-carried than
chance -- was told to "check that your leading entries are not simply your largest
sets." Measured on seven real published screens in results/external_nulls/: all
seven have counting structure and only two clear their own null.

THIS IS THE SAME FUNCTION as results/breadth/null_baselines.py::null_baseline,
which produced the published null column for the breadth arm. It was moved here
rather than copied, for the same reason `audit()` itself lives in this package and
the study imports it: two copies of a definition drift and one does not.
packages/denali-audit/tests/test_nulls.py pins these values against the committed
results/breadth/null_baselines.json so the move cannot have changed a number.

Reference for the boundary condition: results/breadth/README.md.
"""
from __future__ import annotations

import numpy as np

SEED = 20260816
N_ITER = 300
MIN_SETS = 8

COUNTING_WHY = (
    "every set's hit count is at most its size, so hits and size are counted over "
    "the same members. A count regressed on the number of trials that produced it "
    "recovers the trial count, so some of this R^2 is arithmetic rather than biology.")
NON_COUNTING_WHY = (
    "hit counts here are not bounded by set size, so hits are counted over some "
    "other universe than the set's own members. Size has no arithmetic head start.")


def structure(size, hits) -> dict:
    """Is this a counting mapping? Decided from the data, never from the format name."""
    s = np.asarray(size, dtype=float)
    h = np.asarray(hits, dtype=float)
    ok = np.isfinite(s) & np.isfinite(h)
    s, h = s[ok], h[ok]
    if len(s) == 0:
        return {"structure": "unknown", "frac_hits_le_size": None,
                "why": "no finite rows to decide from"}
    rate = float(h.sum() / s.sum()) if s.sum() else float("nan")
    counting = bool(np.all(h <= s)) and 0.0 <= rate <= 1.0
    return {
        "structure": "counting" if counting else "non-counting",
        "frac_hits_le_size": round(float((h <= s).mean()), 4),
        "why": COUNTING_WHY if counting else NON_COUNTING_WHY,
    }


def no_biology_null(size, hits, r2_fn, n_iter: int = N_ITER, seed: int = SEED):
    """The R^2 this mapping returns with the biology removed. None if undecidable.

    `r2_fn` is injected rather than imported so this module does not import core
    and core does not import a module that imports it. It is always
    `core._r2`-equivalent in practice.

    Counting mappings get a binomial null at the observed constant per-member rate.
    Everything else gets a permutation null. Both are the simplest defensible null
    for their structure, not the only one -- a per-member hit rate that genuinely
    varied with set size would move the baseline, and that limitation is stated in
    results/breadth/README.md rather than hidden here.
    """
    rng = np.random.default_rng(seed)
    s = np.asarray(size, dtype=float)
    h = np.asarray(hits, dtype=float)
    ok = np.isfinite(s) & np.isfinite(h)
    s, h = s[ok], h[ok]
    if len(s) < MIN_SETS:
        return None
    st = structure(s, h)
    counting = st["structure"] == "counting"
    rate = float(h.sum() / s.sum()) if s.sum() else float("nan")

    draws = []
    for _ in range(n_iter):
        sim = rng.binomial(s.astype(int), rate) if counting else rng.permutation(h)
        try:
            v = r2_fn(s, np.log10(1.0 + sim))
        except Exception:
            continue
        if np.isfinite(v):
            draws.append(v)
    if not draws:
        return None
    d = np.asarray(draws, dtype=float)
    lo, hi = float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))
    return {
        "kind": ("binomial constant-rate (hits drawn from the set's own members)"
                 if counting else "permutation (hits not bounded by size)"),
        "expected_r2": round(float(d.mean()), 4),
        "ci95": [round(lo, 4), round(hi, 4)],
        "n_iter": int(len(d)),
    }


def position(observed: float, null: dict | None) -> str | None:
    """ABOVE / INSIDE / BELOW the null's 95% interval."""
    if null is None or not np.isfinite(observed):
        return None
    lo, hi = null["ci95"]
    return "ABOVE" if observed > hi else "BELOW" if observed < lo else "INSIDE"
