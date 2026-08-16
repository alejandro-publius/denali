"""Run denali's audit on SOMEBODY ELSE'S screen.

The finding in this repository is about one dataset. The confound is not. Any
analysis that scores gene sets against a screen inherits it: larger sets return
more hits because a set-level statistic is variance-inflated by size and by
inter-gene correlation, VIF = 1 + (m-1)*rho_bar (Wu & Smyth 2012,
doi:10.1093/nar/gks461). That is arithmetic, not biology, and it does not care
whose screen it is.

So this takes a table any gene-set analysis already produces -- set name, set
size, number of hits -- and reports how much of the ranking is explained by size
alone before the user commits a year to the top of it.

    python -m src.audit_screen mine.csv --set set --size n_genes --hits n_sig
    python -m src.audit_screen --self-test

Optional: a --corr column of mean inter-gene correlation per set upgrades the
report from size-only to the full variance-inflation factor.

WHAT IT WILL NOT DO. It does not rank the sets, name a candidate, or tell anyone
what to chase. Guide-pair concordance in our own data is -0.019, and a tool that
turned a confound estimate into a recommendation would be making exactly the
error it exists to detect.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


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
    if n < 8:
        raise ValueError(f"need at least 8 sets to say anything; got {n}")

    # log1p(hits) is the scale a hit count actually lives on: the difference
    # between 0 and 10 hits matters more than between 500 and 510.
    y = np.log10(1.0 + h)

    def r2(x, y):
        x = np.asarray(x, dtype=float)
        if np.std(x) == 0:
            return float("nan")
        b = np.polyfit(x, y, 1)
        pred = np.polyval(b, x)
        ss_res = float(((y - pred) ** 2).sum())
        ss_tot = float(((y - y.mean()) ** 2).sum())
        return float("nan") if ss_tot == 0 else 1 - ss_res / ss_tot

    out = {
        "n_sets": int(n),
        "size_range": [int(s.min()), int(s.max())],
        "r2_size_alone": round(r2(s, y), 4),
        "spearman_size_vs_hits": round(float(
            pd.Series(s).corr(pd.Series(y), method="spearman")), 4),
        "sets_with_zero_hits": int((h == 0).sum()),
    }

    if corr is not None:
        c = np.asarray(corr, dtype=float)[ok]
        if np.isfinite(c).all():
            vif = 1.0 + (s - 1.0) * c
            out["vif_range"] = [round(float(vif.min()), 2), round(float(vif.max()), 2)]
            out["r2_vif"] = round(r2(np.log10(vif), y), 4)

    share = out.get("r2_vif", out["r2_size_alone"])
    out["share_explained_without_biology"] = share
    out["reading"] = (
        f"{share:.0%} of the variance in this ranking is predicted by how the "
        f"sets were built, with no reference to what any gene does."
    )
    if share >= 0.40:
        out["verdict"] = "CONFOUNDED"
        out["what_to_do"] = (
            "Do not read the top of this ranking as biology. Before committing to "
            "any candidate, re-rank with a size-aware statistic -- a competitive "
            "test that accounts for inter-gene correlation (CAMERA and its "
            "relatives), or a permutation null that preserves set size -- and see "
            "which entries survive. The ones that move most are the ones your "
            "current ranking is least able to justify.")
    elif share >= 0.20:
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
    out["what_this_is_not"] = (
        "Not a candidate list and not a recommendation. This measures a property "
        "of the ranking, not of any gene or pathway in it.")
    out["method"] = ("VIF = 1 + (m-1)*rho_bar, Wu & Smyth 2012, "
                     "Nucleic Acids Research 40(17):e133, doi:10.1093/nar/gks461")
    return out


def audit_replication(sizes, hits_a, hits_b) -> dict:
    """Two screens of the same sets agreed. How much of that is set size?

    "It replicated in a second system" is the strongest evidence most hit lists
    ever get. But if both screens are confounded the same way, agreeing for the
    same wrong reason looks exactly like agreeing for the right one. This
    separates the two.

    sizes : genes measured per set (shared)
    hits_a, hits_b : significant results per set, from two independent screens
    """
    import statsmodels.api as sm
    from scipy.stats import spearmanr

    s = np.asarray(sizes, dtype=float)
    a = np.log10(1.0 + np.asarray(hits_a, dtype=float))
    b = np.log10(1.0 + np.asarray(hits_b, dtype=float))
    ok = np.isfinite(s) & np.isfinite(a) & np.isfinite(b)
    s, a, b = s[ok], a[ok], b[ok]
    n = len(s)
    if n < 8:
        raise ValueError(f"need at least 8 paired sets; got {n}")

    rho, p_raw = spearmanr(a, b)
    X = sm.add_constant(s)
    res_a = sm.OLS(a, X).fit().resid
    res_b = sm.OLS(b, X).fit().resid
    rho_p, p_par = spearmanr(res_a, res_b)

    lost = float(rho - rho_p)
    share = abs(lost / rho) if rho else float("nan")

    k = min(10, max(3, n // 5))
    top = lambda v: set(np.argsort(v)[-k:])
    out = {
        "n_paired_sets": int(n),
        "raw_agreement_spearman": round(float(rho), 4),
        "raw_p": float(f"{p_raw:.4g}"),
        "agreement_after_removing_size": round(float(rho_p), 4),
        "p_after_removing_size": float(f"{p_par:.4g}"),
        "agreement_explained_by_size": round(lost, 4),
        "share_of_agreement_that_is_size": round(float(share), 4),
        f"top_{k}_overlap_observed": round(len(top(a) & top(b)) / k, 3),
        f"top_{k}_overlap_from_SIZE_ALONE": round(len(top(s) & top(b)) / k, 3),
        f"top_{k}_overlap_by_chance": round(k / n, 3),
    }
    out["reading"] = (
        f"Raw agreement between the two screens is rho {rho:+.3f}. Removing set "
        f"size from both drops it to {rho_p:+.3f}, so {share:.0%} of the apparent "
        f"replication is carried by how the sets were built rather than by the "
        f"biology replicating.")
    if share >= 0.25:
        out["verdict"] = "REPLICATION PARTLY ARTIFACTUAL"
        out["what_to_do"] = (
            "Do not treat agreement between these two screens as independent "
            "confirmation. Both are confounded the same way, so a set can agree "
            "for the same wrong reason in both. Re-rank each screen with a "
            "size-aware statistic first, then ask whether the agreement survives.")
    else:
        out["verdict"] = "REPLICATION MOSTLY SURVIVES SIZE"
        out["what_to_do"] = (
            "Most of the agreement is not explained by set size. That is the good "
            "case and it is worth stating explicitly, because most replication "
            "claims are never checked this way.")
    out["what_this_is_not"] = (
        "Not a candidate list. This measures a property of the agreement between "
        "two rankings, not of any set in them.")
    return out


def self_test() -> int:
    """Run the audit on denali's own frozen screen and check the known answer."""
    S = pd.read_csv("results/frozen/program_summary.csv")
    got = audit(S.n_present, S.n_hits_q05, S.coherence)
    expect = 0.4649                      # results/sensitivity/stripped_model.json
    ok = abs(got["r2_size_alone"] - expect) < 5e-3
    print(json.dumps(got, indent=2))
    print(f"\nself-test: size-alone R2 {got['r2_size_alone']} vs frozen {expect} "
          f"-> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", nargs="?", help="your gene-set results table")
    ap.add_argument("--set", default="set", help="column of set names")
    ap.add_argument("--size", default="size", help="column of genes measured per set")
    ap.add_argument("--hits", default="hits", help="column of significant results")
    ap.add_argument("--corr", default=None, help="optional: mean inter-gene correlation")
    ap.add_argument("--hits-b", default=None,
                    help="second screen's hit column, to audit a REPLICATION claim")
    ap.add_argument("--self-test", action="store_true",
                    help="run against denali's own frozen screen")
    a = ap.parse_args()

    if a.self_test:
        return self_test()
    if not a.csv:
        ap.error("give a CSV, or --self-test")

    df = pd.read_csv(a.csv)
    missing = [c for c in (a.set, a.size, a.hits) if c not in df.columns]
    if missing:
        print(f"missing column(s) {missing}. Found: {list(df.columns)}", file=sys.stderr)
        return 2

    if a.hits_b:
        if a.hits_b not in df.columns:
            print(f"missing column {a.hits_b!r}. Found: {list(df.columns)}",
                  file=sys.stderr)
            return 2
        rep = audit_replication(df[a.size], df[a.hits], df[a.hits_b])
        rep["source"] = str(Path(a.csv).name)
        print(json.dumps(rep, indent=2))
        print(f"\n{rep['verdict']}: {rep['reading']}\n\n{rep['what_to_do']}")
        return 0

    res = audit(df[a.size], df[a.hits], df[a.corr] if a.corr else None)
    res["source"] = str(Path(a.csv).name)
    print(json.dumps(res, indent=2))
    print(f"\n{res['verdict']}: {res['reading']}\n\n{res['what_to_do']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
