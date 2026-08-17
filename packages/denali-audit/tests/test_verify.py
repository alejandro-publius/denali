"""`verify` must be unable to accuse, and must say what it could not check.

The commercial argument for this subcommand is that it can be pointed at work the
user did not produce. That makes two properties load-bearing rather than nice:
it must never read as an allegation, and "could not be checked" must be a normal
answer rather than an error path.
"""
from __future__ import annotations

import json

import numpy as np
import pytest

from denali_audit.verify import verify

_rng = np.random.default_rng(3)
_S = _rng.integers(10, 600, 60).astype(float)
_ABOVE = (_S, np.clip(_S * 20 + _rng.normal(0, 400, 60), 0, None).round())
_COUNTING = (_S, _rng.binomial(_S.astype(int), 0.1).astype(float))

# Words that would turn a measurement into an allegation. None may ever appear.
BANNED = ("fraud", "fraudulent", "misconduct", "fabricat", "dishonest", "unreliable",
          "bogus", "bad science", "poor quality", "cannot be trusted", "suspicious",
          "overstat", "exaggerat")


@pytest.mark.parametrize("case", [_ABOVE, _COUNTING])
def test_never_reads_as_an_allegation(case):
    blob = json.dumps(verify(*case, claim="We report robust enrichment.")).lower()
    for w in BANNED:
        assert w not in blob, f"verify() output contains {w!r}"


@pytest.mark.parametrize("case", [_ABOVE, _COUNTING])
def test_always_lists_what_it_could_not_check(case):
    r = verify(*case)
    assert r["not_verifiable"], "an empty not-verifiable list is never honest here"
    assert all(set(i) == {"what", "why"} for i in r["not_verifiable"])
    # the three structural ones can never be absent
    whats = " ".join(i["what"] for i in r["not_verifiable"])
    assert "biology" in whats and "read depth" in whats and "conclusion" in whats


def test_too_few_sets_is_a_first_class_answer_not_a_crash():
    r = verify([10, 20, 30], [1, 2, 3])
    assert r["status"] == "NOT VERIFIABLE FROM WHAT WAS PROVIDED"
    assert r["to_make_checkable"]
    assert r["not_verifiable"]
    json.dumps(r)


def test_a_degenerate_hit_column_is_not_verifiable_rather_than_cleared():
    """Constant hits shipped a false all-clear once. It must not read as one here."""
    r = verify(_S, np.full(60, 197.0))
    assert r["status"] == "NOT VERIFIABLE FROM WHAT WAS PROVIDED"
    assert "DISTINGUISHABLE" not in r["status"].replace("NOT VERIFIABLE", "")


def test_a_counting_mapping_says_its_r2_is_partly_arithmetic():
    r = verify(*_COUNTING)
    text = " ".join(i["what"] + " " + i["why"] for i in r["not_verifiable"])
    assert "arithmetic" in text and "own members" in text


def test_being_distinguishable_is_never_reported_as_an_endorsement():
    r = verify(*_ABOVE)
    assert r["status"].startswith("DISTINGUISHABLE")
    assert "lowest bar" in r["reading"], (
        "clearing a trivial baseline must not be presented as a strong result")


def test_every_report_carries_symmetry_and_a_reproduce_command():
    for case in (_ABOVE, _COUNTING, ([10, 20, 30], [1, 2, 3])):
        r = verify(*case)
        assert r["reproduce"].startswith("denali verify")
        assert "reproducible by the party being verified" in r["symmetry"]
        assert "not an allegation" in r["what_this_is_not"]


def test_a_claim_is_quoted_verbatim_and_never_paraphrased():
    claim = "Our top pathway is a novel driver of resistance."
    r = verify(*_ABOVE, claim=claim)
    assert r["claim_as_stated"] == claim


def test_a_stated_size_share_is_compared_without_calling_it_a_discrepancy():
    r = verify(*_ABOVE, claimed_size_share=0.10)
    assert "delta_vs_measured" in r
    assert "not necessarily a discrepancy" in r["delta_reading"]
