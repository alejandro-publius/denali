"""The screen-level formats: MAGeCK, BAGEL2, drugZ.

These are the files a screener is holding at the moment the decision gets made --
before any enrichment step has run, which is a step many of them never run at all.
Every fixture here is SYNTHETIC and its gene identifiers are invented: a fixture's
job is to pin the column shape, and inventing the identifiers keeps a real symbol
from ever sitting next to a verdict.

Each adapter is tested for three things: that it is recognised without flags, that
what it maps onto `size` and `hits` is what the tool's own documentation says it is,
and -- where the source tool reports no per-set hit count -- that the mapping is
marked approximate and says why. A silent substitution here would be the exact
failure this project measures.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from denali_audit.adapters import detect, describe_failure
from denali_audit.core import audit, rerank, VERDICTS

FIX = Path(__file__).parent / "fixtures"


def read(name: str) -> pd.DataFrame:
    return pd.read_csv(FIX / name, sep="\t")


# ---------------------------------------------------------------- MAGeCK

def test_mageck_gene_summary_is_recognised():
    m = detect(read("mageck_gene_summary.txt"))
    assert m.fmt == "MAGeCK (gene_summary)"
    assert not m.approximate, "num and neg|goodsgrna are both exact counts"


def test_mageck_maps_guides_and_good_guides():
    df = read("mageck_gene_summary.txt")
    m = detect(df)
    assert m.size.tolist() == df["num"].tolist()
    assert m.hits.tolist() == df["neg|goodsgrna"].tolist()
    assert (m.hits <= m.size).all(), "good guides cannot exceed guides"


def test_mageck_says_which_direction_it_audited():
    """A depletion screen and an enrichment screen are different questions; the
    adapter picks one and must not leave the user guessing which."""
    m = detect(read("mageck_gene_summary.txt"))
    assert "neg" in m.note and "pos|goodsgrna" in m.note


def test_mageck_audit_runs_end_to_end():
    m = detect(read("mageck_gene_summary.txt"))
    r = audit(m.size, m.hits)
    assert r["verdict"] in VERDICTS
    assert r["n_sets"] == 60


def test_constant_guide_library_is_undetermined_not_an_all_clear():
    """Most libraries build every gene with the same number of guides. Size then
    has no variance and the R^2 is undefined -- which the tool must not report as
    'not size-dominated, the good case'."""
    m = detect(read("mageck_gene_summary_constant.txt"))
    r = audit(m.size, m.hits)
    assert r["verdict"] == "UNDETERMINED"
    assert "not an all-clear" in r["what_to_do"]


def test_constant_guide_library_warns_in_the_mapping_too():
    m = detect(read("mageck_gene_summary_constant.txt"))
    assert "constant" in m.note


def test_rerank_on_constant_size_does_not_claim_survival():
    m = detect(read("mageck_gene_summary_constant.txt"))
    df = read("mageck_gene_summary_constant.txt")
    r = rerank(m.size, m.hits, df["id"], top=10)
    assert r["size_is_constant"] is True
    assert "could not be applied" in r["reading"]


# ---------------------------------------------------------------- drugZ

def test_drugz_is_recognised_and_flagged_approximate():
    m = detect(read("drugz_output.txt"))
    assert m.fmt == "drugZ"
    assert m.approximate, "drugZ reports no per-gene count of significant guides"
    assert "numObs" in m.note and "synth" in m.note


def test_drugz_credits_only_significant_genes_their_observations():
    df = read("drugz_output.txt")
    m = detect(df)
    sig = df["fdr_synth"] < 0.05
    assert (m.hits[sig] == df.loc[sig, "numObs"]).all()
    assert (m.hits[~sig] == 0).all()


def test_drugz_size_is_the_observation_count():
    df = read("drugz_output.txt")
    m = detect(df)
    assert m.size.tolist() == df["numObs"].tolist()


# ---------------------------------------------------------------- BAGEL2

def test_bagel_is_recognised_and_flagged_approximate():
    m = detect(read("bagel_bf.txt"))
    assert m.fmt == "BAGEL2"
    assert m.approximate, "a Bayes factor is not a count of significant guides"
    assert "NumObs" in m.note


def test_bagel_credits_genes_whose_bayes_factor_favours_essentiality():
    df = read("bagel_bf.txt")
    m = detect(df)
    pos = df["BF"] > 0
    assert (m.hits[pos] == df.loc[pos, "NumObs"]).all()
    assert (m.hits[~pos] == 0).all()


def test_bagel_audit_runs_end_to_end():
    m = detect(read("bagel_bf.txt"))
    r = audit(m.size, m.hits)
    assert r["n_sets"] == 60
    assert r["verdict"] in VERDICTS


# ---------------------------------------------- files we must refuse, usefully

def test_mageck_per_guide_file_is_refused_by_name():
    df = read("mageck_sgrna_summary.txt")
    assert detect(df) is None
    msg = describe_failure(df)
    assert "sgrna_summary" in msg and "gene_summary.txt" in msg


def test_bagel_without_numobs_is_refused_by_name():
    df = read("bagel_pr.txt")
    assert detect(df) is None
    msg = describe_failure(df)
    assert "NumObs" in msg, "the user must be told which column is missing"


def test_bagel_per_guide_file_is_refused_by_name():
    df = pd.DataFrame({"RNA": ["g1"] * 9, "GENE": ["SYNG0001"] * 9,
                       "BF": range(9), "NumObs": [3] * 9})
    assert detect(df) is None
    assert "per-guide" in describe_failure(df)


# ------------------------------------------------- the rules, on these formats

@pytest.mark.parametrize("name", ["mageck_gene_summary.txt", "drugz_output.txt",
                                  "bagel_bf.txt"])
def test_screen_formats_still_refuse_to_nominate(name):
    """These formats are gene-level, which is precisely where this project makes no
    claims. The tool reports which entries a ranking cannot justify; it must not
    start recommending any of them just because the rows are now genes."""
    df = read(name)
    m = detect(df)
    r = rerank(m.size, m.hits, df[m.set_col], top=10)
    assert "Not a candidate list" in r["what_this_is_not"]
    assert "recommendation" in r["what_this_is_not"]


@pytest.mark.parametrize("name", ["drugz_output.txt", "bagel_bf.txt"])
def test_approximate_inputs_carry_their_warning_into_the_result(name):
    """An approximate mapping that loses its warning on the way to the verdict is
    worse than no adapter at all."""
    m = detect(read(name))
    assert m.approximate and len(m.note) > 40
    assert "stand-in" in m.note


# ------------------------------------------------- a REAL screen, not a mock
# fixtures/mageck_real_slice.txt is every 150th row of the RRA gene_summary.txt
# published with MAGeCKFlute (Liu lab, DFCI), plus the control pseudo-gene, kept
# whole: real column names, real guide counts, real hit counts. The synthetic
# fixtures above pin the FORMAT. These pin what the tool actually says when the
# input was not built to make a point.

def test_real_screen_is_read_without_flags():
    m = detect(read("mageck_real_slice.txt"))
    assert m.fmt == "MAGeCK (gene_summary)"
    assert not m.approximate


def test_real_screen_flags_the_control_pseudo_gene_as_high_leverage():
    """One row pools every non-targeting guide and is 245x a normal gene. It is
    a lever on a straight-line fit, so it is named. It is not removed."""
    m = detect(read("mageck_real_slice.txt"))
    assert "10x the median size or more" in m.note
    assert "Nothing is dropped" in m.note


def test_one_control_row_can_manufacture_a_verdict_and_the_tool_says_so():
    """The finding that came from running this on a real file instead of a mock.

    A pooled library pools every non-targeting guide into one control
    pseudo-gene, so that row has hundreds of guides where every real gene has
    four. On the FULL published screen (19,326 genes) it is harmless: R^2 0.0067
    with it, 0.0099 without. On this 130-row slice of the same file it carries
    the fit -- 0.4137 with, 0.0237 without -- and moves the verdict. A tool
    arguing that rankings get carried by arithmetic must not hand out a verdict
    carried by one point in silence.

    The verdict words changed on 2026-08-17 and the point of the test did not.
    MAGeCK is a counting mapping (good guides <= guides), so its no-biology null
    is large and the raw R^2 of 0.4137 is BELOW it -- which is why the old
    CONFOUNDED band was wrong here and the caution is what actually matters.
    """
    df = read("mageck_real_slice.txt")
    m = detect(df)
    r = audit(m.size, m.hits)
    assert r["mapping"]["structure"] == "counting"
    assert r["verdict"] == "LESS SIZE-CARRIED THAN ITS OWN NULL"
    # The verdict itself is ROBUST here -- the null moves with the leverage point,
    # 0.4897 to 0.1026, so the answer is BELOW either way. What must not be silent
    # is that one row moved the raw R^2 from 0.4137 to 0.0237.
    assert r["verdict_depends_on_extreme_entries"] is False
    assert r["r2_depends_on_extreme_entries"] is True
    assert r["r2_without_extreme_entries"] < 0.20
    assert "Nothing has been dropped" in r["caution"]
    assert "1 entry at least 10x" in r["caution"], "must not read 'entry(ies)'"


def test_the_same_check_is_quiet_when_no_entry_dominates():
    """The caution must be earned. On sets of comparable size -- which is what
    every enrichment format produces -- none of this machinery fires at all."""
    import numpy as np
    rng = np.random.default_rng(7)
    size = rng.integers(10, 600, 40)                  # sets of comparable size
    hits = np.clip(size * 0.08 + rng.normal(0, 3.0, 40), 0, None).round()
    r = audit(size, hits)
    assert "caution" not in r
    assert "n_extreme_entries" not in r


def test_a_standard_library_is_not_size_confounded_at_the_gene_level():
    """The uncomfortable one, and the reason it is written down.

    A pooled library gives nearly every real gene the same number of guides by
    design, so at the GENE level there is very little for set size to explain.
    The full published screen this fixture came from returns R^2 0.0067, NOT
    SIZE-DOMINATED. denali's 46% headline is a PATHWAY-level result, where set
    sizes span an order of magnitude. docs/USERS.md hedges the "run it the
    moment your screen finishes" claim for exactly this reason; if this ever
    changes, revisit that document.

    Measured here on the slice with the control row excluded, which is the
    honest comparison: the slice WITH it is a leverage artefact, tested above.
    """
    df = read("mageck_real_slice.txt")
    real = df[df["num"] < 100]
    r = audit(real["num"], real["neg|goodsgrna"])
    # Was NOT SIZE-DOMINATED. Same meaning, but the new wording refuses to read as
    # a pass: this measure does not flag the ranking, and this measure only ever
    # asked about set size.
    assert r["verdict"] == "LESS SIZE-CARRIED THAN ITS OWN NULL"
    assert r["r2_size_alone"] < 0.10
    assert "not a clean bill of health" in r["what_to_do"]
