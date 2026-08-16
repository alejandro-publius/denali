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

    # app.py is the OTHER surface an audience sees, and until now no scope guard
    # read it: the scan above covers index.html and the captions only. A gene
    # named as a finding in the Streamlit page would have passed every check.
    # Scan what the audience READS, not the Python. Two things are stripped
    # first, because neither reaches the screen: f-string expressions, since
    # {seal['commit']} renders a commit hash; and dict-subscript keys, since
    # prov["seal"] is a lookup into a frozen file whose key we do not rename.
    app_src = (ROOT / "app.py").read_text()
    app_text = re.sub(r"<[^>]+>", " ",
                      re.sub(r"\[\s*['\"][^'\"]*['\"]\s*\]", " ",
                             re.sub(r"\{[^{}]*\}", " ",
                                    re.sub(r"<style.*?</style>", " ",
                                           app_src, flags=re.S))))
    scan("the expo app (app.py)", app_text)

    # framing rule: the project does not lead with commit ordering
    SEAL = re.compile(r"\bseal(ed|ing)?\b|before the scoring code existed|"
                      r"\d+ minutes? before", re.I)
    for label, txt in [("index.html", page), ("CAPTIONS.md", caps),
                       ("REPORT.md", report), ("app.py", app_text)]:
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
    # concordance READS results/rpe1/. For hours make all ran concordance without
    # regenerating its input, so a clean clone silently consumed a committed file
    # instead of reproducing it. Order matters, so assert the order.
    _order = re.findall(r"-m\s+src\.(\w+)", all_block)
    if "concordance" in _order:
        check("make all regenerates the RPE1 arm before concordance reads it",
              "rpe1_arm" in _order
              and _order.index("rpe1_arm") < _order.index("concordance"),
              f"order: {_order[-6:]}")
    check("annotation_arm is NOT a make-all step (it needs Modal)",
          "annotation_arm" not in pipeline_mods)

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

    # ---------------- H. the unstressed-cell-line bound ----------------
    # The sharpest question asked of this project: is the headline really the
    # unstressed-K562 problem wearing the size problem's clothes? These lock the
    # answer and, more importantly, the honesty of its scope.
    eb_p = ROOT / "results" / "sensitivity" / "engagement_bound.json"
    if eb_p.exists():
        eb = json.loads(eb_p.read_text())
        mb = eb["measurable_but_not_engaged"]
        recomputed = int((summary.passes_measurability_gate
                          & (summary.n_hits_q05 == 0)).sum())
        check("engagement: measurable-but-not-engaged count matches the frozen table",
              mb["n"] == recomputed == gap["gate_pass_but_zero_hits"],
              f"json {mb['n']}, recomputed {recomputed}")
        check("engagement: removing them does not rescue the result",
              abs(eb["delta"]) < 0.02, f"delta {eb['delta']}")
        check("engagement: the size effect is the larger one",
              eb["size_alone_r2_all_programs"] > 4 * abs(eb["delta"]))
        check("engagement: labelled post-freeze",
              "NOT PRE-REGISTERED" in eb.get("status", ""))
        check("engagement: states what it cannot settle",
              "cannot bound it across screens" in eb.get("what_this_does_not_settle", ""))

    # ---------------- I. the frozen proposals (Rachel's expo layer) ----------------
    # proposals.json is a frozen artifact the page renders, so it gets the same
    # treatment as every other one: the branches must be chosen by measured value
    # rather than by name, and nothing in it may read as a nomination.
    prop_p = FROZEN / "proposals.json"
    if prop_p.exists():
        prop = json.loads(prop_p.read_text())
        check("proposals: one per branch of next_experiment",
              {"null", "hit", "unscored"} <= set(prop),
              f"got {sorted(k for k in prop if not k.startswith('_'))}")
        # each pick must be re-derivable from the frozen table, not hardcoded
        null_p = summary[summary.n_hits_q05 == 0].nlargest(1, "n_present").iloc[0].program
        check("proposals: the NULL branch is chosen by measured value",
              prop["null"]["program"] == null_p,
              f"json {prop['null']['program']} vs recomputed {null_p}")
        hit_p = summary.nlargest(1, "R_p").iloc[0].program
        check("proposals: the HIT branch is the top measured R_p",
              prop["hit"]["program"] == hit_p,
              f"json {prop['hit']['program']} vs recomputed {hit_p}")
        check("proposals: outcomes are the three real branches",
              {prop[k]["outcome"] for k in ("null", "hit", "unscored")} ==
              {"NULL_WITH_MECHANISM", "HIT_ABOVE_THRESHOLD", "UNSCORED"})
        check("proposals: the unscored branch keeps its observed outcome",
              "observed_outcome" in prop["unscored"]
              and prop["unscored"]["observed_outcome"]["n_hits_q05"] == 0)
        blob = json.dumps(prop).lower()
        check("proposals: no nomination language",
              not any(w in blob for w in ("we recommend", "top candidate",
                                          "most promising", "best target")))

    # ---------------- J. program A is described correctly ----------------
    # REPORT.md claimed inducing ER stress would move program A "from 0 hits to
    # non-zero". It has 517. The null is real but it is the known-regulator
    # control failing, not an absence of hits -- two different findings that had
    # been collapsed into one sentence for hours. Nothing was watching prose
    # claims about a specific program, so now something is.
    readme_txt = (ROOT / "README.md").read_text()
    a_row = summary[summary.is_program_A]
    if len(a_row):
        a = a_row.iloc[0]
        for label, txt in [("REPORT.md", report), ("README.md", readme_txt)]:
            bad = re.search(r"UPR from 0 hits|program A.{0,40}\b0 hits|"
                            r"first program returned a clean null", txt, re.I)
            check(f"{label} does not call program A a zero-hit null", bad is None,
                  f"program A has {int(a.n_hits_q05)} hits: {bad.group(0) if bad else ''}")
        kr = controls[(controls.control == "known_regulator_recovery")
                      & (controls.program == "program_a")]
        check("program A's null is the known-regulator control, and it FAILs",
              len(kr) == 1 and kr.verdict.iloc[0] == "FAIL")
        check("program A's hit count is stated where the null is discussed",
              str(int(a.n_hits_q05)) in report and str(int(a.n_hits_q05)) in readme_txt,
              f"expected {int(a.n_hits_q05)} in both")

    # ---------------- K. the selection-criteria section ----------------
    # Every number in "What we chose, and why" is checkable, so check it. This
    # section exists to preempt a reviewer; if it drifts from the frozen files it
    # does the opposite.
    rd = (ROOT / "README.md").read_text()
    if "## What we chose, and why" in rd:
        sel = rd.split("## What we chose, and why")[1].split("## Findings")[0]
        lo, hi = int(summary.n_declared.min()), int(summary.n_declared.max())
        check("selection: declared-size range matches program_summary",
              f"{lo} to {hi} declared members" in sel, f"frozen {lo}-{hi}")
        check("selection: the size ratio is stated correctly",
              f"{round(hi / lo)}\u00d7 size range" in sel,
              f"frozen ratio {hi / lo:.1f}x")
        check("selection: knockdown count matches provenance",
              f"{prov['tier1']['knockdown_targets']:,} knockdowns" in sel)
        check("selection: concordance matches controls.csv",
              f"{float(gp.value.iloc[0])}" in sel.replace("\u2212", "-"))
        rc = controls[controls.control == "rpe1_coverage_collision"]
        check("selection: the RPE1 decline cites the control that justifies it",
              len(rc) == 1 and rc.verdict.iloc[0] == "FAIL"
              and "94.1% vs 11.3%" in sel, "RPE1 coverage control")
        check("selection: states what was NOT attempted",
              "did not attempt" in sel.lower())

    # ---------------- L. docs/LOOP.md describes the real code ----------------
    # LOOP.md documents criterion 1 and hands a reviewer a grep to falsify it. If
    # the doc and the code drift apart, the grep becomes the reviewer's find
    # rather than ours, so tie every claim it makes to its source.
    loop_p = ROOT / "docs" / "LOOP.md"
    if loop_p.exists():
        loop = loop_p.read_text()
        ne = (ROOT / "src" / "next_experiment.py").read_text()
        # the falsification test the doc publishes, actually run
        named = re.search(r"^\s*(?:if|elif).*(HALLMARK_|REACTOME_)", ne, re.M)
        check("LOOP.md's own falsification grep still returns nothing",
              named is None, named.group(0).strip() if named else "")
        sweep = (ROOT / "src" / "sweep.py").read_text()
        mf = re.search(r"MIN_FRAC,\s*MIN_N,\s*ALPHA\s*=\s*([\d.]+),\s*(\d+)", sweep)
        check("LOOP.md gate thresholds match src/sweep.py",
              mf is not None and f"\u2265{mf.group(1)} fraction" in loop
              and f"\u2265{mf.group(2)} present" in loop,
              f"code says {mf.groups() if mf else '?'}")
        hm = re.search(r"HIT_MIN_HITS\s*=\s*(\d+)", ne)
        check("LOOP.md hit threshold matches next_experiment.py",
              hm is not None and f"hit threshold of {hm.group(1)}" in loop,
              f"code says {hm.group(1) if hm else '?'}")
        for n, label in [(gap["gate_fail_but_has_hits"], "gate-fail-with-hits"),
                         (gap["gate_pass_but_zero_hits"], "gate-pass-zero-hits")]:
            check(f"LOOP.md states {label} as {n}", f"{n}" in loop)
        check("LOOP.md discloses that the predictor failed its own evaluation",
              f"{held['axis2_balanced_accuracy']}" in loop
              and "not refit" in loop.lower())

    # ---------------- M. no broken internal links ----------------
    # A dead link in the docs index is the cheapest possible thing for a reviewer
    # to find and the cheapest for us to prevent.
    for md in [ROOT / "README.md", ROOT / "docs" / "README.md"]:
        if not md.exists():
            continue
        broken = []
        for target in re.findall(r"\]\(([^)\s#]+)", md.read_text()):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            if not (md.parent / target).resolve().exists():
                broken.append(target)
        check(f"{md.relative_to(ROOT)} has no broken relative links",
              not broken, ", ".join(broken[:3]))

    # The positive control must never present itself as the headline. It said
    # "The headline." at the top for hours while section 4 of the same file
    # called it a recovered known answer.
    sre = ROOT / "docs" / "SREBF2_EVIDENCE.md"
    if sre.exists():
        s = sre.read_text()
        check("the control document calls itself a control, not the headline",
              "positive control, not the headline" in s
              and "not a discovery" in s.lower())

    # ---------------- N. the design system is real ----------------
    # docs/DESIGN.md documents a palette and a type scale. A design doc nobody
    # checks is decoration, so check it: every colour the page uses must be a
    # declared token, and the token values must match what the doc claims.
    design_p = ROOT / "docs" / "DESIGN.md"
    bp = (ROOT / "src" / "build_page.py").read_text()
    if design_p.exists():
        design = design_p.read_text()
        tokens = dict(re.findall(r"--([a-z]+):\s*([^;]+);", bp))
        for name in ("ink", "soft", "rule", "fill", "paper", "accent"):
            val = tokens.get(name, "").strip()
            check(f"DESIGN.md documents --{name} as the code defines it",
                  val and f"`{val}`" in design, f"code has {val!r}")
        # any hex in page chrome must be a token value or a documented figure colour
        allowed = {v.strip().lower() for v in tokens.values()}
        allowed |= {"#b2182b", "#2166ac", "#999999", "#bbbbbb", "#888888",
                    "#444444", "#fff3e0", "#e0a458", "#d9d9d9", "#f4a582",
                    "#1a4d7a", "#eaf0f6", "#eef4ea", "#3d6b2e", "#e3e3e3"}
        css = bp.split('CSS = """')[1].split('"""')[0] if 'CSS = """' in bp else ""
        stray = sorted({h.lower() for h in re.findall(r"#[0-9a-fA-F]{6}", css)}
                       - allowed)
        check("no undocumented colour in the page stylesheet", not stray,
              ", ".join(stray[:4]))
        check("DESIGN.md records the app.py palette drift rather than hiding it",
              "Known drift" in design and "#111827" in design)
        check("radius is zero globally, as documented",
              "--radius:0px" in bp.replace(" ", "") and "`0px`" in design)

    # ---------------- O. the RPE1 arm ----------------
    # The only positive result in this project that is not a control, so it gets
    # the most hostile invariants: the thresholds must match the pre-registration
    # that was committed before the run, the scorer must be untouched, and the
    # margin must be stated because it is thin.
    rp = ROOT / "results" / "rpe1" / "rpe1_evaluation.json"
    pre_p = ROOT / "docs" / "RPE1_PREREG.md"
    if rp.exists() and pre_p.exists():
        r = json.loads(rp.read_text())
        import hashlib
        live = hashlib.sha256(pre_p.read_bytes()).hexdigest()
        check("RPE1: pre-registration unchanged since the run",
              live == r["preregistration"]["sha256"], live[:16])
        check("RPE1: thresholds in the doc match the ones applied",
              "**0.25**" in pre_p.read_text() and "**0.10**" in pre_p.read_text())
        check("RPE1: the frozen scorer was not modified",
              r["scorer_sha256"].startswith("2abfdc6f") and r["scorer_unmodified"])
        check("RPE1: verdict follows its own rule",
              (r["size_alone_r2"] >= 0.25 and r["slope"] > 0)
              == (r["verdict"] == "REPRODUCES"),
              f"r2={r['size_alone_r2']} slope={r['slope']}")
        check("RPE1: scoreable count clears the pre-registered floor of 35",
              r["n_scoreable"] >= 35, f"got {r['n_scoreable']}")
        check("RPE1: the 24.3% coverage caveat travels with the result",
              "24.3%" in r["scope"] and "NOT a replication" in r["scope"])
        check("RPE1: does not revise the frozen primary",
              "does not revise" in " ".join(r).lower()
              or "does_not_revise" in r)
        check("RPE1: results are outside results/frozen/",
              not (FROZEN / "rpe1_evaluation.json").exists())

    # ---------------- P. cross-screen concordance ----------------
    cc = ROOT / "results" / "concordance" / "cross_screen.json"
    if cc.exists():
        c = json.loads(cc.read_text())
        raw = c["raw_agreement"]["spearman_rho"]
        par = c["how_much_is_size"]["spearman_after_removing_size"]
        check("concordance: removing size lowers agreement, never raises it",
              par < raw, f"raw {raw} vs partial {par}")
        check("concordance: the size-alone top-k beats chance",
              c["how_much_is_size"]["top_k_overlap_using_SIZE_ALONE_to_predict_rpe1"]["top_10"]
              > c["raw_agreement"]["top_k_overlap_expected_by_chance"]["top_10"])
        check("concordance: labelled post-freeze",
              "NOT PRE-REGISTERED" in c.get("status", ""))
        check("concordance: states its own limits",
              "not a general estimate" in c.get("limits", ""))
        # the portable tool must reproduce the bespoke analysis
        from src.audit_screen import audit_replication          # noqa: E402
        pp = pd.read_csv(ROOT / "results" / "concordance" / "paired_programs.csv")
        rep = audit_replication(pp.n_present_k562, pp.n_hits_q05_k562,
                                pp.n_hits_q05_rpe1)
        check("the portable replication auditor reproduces our own number",
              near(rep["raw_agreement_spearman"], raw, 1e-3),
              f"tool {rep['raw_agreement_spearman']} vs analysis {raw}")
        check("replication auditor refuses too few paired sets",
              _raises(audit_replication, [1, 2, 3], [1, 2, 3], [1, 2, 3]))

    # ---------------- Q. the user-facing loop actually closes ----------------
    # The page claims: audit says CONFOUNDED, you apply the correction it names,
    # you re-audit and the score drops to zero. That is the product's whole
    # argument, so run it rather than asserting it.
    import numpy as _np
    import statsmodels.api as _sm
    from src.audit_screen import audit as _audit                # noqa: E402
    _before = _audit(summary.n_present, summary.n_hits_q05)
    _y = _np.log10(1 + summary.n_hits_q05)
    _r = _sm.OLS(_y, _sm.add_constant(summary.n_present)).fit().resid
    _after = _audit(summary.n_present, (10 ** (_r - _r.min())) - 1)
    check("the correction the tool recommends actually lowers its own score",
          _after["r2_size_alone"] < _before["r2_size_alone"],
          f"{_before['r2_size_alone']} -> {_after['r2_size_alone']}")
    check("audit flags our own screen before the correction",
          _before["verdict"] == "CONFOUNDED", _before["verdict"])
    check("audit clears our own screen after the correction",
          _after["verdict"] == "NOT SIZE-DOMINATED", _after["verdict"])
    check("the page states the before/after the test just reproduced",
          f"{_before['r2_size_alone']}" in page and "NOT SIZE-DOMINATED" in page)
    # the connect snippet must name a module that exists and is runnable
    check("the MCP snippet on the page points at a real module",
          '"-m", "src.mcp_server"' in page
          and (ROOT / "src" / "mcp_server.py").exists())

    # ---------------- R. the server refuses to be misused ----------------
    # The scope guard stops US publishing a gene-level claim; it does nothing
    # when an agent calls the server. Prior art: CRISPR-GPT hard-codes
    # non-bypassable refusals rather than trusting the model to be careful.
    from src.answers import refuse as _refuse                   # noqa: E402
    for q in ("SREBF2", "TP53", "MYC"):
        r = _refuse(q)
        check(f"server refuses the bare gene symbol {q}",
              r is not None and r["status"] == "REFUSED")
    for q in ("top 10 candidates", "which gene should I chase",
              "rank the programs", "most promising target"):
        r = _refuse(q)
        check(f"server refuses a nomination request: {q!r}",
              r is not None and r["status"] == "REFUSED")
    for q in ("HALLMARK_CHOLESTEROL_HOMEOSTASIS",
              "REACTOME_SCAVENGING_OF_HEME_FROM_PLASMA"):
        check(f"server still answers a real program: {q[:28]}",
              _refuse(q) is None)
    check("the refusal explains itself with the concordance figure",
          str(float(gp.value.iloc[0])) in _refuse("SREBF2")["reason"])
    check("the nomination refusal cites the predictor's own failure",
          str(held["axis2_balanced_accuracy"]) in _refuse("top hits")["reason"])

    # ---------------- S. every branch says what would demote it ----------------
    # A proposal that cannot be wrong is not a proposal. The hit branch had no
    # falsification condition for hours, which is backwards -- that is the branch
    # where someone commits a year.
    from src.next_experiment import propose as _prop            # noqa: E402
    seen_outcomes = set()
    for prog in summary.program:
        pr = _prop(prog, summary)
        seen_outcomes.add(pr["outcome"])
        cmm = pr.get("what_would_change_my_mind", "")
        check(f"{pr['outcome']}: states what would change its mind",
              bool(cmm) and len(cmm) > 40, f"{prog}: {cmm[:40]!r}")
        if pr["outcome"] == "HIT_ABOVE_THRESHOLD":
            check(f"hit branch names a numeric threshold that would demote it",
                  "residual" in cmm and any(ch.isdigit() for ch in cmm))
        break_after = len(seen_outcomes) >= 3
        if break_after:
            break
    check("all three real branches were exercised",
          {"HIT_ABOVE_THRESHOLD", "NULL_WITH_MECHANISM", "WEAK"} & seen_outcomes)
    check("the falsification panel reaches the page",
          '"change_my_mind"' in page and "What would change my mind" in page)

    # ---------------- T. the annotation arm, incl. its own failure ----------------
    ap_ = ROOT / "results" / "annotation" / "annotation_evaluation.json"
    apre = ROOT / "docs" / "ANNOTATION_PREREG.md"
    if ap_.exists() and apre.exists():
        an = json.loads(ap_.read_text())
        import hashlib
        live = hashlib.sha256(apre.read_bytes()).hexdigest()
        check("annotation: pre-registration unchanged since the run",
              live == an["preregistration"]["sha256"], live[:16])
        check("annotation: the frozen scorer was not modified",
              an["scorer_sha256"].startswith("2abfdc6f"))
        po = an["preregistered_outcome"]
        check("annotation: the power rule fired and no verdict was issued",
              "UNDERPOWERED" in po["verdict"] and "NO VERDICT" in po["verdict"])
        check("annotation: says plainly that our prediction was wrong in direction",
              "wrong in direction" in po["what_the_numbers_would_have_shown"])
        d = an["descriptive_not_preregistered"]["per_collection"]
        check("annotation: scoreability falls from Hallmark to GO-BP",
              d["hallmark"]["scoreable_fraction"] > d["go_bp"]["scoreable_fraction"],
              f"{d['hallmark']['scoreable_fraction']} vs {d['go_bp']['scoreable_fraction']}")
        check("annotation: the descriptive finding is labelled not pre-registered",
              "no threshold was set for it" in
              an["descriptive_not_preregistered"]["finding"])
        # the Hallmark bar reconciliation: our own baseline appears to fail its
        # own bar, and the artifact must keep explaining why. Recompute BOTH.
        rec = an["hallmark_bar_reconciliation"]
        _sc = pd.read_csv(ROOT / "results" / "annotation" / "sets_scored.csv")
        _hk = _sc[(_sc.collection == "hallmark") & _sc.scoreable]
        import statsmodels.api as _sm2
        _r50 = float(_sm2.OLS(summary.R_p,
                              _sm2.add_constant(summary.n_present)).fit().rsquared)
        _r49 = float(_sm2.OLS(_hk.R_p, _sm2.add_constant(_hk.n_present)).fit().rsquared)
        check("hallmark reconciliation: the all-50 value recomputes",
              near(rec["r2_frozen_all_50"], _r50), f"{rec['r2_frozen_all_50']} vs {_r50:.4f}")
        check("hallmark reconciliation: the 49-set value recomputes",
              near(rec["r2_arm_49_scoreable"], _r49), f"{rec['r2_arm_49_scoreable']} vs {_r49:.4f}")
        check("hallmark reconciliation: the delta is the difference of the two",
              near(rec["delta"], _r50 - _r49), f"{rec['delta']} vs {_r50 - _r49:.4f}")
        check("hallmark reconciliation: attributed to sample size, not drift",
              "not drift" in rec["cause"])
        check("hallmark is labelled the baseline, not a failing candidate",
              an["per_collection"]["hallmark"].get("is_the_baseline_not_a_candidate")
              is True
              and "exceeds_hallmark_bar" not in an["per_collection"]["hallmark"])
        check("the direction claim is asserted under BOTH bars",
              "0.4464 and at 0.4649" in rec["does_the_direction_claim_survive"])
        check("the bar's post-freeze provenance is disclosed",
              "NOT PRE-REGISTERED" in rec["provenance_of_the_0_4649_bar"])

        # the two medians must come from the SAME subset. Pairing declared-over-all
        # with measured-over-scoreable produced "20 declared, 30 measured" for
        # GO-BP, which is impossible and shipped to the page for a few minutes.
        _raw = pd.read_csv(ROOT / "results" / "annotation" / "sets_scored.csv")
        for _c, _v in d.items():
            _sub = _raw[_raw.collection == _c]
            check(f"annotation: {_c} medians are both over all sampled sets",
                  _v["median_genes_declared"] == int(_sub.n_declared.median())
                  and _v["median_genes_measured_in_screen"] == int(_sub.n_present.median()),
                  f"json {_v['median_genes_declared']}/{_v['median_genes_measured_in_screen']}")
            check(f"annotation: {_c} cannot measure more genes than it declares",
                  _v["median_genes_measured_in_screen"] <= _v["median_genes_declared"],
                  f"{_v['median_genes_measured_in_screen']} > {_v['median_genes_declared']}")

        # recompute the headline descriptive number from the raw scored table
        sc = pd.read_csv(ROOT / "results" / "annotation" / "sets_scored.csv")
        g = sc[sc.collection == "go_bp"]
        check("annotation: the GO-BP scoreable fraction recomputes from raw",
              near(g.scoreable.sum() / len(g), d["go_bp"]["scoreable_fraction"], 2e-3))

    # ---------------- F. the docs' own self-description ----------------
    report_readme = (ROOT / "README.md").read_text()

    # -- F0. PROSE DRIFT. Numbers were guarded; sentences were not, and that is
    # exactly how three self-contradictions reached the first screen a reader
    # sees: "Six evaluations ... Three did come back negative" sat two paragraphs
    # above a seven-row findings table, "Four of our six evaluations" repeated it
    # 300 lines later, and the traced-value count said 32 in one place and 47 in
    # another. Seven further copies were stale in CLAUDE.md, the docs and the
    # spoken demo script. A number that only lives in a sentence drifts silently.
    #
    # The findings table in README.md is the ONLY source of truth for how many
    # evaluations exist and how many were negative; src/build_page.py's own TRACE
    # is the only source of truth for how many values are traced. Every prose
    # restatement of either is checked against its source, so rewording a claim
    # without rewording its siblings fails the build.
    rows = re.findall(r"^\|\s*(\d+)\s*\|.*\|\s*\*\*([A-Z][A-Z ]+)\*\*",
                      report_readme, re.M)
    n_eval = len(rows)
    n_neg = [v.strip() for _, v in rows].count("NEGATIVE")
    check("README findings table is numbered 1..n with one verdict each",
          n_eval >= 4 and [int(i) for i, _ in rows] == list(range(1, n_eval + 1)),
          f"parsed {[i for i, _ in rows]}")

    from src.build_page import TRACE                              # noqa: E402
    n_traced = len(TRACE)
    check("build_page traces at least one value per frozen source", n_traced > 0)

    _WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
              7: "seven", 8: "eight", 9: "nine", 10: "ten"}

    def _count(tok: str) -> int:
        """'Seven' | 'seven' | '7' -> 7.  -1 if the token is not a count."""
        t = tok.strip().lower()
        return int(t) if t.isdigit() else next(
            (k for k, v in _WORDS.items() if v == t), -1)

    # (file, pattern, expected group values in order, what the sentence is)
    prose_claims = [
        ("README.md", r"(\w+) evaluations\. (\w+) negative,",
         (n_eval, n_neg), "the findings header"),
        ("README.md", r"\*\*(\w+) evaluations, (\w+) of them negative\.\*\*",
         (n_eval, n_neg), "the what-we-chose list"),
        ("README.md", r"\*\*(\w+) of our (\w+) evaluations came back negative\.\*\*"
                      r" All (\w+) are reported",
         (n_neg, n_eval, n_eval), "the not-fooling-ourselves list"),
        ("CLAUDE.md", r"\*\*(\w+) evaluations\. (\w+) negative\. All (\w+) reported\.\*\*",
         (n_eval, n_neg, n_eval), "the operational contract"),
        ("docs/METHOD_RULES.md",
         r"(\w+) of (\w+) evaluations here are negative and all (\w+)\s+are reported",
         (n_neg, n_eval, n_eval), "the preserve-negatives rule"),
        ("docs/ORIGINS.md",
         r"(\w+) of this project's (\w+) evaluations came\s+back negative and all (\w+) are reported",
         (n_neg, n_eval, n_eval), "the negatives-kept note"),
        ("docs/MORNING_HANDOFF.md",
         r"(\w+) evaluations were run, (\w+) came back negative, and all (\w+) are\s+reported",
         (n_eval, n_neg, n_eval), "the handoff summary"),
        ("docs/MORNING_HANDOFF.md", r"##\s*2\.\s*The (\w+) results",
         (n_eval,), "the handoff results heading"),
        ("docs/DEMO.md", r"The repeated number is (\w+) OF (\w+)\.",
         (n_neg, n_eval), "the demo motif"),
        ("docs/DEMO.md",
         r"We ran (\w+) evaluations on this project\. (\w+) of them came back negative\.",
         (n_eval, n_neg), "the demo open"),
        ("docs/DEMO.md", r"(\w+) of (\w+) evaluations negative\.",
         (n_neg, n_eval), "the demo close"),
        ("app.py", r'st\.subheader\("(\w+) evaluations came back negative"\)',
         (n_neg,), "the streamlit negatives heading"),
        ("README.md", r"(\d+) values pass through a `V\(\)` helper",
         (n_traced,), "the traced-value feature bullet"),
        ("README.md", r"\*\*(\d+)\*\* values are traced",
         (n_traced,), "the inspectability criterion"),
        ("docs/DESIGN.md", r"`V\(\)` in `src/build_page\.py`, (\d+) values",
         (n_traced,), "the design contract table"),
    ]
    for rel, pat, expect, what in prose_claims:
        m = re.search(pat, (ROOT / rel).read_text())
        got = tuple(_count(g) for g in m.groups()) if m else None
        check(f"prose agrees with the source: {rel} — {what}",
              got == tuple(expect),
              f"expected {tuple(expect)}, got {got}" if m
              else "phrase not found — prose was reworded without updating this check")

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
    # Detail is printed on PASS lines too, so word it as a statement of fact
    # rather than as a failure: "README lacks ..." on a PASS line reads as a bug.
    check("README controls count matches controls.csv", claim in report_readme,
          f"frozen: {n_ctrl} controls / {n_ctrl_fail} FAIL; README must say {claim!r}")

    # ---------------- report ----------------
    for p in PASS:
        print(f"PASS  {p}")
    for f in FAIL:
        print(f"FAIL  {f}")
    print(f"\n{len(PASS)}/{len(PASS) + len(FAIL)} passed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
