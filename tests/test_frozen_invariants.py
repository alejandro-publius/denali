"""Invariants over results/frozen/. Not biology — these lock the facts every
claim in this repository rests on, so a silent change fails loudly instead of
producing a confidently wrong page.

    .venv/bin/python tests/test_frozen_invariants.py     # or: make test

Three classes of check:
  A  the frozen numbers are what we say they are
  B  every headline number in REPORT.md and the page traces to a frozen file
  C  the scope rule -- no novel gene named -- enforced by scanning the rendered
     text rather than trusted to memory
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / "results" / "frozen"
FIGS = ROOT / "results" / "figures"
PASS: list[str] = []
FAIL: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    (PASS if cond else FAIL).append(f"{name}{'  --  ' + detail if detail else ''}")


def near(a: float, b: float, tol: float = 5e-4) -> bool:
    return abs(float(a) - float(b)) <= tol


def _raises(fn, *args) -> bool:
    """True if fn refuses the input. A guard that never fires is not a guard."""
    try:
        fn(*args)
        return False
    except Exception:
        return True


def html_unescape_contains(page: str, s: str) -> bool:
    """The page escapes its embedded JSON, so compare against the escaped form."""
    from html import escape
    return s in page or escape(s) in page or escape(s).replace("&#x27;", "'") in page


# --------------------------------------------------------------------------
def main() -> int:
    prov = json.loads((FROZEN / "provenance.json").read_text())
    held = json.loads((FROZEN / "heldout_evaluation.json").read_text())
    pred = json.loads((FROZEN / "predictor.json").read_text())
    sens = json.loads((ROOT / "results" / "sensitivity" / "stripped_model.json").read_text())
    summary = pd.read_csv(FROZEN / "program_summary.csv")
    controls = pd.read_csv(FROZEN / "controls.csv")
    ds = prov["deciding_statistic"]
    gap = prov["gap_numbers"]

    # ---------------- 0. every shipped module must at least parse ----------------
    for f in sorted((ROOT / "src").glob("*.py")) + sorted((ROOT / "tests").glob("*.py")):
        try:
            compile(f.read_text(), str(f), "exec")
            okc, err = True, ""
        except SyntaxError as e:
            okc, err = False, f"line {e.lineno}: {e.msg}"
        check(f"{f.relative_to(ROOT)} parses", okc, err)

    # ---------------- A. the frozen numbers ----------------
    m = pd.read_csv(FROZEN / "matrix.csv", index_col=0)
    check("matrix.csv is 9,837 x 50", m.shape == (9837, 50), f"got {m.shape}")
    check("program_summary has 50 rows", len(summary) == 50, f"got {len(summary)}")

    check("adj R2 all six = 0.751", near(ds["adjusted_r2_all_six"], 0.7511),
          f"got {ds['adjusted_r2_all_six']}")
    check("adj R2 outcome-independent = 0.561",
          near(ds["adjusted_r2_x_independent_only"], 0.5606),
          f"got {ds['adjusted_r2_x_independent_only']}")
    check("program size alone explains 0.4649",
          near(sens["set_size_alone"]["r2"], 0.4649),
          f"got {sens['set_size_alone']['r2']}")
    check("post-freeze: measurement-only collapses to 0.152",
          near(sens["measurement_only_three"]["adj_r2"], 0.152),
          f"got {sens['measurement_only_three']['adj_r2']}")
    check("post-freeze: construction-only reaches 0.697",
          near(sens["construction_only_three"]["adj_r2"], 0.6965),
          f"got {sens['construction_only_three']['adj_r2']}")

    # the gate. NOTE 30 programs FAIL the gate; the "wrong 20 times" claim is the
    # 20 that fail it and still produce hits. These are different numbers.
    check("30 of 50 programs fail the measurability gate",
          gap["programs_failing_measurability_gate"] == 30,
          f"got {gap['programs_failing_measurability_gate']}")
    check("the gate is wrong 20 of 50 (fails but produces hits)",
          gap["gate_fail_but_has_hits"] == 20, f"got {gap['gate_fail_but_has_hits']}")
    check("exactly 1 of 50 passes the gate with zero hits",
          gap["gate_pass_but_zero_hits"] == 1, f"got {gap['gate_pass_but_zero_hits']}")
    check("11 of 50 programs return zero hits",
          gap["programs_with_zero_hits"] == 11, f"got {gap['programs_with_zero_hits']}")

    check("held-out balanced accuracy = 0.4375",
          near(held["axis2_balanced_accuracy"], 0.4375),
          f"got {held['axis2_balanced_accuracy']}")
    check("held-out has ZERO true positives",
          held["axis2_confusion"]["tp"] == 0, f"got {held['axis2_confusion']['tp']}")
    check("held-out Spearman rho = +0.526", near(held["axis1_spearman_rho"], 0.5257),
          f"got {held['axis1_spearman_rho']}")
    check("held-out verdict is UNDERPOWERED (1 of 10 passed the gate)",
          held["underpowered_and_inconclusive"] is True and held["n_passing_gate"] == 1,
          f"gate-passing {held['n_passing_gate']}")
    check("held-out was NOT refit", held["refit_after_seeing_results"] is False)

    ess = ds["coefficients"]["essentiality_density"]
    essp = ds["pvalues"]["essentiality_density"]
    check("essentiality coefficient is -0.021 (NEGATIVE, magnitude 0.021)",
          near(ess, -0.0206, 1e-3), f"got {ess}")
    check("essentiality p = 0.90", near(essp, 0.898, 5e-3), f"got {essp}")

    gp = controls[controls.control == "guide_pair_concordance"]
    check("guide-pair concordance control exists", len(gp) == 1)
    if len(gp):
        check("guide-pair concordance = -0.019", near(float(gp.value.iloc[0]), -0.019),
              f"got {gp.value.iloc[0]}")
    check("4 of 7 controls are FAIL and they are kept",
          int((controls.verdict == "FAIL").sum()) == 4,
          f"got {(controls.verdict=='FAIL').sum()}")

    check("scorer unchanged from the run that produced these numbers",
          prov["seal"].get("scorer_unchanged", prov["seal"].get("seal_intact")) is True)
    check("predictor was frozen before the held-out set was opened",
          pred["frozen_before_heldout_opened"] is True)
    check("held-out evaluation used the frozen predictor",
          held["predictor_sha256"].startswith("610f2a75"),
          held["predictor_sha256"][:16])

    # ---------------- B. docs trace to frozen files ----------------
    report = (ROOT / "REPORT.md").read_text()
    page = (ROOT / "index.html").read_text()
    check("index.html is standalone (figures inlined as base64)",
          "base64," in page, "figures must be embedded, not linked")
    # The page is now interactive. The constraint that matters at an expo is not
    # "no controls" but "nothing that can fail unattended" -- so: no network.
    for pat, label in [(r"\bfetch\s*\(", "fetch()"),
                       (r"XMLHttpRequest", "XMLHttpRequest"),
                       (r"<script[^>]+src=", "external script"),
                       (r'src="https?://', "remote asset"),
                       (r'<link[^>]+href="https?://', "remote stylesheet")]:
        check(f"page makes no network call: {label}",
              not re.search(pat, page, re.I))
    check("explorer data is embedded, not fetched", "const DATA = [" in page)
    check("all 50 programs embedded in the explorer",
          page.count('"program":"HALLMARK_') == 50,
          f"got {page.count(chr(34) + 'program' + chr(34) + ':' + chr(34) + 'HALLMARK_')}")
    check("gate-fail-with-hits rows match provenance",
          page.count('"gate_fail_with_hits":true') == gap["gate_fail_but_has_hits"],
          f"page {page.count(chr(34)+'gate_fail_with_hits'+chr(34)+':true')} vs frozen {gap['gate_fail_but_has_hits']}")
    caps = (FIGS / "CAPTIONS.md").read_text()
    both = report + page + caps

    traced = {
        "0.751": ds["adjusted_r2_all_six"], "0.561": ds["adjusted_r2_x_independent_only"],
        "46.5": round(sens["set_size_alone"]["r2"] * 100, 1),
        "0.4375": held["axis2_balanced_accuracy"],
        "0.152": sens["measurement_only_three"]["adj_r2"],
        "0.697": sens["construction_only_three"]["adj_r2"],
    }
    for text, frozen in traced.items():
        present = text in both
        matches = near(float(text), float(frozen), 6e-3) or \
            near(float(text) / 100, float(frozen), 6e-3)
        check(f"'{text}' in docs traces to a frozen value", present and matches,
              f"in docs={present} frozen={frozen}")

    # docs use a Unicode minus; the CSVs use an ASCII hyphen. Normalise both.
    norm = lambda x: x.replace("\u2212", "-").replace("\u2013", "-")
    for n in ["9,837", "20 of 50", "-0.019", "0.4375"]:
        check(f"headline '{n}' appears in REPORT.md", norm(n) in norm(report))

    # ---------------- C. the scope rule, enforced ----------------
    # No NOVEL gene may be named. A known gene may appear only as a recovered
    # known answer. Scan the page text and the captions for gene symbols sitting
    # next to verdict language.
    gmt = ROOT / "data" / "genesets" / "h.all.v2026.1.Hs.symbols.gmt"
    universe = set()
    for line in gmt.read_text().splitlines():
        universe.update(line.split("\t")[2:])
    universe = {g for g in universe if len(g) >= 4}          # avoid 2-3 char noise

    VERDICT = re.compile(
        r"\b(novel|discover\w*|candidate|nominat\w*|new target|we found|"
        r"identif\w+|driver|our (?:hit|target)|promising)\b", re.I)
    ALLOWED = re.compile(
        r"(recovered known answer|textbook|not claim\w*|do not claim|"
        r"positive control|control,? not|known regulator|canonical)", re.I)

    def scan(label: str, text: str) -> None:
        hits = []
        for g in universe:
            for mt in re.finditer(rf"\b{re.escape(g)}\b", text):
                w = text[max(0, mt.start() - 260): mt.end() + 260]
                if VERDICT.search(w) and not ALLOWED.search(w):
                    hits.append(f"{g}: …{w[230:330].strip()}…")
        check(f"scope rule: no gene named as a finding in {label}", not hits,
              hits[0] if hits else "")

    # page text = the literal strings app.py renders
    page_text = re.sub(r"<[^>]+>", " ", re.sub(r"<style.*?</style>|<img[^>]*>", " ", page, flags=re.S))
    scan("the page (index.html)", page_text)
    scan("results/figures/CAPTIONS.md", caps)

    # framing rule: the project does not lead with commit ordering
    SEAL = re.compile(r"\bseal(ed|ing)?\b|before the scoring code existed|"
                      r"\d+ minutes? before", re.I)
    for label, txt in [("index.html", page), ("CAPTIONS.md", caps),
                       ("REPORT.md", report)]:
        hit = SEAL.search(txt)
        check(f"no seal framing in {label}", hit is None,
              txt[max(0, hit.start()-60):hit.end()+60].replace("\n", " ") if hit else "")

    # The seal guard above scans rendered TEXT. Two figures had "SEALED program"
    # drawn into the PNG, where no text scan can reach it -- the guard passed for
    # weeks while the framing sat in the two most prominent images on the page.
    # Pixels cannot be scanned, so scan the code that draws them.
    figsrc = (ROOT / "src" / "figures_matrix.py").read_text()
    for m in re.finditer(r'["\']([^"\']*)["\']', figsrc):
        if SEAL.search(m.group(1)):
            check("no seal framing baked into a figure label", False, m.group(1)[:70])
            break
    else:
        check("no seal framing baked into a figure label", True)
    check("figure inputs are in-repo, not absolute paths",
          not re.search(r'Path\(\s*["\']/', figsrc),
          "an absolute path breaks make all on every other machine")

    check("scope limit is stated on the page", "-0.019" in page or "\u22120.019" in page)
    check("scope limit is stated in the captions",
          "gene-level" in caps or "0.019" in caps or "pointer layer" in caps)

    # ---------------- D. the tool-chain strip ----------------
    # The page says the callable surface reports its own failure verbatim. That
    # is only true if the page and the server read the same string object, so
    # check the object, not a lookalike substring.
    sys.path.insert(0, str(ROOT))
    from src.answers import SCOPE, VALIDATION, unscored          # noqa: E402
    wire = unscored("HALLMARK_A_PROGRAM_WE_NEVER_SCORED", pred["residual_sd"])
    for label, s in [("predictor_validation", VALIDATION), ("scope_limit", SCOPE)]:
        check(f"page quotes the server's {label} verbatim",
              html_unescape_contains(page, s), s[:52] + "\u2026")
    check("the server volunteers its failure unasked",
          wire["predictor_validation"] is VALIDATION and "worse than chance" in VALIDATION)
    check("the wire example carries the frozen balanced accuracy",
          f"{held['axis2_balanced_accuracy']:.4f}" in VALIDATION, VALIDATION)

    # "Touched a number" is a claim about this repository, so run the grep the
    # page invites a reviewer to run. Scope it to what `make all` actually runs:
    # src/modal_sweep.py imports modal by design, but it REPRODUCES the frozen
    # files rather than producing them, and it is deliberately not a make-all
    # step. That distinction is the whole claim, so assert it rather than
    # loosening the guard until it passes.
    mk = (ROOT / "Makefile").read_text()
    all_block = mk.split("all:")[1].split("\n\n")[0] if "all:" in mk else mk
    pipeline_mods = set(re.findall(r"-m\s+src\.(\w+)", all_block))
    check("make all runs a non-empty module list", len(pipeline_mods) >= 5,
          f"found {sorted(pipeline_mods)}")
    check("modal_sweep is NOT a make-all step (it verifies, it does not produce)",
          "modal_sweep" not in pipeline_mods)

    src_text = "\n".join((ROOT / "src" / f"{m}.py").read_text()
                         for m in sorted(pipeline_mods)
                         if (ROOT / "src" / f"{m}.py").exists())
    for tool in ["modal", "esm", "benchflow", "benchling", "paperclip"]:
        used = re.search(rf"^\s*(?:import|from)\s+{tool}\b", src_text, re.I | re.M)
        check(f"no make-all module imports {tool} -- 'touched a number: no' holds",
              used is None, used.group(0).strip() if used else "")

    # ---------------- E. the post-freeze VIF check ----------------
    # Verified twice by independent implementations; these lock the values and
    # the framing. The check must never present itself as pre-registered, and
    # log-VIF must only ever be compared to the UPPER bound -- it inherits
    # coherence's partial circularity.
    vif_p = ROOT / "results" / "sensitivity" / "vif_camera.json"
    if vif_p.exists():
        vif = json.loads(vif_p.read_text())
        a = vif["adj_r2"]
        check("VIF: log-VIF alone = 0.726", near(a["log_vif_alone"], 0.7257),
              f"got {a['log_vif_alone']}")
        check("VIF: all-six reference matches the frozen headline",
              near(a["all_six_features"], ds["adjusted_r2_all_six"], 1e-3),
              f"{a['all_six_features']} vs frozen {ds['adjusted_r2_all_six']}")
        check("VIF: coherence-flattened bound = 0.463",
              near(a["vif_coherence_flattened"], 0.4629),
              f"got {a['vif_coherence_flattened']}")
        check("VIF: labelled post-freeze, not pre-registered",
              "NOT PRE-REGISTERED" in vif.get("status", ""))
        check("VIF: circularity comparison rule is stated",
              "UPPER bound" in vif.get("comparison_rule", ""))
        check("VIF: does not claim to replace the primary",
              "pre-registered primary" in vif.get("does_not_replace", ""))
        check("VIF: cites the external theory (Wu & Smyth 2012)",
              "10.1093/nar/gks461" in vif.get("citation", ""))

    # The Modal run's own claim is that it reproduces the frozen numbers. Do not
    # take its word for it either -- it writes a verdict and this reads it back.
    agree = ROOT / "results" / "modal" / "agreement.json"
    if agree.exists():
        a = json.loads(agree.read_text())
        check("Modal reproduced all 50 programs from the frozen result",
              a["reproduces_frozen"] and a["n_programs"] == 50
              and not a["mismatched_columns"], str(a.get("mismatched_columns")))

    # A frozen artifact with a timing field cannot be byte-compared across
    # machines, which is exactly what the reproduction check does.
    for jf in sorted(FROZEN.glob("*.json")):
        txt = jf.read_text()
        check(f"{jf.name} carries no wall-clock field",
              "wall_clock" not in txt and "elapsed" not in txt)

    # FIG 4 drew its lines in set-iteration order, so the same picture produced
    # different bytes per process. Both orderings must now be sorted.
    fm = (ROOT / "src" / "figures_matrix.py").read_text()
    check("fig4 sorts before drawing (no per-process PNG drift)",
          "sorted(gs)" in fm and "-len(kv[1]), kv[0]" in fm)

    # ---------------- G. the portable audit ----------------
    # audit_screen.py runs this project's check on somebody else's screen. It is
    # the only thing here that claims to generalise, so it is tested on data it
    # has never seen: two synthetic screens with known answers, one confounded by
    # construction and one clean. If it cannot tell those apart it is useless.
    from src.audit_screen import audit                          # noqa: E402
    rng = __import__("numpy").random.default_rng(20260815)
    sz = rng.integers(10, 300, 60)
    conf = audit(sz, (sz * rng.uniform(1.5, 3.0, 60)).astype(int))
    clean = audit(sz, rng.integers(0, 400, 60))
    check("audit flags a size-confounded screen", conf["verdict"] == "CONFOUNDED",
          f"r2={conf['r2_size_alone']}")
    check("audit clears a screen that is not size-driven",
          clean["verdict"] == "NOT SIZE-DOMINATED", f"r2={clean['r2_size_alone']}")
    check("audit reproduces our own frozen size-alone value",
          near(audit(summary.n_present, summary.n_hits_q05)["r2_size_alone"],
               sens["set_size_alone"]["r2"], 5e-3))
    check("audit refuses to rank or recommend",
          "not a candidate list" in conf["what_this_is_not"].lower()
          and not any("rank_" in k or k == "top" for k in conf))
    check("audit needs enough sets to say anything",
          _raises(audit, [10, 20, 30], [1, 2, 3]))

    # ---------------- F. the docs' own self-description ----------------
    report_readme = (ROOT / "README.md").read_text()
    # These are hand-typed and therefore drift: the badge said 84, the Tests
    # section said 84, and the plain-language section said 86, while the suite
    # was at 99. A judge who finds a stale test count stops trusting every other
    # number, so the suite now counts itself and checks what the README claims.
    total = len(PASS) + len(FAIL) + 4    # +4: the three below, plus the controls one
    for pat, label in [(r"badge/tests-(\d+)-", "the CI badge"),
                       (r"\*\*(\d+) assertions\*\*", "the Tests section"),
                       (r"\*\*(\d+) automated checks\*\*", "the plain-language section")]:
        m = re.search(pat, report_readme)
        stated = int(m.group(1)) if m else -1
        check(f"README test count in {label} matches the suite",
              stated == total, f"says {stated}, suite has {total}")

    # Same failure mode, different number: controls.csv is the only truth.
    n_ctrl, n_ctrl_fail = len(controls), int((controls.verdict == "FAIL").sum())
    words = {3: "three", 4: "four", 5: "five", 6: "six", 7: "Seven", 8: "eight"}
    claim = (f"**{words[n_ctrl]} controls with published outcomes, "
             f"{words[n_ctrl_fail]} of them failing**")
    check("README controls count matches controls.csv", claim in report_readme,
          f"frozen: {n_ctrl} controls / {n_ctrl_fail} FAIL; README lacks {claim!r}")

    # ---------------- report ----------------
    for p in PASS:
        print(f"PASS  {p}")
    for f in FAIL:
        print(f"FAIL  {f}")
    print(f"\n{len(PASS)}/{len(PASS) + len(FAIL)} passed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
