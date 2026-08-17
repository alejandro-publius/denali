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


# ---------------------------------------------------------------------------
# baseline(). The load-bearing test is the first one: a "model" that is really
# just set size wearing a hat must NOT be reported as beating set size. The
# first implementation failed exactly that, on the error metrics, because its
# baseline was fitted on the wrong scale -- so the test is written from the
# failure rather than from the intended behaviour.

def _size_carried_case(n=60, seed=7):
    rng = np.random.default_rng(seed)
    size = rng.integers(10, 600, n)
    truth = np.clip(size * 0.08 + rng.normal(0, 4, n), 0, None).round()
    sizeish = size * 0.08 + rng.normal(0, 4, n)      # a model that knows nothing
    informed = truth + rng.normal(0, 1, n)           # a model that knows something
    return size, truth, sizeish, informed


@pytest.mark.parametrize("metric", ["spearman", "pearson", "r2", "mae", "rmse",
                                    "top_k_overlap"])
def test_a_model_that_is_only_size_does_not_beat_size(metric):
    from denali_audit.core import baseline
    size, truth, sizeish, _ = _size_carried_case()
    r = baseline(size, truth, sizeish, metric=metric)
    assert r["beats_size_alone"] is False, (
        f"{metric}: a size-plus-noise model was reported as beating a size-only "
        f"baseline ({r['your_score']} vs {r['size_only_score']}). The baseline "
        "is under-specified and is flattering the caller.")


@pytest.mark.parametrize("metric", ["spearman", "pearson", "r2", "mae", "rmse",
                                    "top_k_overlap"])
def test_a_model_that_knows_something_does_beat_size(metric):
    from denali_audit.core import baseline
    size, truth, _, informed = _size_carried_case()
    r = baseline(size, truth, informed, metric=metric)
    assert r["beats_size_alone"] is True, f"{metric}: {r['reading']}"


def test_lower_is_better_metrics_are_scored_in_the_right_direction():
    from denali_audit.core import baseline
    size, truth, _, informed = _size_carried_case()
    r = baseline(size, truth, informed, metric="mae")
    assert r["higher_is_better"] is False
    # the informed model's MAE is lower, and a lower error must read as a win
    assert r["your_score"] < r["size_only_score"]
    assert r["delta"] > 0 and r["beats_size_alone"] is True


def test_the_baseline_is_out_of_sample_not_a_refit():
    """A baseline that saw the row it predicts is not a baseline."""
    from denali_audit.core import baseline
    size, truth, _, _ = _size_carried_case()
    got = np.array(baseline(size, truth, truth, metric="mae")["baseline_predictions"])
    in_sample = 10 ** np.polyval(
        np.polyfit(size, np.log10(1 + truth), 1), size) - 1
    raw_in_sample = np.polyval(np.polyfit(size, truth, 1), size)
    assert not np.allclose(got, in_sample, atol=1e-6)
    assert not np.allclose(got, raw_in_sample, atol=1e-6)
    assert "leave-one-out" in baseline(
        size, truth, truth, metric="mae")["how_the_baseline_was_built"]


def test_metric_is_never_guessed():
    from denali_audit.core import baseline
    size, truth, _, informed = _size_carried_case()
    with pytest.raises(ValueError, match="name the metric"):
        baseline(size, truth, informed)
    with pytest.raises(ValueError, match="unrecognised metric"):
        baseline(size, truth, informed, metric="auroc")


def test_unknown_metric_can_still_get_the_baseline_predictions():
    """Refusing to guess must not mean refusing to be useful."""
    from denali_audit.core import baseline
    size, truth, _, informed = _size_carried_case()
    r = baseline(size, truth, informed, metric="none")
    assert len(r["baseline_predictions"]) == len(size)
    assert "your_score" not in r and "delta" not in r


def test_refuses_mismatched_lengths_rather_than_aligning_them():
    from denali_audit.core import baseline
    with pytest.raises(ValueError, match="same length"):
        baseline([10] * 12, [1] * 12, [1] * 11, metric="mae")


def test_refuses_too_few_sets():
    from denali_audit.core import baseline
    with pytest.raises(ValueError, match="at least 8"):
        baseline([10, 20, 30], [1, 2, 3], [1, 2, 3], metric="mae")


