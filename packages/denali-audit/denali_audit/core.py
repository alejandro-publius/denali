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

from . import nulls as _nulls

MIN_SETS = 8

CONFOUNDED = 0.40
PARTIAL = 0.20

# The verdict vocabulary, in one place. Null-relative since 2026-08-17: a band on
# the raw R^2 is what misled, because for a counting mapping the no-biology value
# is large. None of these three is a pass -- see each what_to_do.
VERDICT_ABOVE = "MORE SIZE-CARRIED THAN ITS OWN NULL"
VERDICT_INSIDE = "INDISTINGUISHABLE FROM ITS OWN NULL"
VERDICT_BELOW = "LESS SIZE-CARRIED THAN ITS OWN NULL"
VERDICT_UNDETERMINED = "UNDETERMINED"
VERDICTS = (VERDICT_ABOVE, VERDICT_INSIDE, VERDICT_BELOW, VERDICT_UNDETERMINED)


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
        # WHY the R^2 is undefined decides what to tell the user, and there are
        # two different reasons. Constant SIZE means the predictor has no
        # variance; constant HITS (every set returned the same count -- most
        # often zero, a screen where nothing reached significance) means the
        # OUTCOME has none. Both land here, and until 2026-08-16 both were
        # reported as "every set is the same size", which is a false statement
        # about the user's data whenever it was the hits that were constant.
        # Found by dropping an all-zero-hits table into the page runner.
        out["verdict"] = "UNDETERMINED"
        constant_size = bool(np.std(s) == 0)
        if constant_size:
            out["reading"] = (
                "This ranking cannot be audited for size: every set is the same size, "
                "so set size has no variation with which to explain anything.")
            out["what_to_do"] = (
                "This is not an all-clear. Size is ruled out here by construction, but "
                "the other ways a ranking can be carried by how it was measured -- "
                "read depth, guide efficacy, replicate count -- are untested and this "
                "tool does not test them. If your sets do vary in size, check you "
                "passed the right column.")
        else:
            n_zero = int((h == 0).sum())
            out["reading"] = (
                "This ranking cannot be audited for size: every set returned the same "
                "number of hits" + (" (zero)" if n_zero == n else "") + ", so there is "
                "no variation in the ranking for set size or anything else to explain.")
            out["what_to_do"] = (
                "This is not an all-clear and it is not a ranking. Nothing here "
                "distinguishes any set from any other, so there is no top to audit. "
                "If you expected hits, check the significance threshold and the "
                "column you passed; if the screen genuinely returned nothing, that "
                "is the result and no re-ranking will change it.")
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

    # THE VERDICT IS RELATIVE TO THIS MAPPING'S OWN NULL, NOT TO A BAND ON THE RAW
    # R^2. Until 2026-08-17 it was a band -- CONFOUNDED at 0.40, PARTIALLY at 0.20 --
    # and those thresholds were calibrated on THIS project's screen, whose hits count
    # perturbations. Nine of the ten formats adapters.detect() accepts instead count
    # hits over the set's own members, where a large R^2 is arithmetic and the
    # no-biology value is nowhere near zero. On seven real published screens
    # (results/external_nulls/) only two clear their own null, and one measured at
    # 0.36 against a null of 0.72 -- less size-carried than chance -- was being told
    # to check whether its leading entries were simply its largest sets.
    #
    # The null is a SIZE-ALONE null, so it is compared against r2_size_alone rather
    # than against the VIF share, for the same reason the corpus percentile is:
    # comparing a VIF number against a size-alone reference is a category error.
    out["mapping"] = _nulls.structure(s, h)
    null = _nulls.no_biology_null(s, h, _r2)
    pos = _nulls.position(out["r2_size_alone"], null)
    if null is not None:
        out["no_biology_null"] = {**null, "position": pos}

    if pos == "ABOVE":
        out["verdict"] = "MORE SIZE-CARRIED THAN ITS OWN NULL"
        out["what_to_do"] = (
            "This ranking is more predicted by set size than a version of itself "
            "with no biology in it. Before committing to any candidate, re-rank "
            "with a size-aware statistic -- a competitive test that accounts for "
            "inter-gene correlation (CAMERA and its relatives), or a permutation "
            "null that preserves set size -- and see which entries survive. The "
            "ones that move most are the ones your current ranking is least able "
            "to justify.")
    elif pos == "INSIDE":
        out["verdict"] = "INDISTINGUISHABLE FROM ITS OWN NULL"
        out["what_to_do"] = (
            "By this measure you cannot tell this ranking apart from one with no "
            "biology in it at all. That is not a clean result and it is not a "
            "problem you can fix by re-ranking: the size relationship here is what "
            "the arithmetic of the mapping produces on its own. It does not mean "
            "your screen found nothing -- it means THIS measure cannot separate "
            "what you found from how the sets were built, and a different line of "
            "evidence has to do that work.")
    elif pos == "BELOW":
        out["verdict"] = "LESS SIZE-CARRIED THAN ITS OWN NULL"
        out["what_to_do"] = (
            "Set size predicts this ranking LESS than it would with no biology in "
            "it at all. This is not a clean bill of health and nothing here is a "
            "pass: it means this particular measure does not flag this ranking, "
            "and this measure only ever asked about set size. Read depth, guide "
            "efficacy, replicate count and every other way a ranking can be "
            "carried by how it was measured are untested, and this tool does not "
            "test them.")
    else:
        out["verdict"] = "UNDETERMINED"
        out["what_to_do"] = (
            "The no-biology null for this mapping could not be computed, so the "
            "size share above cannot be read as high or low. It is a descriptive "
            "number with nothing to compare it against, and it is not evidence "
            "either way.")
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
        # The comparison has to be made in the SAME vocabulary as the verdict, and
        # against the null of the TRIMMED data -- dropping the extreme entries
        # changes the size distribution, so it changes the null too. Comparing the
        # old raw-R^2 bands against the new null-relative verdict would make this
        # caution fire on every screen that has an extreme entry, which is a
        # different defect from the one it was written to catch.
        def _verdict_without(v):
            if not np.isfinite(v):
                return "UNDETERMINED"
            nl = _nulls.no_biology_null(s[~extreme], h[~extreme], _r2)
            p = _nulls.position(v, nl)
            return {"ABOVE": "MORE SIZE-CARRIED THAN ITS OWN NULL",
                    "INSIDE": "INDISTINGUISHABLE FROM ITS OWN NULL",
                    "BELOW": "LESS SIZE-CARRIED THAN ITS OWN NULL"}.get(p, "UNDETERMINED")
        # Fire when the verdict moves OR when the raw R^2 moves by more than the
        # null's own width. The second clause is not a magic number: it is the
        # uncertainty of the null itself, so "this point moved the answer by more
        # than the answer's own error bar" is self-calibrating.
        #
        # It is needed because the null-relative verdict is ROBUST to exactly the
        # artefact the old band was fooled by. On the real MAGeCK slice, one control
        # pseudo-gene moves the observed R^2 from 0.4137 to 0.0237 -- and moves the
        # null from 0.4897 to 0.1026 with it, so the verdict is BELOW either way.
        # That robustness is a genuine improvement and it must not become silence:
        # a tool arguing that rankings get carried by arithmetic still owes the user
        # the fact that one row carried its headline number.
        _vw = _verdict_without(r2_without)
        _band_w = (out["no_biology_null"]["ci95"][1] - out["no_biology_null"]["ci95"][0]
                   if "no_biology_null" in out else 0.0)
        _moved = (np.isfinite(r2_without)
                  and abs(out["r2_size_alone"] - r2_without) > max(_band_w, 1e-9))
        if _vw != out["verdict"] or _moved:
            out["verdict_depends_on_extreme_entries"] = (_vw != out["verdict"])
            out["r2_depends_on_extreme_entries"] = bool(_moved)
            k_x = int(extreme.sum())
            out["caution"] = (
                f"This verdict rests on {k_x} "
                f"{'entry' if k_x == 1 else 'entries'} at least 10x "
                f"the median size. Without {'it' if k_x == 1 else 'them'} "
                f"the same check returns "
                f"{_vw} (R^2 {out['r2_without_extreme_entries']}). In a "
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


BASELINE_METRICS = {
    "spearman": "higher",
    "pearson": "higher",
    "r2": "higher",
    "mae": "lower",
    "rmse": "lower",
    "top_k_overlap": "higher",
}

# Metrics that read only the ORDER of the predictions. They get a different
# size-only baseline from the ones that read the values, and the reason is not
# cosmetic -- see `_size_only_ranking`.
RANK_METRICS = frozenset({"spearman", "top_k_overlap"})


def _r2_of_predictions(pred, y) -> float:
    """R^2 of a prediction vector against truth. NOT `_r2`, which fits a line first.

    The difference matters and is easy to miss: `_r2(x, y)` reports how well the
    BEST line through x predicts y, which is scale-free and cannot be negative.
    This reports how well `pred` itself predicts y, which is what a model is
    scored on, and which goes negative when the predictions are worse than the
    mean. Scoring a caller's model with the first would silently rescale their
    predictions and flatter them.
    """
    ss_res = float(((y - pred) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    return float("nan") if ss_tot == 0 else 1.0 - ss_res / ss_tot


def _pearson(x, y) -> float:
    xs, ys = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if np.std(xs) == 0 or np.std(ys) == 0:
        return float("nan")
    return float(np.corrcoef(xs, ys)[0, 1])


def _top_k_overlap(pred, y, k) -> float:
    n = len(y)
    k = max(1, min(int(k), n))
    a = set((-np.asarray(pred, dtype=float)).argsort(kind="stable")[:k].tolist())
    b = set((-np.asarray(y, dtype=float)).argsort(kind="stable")[:k].tolist())
    return len(a & b) / float(k)


def _score(metric: str, pred, y, k: int) -> float:
    if metric == "spearman":
        return _spearman(pred, y)
    if metric == "pearson":
        return _pearson(pred, y)
    if metric == "r2":
        return _r2_of_predictions(pred, y)
    if metric == "mae":
        return float(np.abs(y - pred).mean())
    if metric == "rmse":
        return float(np.sqrt(((y - pred) ** 2).mean()))
    if metric == "top_k_overlap":
        return _top_k_overlap(pred, y, k)
    raise ValueError(f"unknown metric {metric!r}")


def _loo_line(x, t):
    """Leave-one-out predictions from a straight-line fit of t on x.

    A baseline fitted on the same rows it is then scored against has seen the
    answers, which makes it look better than it is and makes anything measured
    against it look worse. The closed form is exact and costs one pass:
    t_i^(-i) = t_i - e_i / (1 - h_i), with h_i the leverage of row i.

    Returns (predictions, exact). `exact` is False when one row carries
    essentially the whole fit, so dropping it leaves the line undefined and the
    in-sample fit is returned instead -- reported, never hidden, because such a
    baseline saw the rows it is scored on and is therefore flattered.
    """
    n = len(x)
    fit = np.polyval(np.polyfit(x, t, 1), x)
    sxx = float(((x - x.mean()) ** 2).sum())
    denom = 1.0 - (1.0 / n + (x - x.mean()) ** 2 / sxx)
    if not bool((denom > 1e-9).all()):
        return fit, False
    return t - (t - fit) / denom, True


def _size_only_ranking(s, y):
    """The size-only baseline for a metric that reads only the ORDER: set size.

    WHY THIS IS NOT THE LEAVE-ONE-OUT FIT. A rank metric cannot see the values,
    so fitting anything is wasted -- and worse than wasted. The leave-one-out
    correction moves each prediction toward its own row's truth and back again,
    which perturbs the ORDER slightly and costs the baseline rank accuracy it
    should not be losing. Caught by the MCP fixture: a "model" that was set size
    times thirty came out ahead of a size-only baseline on Spearman, 0.9091 to
    0.8252, which is the tool crediting a model that knows nothing.

    So for rank metrics the baseline is set size itself, unfitted. Nothing is
    estimated from the data except one bit -- whether bigger sets rank higher or
    lower -- taken from the sign of the size/truth slope and stated below. This
    is also the null that EGAD has shipped as node-degree AUROC since 2017
    (doi:10.1093/bioinformatics/btw695); the method here is not novel and this
    module does not pretend otherwise.
    """
    if np.std(s) == 0:
        return None, ("set size is constant here, so it induces no ranking at "
                      "all and there is no size-only order to compare against")
    t = np.log10(1.0 + y) if bool((y >= 0).all()) else np.asarray(y, dtype=float)
    slope = float(np.polyfit(s, t, 1)[0])
    sign = 1.0 if slope >= 0 else -1.0
    return s * sign, (
        "set size itself, ranked " + ("largest first" if sign > 0 else
                                      "smallest first")
        + " -- no fit and no fitted parameters, only that one direction, taken "
          "from the sign of the size/truth slope")


def _size_only_predictions(s, y):
    """What set size alone predicts for each set, WITHOUT having seen that set.

    WHY THERE ARE TWO CANDIDATES AND NOT ONE. The first version of this fitted
    log10(1+y) and back-transformed, because that is the scale the rest of this
    module works on. On a truth column that is close to linear in size, that
    baseline is badly specified and scores far worse than it should: a "model"
    that was literally size plus noise beat it 3.79 to 6.49 on MAE, purely
    because of the transform. A weak baseline is not a neutral error here. It
    hands out "your model beats size alone" verdicts that a better-specified
    size-only model would have taken away, which is the exact failure this
    function exists to prevent.

    So the baseline is the better of a stated two-member family -- the log fit
    back-transformed, and a raw-scale fit -- each computed leave-one-out. The
    choice is made on leave-one-out squared error against the truth, a FIXED
    criterion named here in advance. It is deliberately not the caller's own
    metric: selecting the baseline on the same metric the caller is judged by
    would let this tool tune how bad anyone looks.

    Both members are monotone in size up to the leave-one-out correction, so
    for rank metrics the choice barely moves anything; it is the value metrics
    (mae, rmse, r2, pearson) that need it.
    """
    n = len(s)
    if np.std(s) == 0:
        # Size has no variance, so "predict from size" degenerates to "predict
        # the mean". Still leave-one-out, still a real baseline, and reported
        # as contributing nothing FROM SIZE rather than quietly passed off as
        # a size-only predictor that worked.
        return (y.sum() - y) / (n - 1.0), "mean-only (set size is constant)"

    cands = []
    raw, raw_ok = _loo_line(s, np.asarray(y, dtype=float))
    cands.append((raw, "a raw-scale least-squares fit of truth on size", raw_ok))
    if bool((y >= 0).all()):
        lg, lg_ok = _loo_line(s, np.log10(1.0 + y))
        # Numerical guard only: an extrapolated leave-one-out value on the log
        # scale can overflow the back-transform on a pathological table.
        cands.append((10.0 ** np.clip(lg, -12.0, 12.0) - 1.0,
                      "a least-squares fit of log10(1+truth) on size, "
                      "back-transformed", lg_ok))

    sse = [float(((y - p) ** 2).sum()) if np.isfinite(p).all() else float("inf")
           for p, _, _ in cands]
    best = int(np.argmin(sse))
    pred, label, exact = cands[best]
    how = label + (", leave-one-out" if exact else
                   ", IN-SAMPLE (one row has leverage ~1, so leave-one-out is "
                   "undefined and this baseline is flattered)")
    if len(cands) > 1:
        how += (". Chosen as the better of two stated size-only fits on "
                "leave-one-out squared error -- a fixed criterion, not the "
                "metric you are scored by")
    return pred, how


def baseline(sizes, hits, predicted, metric=None, k=10) -> dict:
    """How much of your model's apparent performance is recoverable from set size?

    sizes : members per set   hits : the truth your model is scored against
    predicted : your model's score per set, same order
    metric : how YOU evaluate. Named, never guessed -- see BASELINE_METRICS.

    Every team that reports "our model beats baseline" computes its own
    baseline, differently, and nobody can check it. This computes one: the
    score a predictor that sees ONLY how big each set is achieves on the
    caller's own evaluation, next to the caller's own score.

    It is a measurement, not a verdict. A model can be worth having and not
    beat this, and beating it says nothing about whether any individual
    prediction is right.
    """
    s = np.asarray(sizes, dtype=float)
    y = np.asarray(hits, dtype=float)
    p = np.asarray(predicted, dtype=float)
    if not (len(s) == len(y) == len(p)):
        raise ValueError(
            f"sizes, hits and predicted must be the same length; got "
            f"{len(s)}, {len(y)}, {len(p)}. This tool will not align them for you.")
    ok = np.isfinite(s) & np.isfinite(y) & np.isfinite(p)
    s, y, p = s[ok], y[ok], p[ok]
    n = len(s)
    if n < MIN_SETS:
        raise ValueError(f"need at least {MIN_SETS} sets to say anything; got {n}")

    # The metric is asked for, never inferred. Guessing it would make every
    # number below a different quantity from the one the caller reports, which
    # is the failure this whole subcommand exists to stop.
    known = ", ".join(sorted(BASELINE_METRICS))
    if metric is None:
        raise ValueError(
            "name the metric you evaluate with -- this tool will not guess it, "
            f"because a baseline scored with a different metric than yours is "
            f"not a comparison. Recognised: {known}. If yours is not one of "
            "these, ask for 'none' and score the returned baseline predictions "
            "yourself.")
    metric = str(metric).strip().lower()
    if metric not in BASELINE_METRICS and metric != "none":
        raise ValueError(
            f"unrecognised metric {metric!r}. This tool will not approximate it "
            f"with something adjacent. Recognised: {known}. For anything else "
            "ask for 'none': the size-only baseline's per-set predictions come "
            "back and you score them with your own metric, on your own terms.")

    # The FORM of the baseline follows from what kind of metric it will be
    # scored with, which is a property of the metric and known before any score
    # is computed. It is deliberately not chosen by which form scores better:
    # picking the baseline on the caller's own metric would let this tool tune
    # how bad anyone looks.
    value_pred, value_how = _size_only_predictions(s, y)
    if metric in RANK_METRICS:
        base_pred, how = _size_only_ranking(s, y)
    else:
        base_pred, how = value_pred, value_how

    out = {
        "n_sets": int(n),
        "metric": metric,
        "baseline_predictions": [round(float(v), 6) for v in value_pred],
        "how_the_baseline_was_built":
            "one predictor, and it is set size: " + how,
        "what_this_is_not": (
            "Not a judgement of your model, not a leaderboard entry, and not a "
            "claim that any model is bad. It measures what set construction "
            "alone recovers on YOUR evaluation, so that 'we beat baseline' is a "
            "number someone else can reproduce."),
    }
    if np.std(s) == 0:
        out["size_is_constant"] = True

    if metric == "none":
        out["reading"] = (
            f"No metric was named, so nothing is scored. `baseline_predictions` "
            f"holds what a size-only predictor predicts for each of your {n} "
            f"sets, in your input's order, leave-one-out. Score those with your "
            f"own metric and compare against your model's score on the same "
            f"rows. If your metric reads only the ORDER of predictions, use set "
            f"size itself as the baseline instead -- no fit is needed and none "
            f"should be used.")
        return out

    if base_pred is None:
        # Constant size and a rank metric: there is no size-only order at all.
        out["reading"] = (
            "Every set here is the same size, so set size induces no ranking "
            f"and there is nothing for your {metric} to be compared against. "
            "This is not a result in your favour -- it is a comparison that "
            "cannot be made.")
        out["your_score"] = None
        out["size_only_score"] = None
        return out

    direction = BASELINE_METRICS[metric]
    yours = _score(metric, p, y, k)
    base = _score(metric, base_pred, y, k)
    if metric == "top_k_overlap":
        out["k"] = int(max(1, min(int(k), n)))

    out["your_score"] = None if not np.isfinite(yours) else round(float(yours), 4)
    out["size_only_score"] = None if not np.isfinite(base) else round(float(base), 4)
    out["higher_is_better"] = direction == "higher"

    if not (np.isfinite(yours) and np.isfinite(base)):
        out["reading"] = (
            f"The {metric} could not be computed on these columns -- one of them "
            f"has no variation, or the two scores are not both defined. Nothing "
            f"is being claimed either way.")
        return out

    gap = (yours - base) if direction == "higher" else (base - yours)
    out["delta"] = round(float(gap), 4)
    out["beats_size_alone"] = bool(gap > 0)
    if gap > 0:
        tail = f"Your model beats size alone by {gap:.4f}."
    elif gap == 0:
        tail = "Your model exactly ties size alone."
    else:
        tail = (f"Your model does not beat size alone: size alone is ahead by "
                f"{abs(gap):.4f}.")
    out["reading"] = (
        f"On {metric}, your predictions score {out['your_score']} and a "
        f"predictor that sees only how big each set is scores "
        f"{out['size_only_score']}. " + tail)

    # The brief's question -- what share of the apparent performance needs no
    # model -- is a ratio, and a ratio is only meaningful where the metric runs
    # in a direction that makes one. Reported where it is, withheld with a
    # reason where it is not, rather than printed as a number that reads
    # convincing and means nothing.
    if direction == "higher" and yours > 0 and base >= 0:
        # Deliberately NOT capped at 1. A baseline that outscores the model
        # gives a share above 1, and that is the reading -- clamping it to
        # "100% recovered" would hide the case worth knowing about.
        out["share_of_your_score_the_baseline_recovers"] = round(float(base / yours), 4)
    else:
        out["share_of_your_score_the_baseline_recovers"] = None
        out["share_withheld_because"] = (
            "a share is only interpretable where a higher score is better and "
            f"your score is above zero; {metric} here is neither, so the two "
            "scores are reported side by side instead.")

    out["your_predictions_may_be_in_sample"] = (
        "The size-only baseline never saw the row it predicts. Your model's "
        "predictions were supplied, so this tool cannot tell whether they were "
        "produced the same way. If they were fitted on these same sets, the "
        "comparison favours them.")

    # Scope limit 6, carried at the point it applies. Where hits are counted
    # over the set's own members, size predicting hits is partly arithmetic
    # rather than a confound -- so a strong baseline here is expected and is
    # not by itself evidence that anyone's ranking is carried by size.
    if bool((y <= s).all()):
        out["boundary_condition"] = (
            "Every set's truth value is at most its size, so the two are "
            "counted over the same members. Regressing a count on the number of "
            "trials that produced it recovers the trial count, and a strong "
            "size-only baseline there is arithmetic before it is a confound. "
            "Read the gap between the two scores, not the baseline's absolute "
            "level. See scope limit 6.")

    # Context, not an input to anything above: how size-carried the truth column
    # is on its own terms. A model beating size alone on a ranking size barely
    # explains is a different achievement from beating it on one size dominates.
    try:
        a = audit(s, y)
        out["truth_ranking"] = {"verdict": a.get("verdict"),
                                "r2_size_alone": a.get("r2_size_alone")}
    except ValueError:
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
