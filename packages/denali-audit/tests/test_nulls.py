"""The null moved into this package. Prove the move did not change a number.

`nulls.no_biology_null` is the same computation that produced the published null
column in results/breadth/null_baselines.json. It was moved here rather than
copied so there is one definition, and this file is what makes "the same" checkable
rather than asserted.

The research-repo path mirrors test_core.py: look next to the package first, then
DENALI_RESEARCH_REPO. Where a check genuinely cannot run without the study, it
SKIPS LOUDLY -- and the skip is itself asserted against, because a check that
vanishes with its input is the failure mode this repository has hit four times
(docs/METHOD_RULES.md, Evidence).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pytest

from denali_audit import nulls
from denali_audit.core import _r2, audit

RESEARCH = os.environ.get("DENALI_RESEARCH_REPO") or str(Path(__file__).resolve().parents[3])
NULLS_JSON = Path(RESEARCH) / "results" / "breadth" / "null_baselines.json"
FROZEN = Path(RESEARCH) / "results" / "frozen" / "program_summary.csv"
EXTERNAL = Path(RESEARCH) / "audits" / "external"

needs_study = pytest.mark.skipif(
    not (NULLS_JSON.exists() and FROZEN.exists()),
    reason="set DENALI_RESEARCH_REPO to a clone of the study")


@needs_study
def test_vendored_null_reproduces_the_published_arm_exactly():
    """The number this package computes IS the number the breadth arm published."""
    import pandas as pd
    s = pd.read_csv(FROZEN)
    got = nulls.no_biology_null(s.n_present.values, s.n_hits_q05.values, _r2)
    pub = json.loads(NULLS_JSON.read_text())["arms"]["denali_primary_published_0.4649"]
    assert got["expected_r2"] == pub["null_mean_r2"], (got, pub)
    assert got["ci95"] == pub["null_ci95"], (got, pub)
    assert nulls.position(0.4649, got) == "ABOVE"


@needs_study
def test_the_published_headline_survives_the_new_vocabulary():
    """0.4649 must still be the strong result, in the words that replaced the bands.

    This is the check that would have caught a verdict rewrite quietly demoting the
    study's own finding. Our screen is the one NON-counting input the package sees:
    hits count perturbations, so size has no arithmetic head start and the null sits
    near zero.
    """
    import pandas as pd
    s = pd.read_csv(FROZEN)
    r = audit(s.n_present.values, s.n_hits_q05.values)
    assert r["r2_size_alone"] == 0.4649
    assert r["mapping"]["structure"] == "non-counting"
    assert r["verdict"] == "MORE SIZE-CARRIED THAN ITS OWN NULL"
    assert r["no_biology_null"]["position"] == "ABOVE"


@needs_study
def test_real_published_screens_are_counting_and_mostly_do_not_clear():
    """The finding that forced this change, pinned so it cannot quietly reverse."""
    import pandas as pd
    from denali_audit import adapters
    seen, cleared = 0, 0
    for d in sorted(p for p in EXTERNAL.iterdir() if p.is_dir()):
        f = d / "std.csv"
        if not f.exists():
            continue
        m = adapters.detect(pd.read_csv(f))
        assert m is not None, f"{d.name} stopped parsing"
        size = pd.to_numeric(m.size, errors="coerce")
        hits = pd.to_numeric(m.hits, errors="coerce")
        r = audit(size, hits)
        assert r["mapping"]["structure"] == "counting", d.name
        seen += 1
        cleared += r["verdict"] == "MORE SIZE-CARRIED THAN ITS OWN NULL"
    assert seen == 7, f"expected the seven external screens, saw {seen}"
    assert cleared == 2, f"expected 2 of 7 to clear their null, got {cleared}"


def test_structure_is_decided_from_data_not_from_a_format_name():
    counting = nulls.structure([100, 200, 50], [10, 20, 5])
    assert counting["structure"] == "counting"
    assert counting["frac_hits_le_size"] == 1.0
    free = nulls.structure([10, 20, 5], [100, 200, 50])
    assert free["structure"] == "non-counting"


def test_a_counting_mapping_gets_a_binomial_null_and_it_is_not_near_zero():
    """The whole reason the bands were wrong: no-biology here is large, not ~0."""
    rng = np.random.default_rng(0)
    size = rng.integers(20, 500, 60).astype(float)
    hits = rng.binomial(size.astype(int), 0.1).astype(float)   # pure arithmetic
    n = nulls.no_biology_null(size, hits, _r2)
    assert "binomial" in n["kind"]
    assert n["expected_r2"] > 0.3, n
    r = audit(size, hits)
    assert r["verdict"] != "MORE SIZE-CARRIED THAN ITS OWN NULL", (
        "a ranking generated with NO biology at all was called more size-carried "
        "than its own null")


def test_no_verdict_reads_as_a_pass():
    """Every branch must carry a caveat. None of the three is a clean bill."""
    rng = np.random.default_rng(1)
    size = rng.integers(20, 500, 60).astype(float)
    for hits in (rng.binomial(size.astype(int), 0.1).astype(float),
                 (size * 3 + rng.normal(0, 1, 60)).clip(0)):
        w = audit(size, hits)["what_to_do"].lower()
        assert "not a clean" in w or "cannot tell" in w or "least able to justify" in w, w
        for banned in ("good case", "all-clear", "you are fine", "no problem"):
            assert banned not in w, (banned, w)


def test_the_guard_file_this_suite_depends_on_is_present():
    """Asserted, not gated. If the study is absent the checks above SKIP, and a
    skipped check and a passing check look identical unless something says so."""
    if not NULLS_JSON.exists():
        pytest.fail(
            f"{NULLS_JSON} is absent, so the checks pinning this package's null to "
            "the published arm did not run. That is a silent loss of coverage, not "
            "a pass. Set DENALI_RESEARCH_REPO or run from the study checkout.")