def test_constant_size_degenerates_to_the_mean_and_says_so():
    from denali_audit.core import baseline
    rng = np.random.default_rng(4)
    truth = rng.integers(0, 40, 20)
    r = baseline([50] * 20, truth, truth + rng.normal(0, 1, 20), metric="mae")
    assert r["size_is_constant"] is True
    assert "mean-only" in r["how_the_baseline_was_built"]


def test_carries_the_scope_limit_6_boundary_where_it_applies():
    """hits counted over the set's own members: a strong baseline is arithmetic."""
    from denali_audit.core import baseline
    rng = np.random.default_rng(9)
    size = rng.integers(20, 400, 40)
    overlap = np.array([rng.integers(0, s) for s in size])       # hits <= size
    r = baseline(size, overlap, overlap + rng.normal(0, 2, 40), metric="spearman")
    assert "boundary_condition" in r
    assert "scope limit 6" in r["boundary_condition"]
    # and NOT where hits are counted over something else entirely
    big = overlap * 30 + 100
    assert "boundary_condition" not in baseline(
        size, big, big + rng.normal(0, 2, 40), metric="spearman")


def test_baseline_never_judges_the_model():
    from denali_audit.core import baseline
    size, truth, _, informed = _size_carried_case()
    r = baseline(size, truth, informed, metric="spearman")
    assert "not a claim that any model is bad" in r["what_this_is_not"].lower()
    blob = " ".join(str(v) for v in r.values()).lower()
    for word in ("candidate", "nominate", "recommend"):
        assert word not in blob or "not a" in blob


def test_rerank_leaves_an_unconfounded_ranking_alone():
    from denali_audit.core import rerank
    rng = np.random.default_rng(2)
    size = rng.integers(10, 600, 60)
    hits = rng.integers(0, 50, 60)          # unrelated to size
    r = rerank(size, hits, top=10)
    assert r["survived_top_n"] >= 7, "an unconfounded ranking should mostly survive"


# ---------------------------------------------------------------------------
# atlas(). The claim is that a citation means ONE thing: every caller who looks
# up the same screen gets the same floor, and the string they cite pins the
# exact table it came from. So the tests are about identity and refusal, not
# about the numbers being any particular value.

def test_every_atlas_floor_is_a_real_r2():
    from denali_audit.atlas import FLOORS, N_SCREENS
    assert len(FLOORS) == N_SCREENS
    for sid, row in FLOORS.items():
        r2_log, r2_raw, n_hits, n_measured, n_sets, pmid = row
        assert isinstance(sid, int)
        assert 0.0 <= r2_log <= 1.0, f"screen {sid}: floor {r2_log} is not an R^2"
        assert 0.0 <= r2_raw <= 1.0, f"screen {sid}: raw floor {r2_raw} is not an R^2"
        assert n_hits > 0 and n_measured > 0 and n_sets >= 8
        assert pmid, f"screen {sid} has no PubMed id to attribute it to"


def test_a_screen_outside_the_atlas_is_refused_not_guessed():
    from denali_audit.atlas import floor
    for bad in (999999999, "not-a-number", None, ""):
        r = floor(bad)
        assert r["status"] == "NOT_IN_ATLAS", f"{bad!r} produced {r['status']}"
        assert "no_biology_floor" not in r, (
            f"{bad!r} was given a floor it has no right to")


def test_a_lookup_carries_what_it_is_not_and_how_to_cite():
    from denali_audit.atlas import FLOORS, floor
    r = floor(sorted(FLOORS)[0])
    assert r["status"] == "IN_ATLAS"
    assert "not a quality score" in r["what_this_is_not"].lower()
    assert "doi:10.1002/pro.3978" in r["cite"], "the source data must be cited"
    assert r["source_sha256"] in r["cite"] or r["source_sha256"][:16] in r["cite"]


def test_the_citation_pins_the_exact_table():
    """A citation that does not identify the data is not a citation."""
    from denali_audit.atlas import N_SCREENS, SOURCE_SHA256, citation
    c = citation()
    assert SOURCE_SHA256[:16] in c
    assert str(N_SCREENS) in c
    assert len(SOURCE_SHA256) == 64


def test_the_atlas_names_no_gene_and_no_gene_set():
    """The scope limit, enforced on the one module that ships bulk data."""
    from denali_audit import atlas
    import pathlib
    src = pathlib.Path(atlas.__file__).read_text()
    # Hallmark set names are the thing most likely to leak in with screen rows.
    assert "HALLMARK_" not in src
