"""Is a claim you did not produce distinguishable from a trivial baseline?

WHO THIS IS FOR. Someone assessing a result they did not generate -- a reviewer, a
program officer, an analyst reading a data room. They have a supplementary table
and a sentence from a paper. They do not have the pipeline, the raw data, or the
authors on the phone.

WHAT IT CAN ANSWER, and it is one narrow thing: whether a set-level enrichment
ranking is distinguishable from what the same table would look like with no
biology in it. That is the only question this package has ever been able to
answer, and `verify` exists to stop that being oversold.

WHAT IT REFUSES TO DO. It does not rate a paper, a laboratory, a company or a
person. It does not call anything fraudulent, weak, or unreliable. A ranking that
is indistinguishable from its null is not a wrong result and its authors are not
doing anything improper -- most published enrichment rankings have never been
asked this question, because until recently nothing packaged asked it.

WHY "NOT VERIFIABLE" IS THE NORMAL ANSWER. Most claims a reader wants checked are
not about set size at all, and this tool cannot reach them. That is designed as
the primary path, printed at the same size as everything else, and never dressed
up as a failure of the claim. A claim that cannot be checked from what was
provided is a statement about what was provided.

SYMMETRY IS THE WHOLE ETHIC. Every number in a verification report is reproducible
by the person being verified, from the same file, with the command printed in the
report. A verification somebody cannot rerun against you is not verification.

Prior art, and the method is not ours: EGAD shipped node-degree AUROC as a
built-in null in 2017 (doi:10.1093/bioinformatics/btw695); Crow et al. PNAS 2019
did the cross-dataset version; GREAT (doi:10.1038/nbt.1630) corrects region-size
bias. What is packaged here is the instrument, not the idea.
"""
from __future__ import annotations

from . import __version__
from .core import MIN_SETS, audit

# Things this tool cannot reach, stated once so every report carries the same list
# rather than each surface inventing its own.
NEVER_CHECKABLE = (
    ("the biology of any set in the ranking",
     "this tool reads only set sizes and hit counts; it never sees a gene, an "
     "effect size, or an experiment"),
    ("read depth, guide efficacy, batch and replicate structure",
     "these are other ways a ranking can be carried by how it was measured, and "
     "this tool tests none of them"),
    ("whether the study's conclusion is correct",
     "a ranking is one line of evidence in a paper and usually not the load-bearing "
     "one"),
)


