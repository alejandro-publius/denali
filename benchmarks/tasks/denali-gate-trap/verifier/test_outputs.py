"""Grade the agent's predictions against the frozen screen result.

Balanced accuracy, so a constant answer scores 0.5. The reward is normalised
against two documented reference points rather than raw:

    0.00  at or below always-true          (balanced accuracy 0.5000)
    0.50  matching the naive quality gate  (balanced accuracy 0.6981)
    1.00  at perfect                       (balanced accuracy 1.0000)

The answer key is the measured outcome in results/frozen/program_summary.csv of
the denali repository: whether each program had at least one knockdown at q<0.05.
It is never present in the agent's environment.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ANSWER = pathlib.Path("/logs/artifacts/answer.json")
REWARD = pathlib.Path("/logs/verifier/reward.txt")

CHANCE = 0.5000        # always-true / always-false
GATE = 0.6981          # the naive measurability filter, measured


def main() -> int:
    REWARD.parent.mkdir(parents=True, exist_ok=True)
    key = json.loads((HERE / "answer_key.json").read_text())

    if not ANSWER.exists():
        print(f"no answer at {ANSWER}", file=sys.stderr)
        REWARD.write_text("0.0\n")
        return 0
    try:
        pred = json.loads(ANSWER.read_text())
    except json.JSONDecodeError as e:
        print(f"answer.json is not valid JSON: {e}", file=sys.stderr)
        REWARD.write_text("0.0\n")
        return 0
    if not isinstance(pred, dict):
        print("answer.json must be an object mapping program -> bool", file=sys.stderr)
        REWARD.write_text("0.0\n")
        return 0

    missing = sorted(set(key) - set(pred))
    if missing:
        print(f"{len(missing)} programs missing, first: {missing[:3]}", file=sys.stderr)
        REWARD.write_text("0.0\n")
        return 0

    tp = tn = fp = fn = 0
    for prog, truth in key.items():
        p = bool(pred[prog])
        if p and truth:
            tp += 1
        elif p and not truth:
            fp += 1
        elif not p and truth:
            fn += 1
        else:
            tn += 1

    sens = tp / (tp + fn) if (tp + fn) else 0.0
    spec = tn / (tn + fp) if (tn + fp) else 0.0
    bal = (sens + spec) / 2

    reward = max(0.0, min(1.0, (bal - CHANCE) / (1.0 - CHANCE)))
    print(f"tp={tp} tn={tn} fp={fp} fn={fn}")
    print(f"sensitivity      {sens:.4f}")
    print(f"specificity      {spec:.4f}")
    print(f"balanced accuracy {bal:.4f}   (chance {CHANCE}, naive gate {GATE})")
    print(f"reward            {reward:.4f}")
    if bal > GATE:
        print("BEAT the naive measurability gate.")
    REWARD.write_text(f"{reward:.4f}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
