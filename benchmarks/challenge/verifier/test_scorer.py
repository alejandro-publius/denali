"""Does the scorer discriminate, or does it rubber-stamp?

A verifier that only checks the happy path is the fourth kind of guard this project
keeps finding: one that passes while testing nothing. Every case below is an answer
somebody could actually submit, and each must be rejected or scored the way it says.

    python benchmarks/challenge/verifier/test_scorer.py
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
CHALLENGE = HERE.parent
ROOT = CHALLENGE.parent.parent
SCORE = CHALLENGE / "scorer" / "score.py"

sys.path.insert(0, str(CHALLENGE / "scorer"))
import score as S  # noqa: E402

FAILURES: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    print(f"  {'ok  ' if cond else 'FAIL'}  {name}{('  — ' + detail) if detail and not cond else ''}")
    if not cond:
        FAILURES.append(name)


def run(path: Path | None) -> tuple[int, str]:
    cmd = [sys.executable, str(SCORE)] + ([str(path)] if path else [])
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    return p.returncode, p.stdout + p.stderr


def write(tmp: Path, name: str, text: str) -> Path:
    f = tmp / name
    f.write_text(text)
    return f


def main() -> int:
    inp = S.load_input()
    truth = S.load_truth(inp["set"])
    sets = inp["set"].tolist()

    print("\nthe scorer's own arithmetic")
    perfect = S.spearman_vs(truth, truth)
    check("submitting the truth scores rho 1.0", abs(perfect - 1.0) < 1e-12, f"got {perfect}")
    rev = S.spearman_vs(-truth, truth)
    check("submitting the truth reversed scores rho -1.0", abs(rev + 1.0) < 1e-12, f"got {rev}")
    base = S.spearman_vs(inp["size"].to_numpy(float), truth)
    check("baseline reproduces the study's published size-alone top-10 of 0.60",
          abs(S.top_k_overlap(inp["size"].to_numpy(float), truth) - 0.60) < 1e-12)
    naive = S.spearman_vs(inp["hits"].to_numpy(float), truth)
    check("raw-hits entry reproduces the study's published cross-screen rho 0.6633",
          abs(naive - 0.6633) < 5e-5, f"got {naive:.6f}")

    print("\nthe target's size confound, which was hand-typed once and must not be again")
    conf = S.target_size_confound(inp)
    board = (CHALLENGE / "board.md").read_text() if (CHALLENGE / "board.md").exists() else ""
    check("board.md states the derived confound, not a quoted one",
          f"R² {conf:.4f}" in board, f"derived {conf:.4f} absent from board.md")
    check("README states the derived confound too",
          f"R² {conf:.4f}" in (CHALLENGE / "README.md").read_text())
    # The first version of this check was `"0.214" in text and "concordance" not in
    # text`, which passed while testing nothing: nearly every file here names
    # results/concordance/, so the second clause was always false. Found by mutating
    # a bare "R² 0.214" back in and watching the suite stay green. It now pins the
    # CLAIM form, which is what a reintroduced quote would actually look like.
    claims = [p.name for p in CHALLENGE.rglob("*.md")
              if "R² 0.214" in p.read_text() or "R^2 0.214" in p.read_text()]
    check("no file states the cross-screen 0.214 as if it were the target's confound",
          not claims, f"stated in {claims}")
    # Pins the provenance claim the docstring makes: 0.214 is RPE1 hits on K562's
    # sizes, not on RPE1's. If someone "corrects" it to the RPE1 arm's 0.2758 this
    # goes red and says why.
    paired = pd.read_csv(S.PAIRED).set_index("program").loc[sets]
    cross = S._r2(paired["n_present_k562"].to_numpy(float),
                  np.log10(1 + paired["n_hits_q05_rpe1"].to_numpy(float)))
    check("the concordance arm's 0.214 is reproduced as RPE1 hits on K562 sizes",
          abs(cross - 0.214) < 5e-4, f"got {cross:.4f}")
    check("that is a different number from the target's own confound",
          abs(cross - conf) > 0.05, f"{cross:.4f} vs {conf:.4f}")

    print("\nthe scope-limit-6 guard, mutated on purpose")
    ok_shape = True
    try:
        S.guard_scope_limit_6(np.array([10.0, 200.0]), np.array([5.0, 60.0]))
        ok_shape = False       # overlap-shaped input (hits <= size) must be refused
    except SystemExit:
        pass
    check("refuses a mapping where hits are counted over the set's own members", ok_shape)
    passes_real = True
    try:
        S.guard_scope_limit_6(inp["size"].to_numpy(float), inp["hits"].to_numpy(float))
    except SystemExit:
        passes_real = False
    check("accepts the real evaluation set", passes_real)

    print("\nsubmissions that must be rejected")
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        head = "set,score\n"
        cases = [
            ("constant score", head + "".join(f"{s},1.0\n" for s in sets)),
            ("missing one set", head + "".join(f"{s},{i}\n" for i, s in enumerate(sets[:-1]))),
            ("duplicate set", head + "".join(f"{s},{i}\n" for i, s in enumerate(sets))
                                   + f"{sets[0]},99\n"),
            ("non-numeric score", head + "".join(f"{s},{'high' if i == 0 else i}\n"
                                                 for i, s in enumerate(sets))),
            ("infinite score", head + "".join(f"{s},{'inf' if i == 0 else i}\n"
                                              for i, s in enumerate(sets))),
            ("wrong column names", "gene,value\n" + "".join(f"{s},{i}\n" for i, s in enumerate(sets))),
            ("unknown set names", head + "".join(f"NOT_A_SET_{i},{i}\n" for i in range(len(sets)))),
            ("malformed csv", 'set,score\n"unclosed,1\n'),
            ("empty file", ""),
        ]
        for name, text in cases:
            rc, out = run(write(tmp, "sub.csv", text))
            check(f"rejects: {name}", rc != 0, f"exit {rc}")

        rc, out = run(tmp / "does_not_exist.csv")
        check("rejects: no submission file at all", rc != 0, f"exit {rc}")

        print("\nsubmissions that must be accepted")
        oracle = head + "".join(f"{s},{t}\n" for s, t in zip(sets, truth))
        rc, out = run(write(tmp, "oracle.csv", oracle))
        check("accepts the oracle and scores it 1.0000", rc == 0 and "1.0000" in out, f"exit {rc}")

        extra = "set,size,hits,score\n" + "".join(
            f"{r.set},{r.size},{r.hits},{i}\n" for i, r in enumerate(inp.itertuples()))
        rc, out = run(write(tmp, "extra.csv", extra))
        check("accepts a tool's own output table with a score column appended", rc == 0, f"exit {rc}")

        shuffled = pd.DataFrame({"set": sets, "score": truth}).sample(frac=1, random_state=0)
        f = tmp / "shuf.csv"
        f.write_text(shuffled.to_csv(index=False))
        rc, out = run(f)
        check("accepts rows in any order and still scores 1.0000", rc == 0 and "1.0000" in out)

    print("\ndeterminism")
    a = S.null_and_bootstrap(inp["size"].to_numpy(float), truth)
    b = S.null_and_bootstrap(inp["size"].to_numpy(float), truth)
    check("the permutation null is reproducible", a == b)
    check("the baseline beats its own permutation null", a["baseline_beats_null"],
          f"p = {a['null_p']}")

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILED: {', '.join(FAILURES)}")
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
