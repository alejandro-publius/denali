"""How much of a set-level ranking is explained by how the sets were built?

`audit()` here is THE definition, not a copy of one. It began as a verbatim vendoring
of src/audit_screen.py in the denali research repository -- the code that produced the
published figures -- and for a while both files carried the same forty lines with
nothing checking them against each other. That is now the other way round: the study's
src/audit_screen.py imports this function, so the research and the shipped tool run the
same bytes and there is no second copy to drift from.

It must not move: packages/denali-audit/tests/test_core.py asserts that this reproduces
the published headline of 0.4649 on the frozen research data, so a change that moves a
number fails the build.

`audit_replication()` below is the exception -- see its docstring. It is genuinely a
different function from the study's, returns different numbers, and is deliberately
left that way.

Reference: VIF = 1 + (m-1)*rho_bar, Wu & Smyth 2012, Nucleic Acids Research
40(17):e133, doi:10.1093/nar/gks461.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

MIN_SETS = 8

CONFOUNDED = 0.40
PARTIAL = 0.20


def _spearman(x, y) -> float:
    """Spearman by its definition: Pearson on the ranks, average ranks for ties.

    Not a reimplementation for its own sake. `pd.Series.corr(method="spearman")`
    imports scipy, which this package does not depend on -- so on a clean install
    `denali audit` died with ModuleNotFoundError, and every machine that had scipy
    for other reasons hid it. Pulling in scipy for one rank correlation is a large
    dependency for a tool whose whole argument is that it should be trivial to run.
    Verified to agree with scipy.stats.spearmanr to 1e-12 on the frozen study data
    and on every fixture in the suite.
    """
    xs, ys = pd.Series(np.asarray(x, dtype=float)), pd.Series(np.asarray(y, dtype=float))
    if xs.std() == 0 or ys.std() == 0:
        return float("nan")
    return float(np.corrcoef(xs.rank(), ys.rank())[0, 1])


def _r2(x, y) -> float:
    x = np.asarray(x, dtype=float)
    if np.std(x) == 0:
        return float("nan")
    b = np.polyfit(x, y, 1)
    pred = np.polyval(b, x)
    ss_res = float(((y - pred) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    return float("nan") if ss_tot == 0 else 1 - ss_res / ss_tot


def audit(sizes, hits, corr=None) -> dict:
    """How much of a set-level hit ranking is explained by set size alone?

    sizes : genes measured per set        hits : significant results per set
    corr  : optional mean inter-gene correlation per set

    Returns plain numbers. No verdict about any individual set.
    """
    s = np.asarray(sizes, dtype=float)
    h = np.asarray(hits, dtype=float)
    ok = np.isfinite(s) & np.isfinite(h)
    s, h = s[ok], h[ok]
    n = len(s)
    if n < MIN_SETS:
        raise ValueError(f"need at least {MIN_SETS} sets to say anything; got {n}")

    # log1p(hits) is the scale a hit count actually lives on: the difference
    # between 0 and 10 hits matters more than between 500 and 510.
    y = np.log10(1.0 + h)

    out = {
        "n_sets": int(n),
        "size_range": [int(s.min()), int(s.max())],
        "r2_size_alone": round(_r2(s, y), 4),
        "spearman_size_vs_hits": round(_spearman(s, y), 4),
        "sets_with_zero_hits": int((h == 0).sum()),
    }

    if corr is not None:
        c = np.asarray(corr, dtype=float)[ok]
        if np.isfinite(c).all():
            vif = 1.0 + (s - 1.0) * c
            out["vif_range"] = [round(float(vif.min()), 2), round(float(vif.max()), 2)]
            out["r2_vif"] = round(_r2(np.log10(vif), y), 4)

    share = out.get("r2_vif", out["r2_size_alone"])
    out["share_explained_without_biology"] = share

    # A non-finite share means the question could not be ASKED -- every set is the
    # same size, so size has no variance to explain anything with. Falling through
    # to the final branch would report that as "not size-dominated, the good case",
    # which is a reassurance the data does not support. It changes no number: it
    # only stops a NaN from being read as an all-clear. Screen-level inputs
    # (MAGeCK, BAGEL, drugZ) hit it routinely, because most libraries build every
    # gene with the same number of guides. The study gets this branch too now,
    # since src/audit_screen.py imports this function rather than copying it.
    if not np.isfinite(share):
        out["verdict"] = "UNDETERMINED"
        out["reading"] = (
            "This ranking cannot be audited for size: every set is the same size, "
            "so set size has no variation with which to explain anything.")
        out["what_to_do"] = (
            "This is not an all-clear. Size is ruled out here by construction, but "
            "the other ways a ranking can be carried by how it was measured -- "
            "read depth, guide efficacy, replicate count -- are untested and this "
            "tool does not test them. If your sets do vary in size, check you "
            "passed the right column.")
        out["what_this_is_not"] = (
            "Not a candidate list and not a recommendation. This measures a property "
            "of the ranking, not of any gene or pathway in it.")
        out["method"] = ("VIF = 1 + (m-1)*rho_bar, Wu & Smyth 2012, "
                         "Nucleic Acids Research 40(17):e133, doi:10.1093/nar/gks461")
        return out

    out["reading"] = (
        f"{share:.0%} of the variance in this ranking is predicted by how the "
        f"sets were built, with no reference to what any gene does."
    )
    if share >= CONFOUNDED:
        out["verdict"] = "CONFOUNDED"
        out["what_to_do"] = (
            "Do not read the top of this ranking as biology. Before committing to "
            "any candidate, re-rank with a size-aware statistic -- a competitive "
            "test that accounts for inter-gene correlation (CAMERA and its "
            "relatives), or a permutation null that preserves set size -- and see "
            "which entries survive. The ones that move most are the ones your "
            "current ranking is least able to justify.")
    elif share >= PARTIAL:
        out["verdict"] = "PARTIALLY CONFOUNDED"
        out["what_to_do"] = (
            "Size is a visible but not dominant driver here. Report it alongside "
            "the ranking, and check that your leading entries are not simply your "
            "largest sets.")
    else:
        out["verdict"] = "NOT SIZE-DOMINATED"
        out["what_to_do"] = (
            "Set size does not explain much of this ranking. That is the good "
            "case, and it is worth stating explicitly -- most published set-level "
            "rankings never check.")
    # Does one enormous entry carry the whole verdict?
    #
    # Real case, found by running this on a published screen rather than on a
    # fixture: a pooled library pools every non-targeting guide into one control
    # pseudo-gene, which then has hundreds of guides where every real gene has
    # four. On the full 19,326-gene screen that single row is harmless (R^2
    # 0.0067 with it, 0.0099 without). Take a 130-row slice of the same file and
    # it becomes 0.4137 with and 0.0237 without -- CONFOUNDED, on the strength of
    # one control row. A tool whose entire argument is that rankings get carried
    # by arithmetic cannot itself hand out a verdict carried by one point and say
    # nothing. Nothing is dropped; the dependence is reported.
    extreme = s >= 10.0 * float(np.median(s)) if np.median(s) > 0 else np.zeros(n, bool)
    if extreme.any() and (n - int(extreme.sum())) >= MIN_SETS:
        r2_without = _r2(s[~extreme], y[~extreme])
        out["n_extreme_entries"] = int(extreme.sum())
        out["r2_without_extreme_entries"] = (None if not np.isfinite(r2_without)
                                             else round(r2_without, 4))
        def _band(v):
            if not np.isfinite(v): return "UNDETERMINED"
            return ("CONFOUNDED" if v >= CONFOUNDED
                    else "PARTIALLY CONFOUNDED" if v >= PARTIAL else "NOT SIZE-DOMINATED")
        if _band(r2_without) != out["verdict"]:
            out["verdict_depends_on_extreme_entries"] = True
            k_x = int(extreme.sum())
            out["caution"] = (
                f"This verdict rests on {k_x} "
                f"{'entry' if k_x == 1 else 'entries'} at least 10x "
                f"the median size. Without {'it' if k_x == 1 else 'them'} "
                f"the same check returns "
                f"{_band(r2_without)} (R^2 {out['r2_without_extreme_entries']}). In a "
                "pooled library that entry is usually the non-targeting control "
                "pseudo-gene rather than a set of interest. Nothing has been dropped "
                "-- decide which table you meant to audit, and rerun.")

    out["what_this_is_not"] = (
        "Not a candidate list and not a recommendation. This measures a property "
        "of the ranking, not of any gene or pathway in it.")
    out["method"] = ("VIF = 1 + (m-1)*rho_bar, Wu & Smyth 2012, "
                     "Nucleic Acids Research 40(17):e133, doi:10.1093/nar/gks461")

    # Context, added after the fact and never feeding it: an R^2 is not a judgement
    # until you know what a normal screen looks like. Size-alone is used for the
    # comparison even when a VIF figure exists, because the reference distribution
    # was built size-alone -- comparing a VIF number against it would be a category
    # error dressed as a percentile.
    try:
        from .reference import context
        out.update(context(out["r2_size_alone"]))
    except Exception:
        pass
    return out


def audit_replication(sizes, hits_a, hits_b) -> dict:
    """When two independent screens agree, how much of the agreement is set size?

    The question a biologist actually has when a hit list "replicated": both screens
    are confounded the same way, so agreeing for the same wrong reason looks exactly
    like agreeing for the right one.

    THE ONE PLACE THIS PACKAGE AND THE STUDY DIVERGE. `audit()` is shared -- the
    study imports it from here. This function is not, and it is not a copy either:
    it residualises on log10(size) where src/audit_screen.py residualises on raw
    size, so on the same input the two return different numbers (0.4507 here
    against 0.4934 there; 32% of the agreement against 26%). Neither is wrong,
    but they are not interchangeable and the difference is not rounding.

    They stay apart because each already carries a frozen surface: the study's
    produced evaluation 6's published 26%, this one is what `denali audit --hits-b`
    has always returned. Collapsing them would move a published number after the
    fact. Both are pinned by the research repo's invariant suite instead, so the
    gap cannot widen unnoticed.
    """
    s = np.asarray(sizes, dtype=float)
    a = np.asarray(hits_a, dtype=float)
    b = np.asarray(hits_b, dtype=float)
    ok = np.isfinite(s) & np.isfinite(a) & np.isfinite(b)
    s, a, b = s[ok], a[ok], b[ok]
    if len(s) < MIN_SETS:
        raise ValueError(f"need at least {MIN_SETS} paired sets; got {len(s)}")

    la, lb, ls = np.log10(1 + a), np.log10(1 + b), np.log10(s)

    def _resid(y, x):
        bb = np.polyfit(x, y, 1)
        return y - np.polyval(bb, x)

    raw = _spearman(la, lb)
    net = _spearman(_resid(la, ls), _resid(lb, ls))
    explained = float("nan") if raw == 0 else round(100 * (1 - abs(net) / abs(raw)), 1)

    return {
        "n_sets": int(len(s)),
        "agreement_raw": round(raw, 4),
        "agreement_after_removing_size": round(net, 4),
        "pct_of_agreement_that_is_size": explained,
        "reading": (
            f"{explained:.0f}% of the apparent agreement between these two screens is "
            f"explained by set size. Both are confounded the same way, so agreeing for "
            f"the same wrong reason is indistinguishable from agreeing for the right one."
        ),
        "what_this_is_not": (
            "Not a claim about any individual set, and not a claim that either screen "
            "is wrong. It measures what the replication is worth as evidence."),
    }


def rerank(sizes, hits, names=None, top=20) -> dict:
    """Apply the correction this tool has always only named.

    `audit()` tells you a ranking is size-confounded and then says: re-rank with a
    size-aware statistic and see which entries survive. Until now it did not do that,
    which left the user holding a diagnosis and no treatment.

    The correction is the one the concordance arm already uses -- regress log10(1+hits)
    on set size and rank by the residual, so a set is scored on how far it beats what
    its size alone predicts. A large set with many hits is unremarkable; a small set
    with the same count is not.

    THIS DOES NOT NOMINATE ANYTHING. It reports which entries the ORIGINAL ranking is
    least able to justify -- the ones whose position was carried by size. That is the
    inverse of a candidate list and it is the only direction this tool moves in.
    """
    s = np.asarray(sizes, dtype=float)
    h = np.asarray(hits, dtype=float)
    ok = np.isfinite(s) & np.isfinite(h)
    idx = np.flatnonzero(ok)
    s, h = s[ok], h[ok]
    n = len(s)
    if n < MIN_SETS:
        raise ValueError(f"need at least {MIN_SETS} sets to say anything; got {n}")

    if names is None:
        nm = np.array([f"set {i}" for i in idx])
    else:
        nm = np.asarray(names, dtype=object)[ok]

    y = np.log10(1.0 + h)
    constant_size = bool(np.std(s) == 0)
    if constant_size:
        # Nothing can move: the correction subtracts the same number from every
        # entry, so the corrected order is the original order. Reporting that as
        # "your ranking survived the correction" would be a pass it never sat.
        resid = y - y.mean()
    else:
        b = np.polyfit(s, y, 1)
        resid = y - np.polyval(b, s)

    # rank 1 = top. Original ranking is by raw hits, corrected by size-adjusted residual.
    orig = (-h).argsort(kind="stable").argsort(kind="stable") + 1
    corr = (-resid).argsort(kind="stable").argsort(kind="stable") + 1
    move = orig - corr                       # negative = fell once size was removed

    k = min(int(top), n)
    was_top = orig <= k
    still_top = corr <= k
    survived = int((was_top & still_top).sum())
    dropped = np.flatnonzero(was_top & ~still_top)
    order = dropped[np.argsort(corr[dropped])] if dropped.size else dropped

    rows = [{
        "name": str(nm[i]),
        "size": int(s[i]),
        "hits": int(h[i]),
        "rank_original": int(orig[i]),
        "rank_size_aware": int(corr[i]),
        "moved": int(move[i]),
    } for i in order]

    reading = (
        f"Of your top {k}, {survived} hold their place once set size is accounted "
        f"for and {k - survived} do not. The ones that move are the entries your "
        f"current ranking is least able to justify.")
    if constant_size:
        reading = (
            "Every set here is the same size, so the size correction cannot move "
            "anything and nothing below is evidence either way. This is not a "
            "ranking that survived the correction; it is one the correction could "
            "not be applied to.")

    return {
        "n_sets": n,
        "top_n": k,
        "survived_top_n": survived,
        "left_top_n": int(k - survived),
        "size_is_constant": constant_size,
        "biggest_fall": int(max((-move[dropped]).max(), 0)) if dropped.size else 0,
        "left_the_top": rows,
        "correction": "log10(1+hits) regressed on set size; ranked by residual",
        "reading": reading,
        "what_this_is_not": (
            "Not a candidate list. This says which entries were carried by size, not "
            "which to chase. Nothing here is a recommendation to validate anything."),
    }
