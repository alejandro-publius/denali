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
from denali_audit.core import audit, rerank

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
    assert r["verdict"] in {"CONFOUNDED", "PARTIALLY CONFOUNDED", "NOT SIZE-DOMINATED"}
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
    assert r["verdict"] in {"CONFOUNDED", "PARTIALLY CONFOUNDED",
                            "NOT SIZE-DOMINATED", "UNDETERMINED"}


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
