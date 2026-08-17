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
import pathlib
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
    "results/figures/CAPTIONS.md", "results/corpus_rerank/README.md",
    # Added after both drifted unnoticed: SUBMISSION_IMPACTFORGE.md stated a
    # stale cross-surface count and stale dependency floors, and the package
    # README told readers to install from PyPI where nothing is published.
    # A prose surface nobody registered is a prose surface nobody checks.
    "docs/SUBMISSION_IMPACTFORGE.md", "packages/denali-audit/README.md",
]

# Any .md a reader can reach that states a headline number should be in
# SURFACES above. This catches the ones nobody remembered to add.
_UNREGISTERED_HINT = ("docs", "packages")

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

    # ---- preconditions: a missing input must fail, not skip ----------------
    # Twenty of the check() calls in this file sit inside `if <file>.exists()`.
    # That is reasonable per block and disastrous in aggregate: delete an input
    # and those checks do not fail, they VANISH, and the suite prints a smaller
    # green number that looks exactly like the larger one. It is the same
    # "passed while testing nothing" shape as the three guards in
    # docs/METHOD_RULES.md, arrived at by a fourth route -- a branch that is
    # never entered rather than a clause that is never false.
    #
    # Found by the session that owns benchmarks/, reading the block that had
    # just been added to codify the rule against exactly this. Mutating the
    # guarded CONTENT four ways never touched it, because every one of those
    # mutations left the file present and exercised the true branch. The
    # precondition has to be mutated too, which is now a line in METHOD_RULES.
    REQUIRED_INPUTS = (
        "README.md",
        "audit.html",
        "examples/example_gprofiler.csv",
        "results/frozen/program_summary.csv",
        "results/concordance/paired_programs.csv",
        "results/corpus/corpus_per_screen.csv",
        "packages/denali-audit/denali_audit/atlas.py",
    )
    absent = [p for p in REQUIRED_INPUTS if not (ROOT / p).exists()]
    check("cross-surface: every input the gated blocks derive from is present",
          not absent,
          f"absent: {absent} — the checks that read these would silently "
          f"disappear rather than fail, and this suite would still print green")

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
    # Runs past any count this project will plausibly reach. It stopped at
    # twelve, and the day a thirteenth evaluation landed `words.get(13, "")`
    # returned the empty string, so the guard compared every surface against
    # "nine of  evaluations" and reported them all wrong with a blank where the
    # number should be. A lookup table that silently returns a falsy default is
    # the same shape as the guards in METHOD_RULES: it did not fail, it produced
    # a confident sentence with a hole in it.
    words = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
             7: "seven", 8: "eight", 9: "nine", 10: "ten", 11: "eleven",
             12: "twelve", 13: "thirteen", 14: "fourteen", 15: "fifteen",
             16: "sixteen", 17: "seventeen", 18: "eighteen", 19: "nineteen",
             20: "twenty"}
    check("cross-surface: the number-word table covers the current counts",
          n_eval in words and n_neg in words,
          f"no word for n_eval={n_eval} or n_neg={n_neg}; the guard would "
          f"compare surfaces against a sentence with a blank in it")
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

    # A markdown table with a blank line in it silently becomes literal pipe
    # text. The findings table -- the single source of truth this whole suite
    # parses -- shipped with five blank lines in it and a paragraph splitting
    # rows 9 and 10, so seven of eleven rows did not render on GitHub at all.
    # The parser that reads it does not care about blank lines; a reader does.
    for s, txt in texts.items():
        if not s.endswith(".md"):
            continue
        block, blank_in_table, para_in_table = [], 0, 0
        prev_pipe = False
        for i, ln in enumerate(txt.split("\n")):
            is_pipe = ln.startswith("|")
            if prev_pipe and not is_pipe and ln.strip():
                # a non-blank non-pipe line directly after a row: fine only if
                # the table has ended (no pipe row follows within 2 lines)
                nxt = txt.split("\n")[i + 1:i + 3]
                if any(x.startswith("|") for x in nxt):
                    para_in_table += 1
            if prev_pipe and not ln.strip():
                nxt = txt.split("\n")[i + 1:i + 2]
                if nxt and nxt[0].startswith("|"):
                    blank_in_table += 1
            prev_pipe = is_pipe
        check(f"cross-surface: no markdown table in {s} is broken by a blank line "
              "or a paragraph",
              blank_in_table == 0 and para_in_table == 0,
              f"{blank_in_table} blank line(s) and {para_in_table} paragraph(s) "
              "inside a table -- those rows render as literal pipes")

    # The rerank table in the README is the project's single strongest
    # demonstration -- our own number one falling twenty-three places -- and it
    # is 35 hand-typed cells. Re-derive it from the packaged tool rather than
    # trusting that it was right the day it was pasted in.
    readme_md = texts.get("README.md", "")
    if "## What the tool does to our own result" in readme_md:
        import subprocess, tempfile, csv as _csv
        sec = readme_md.split("## What the tool does to our own result", 1)[1]
        rows = re.findall(
            r"^\| `(HALLMARK_\w+)` \| ([\d,]+) \| ([\d,]+) \| \*{0,2}(\d+) → (\d+)\*{0,2} \| −(\d+) \|",
            sec, re.M)
        import shutil
        # PATH first so CI (system python) finds it, venv second for local use.
        # NOT an optional skip: CI installs the package precisely so this runs,
        # and a guard that quietly no-ops in the one environment that gates
        # every push is the failure mode this repo keeps rediscovering.
        venv = pathlib.Path(shutil.which("denali") or (ROOT / ".venv" / "bin" / "denali"))
        summ = ROOT / "results" / "frozen" / "program_summary.csv"
        if not rows:
            check("cross-surface: the README rerank table is parseable", False,
                  "no rows matched -- the table changed shape or vanished")
        elif not venv.exists():
            check("cross-surface: the README rerank table matches the tool", False,
                  "denali is not installed, so this check cannot run. "
                  "`pip install -e packages/denali-audit`. It fails rather than "
                  "skipping on purpose.")
        else:
            with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False,
                                             newline="") as fh:
                w = _csv.writer(fh); w.writerow(["set", "size", "hits"])
                with open(summ, newline="") as src:
                    for r in _csv.DictReader(src):
                        w.writerow([r["program"], r["n_present"], r["n_hits_q05"]])
                tmp = fh.name
            out = subprocess.run([str(venv), "rerank", tmp, "--top", "10"],
                                 capture_output=True, text=True, timeout=120).stdout
            live = {m.group(1): (int(m.group(2)), int(m.group(3)), int(m.group(4)),
                                 int(m.group(5)), int(m.group(6)))
                    for m in re.finditer(
                        r"(HALLMARK_\w+)\s+(\d+)\s+(\d+)\s+(\d+) -> (\d+)\s+\((-\d+)\)", out)}
            bad = []
            for name, size, hits, r1, r2, d in rows:
                want = (int(size.replace(",", "")), int(hits.replace(",", "")),
                        int(r1), int(r2), -int(d))
                if live.get(name) != want:
                    bad.append(f"{name}: README {want} vs tool {live.get(name)}")
            check("cross-surface: every cell of the README rerank table matches "
                  "the packaged tool",
                  not bad and len(rows) == len(live),
                  "; ".join(bad[:3]) if bad
                  else f"{len(rows)} rows x 5 cells re-derived from `denali rerank`")

    # ---- the web surface must be the package, not a copy of it ------------
    # audit.html runs denali_audit in the browser by carrying its source inline.
    # That is the only way the page can claim to be "the same code"; it is also
    # a second copy, and a second copy goes stale. The builder is re-run here and
    # the committed page must match it byte for byte.
    page = ROOT / "audit.html"
    if page.exists():
        sys.path.insert(0, str(ROOT / "web"))
        import build_audit_page
        check("cross-surface: audit.html carries the CURRENT package source",
              build_audit_page.build() == page.read_text(),
              "stale — run: python3 web/build_audit_page.py")
        inlined = json.loads(re.search(
            r'<script id="denali-src" type="application/json">(.*?)</script>',
            page.read_text(), re.S).group(1).replace("<\\/", "</"))
        pkg = ROOT / "packages" / "denali-audit" / "denali_audit"
        drift = [n for n, src in inlined.items() if (pkg / n).read_text() != src]
        check("cross-surface: every module inlined in audit.html is byte-identical "
              "to the packaged one", not drift, ", ".join(drift))

        # THE CONVERSE, which is the direction that actually broke. The check
        # above compares the modules that ARE inlined against the package and has
        # nothing to say about a package module that is NOT inlined. When core.py
        # grew `from . import nulls`, audit.html shipped a denali_audit without
        # nulls.py and died with a circular-import ImportError on the first click,
        # for every visitor, while this file stayed green. Found by driving the
        # page in a browser, not by reading it.
        missing = sorted({q.name for q in pkg.glob("*.py")} - set(inlined))
        check("cross-surface: audit.html inlines EVERY module the package has",
              not missing,
              f"absent from the page: {missing} — the page builds a denali_audit "
              f"that cannot import itself")

        # And the strongest form: the inlined set must actually be importable on
        # its own. A module list can be complete and still not work.
        import shutil as _sh
        import subprocess as _sp
        import tempfile as _tf
        _d = pathlib.Path(_tf.mkdtemp(prefix="denali-inline-"))
        (_d / "denali_audit").mkdir()
        for _n, _src in inlined.items():
            (_d / "denali_audit" / _n).write_text(_src)
        _r = _sp.run([sys.executable, "-c", "import denali_audit"],
                     capture_output=True, text=True, cwd=_d, timeout=120)
        check("cross-surface: the module set audit.html ships can import itself",
              _r.returncode == 0,
              (_r.stderr or "").strip().splitlines()[-1] if _r.stderr else "")
        _sh.rmtree(_d, ignore_errors=True)

        # The inlined MODULES are byte-checked above. The page's own driver --
        # the ~50 lines of Python the page wraps around them -- is not a module
        # and was checked by nothing, so a NameError in it shipped green and
        # only appeared when a browser ran it. Execute it here against the real
        # package and require it to agree with the package's own functions.
        drv = re.search(r"var DRIVER = \[(.*?)\]\.join\(\"\\n\"\);",
                        page.read_text(), re.S)
        check("cross-surface: audit.html carries an extractable Python driver",
              drv is not None)
        if drv:
            import io as _io
            import pandas as _pd
            sys.path.insert(0, str(pkg.parent))
            ns: dict = {}
            try:
                exec(compile("\n".join(json.loads("[" + drv.group(1) + "]")),
                             "<audit.html driver>", "exec"), ns)
                err = None
            except Exception as e:                              # noqa: BLE001
                err = f"{type(e).__name__}: {e}"
            check("cross-surface: the page's Python driver imports and compiles",
                  err is None, err or "")
            if err is None:
                ex = (ROOT / "examples" / "example_gprofiler.csv")
                got = json.loads(ns["run"](ex.read_text(), ex.name))
                from denali_audit.core import audit as _pkg_audit
                from denali_audit.adapters import detect as _pkg_detect
                _df = _pd.read_csv(_io.StringIO(ex.read_text()))
                _m = _pkg_detect(_df)
                want = _pkg_audit(_m.size, _m.hits)
                check("cross-surface: the page's driver returns the package's "
                      "own audit numbers",
                      got.get("ok") and got["audit"]["r2_size_alone"]
                      == want["r2_size_alone"]
                      and got["audit"]["verdict"] == want["verdict"],
                      f"page {got.get('audit', {}).get('r2_size_alone')} vs "
                      f"package {want['r2_size_alone']}")
                # Every metric the page offers must be one the package accepts,
                # or the dropdown hands the user a refusal.
                from denali_audit.core import BASELINE_METRICS as _BM
                check("cross-surface: every metric the page offers is one the "
                      "package implements",
                      sorted(got.get("metrics", [])) == sorted(_BM),
                      f"page {sorted(got.get('metrics', []))} vs "
                      f"package {sorted(_BM)}")
                # The baseline route, end to end through the page's own driver.
                _b = json.loads(ns["run_baseline"](
                    ex.read_text(), ex.name, "query_size", "spearman", 10))
                check("cross-surface: the page's baseline driver refuses a "
                      "constant prediction column rather than scoring it",
                      _b.get("ok") is True
                      and _b["baseline"].get("your_score") is None,
                      str(_b)[:120])
                _bad = json.loads(ns["run_baseline"](
                    ex.read_text(), ex.name, "intersection_size", "auroc", 10))
                check("cross-surface: the page's baseline driver refuses a "
                      "metric the package does not know",
                      _bad.get("ok") is False
                      and "unrecognised metric" in _bad.get("message", ""),
                      str(_bad)[:120])
                # The atlas lookup, through the page, must return the package's
                # own number -- and must refuse rather than invent one for a
                # screen it does not carry.
                from denali_audit.atlas import FLOORS, N_SCREENS
                from denali_audit.atlas import floor as _pkg_floor
                _sid = sorted(FLOORS)[0]
                _pf = json.loads(ns["run_floor"](str(_sid)))
                check("cross-surface: the page's atlas lookup returns the "
                      "package's own floor",
                      _pf.get("no_biology_floor")
                      == _pkg_floor(_sid)["no_biology_floor"],
                      f"page {_pf.get('no_biology_floor')} vs package "
                      f"{_pkg_floor(_sid)['no_biology_floor']}")
                check("cross-surface: the page's atlas lookup refuses a screen "
                      "it does not carry rather than inventing a floor",
                      json.loads(ns["run_floor"]("999999")).get("status")
                      == "NOT_IN_ATLAS"
                      and json.loads(ns["run_floor"]("zzz")).get("status")
                      == "NOT_IN_ATLAS")
                # The page states the atlas size in prose. It is injected from
                # the package at build time, so it cannot be stale -- but only
                # if nobody types it back in, which is what this catches.
                check("cross-surface: the atlas size stated on the page is the "
                      "size the shipped atlas actually has",
                      f"<b>{N_SCREENS:,}</b>" in page.read_text(),
                      f"page does not state {N_SCREENS:,}")

    # NO SURFACE STATES A COUNT OF docs/ FILES, and this guard exists to keep it
    # that way rather than to check the count is right.
    #
    # It was the other way round twice. First the index said 33 and the README
    # said twenty-seven while there were 40, and the fix was to correct them and
    # pin the value. Then a single new pre-registration took docs/ from 43 to 44
    # and both surfaces were stale again within the day, red for every session
    # sharing the checkout. A hand-typed count of files on disk cannot be
    # derived at build time in a static markdown file, so under this repo's own
    # rule -- no number typed into prose -- it should not be there at all. It
    # also told the reader nothing: "a lot" is the entire content of "43".
    #
    # So the number is gone from both sentences and this asserts its absence.
    # Anyone reintroducing one gets a red build with the reason.
    for _s, _pat in (("docs/README.md", r"\b(\d+|[a-z]+-?[a-z]*) files is a lot"),
                     ("README.md",
                      r"documentation index\*\*[^.\n]{0,20}— (\d+|[a-z-]+) files")):
        _t = texts.get(_s, (ROOT / _s).read_text() if (ROOT / _s).exists() else "")
        _m = re.search(_pat, _t, re.M)
        check(f"cross-surface: {_s} does not hand-type a count of docs/ files",
              _m is None,
              f"states {_m.group(1)!r} files — a count that cannot derive at "
              f"build time goes stale on the next doc added, and has twice"
              if _m else "")

    # The README states the size confound in the challenge's TARGET, and that
    # number has now been wrong twice in two different ways. First it was
    # `0.214` quoted out of results/concordance/cross_screen.json, which is RPE1
    # regressed on K562's sizes -- a cross-screen quantity, not a property of
    # the target. Then it was "corrected" to evaluation 5's 0.2758, which is the
    # full RPE1 arm over 49 scoreable programs and not the paired 50 the board
    # actually scores. Three defensible values, one correct answer per question.
    #
    # The challenge verifier believes it pins this, but its check reads
    # benchmarks/challenge/README.md rather than the top-level one, so this
    # surface was never covered. Derived here from the frozen paired file with
    # the packaged function, so it cannot be quoted from anywhere.
    paired = ROOT / "results" / "concordance" / "paired_programs.csv"
    if paired.exists() and readme:
        import numpy as _np
        import pandas as _pd
        sys.path.insert(0, str(ROOT / "packages" / "denali-audit"))
        from denali_audit.core import _r2 as _pkg_r2
        _p = _pd.read_csv(paired)
        _want = round(_pkg_r2(_p.n_present_rpe1.to_numpy(float),
                              _np.log10(1.0 + _p.n_hits_q05_rpe1.to_numpy(float))), 4)
        _m = re.search(r"RPE1's own set sizes\s*\n?\s*explain \*\*R² ([\d.]+)\*\*",
                       readme)
        check("cross-surface: the README's target-confound R2 is the one the "
              "board actually scores against",
              _m is not None and float(_m.group(1)) == _want,
              f"README says {_m.group(1) if _m else 'nothing'}, derived {_want}")
        # And the three estimands must stay BOUND TO THEIR OWN DESCRIPTIONS in
        # the paragraph that exists to keep them apart.
        #
        # The first version of this checked `all(v in readme for v in (...))`,
        # which passed while testing nothing: every one of those three strings
        # also occurs elsewhere in the README, so replacing 0.2758 inside the
        # disambiguation with 0.9999 left the guard green. Found by mutating
        # exactly that and watching it pass -- the same shape as the check it
        # was written to replace. It now pins each value to the phrase that
        # identifies which question it answers, scoped to the paragraph.
        _para = re.search(r"\*Three different R² values.*?\n\n", readme, re.S)
        _bindings = ((r"\*\*0\.3090\*\* is RPE1's hits on RPE1's own sizes",
                      "0.3090 = target confound"),
                     (r"\*\*0\.2758\*\* is \[evaluation 5\]",
                      "0.2758 = evaluation 5"),
                     (r"\*\*0\.214\*\* is", "0.214 = cross-screen"))
        _missing = [] if _para is None else [
            lbl for pat, lbl in _bindings
            if not re.search(pat, _para.group(0))]
        check("cross-surface: the README binds each of the three RPE1 "
              "estimands to the question it answers",
              _para is not None and not _missing,
              "no disambiguation paragraph" if _para is None
              else f"unbound: {_missing}")
        # The cross-screen value must also still be described as cross-screen.
        check("cross-surface: the README does not present the cross-screen "
              "0.214 as a property of RPE1",
              _para is not None
              # NOT [^.]* — the sentence names cross_screen.json and the dots in
              # the filename ended that class immediately, so the guard failed
              # on correct text. A bounded any-char window is what was meant.
              and re.search(r"\*\*0\.214\*\*.{0,220}K562", _para.group(0),
                            re.S) is not None,
              "0.214 is stated without saying it regresses on K562's sizes")

    # ---- screen.html must not drift from the data it renders ---------------
    # Same discipline as audit.html and atlas.py: the page is regenerated here
    # and the committed one must match, so a change to the stage content or to
    # the corpus reference classes that never reaches the page is a red build
    # rather than a companion quietly telling planners something the repository
    # no longer believes.
    screen_html = ROOT / "screen.html"
    if screen_html.exists():
        sys.path.insert(0, str(ROOT))
        import importlib
        _bs = importlib.import_module("web.build_screen_page")
        check("cross-surface: screen.html carries the CURRENT stage data",
              _bs.build() == screen_html.read_text(),
              "stale — run: .venv/bin/python -m web.build_screen_page")
        # The floors it shows a planner must be the corpus's own, not a copy.
        import json as _j
        import pandas as _pdd
        _ref = _j.loads(re.search(
            r'<script id="reference-src" type="application/json">(.*?)</script>',
            screen_html.read_text(), re.S).group(1).replace("<\\/", "</"))
        _corpus = _pdd.read_csv(ROOT / "results" / "corpus" / "corpus_per_screen.csv")
        check("cross-surface: the companion's screen count is the corpus's",
              _ref["n_screens"] == len(_corpus),
              f"page {_ref['n_screens']} vs corpus {len(_corpus)}")
        # The design-time projection must never present itself as a prediction.
        # This is the one claim on that page that would be actively harmful if it
        # drifted, because a planner would act on it before spending money.
        _txt = screen_html.read_text()
        check("cross-surface: the design-time floor refuses to predict a "
              "single screen",
              "cannot tell you where your screen" in _txt
              and "0.0935" in _txt,
              "the projection must cite evaluation 13's negative as the reason "
              "it shows a range rather than a number")

    # ---- the atlas must not drift from the corpus it summarises ------------
    # Same discipline as audit.html: the generated module is regenerated here
    # and the committed one must match, so a corpus edit that never reaches the
    # shipped atlas is a red build rather than a citation that means two things.
    atlas_py = ROOT / "packages" / "denali-audit" / "denali_audit" / "atlas.py"
    if atlas_py.exists():
        sys.path.insert(0, str(ROOT))
        import importlib
        _ba = importlib.import_module("src.build_atlas")
        check("cross-surface: atlas.py carries the CURRENT corpus",
              _ba.build() == atlas_py.read_text(),
              "stale — run: .venv/bin/python -m src.build_atlas")
        import hashlib as _hl
        _csv = ROOT / "results" / "corpus" / "corpus_per_screen.csv"
        _want = _hl.sha256(_csv.read_bytes()).hexdigest()
        check("cross-surface: the hash the atlas tells people to cite is the "
              "hash of the table it came from",
              f'SOURCE_SHA256 = {_want!r}' in atlas_py.read_text(),
              f"expected {_want[:16]}")

    for p in passed:
        print(f"PASS  {p}")
    for f in failed:
        print(f"FAIL  {f}")
    print(f"\n{len(passed)}/{len(passed) + len(failed)} cross-surface checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
