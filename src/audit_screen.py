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

WHERE THE ARITHMETIC LIVES. `audit()` is imported from `denali_audit.core`, the
packaged tool in `packages/denali-audit/`. It used to be a second copy of the
same forty lines here. The two copies agreed on the day they were written and
nothing enforced that they would keep agreeing -- the anti-drift test checked the
PACKAGE against the published 0.4649 and never checked the package against this
file. Importing removes the second copy, so the divergence has nowhere to happen,
and it means the study runs on its own product rather than on a private fork of
it. If the packaged maths ever moves, every number in `audits/external/` and the
`--self-test` below move with it and the invariant suite says so.

NOT TO BE CONFUSED WITH the second implementation in `results/independent/`.
`src/independent_recompute.py` is DELIBERATELY a separate implementation of the
headline statistic, written from the method section without reading the original,
using different libraries at every step. It exists precisely to be different --
agreement between it and the frozen path is evidence. The duplication removed
here was the other kind: two copies of the same code with nothing checking them
against each other, where agreement was evidence of nothing.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# src/__init__.py puts the vendored packages/denali-audit on the path, so this
# resolves to the in-repo copy with nothing installed.
from denali_audit.core import audit                             # noqa: E402

__all__ = ["audit", "audit_replication", "self_test", "main"]


def audit_replication(sizes, hits_a, hits_b) -> dict:
    """Two screens of the same sets agreed. How much of that is set size?

    "It replicated in a second system" is the strongest evidence most hit lists
    ever get. But if both screens are confounded the same way, agreeing for the
    same wrong reason looks exactly like agreeing for the right one. This
    separates the two.

    sizes : genes measured per set (shared)
    hits_a, hits_b : significant results per set, from two independent screens

    THIS ONE IS NOT IMPORTED FROM THE PACKAGE, and that is deliberate. Unlike
    `audit()`, the package's `audit_replication()` is not a copy of this function
    -- it is a leaner one that residualises on log10(size) where this residualises
    on raw size, and the two therefore return DIFFERENT NUMBERS on the same input:
    agreement-after-removing-size 0.4934 here against 0.4507 there, 26% of the
    agreement against 32%. Neither is wrong; they answer slightly different
    questions and they were written months apart for different callers.

    They are kept apart because each is load-bearing for a surface that is already
    frozen. This one produced evaluation 6's published 26% and feeds
    `src/offtarget_audit.py`; the packaged one is what `denali audit --hits-b`
    has always returned to users. Unifying them would silently move a published
    number, and the analysis is closed. So both are pinned instead: the invariant
    suite asserts both values on the frozen paired data, which turns a difference
    that nothing was watching into one that cannot move without failing the build.
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
