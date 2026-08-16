"""Grade the agent's confound estimates against the measured values.

Mean absolute error, normalised against the STRONGER of two constant baselines:

    constant 0.5           MAE 0.1585
    constant at true mean  MAE 0.1395   <- the zero point

The second one already knows the right average and still cannot tell the screens
apart, so it is the honest floor. Normalising against the weaker baseline would
hand out reward for guessing the mean, which is the behaviour this task exists
to catch.

    reward = max(0, 1 - MAE / 0.1395)

The answer key is computed by src/audit_screen.py in the denali repository over
seven real published studies, and is never present in the agent's environment.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ANSWER = pathlib.Path("/logs/artifacts/answer.json")
REWARD = pathlib.Path("/logs/verifier/reward.txt")

BASELINE_MAE = 0.1395     # constant at the true mean
WEAK_BASELINE_MAE = 0.1585  # constant 0.5, reported for context only


def fail(msg: str) -> int:
    print(msg, file=sys.stderr)
    REWARD.parent.mkdir(parents=True, exist_ok=True)
    REWARD.write_text("0.0\n")
    return 0


def main() -> int:
    REWARD.parent.mkdir(parents=True, exist_ok=True)
    key = json.loads((HERE / "answer_key.json").read_text())
    truth = {k: v["r2_size_alone"] for k, v in key.items()}

    if not ANSWER.exists():
        return fail(f"no answer at {ANSWER}")
    try:
        pred = json.loads(ANSWER.read_text())
    except json.JSONDecodeError as e:
        return fail(f"answer.json is not valid JSON: {e}")
    if not isinstance(pred, dict):
        return fail("answer.json must be an object mapping screen -> number")

    missing = sorted(set(truth) - set(pred))
    if missing:
        return fail(f"{len(missing)} screens missing: {missing}")

    errs, rows = [], []
    for name in sorted(truth):
        raw = pred[name]
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            return fail(f"{name}: expected a number in [0,1], got {raw!r}")
        p = float(raw)
        if not (0.0 <= p <= 1.0):
            return fail(f"{name}: {p} is outside [0, 1]")
        e = abs(p - truth[name])
        errs.append(e)
        rows.append((name, p, truth[name], e))

    mae = sum(errs) / len(errs)
    reward = max(0.0, min(1.0, 1.0 - mae / BASELINE_MAE))

    print(f"{'screen':<12}{'predicted':>10}{'measured':>10}{'abs err':>10}")
    for name, p, t, e in rows:
        print(f"{name:<12}{p:>10.4f}{t:>10.4f}{e:>10.4f}")
    print(f"\nMAE               {mae:.4f}")
    print(f"  constant 0.5    {WEAK_BASELINE_MAE:.4f}")
    print(f"  constant mean   {BASELINE_MAE:.4f}   <- reward zero point")
    print(f"reward            {reward:.4f}")
    if mae < BASELINE_MAE:
        print("BEAT the mean-knowing constant baseline: the estimates discriminate.")
    else:
        print("Did not beat a constant. These estimates do not discriminate "
              "between screens.")
    REWARD.write_text(f"{reward:.4f}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
