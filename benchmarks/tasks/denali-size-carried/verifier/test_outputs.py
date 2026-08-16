"""Grade which top-10 entries the agent called size-carried.

Every one of the 70 entries (7 screens x top 10) is a binary decision, pooled
across screens and graded against the size-aware residual:

    fit log10(1+hits) on raw size over ALL sets in the screen, re-rank by the
    residual, and call an entry size-carried if it is top 10 by hits and not
    top 10 by residual.

    reward = max(0, 2 * balanced_accuracy - 1)

Balanced accuracy rather than accuracy or F1 because the classes are unbalanced
47 carried / 23 surviving, and every metric that ignores that hands most of the
reward to whichever constant matches the majority. Under balanced accuracy both
constants -- "all carried" and "none carried" -- score exactly 0.5 and therefore
reward exactly 0. That zero point is arithmetic, not a tuned baseline: it does
not move if the answer key is regenerated on different screens.

Deterministic and entirely in code. No model judges this task.

The answer key is derived from denali_audit.core.rerank in the denali repository
and is never present in the agent's environment.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ANSWER = pathlib.Path("/logs/artifacts/answer.json")
REWARD = pathlib.Path("/logs/verifier/reward.txt")

TOP = 10


def fail(msg: str) -> int:
    print(msg, file=sys.stderr)
    REWARD.parent.mkdir(parents=True, exist_ok=True)
    REWARD.write_text("0.0\n")
    return 0


def main() -> int:
    REWARD.parent.mkdir(parents=True, exist_ok=True)
    key = json.loads((HERE / "answer_key.json").read_text())
    truth = {s: set(v["size_carried_ranks"]) for s, v in key.items()}

    if not ANSWER.exists():
        return fail(f"no answer at {ANSWER}")
    try:
        pred_raw = json.loads(ANSWER.read_text())
    except json.JSONDecodeError as e:
        return fail(f"answer.json is not valid JSON: {e}")
    if not isinstance(pred_raw, dict):
        return fail("answer.json must be an object mapping screen -> list of ranks")

    missing = sorted(set(truth) - set(pred_raw))
    if missing:
        return fail(f"{len(missing)} screens missing: {missing}")

    pred = {}
    for screen in sorted(truth):
        raw = pred_raw[screen]
        if not isinstance(raw, list):
            return fail(f"{screen}: expected a list of ranks, got {type(raw).__name__}")
        got = set()
        for r in raw:
            if isinstance(r, bool) or not isinstance(r, int):
                return fail(f"{screen}: ranks must be integers 1-{TOP}, got {r!r}")
            if not (1 <= r <= TOP):
                return fail(f"{screen}: rank {r} is outside 1-{TOP}")
            got.add(r)
        pred[screen] = got

    tp = fp = tn = fn = 0
    rows = []
    for screen in sorted(truth):
        t, p = truth[screen], pred[screen]
        s_tp = len(p & t)
        s_fp = len(p - t)
        s_fn = len(t - p)
        s_tn = TOP - s_tp - s_fp - s_fn
        tp, fp, tn, fn = tp + s_tp, fp + s_fp, tn + s_tn, fn + s_fn
        rows.append((screen, len(t), len(p), s_tp, s_fp, s_fn,
                     (s_tp + s_tn) / TOP))

    sens = tp / (tp + fn) if (tp + fn) else 0.0
    spec = tn / (tn + fp) if (tn + fp) else 0.0
    bal = 0.5 * (sens + spec)
    reward = max(0.0, min(1.0, 2.0 * bal - 1.0))

    print(f"{'screen':<12}{'carried':>9}{'called':>8}{'hit':>5}{'false+':>8}"
          f"{'missed':>8}{'accuracy':>10}")
    for name, nt, np_, s_tp, s_fp, s_fn, acc in rows:
        print(f"{name:<12}{nt:>9}{np_:>8}{s_tp:>5}{s_fp:>8}{s_fn:>8}{acc:>10.2f}")
    total = tp + fp + tn + fn
    print(f"\n{total} decisions: {tp} correctly called carried, {tn} correctly "
          f"left alone, {fp} false positives, {fn} missed")
    print(f"sensitivity       {sens:.4f}   (of the size-carried entries)")
    print(f"specificity       {spec:.4f}   (of the entries that survive)")
    print(f"balanced accuracy {bal:.4f}   (both constants score 0.5000 here)")
    print(f"reward            {reward:.4f}")
    if reward <= 0.0:
        print("No better than calling every entry the same way. This answer does "
              "not tell carried entries from surviving ones.")
    REWARD.write_text(f"{reward:.4f}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
