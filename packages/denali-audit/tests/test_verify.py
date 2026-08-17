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


# --- the report artifact -----------------------------------------------------

def test_report_is_self_contained_and_makes_no_network_call():
    """It is used on data-room material. Nothing may leave the machine."""
    from denali_audit.verify import report_html
    html = report_html(verify(*_ABOVE, claim="A claim.", source="t.csv"))
    for bad in ("http://", "https://", "<script", "src=", "@import", "fetch(", "XMLHttpRequest"):
        assert bad not in html, f"report references {bad!r}"


def test_report_escapes_a_claim_that_contains_markup():
    """The claim is quoted from a document nobody here controls."""
    from denali_audit.verify import report_html
    nasty = '<script>alert(1)</script> & "quoted" <b>'
    html = report_html(verify(*_ABOVE, claim=nasty))
    assert "<script>alert" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "&amp;" in html and "&quot;" in html


def test_report_carries_the_reproduce_command_and_the_boundary():
    from denali_audit.verify import report_html
    r = verify(*_ABOVE, claim="A claim.", source="t.csv")
    html = report_html(r)
    assert r["reproduce"] in html
    assert "not an allegation" in html
    assert "Nothing was uploaded" in html
    assert "no account, no server" in html


def test_report_never_shows_a_bare_point_estimate_for_the_baseline():
    """The brief's rule: the delta always carries its uncertainty."""
    from denali_audit.verify import report_html
    html = report_html(verify(*_ABOVE))
    assert "95% interval" in html


def test_report_works_when_nothing_could_be_verified():
    """The not-verifiable path is the common one and must still produce a page."""
    from denali_audit.verify import report_html
    html = report_html(verify([10, 20, 30], [1, 2, 3]))
    assert "NOT VERIFIABLE FROM WHAT WAS PROVIDED" in html
    assert "<h1>" in html and "</main>" in html


def test_the_readme_states_the_real_number_of_banned_words():
    """A count typed into prose must match the list it counts.

    I wrote "fourteen words" into the package README while BANNED had thirteen
    entries, minutes after reporting on this exact failure class elsewhere in the
    repository. Correcting the number fixes today; this guard fixes tomorrow, when
    somebody adds a word and the prose silently stops being true.

    Source-tree check: a wheel carries the README as metadata, not as a file at
    this path, so absence there is legitimate and is distinguished from a README
    that has moved or been deleted inside a checkout.
    """
    from pathlib import Path
    readme = Path(__file__).resolve().parents[1] / "README.md"
    if not readme.exists():
        pkg_root = readme.parent
        assert not (pkg_root / "denali_audit").is_dir(), (
            f"{readme} is missing but a source checkout is present at {pkg_root}")
        pytest.skip("no source tree here (wheel-only run); this check is in-repo only")
    words = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
             7: "seven", 8: "eight", 9: "nine", 10: "ten", 11: "eleven",
             12: "twelve", 13: "thirteen", 14: "fourteen", 15: "fifteen",
             16: "sixteen", 17: "seventeen", 18: "eighteen", 19: "nineteen",
             20: "twenty"}
    # WHITESPACE-NORMALISED, AND THE MISSING CASE FAILS RATHER THAN RETURNS.
    # The first version searched the raw text for "words including" and returned
    # quietly when it was absent. The README wraps that line, so the substring was
    # never contiguous, the early return always fired, and the guard passed with
    # BANNED at fourteen against a README saying thirteen. Caught by mutating
    # BANNED and watching it stay green -- not by reading it.
    t = " ".join(readme.read_text().split())
    import re
    m = re.search(r"never to contain (\w+) words including", t)
    assert m, ("the README sentence this guard keeps in step is gone or reworded. "
               "Update this test deliberately; do not let it pass by not finding "
               "its subject.")
    expected = words.get(len(BANNED))
    assert expected, f"add a number word for {len(BANNED)} to this test"
    assert m.group(1) == expected, (
        f"the README says {m.group(1)!r} banned words; BANNED has {len(BANNED)}")
