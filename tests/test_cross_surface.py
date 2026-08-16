"""Does any rendered surface disagree with any other about the same number?

The main suite checks each surface against the frozen files. That catches a
surface drifting from the data. It does not catch two surfaces drifting from
each other in a place neither is individually asserted -- which is how this
project has repeatedly ended up with "ten evaluations" on one page and eleven on
another, and how a stale figure survives in a doc nobody thought to guard.

This asks a different question: for each named quantity, gather every value any
surface states for it, and fail if they are not all the same.

The design decision that matters is that a quantity is found by its SURROUNDING
PHRASE, not by its value. Searching for "0.751" only finds surfaces that already
agree; searching for "adj R²" and then reading the number next to it finds the
one that says 0.75.

    .venv/bin/python tests/test_cross_surface.py

Run by `make test` after the main suite. Adding a quantity is one row.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Every surface a reader can actually reach. Not src/ -- code comments are
# allowed to discuss superseded values, and the frozen JSON is the truth these
# are checked against elsewhere.
SURFACES = [
    "README.md", "REPORT.md", "index.html", "app.py",
    "docs/DEMO.md", "docs/SUBMISSION.md", "docs/DECK.md", "docs/LITERATURE.md",
    "docs/CORPUS.md", "docs/ADVERSARIAL.md", "docs/MORNING_HANDOFF.md",
    "docs/LIMITATIONS.md", "docs/LOOP.md", "docs/OFFTARGET.md",
    "results/figures/CAPTIONS.md",
]

# label -> (context regex with ONE capture group, canonical value, equivalents)
# The regex must anchor on words, so a surface stating a WRONG value is found
# rather than skipped. `equivalents` lists spellings that mean the same number.
QUANTITIES = {
    "adj R2, all six features": (
        r"(?:adj(?:usted)?\.? R[²2][^.\n]{0,40}?|all six[^.\n]{0,30}?)\b(0\.7\d{1,3})\b",
        "0.751", {"0.7511", "0.751"}),
    "adj R2, outcome-independent five": (
        r"(?:0\.561|outcome-independent[^.\n]{0,40}?\b(0\.5\d{1,3})\b)",
        "0.561", {"0.561", "0.5606"}),
    "R2, set size alone": (
        r"(?:size alone|set size alone)[^.\n]{0,60}?\b(0\.4\d{1,3}|4\d(?:\.\d)?%)\b",
        "0.4649", {"0.4649", "0.465", "46.5%", "46%"}),
    "held-out balanced accuracy": (
        r"balanced accuracy[^.\n]{0,40}?\b(0\.\d{2,4})\b",
        "0.4375", {"0.4375"}),
    "guide-pair concordance": (
        r"concordance[^.\n]{0,40}?([−-]0\.0\d{1,3})\b",
        "-0.019", {"-0.019", "−0.019"}),
    "corpus median size-confound": (
        r"(?:field's median|median size-confound|median)[^.\n]{0,40}?\b(0\.2\d{1,3})\b",
        "0.224", {"0.224"}),
    # (?<![\d.]) or this matches the "4.4%" inside Tier B's "14.4%" -- the two
    # sit in the same sentence, which is exactly the trap a value-blind pattern
    # falls into.
    "literature Tier A share": (
        r"(?:Tier A|mention (?:gene-)?set size)[^.\n]{0,80}?(?<![\d.])(\d\.\d%)",
        "3.6%", {"3.6%"}),
    "literature Tier B share": (
        r"(?:Tier B|competitive-test machinery)[^.\n]{0,80}?(?<![\d.])(1\d\.\d%)",
        "14.4%", {"14.4%"}),
    "literature resolved count": (
        r"(?:resolved|open access)[^.\n]{0,60}?\b(1\d{2})\b",
        "111", {"111"}),
}


def _norm(v: str) -> str:
    return v.replace("−", "-").strip()


def main() -> int:
    texts = {}
    for s in SURFACES:
        p = ROOT / s
        if p.exists():
            texts[s] = p.read_text(errors="ignore")

    passed, failed = [], []

    def check(name, cond, detail=""):
        (passed if cond else failed).append(f"{name}{'  --  ' + detail if detail else ''}")

    for label, (pat, canon, equiv) in QUANTITIES.items():
        rx = re.compile(pat, re.I)
        seen = {}
        for s, t in texts.items():
            for m in rx.finditer(t):
                g = next((x for x in m.groups() if x), None)
                if g:
                    seen.setdefault(_norm(g), set()).add(s)
        if not seen:
            # A quantity nothing states is a stale row in this table, and that
            # is a defect in the guard rather than in the repo -- say so.
            check(f"cross-surface: {label} is stated somewhere", False,
                  "no surface matched the context pattern; the pattern is stale")
            continue
        bad = {v: ss for v, ss in seen.items() if v not in equiv}
        check(f"cross-surface: every surface agrees on {label}", not bad,
              f"canonical {canon}; found "
              + "; ".join(f"{v!r} in {sorted(x.split('/')[-1] for x in ss)}"
                          for v, ss in (bad or seen).items()))

    # Evaluation and negative counts, read from the README findings table --
    # the same single source of truth the main suite uses, checked here across
    # every surface that spells the number as a word.
    readme = texts.get("README.md", "")
    rows = re.findall(r"^\|\s*(\d+)\s*\|.*\|\s*\*\*([A-Z][A-Z ]+)\*\*", readme, re.M)
    n_eval = len(rows)
    n_neg = [v.strip() for _, v in rows].count("NEGATIVE")
    words = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
             7: "seven", 8: "eight", 9: "nine", 10: "ten", 11: "eleven",
             12: "twelve"}
    ev_w, neg_w = words.get(n_eval, ""), words.get(n_neg, "")
    wrong = {}
    for s, t in texts.items():
        for m in re.finditer(r"\b(\w+) of (\w+) evaluations\b", t, re.I):
            a, b = m.group(1).lower(), m.group(2).lower()
            if (a, b) != (neg_w, ev_w):
                wrong.setdefault(f"{a} of {b}", set()).add(s)
        for m in re.finditer(r"\b(\w+) evaluations\b", t, re.I):
            a = m.group(1).lower()
            if a in words.values() and a != ev_w:
                wrong.setdefault(f"{a} evaluations", set()).add(s)
    check(f"cross-surface: every surface says {neg_w} of {ev_w} evaluations",
          not wrong,
          "; ".join(f"{k!r} in {sorted(x.split('/')[-1] for x in v)}"
                    for k, v in wrong.items()))

    # A claim of the form "git diff X..HEAD matches nothing under src/" is
    # checkable, and three of them shipped returning the opposite of the
    # sentence beside them. Any surface that argues from a commit range must
    # have that argument still be true, or not make it.
    import subprocess
    for s, txt in texts.items():
        for m in re.finditer(
                r"`git diff --name-only ([0-9a-f]{7,40})\.\.HEAD`[^.]{0,120}?"
                r"matches nothing under `src/`", txt):
            sha = m.group(1)
            try:
                out = subprocess.run(
                    ["git", "diff", "--name-only", f"{sha}..HEAD", "--", "src", "Makefile"],
                    cwd=ROOT, capture_output=True, text=True, timeout=30).stdout.strip()
            except Exception as e:                       # noqa: BLE001
                out = f"(could not run: {e})"
            check(f"cross-surface: {s} 'nothing under src/' since {sha} is still true",
                  out == "",
                  f"git says: {out.replace(chr(10), ', ') or '(empty)'}")
        # Same shape, counted rather than listed. Skip text inside *italics* or
        # "quotes": the README explains this failure mode by quoting the bad
        # sentence, and a guard that cannot tell a cautionary example from a
        # live claim would make documenting the lesson impossible.
        for m in re.finditer(r"[Tt]he (one|two|three|four|five) commits? after it", txt):
            ctx = txt[max(0, m.start() - 60):m.start()]
            if ctx.rstrip().endswith(('*"', '"', '*', "'")) or '*"' in ctx[-30:]:
                continue
            check(f"cross-surface: {s} does not count commits that had not been written",
                  False,
                  f"{m.group(0)!r} -- a commit count after a named SHA goes stale "
                  "the moment anyone pushes; name the commit and let the reader re-run")

    for p in passed:
        print(f"PASS  {p}")
    for f in failed:
        print(f"FAIL  {f}")
    print(f"\n{len(passed)}/{len(passed) + len(failed)} cross-surface checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