def verify(sizes, hits, claim: str | None = None, claimed_size_share: float | None = None,
           source: str | None = None, command: str | None = None) -> dict:
    """Verify one enrichment ranking against its own construction-only null.

    claimed_size_share : if the source states how much of its ranking it attributes
        to set size, pass it and the report compares like with like. Almost no
        paper reports this, which is itself the finding, so it is optional and its
        absence is recorded rather than filled in.
    """
    out: dict = {
        "denali_version": __version__,
        "what_was_provided": {
            "source": source,
            "n_rows_usable": None,
        },
        "claim_as_stated": claim,
        "not_verifiable": [],
    }

    try:
        a = audit(sizes, hits)
    except ValueError as e:
        out["status"] = "NOT VERIFIABLE FROM WHAT WAS PROVIDED"
        out["why"] = str(e)
        out["not_verifiable"].append({
            "what": "anything at all about this ranking",
            "why": f"{e}. A construction-only null needs at least {MIN_SETS} sets "
                   "to be estimated; below that the interval is wider than any "
                   "answer it could give."})
        out["to_make_checkable"] = [
            f"report at least {MIN_SETS} sets with both a set size and a count of "
            "significant members"]
        return _finish(out, command)

    out["what_was_provided"]["n_rows_usable"] = a["n_sets"]
    out["floor"] = {
        "r2_size_alone": a["r2_size_alone"],
        "mapping": a["mapping"],
        "no_biology_null": a.get("no_biology_null"),
    }
    out["ranking_verdict"] = a["verdict"]

    null = a.get("no_biology_null")
    if a["verdict"] == "UNDETERMINED" or null is None:
        out["status"] = "NOT VERIFIABLE FROM WHAT WAS PROVIDED"
        out["why"] = a.get("reading", "the question could not be asked of this table")
        out["not_verifiable"].append({
            "what": "whether this ranking is distinguishable from its own null",
            "why": a.get("what_to_do", "")})
    else:
        stable = null.get("verdict_is_stable")
        if a["verdict"] == "MORE SIZE-CARRIED THAN ITS OWN NULL":
            out["status"] = "DISTINGUISHABLE FROM THE CONSTRUCTION-ONLY BASELINE"
            out["reading"] = (
                f"This ranking is predicted by set size more than a version of "
                f"itself containing no biology would be: R^2 {a['r2_size_alone']} "
                f"against a null of {null['expected_r2']} "
                f"(95% interval {null['ci95'][0]}-{null['ci95'][1]}). That means the "
                "size relationship here is not merely arithmetic. It does NOT mean "
                "the ranking is biologically right -- being distinguishable from a "
                "trivial baseline is the lowest bar there is, not a high one.")
        else:
            out["status"] = "NOT DISTINGUISHABLE FROM THE CONSTRUCTION-ONLY BASELINE"
            out["reading"] = (
                f"R^2 {a['r2_size_alone']} against a no-biology null of "
                f"{null['expected_r2']} (95% interval {null['ci95'][0]}-"
                f"{null['ci95'][1]}). By this measure the ranking cannot be told "
                "apart from one built the same way with no biology in it. This is a "
                "statement about what THIS measure can resolve on THIS table. It is "
                "not a finding that the study is wrong, and most published rankings "
                "have never been asked the question.")
        if stable is False:
            out["not_verifiable"].append({
                "what": "the verdict above, with confidence",
                "why": (
                    "the observation sits "
                    f"{null.get('distance_to_edge_in_ci_widths')} interval-widths "
                    "from the boundary and the position changes in "
                    f"{round((1 - null.get('position_stability', 1)) * 100)}% of "
                    "redraws of the null. Treat it as borderline rather than as a "
                    "result.")})

    if a["mapping"]["structure"] == "counting":
        out["not_verifiable"].append({
            "what": "how much of this R^2 is a confound rather than arithmetic",
            "why": (
                "hits are counted over the sets' own members here, so a count is "
                "being regressed on the number of trials that produced it. The "
                "no-biology value is large by construction, which is exactly why "
                "the raw R^2 is compared against it rather than against zero.")})

    if claimed_size_share is None:
        out["not_verifiable"].append({
            "what": "the source's own stated size share, compared like with like",
            "why": ("no claimed size share was supplied. Almost no paper reports "
                    "one, which is the gap this instrument exists in rather than a "
                    "criticism of any particular source.")})
    else:
        out["claimed_size_share"] = claimed_size_share
        out["delta_vs_measured"] = round(float(claimed_size_share) - a["r2_size_alone"], 4)
        out["delta_reading"] = (
            f"The source states {claimed_size_share}; this table measures "
            f"{a['r2_size_alone']}. Difference {out['delta_vs_measured']:+.4f}. A "
            "difference is not necessarily a discrepancy -- estimands differ, and "
            "the source may be computing something adjacent on different rows.")

    for what, why in NEVER_CHECKABLE:
        out["not_verifiable"].append({"what": what, "why": why})

    out["to_make_checkable"] = [
        "state the set size and the count of significant members for every set, not "
        "only the significant ones",
        "state the significance threshold that produced the hit counts",
        "state whether hit counts are over each set's own members or over a larger "
        "universe -- the correct no-biology null differs and so does the reading",
        "report the size share of the ranking alongside the ranking, so a reader "
        "can compare like with like without recomputing it",
    ]
    return _finish(out, command)


def _finish(out: dict, command: str | None) -> dict:
    out["reproduce"] = command or "denali verify YOUR_FILE.csv"
    out["symmetry"] = (
        "Every number above is reproducible by the party being verified, from the "
        "same file, with the command above. Nothing was uploaded and nothing left "
        "this machine.")
    out["what_this_is_not"] = (
        "Not a rating of a paper, a laboratory, a company or a person, and not an "
        "allegation of any kind. It compares one ranking against a baseline "
        "computed from that same ranking's own construction. It names no gene and "
        "no gene set, and it nominates nothing.")
    return out
