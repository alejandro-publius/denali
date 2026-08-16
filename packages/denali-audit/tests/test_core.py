"""The package must compute what the paper computed.

The load-bearing test here is test_reproduces_published_headline. Everything else in
this suite checks behaviour; that one checks IDENTITY. If it fails, the tool and the
study have diverged and one of them is now lying.
"""
from __future__ import annotations

import math
import os
from pathlib import Path

import numpy as np
import pytest

from denali_audit.core import audit, audit_replication
from denali_audit.reference import N_SCREENS, percentile

PUBLISHED_HEADLINE = 0.4649

# The identity test needs the study's frozen data. Two ways to find it, in order:
#
#   1. this file's own location -- the package is vendored INSIDE the research
#      repo at packages/denali-audit, so when you are working in the repo the
#      data is three directories up and no configuration is required.
#   2. DENALI_RESEARCH_REPO, for a standalone checkout of the package.
#
# Path 1 exists because relying on the env var alone meant this test skipped
# everywhere -- including CI -- while the README and the architecture diagram
# both advertised it as the thing that stops the tool and the paper drifting
# apart. A guard nobody runs cannot hold a claim up, and asserting that it does
# is worse than not having it.
_vendored = Path(__file__).resolve().parents[3]
RESEARCH = os.environ.get("DENALI_RESEARCH_REPO") or (
    str(_vendored) if (_vendored / "results" / "frozen" / "program_summary.csv").exists()
    else None)
FROZEN = Path(RESEARCH) / "results" / "frozen" / "program_summary.csv" if RESEARCH else None


@pytest.mark.skipif(not (FROZEN and FROZEN.exists()),
                    reason="set DENALI_RESEARCH_REPO to a clone of the study")
def test_reproduces_published_headline():
    """0.4649 on the frozen research data, or the tool and the paper disagree."""
    import pandas as pd
    s = pd.read_csv(FROZEN)
    got = audit(s["n_present"], s["n_hits_q05"])["r2_size_alone"]
    assert got == PUBLISHED_HEADLINE, (
        f"packaged audit() returns {got}, the study published {PUBLISHED_HEADLINE}. "
        "The maths in core.py is vendored verbatim and must not drift.")


def _synthetic(n=40, slope=0.08, noise=3.0, seed=7):
    rng = np.random.default_rng(seed)
    size = rng.integers(10, 600, n)
    hits = np.clip(size * slope + rng.normal(0, noise, n), 0, None).round()
    return size, hits


def test_size_driven_ranking_is_flagged():
    size, hits = _synthetic()
    r = audit(size, hits)
    assert r["verdict"] == "CONFOUNDED"
    assert r["r2_size_alone"] > 0.4


def test_size_independent_ranking_is_not_flagged():
    rng = np.random.default_rng(11)
    size = rng.integers(10, 600, 60)
    hits = rng.integers(0, 40, 60)          # hits unrelated to size
    r = audit(size, hits)
    assert r["verdict"] == "NOT SIZE-DOMINATED"
    assert r["r2_size_alone"] < 0.2


def test_refuses_too_few_sets():
    with pytest.raises(ValueError, match="at least 8"):
        audit([10, 20, 30], [1, 2, 3])


def test_nans_are_dropped_not_propagated():
    size, hits = _synthetic()
    size = size.astype(float).copy()
    size[0] = np.nan
    r = audit(size, hits)
    assert r["n_sets"] == len(hits) - 1
    assert math.isfinite(r["r2_size_alone"])


def test_constant_size_yields_nan_not_a_crash():
    r = audit([100] * 12, list(range(12)))
    assert math.isnan(r["r2_size_alone"])


def test_all_zero_hits_is_handled():
    r = audit(list(range(10, 220, 10)), [0] * 21)
    assert r["sets_with_zero_hits"] == 21


def test_never_names_a_set():
    """The tool's refusal to nominate is the point, not an omission."""
    size, hits = _synthetic()
    blob = str(audit(size, hits)).lower()
    assert "candidate" not in blob or "not a candidate" in blob
    assert "what_this_is_not" in audit(size, hits)


def test_replication_detects_shared_size_confound():
    rng = np.random.default_rng(3)
    size = rng.integers(10, 600, 50)
    a = np.clip(size * 0.08 + rng.normal(0, 2, 50), 0, None).round()
    b = np.clip(size * 0.08 + rng.normal(0, 2, 50), 0, None).round()
    r = audit_replication(size, a, b)
    assert r["pct_of_agreement_that_is_size"] > 50


def test_corpus_percentile_is_monotone_and_bounded():
    assert percentile(-1) == 0.0
    assert percentile(99) == 100.0
    assert percentile(0.1) < percentile(0.4) < percentile(0.9)
    assert N_SCREENS > 1000


def test_corpus_context_attaches_to_audit():
    size, hits = _synthetic()
    r = audit(size, hits)
    assert "corpus_percentile" in r
    assert "indicative, not exact" in r["corpus_caveat"]


def test_rerank_demotes_size_carried_entries():
    from denali_audit.core import rerank
    rng = np.random.default_rng(5)
    size = rng.integers(10, 600, 60)
    hits = np.clip(size * 0.08 + rng.normal(0, 4, 60), 0, None).round()
    r = rerank(size, hits, [f"P{i}" for i in range(60)], top=20)
    assert r["left_top_n"] > 0
    assert all(x["moved"] < 0 for x in r["left_the_top"]), "a fall must be negative"
    assert "Not a candidate list" in r["what_this_is_not"]


def test_rerank_leaves_an_unconfounded_ranking_alone():
    from denali_audit.core import rerank
    rng = np.random.default_rng(2)
    size = rng.integers(10, 600, 60)
    hits = rng.integers(0, 50, 60)          # unrelated to size
    r = rerank(size, hits, top=10)
    assert r["survived_top_n"] >= 7, "an unconfounded ranking should mostly survive"
