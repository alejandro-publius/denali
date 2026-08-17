"""denali — the check you run on a hit list before you spend a year on it."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from . import __version__
from .adapters import SUPPORTED, describe_failure, detect
from .core import BASELINE_METRICS, audit, audit_replication, baseline, rerank


def _read(path: str) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        sys.exit(f"no such file: {path}")
    sep = "\t" if p.suffix.lower() in (".tsv", ".tab", ".txt") else None
    return pd.read_csv(p, sep=sep, engine="python")


def _resolve(df, a):
    """Explicit column names win; otherwise sniff the format."""
    if a.set and a.size and a.hits:
        from .adapters import Mapping
        return Mapping("manual", a.set, df[a.size], df[a.hits])
    m = detect(df)
    if m is None:
        sys.exit(describe_failure(df))
    return m


def _emit(result, as_json: bool, header: str = "") -> None:
    if as_json:
        print(json.dumps(result, indent=2))
        return
    if header:
        print(header)
    verdict = result.get("verdict")
    if verdict:
        print(f"\n  {verdict}: {result['reading']}\n")
        print(f"  {result['what_to_do']}\n")
        print(f"  sets {result['n_sets']}   size range "
              f"{result['size_range'][0]}-{result['size_range'][1]}   "
              f"R2 size-alone {result['r2_size_alone']}")
        if "r2_vif" in result:
            print(f"  with inter-gene correlation (full VIF): R2 {result['r2_vif']}")
        if result.get("sets_with_zero_hits"):
            print(f"  {result['sets_with_zero_hits']} sets returned nothing")
        if result.get("caution"):
            print(f"\n  ⚠ ONE ENTRY IS CARRYING THIS\n  {result['caution']}")
        if "corpus_percentile" in result:
            print(f"\n  AGAINST THE FIELD\n  {result['corpus_reading']}")
            print(f"  {result['corpus_caveat']}")
    else:
        print(f"\n  {result['reading']}\n")
        print(f"  agreement {result['agreement_raw']} -> "
              f"{result['agreement_after_removing_size']} after removing size "
              f"({result['n_sets']} paired sets)")
    print(f"\n  {result['what_this_is_not']}")


def cmd_audit(a) -> int:
    df = _read(a.file)
    m = _resolve(df, a)
    corr = df[a.corr] if a.corr else None
    res = audit(m.size, m.hits, corr)
    res["input_format"] = m.fmt
    if m.approximate:
        res["input_warning"] = m.note
    head = f"  read as {m.fmt}" + (f" — {m.note}" if m.note else "")
    if m.approximate:
        head += "\n  ⚠ APPROXIMATE INPUT — see the note above; the verdict inherits it."
    _emit(res, a.json, head)
    return 0


def cmd_replication(a) -> int:
    df = _read(a.file)
    m = _resolve(df, a)
    if a.hits_b not in df.columns:
        sys.exit(f"--hits-b column {a.hits_b!r} not found. columns: {list(df.columns)}")
    res = audit_replication(m.size, m.hits, df[a.hits_b])
    res["input_format"] = m.fmt
    _emit(res, a.json, f"  read as {m.fmt}")
    return 0


def cmd_rerank(a) -> int:
    df = _read(a.file)
    m = _resolve(df, a)
    names = df[m.set_col] if m.set_col in df.columns else None
    res = rerank(m.size, m.hits, names, top=a.top)
    if a.json:
        print(json.dumps(res, indent=2))
        return 0
    print(f"  read as {m.fmt}\n")
    print(f"  {res['reading']}\n")
    if res.get("size_is_constant"):
        print(f"  correction: {res['correction']}")
        print(f"  {res['what_this_is_not']}")
        return 0
    if res["left_the_top"]:
        print(f"  {'entry':44s} {'size':>5s} {'hits':>7s}   rank -> size-aware")
        for r in res["left_the_top"]:
            print(f"  {r['name'][:44]:44s} {r['size']:5d} {r['hits']:7d}   "
                  f"{r['rank_original']:4d} -> {r['rank_size_aware']:<4d} ({r['moved']:+d})")
        print(f"\n  biggest fall: {res['biggest_fall']} places")
    else:
        print("  Nothing left the top. This ranking survives its own size correction.")
    print(f"\n  correction: {res['correction']}")
    print(f"  {res['what_this_is_not']}")
    return 0


def cmd_baseline(a) -> int:
    df = _read(a.file)
    m = _resolve(df, a)
    if a.predicted not in df.columns:
        sys.exit(f"--predicted column {a.predicted!r} not found. "
                 f"columns: {list(df.columns)}")
    try:
        res = baseline(m.size, m.hits, df[a.predicted],
                       metric=a.metric, k=a.k)
    except ValueError as e:
        sys.exit(f"  {e}")
    res["input_format"] = m.fmt
    res["predicted_column"] = a.predicted
    if m.approximate:
        res["input_warning"] = m.note
    if a.json:
        print(json.dumps(res, indent=2))
        return 0

    print(f"  read as {m.fmt}" + (f" — {m.note}" if m.note else ""))
    if m.approximate:
        print("  ⚠ APPROXIMATE INPUT — see the note above; both scores inherit it.")
    print(f"\n  {res['reading']}\n")
    if res.get("your_score") is not None:
        better = "higher is better" if res["higher_is_better"] else "lower is better"
        print(f"  {'your model':22s} {res['your_score']}")
        print(f"  {'size alone':22s} {res['size_only_score']}")
        print(f"  {'difference':22s} {res['delta']:+}   ({better})")
        share = res.get("share_of_your_score_the_baseline_recovers")
        if share is not None:
            print(f"\n  A predictor with no model in it reaches {share:.0%} of your "
                  f"score.")
    if res["metric"] == "none":
        print("  Rerun with --json to get them; they do not belong in a "
              "terminal one per line.")
    print(f"\n  sets {res['n_sets']}   metric {res['metric']}")
    print(f"  baseline: {res['how_the_baseline_was_built']}")
    if res.get("truth_ranking"):
        t = res["truth_ranking"]
        print(f"  your truth column on its own: {t['verdict']} "
              f"(R2 size-alone {t['r2_size_alone']})")
    if res.get("boundary_condition"):
        print(f"\n  ⚠ BOUNDARY CONDITION\n  {res['boundary_condition']}")
    if res.get("your_predictions_may_be_in_sample"):
        print(f"\n  {res['your_predictions_may_be_in_sample']}")
    print(f"\n  {res['what_this_is_not']}")
    return 0


def cmd_formats(a) -> int:
    print("Formats recognised without any flags:\n")
    for f in SUPPORTED:
        print(f"  {f}")
    print("\nAnything else: name the columns yourself.")
    print("  denali audit FILE --set <col> --size <col> --hits <col>")
    print("\n  size = how many members that set had")
    print("  hits = how many of them came back significant")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="denali",
        description="How much of your gene-set ranking is explained by how the sets "
                    "were built, rather than by biology?")
    p.add_argument("--version", action="version", version=f"denali {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    def shared(sp):
        sp.add_argument("file", help="the results table your analysis already produced")
        sp.add_argument("--set", help="column of set names")
        sp.add_argument("--size", help="column of members per set")
        sp.add_argument("--hits", help="column of significant results per set")
        sp.add_argument("--json", action="store_true", help="machine-readable output")

    a1 = sub.add_parser("audit", help="audit one ranking")
    shared(a1)
    a1.add_argument("--corr", help="optional: mean inter-gene correlation per set")
    a1.set_defaults(fn=cmd_audit)

    a2 = sub.add_parser("replication",
                        help="two screens agreed — how much of that is set size?")
    shared(a2)
    a2.add_argument("--hits-b", required=True, dest="hits_b",
                    help="column of hits from the SECOND, independent screen")
    a2.set_defaults(fn=cmd_replication)

    a4 = sub.add_parser("rerank",
                        help="apply the size correction and show what moves")
    shared(a4)
    a4.add_argument("--top", type=int, default=20,
                    help="how many of your top entries to check (default 20)")
    a4.set_defaults(fn=cmd_rerank)

    a5 = sub.add_parser(
        "baseline",
        help="how much of your model's score is recoverable from set size alone?")
    shared(a5)
    a5.add_argument("--predicted", required=True,
                    help="column holding YOUR model's predicted score per set")
    a5.add_argument("--metric", required=True,
                    help="how you evaluate. One of: "
                         + ", ".join(sorted(BASELINE_METRICS))
                         + ". Or 'none' to get the baseline's predictions back "
                           "and score them yourself. Never guessed.")
    a5.add_argument("--k", type=int, default=10,
                    help="k for top_k_overlap (default 10)")
    a5.set_defaults(fn=cmd_baseline)

    a3 = sub.add_parser("formats", help="which tool outputs are recognised")
    a3.set_defaults(fn=cmd_formats)

    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
