"""Evaluation 12 — the literature arm read rather than grepped.

Pre-registered in docs/LITERATURE_INFER_PREREG.md, sha256 cd8252ff... at commit
ae63e18, sealed BEFORE any paper was classified. Correction 1 is appended to that
file and was also written before the first label existed: `paperclip map` is
gated to testers on this account and `paperclip cat` truncates at ~1000
characters, so the classifier reads broad-recall `scan` context windows rather
than whole documents. That bounds recall and the correction says so.

WHAT THIS ARM IS. Evaluation 11 asked whether 111 publications MENTION set size,
with `grep -i -c -e` over thirteen patterns, and its own output says a match is
evidence of mention and not of handling. This asks the question that one could
not: did the paper DO anything -- adjust for it, or measure it.

WHAT IT IS NOT. Not a claim that any adjustment was CORRECT, only that it was
made. Not reproducible by re-running: the index moves and a model is not a pure
function. It is reproducible from the committed cache, which is the point of
committing it.

    .venv/bin/python -m src.literature_infer

Reads results/literature_infer/labels_pass*.json (the committed cache) and
results/literature/literature_audit.json (evaluation 11, for the comparison).
Writes results/literature_infer/literature_infer.json. NEVER writes
results/frozen/.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "literature_infer"
REGEX_ARM = ROOT / "results" / "literature" / "literature_audit.json"

# --- FIXED IN THE PRE-REGISTRATION. Do not edit after seeing a value. --------
ACTED_LABELS = ("ADJUSTS", "MEASURES")
CLAIM_A_THRESHOLD = 0.25      # at or above: our framing is materially wrong
CLAIM_B_FLOOR = 0.08
BAND_REFUSAL_WIDTH = 0.10     # wider than this: report the band, no point estimate
POSITIVE_CONTROLS = ("PMC7373179", "PMC5336655", "PMC2661051")
NEGATIVE_CONTROL_CEILING = 0.90
UNRETRIEVED_POWER_FLOOR = 20
# -----------------------------------------------------------------------------


def _load(name: str) -> dict[str, dict]:
    p = OUT / name
    if not p.exists():
        return {}
    return {r["id"]: r for r in json.loads(p.read_text())}


def main() -> int:
    p1 = _load("labels_pass1.json")
    p2 = _load("labels_pass2.json")
    if not p1:
        print("No cached labels in results/literature_infer/. This arm is a dated "
              "observation against a live index and is not part of `make all`; "
              "see docs/LITERATURE_INFER_PREREG.md for how it was produced.")
        return 0

    unretrieved = [k for k, v in p1.items() if v["label"] == "UNRETRIEVED"]
    scored = {k: v for k, v in p1.items() if v["label"] != "UNRETRIEVED"}
    n = len(scored)

    acted_p1 = {k for k, v in scored.items() if v["label"] in ACTED_LABELS}
    # Only positives were re-read, so a paper absent from pass 2 is one pass 1
    # did not call ACTED. The band is built from that asymmetry, not around it.
    acted_p2 = {k for k, v in p2.items() if v["label"] in ACTED_LABELS}

    both = acted_p1 & acted_p2
    either = acted_p1 | acted_p2
    lower, upper = len(both) / n, len(either) / n
    width = upper - lower

    ctrl = {c: (p1.get(c) or {}).get("label", "NOT_CLASSIFIED")
            for c in POSITIVE_CONTROLS}
    ctrl_ok = sum(1 for v in ctrl.values() if v in ACTED_LABELS)

    regex = json.loads(REGEX_ARM.read_text()) if REGEX_ARM.exists() else {}
    regex_union = regex.get("union_either_tier", {}).get("of_resolved")
    regex_tier_a = regex.get("tier_a_explicit_size", {}).get("of_resolved")

    # The pre-registered branches, evaluated on the LOWER bound -- the only one
    # the design earns, because papers pass 1 called NONE were never re-read.
    if ctrl_ok < len(POSITIVE_CONTROLS):
        verdict = "BROKEN — the positive controls did not classify as ACTED"
    elif lower > NEGATIVE_CONTROL_CEILING:
        verdict = "UNINFORMATIVE — the classifier agreed with the prompt"
    elif len(unretrieved) > UNRETRIEVED_POWER_FLOOR:
        verdict = "UNDERPOWERED — too few papers share evaluation 11's denominator"
    elif lower >= CLAIM_A_THRESHOLD:
        verdict = "CLAIM (a) — our framing is materially wrong"
    elif lower >= CLAIM_B_FLOOR:
        verdict = "CLAIM (b) — the regex undercounted but the picture holds"
    else:
        verdict = "CLAIM (c) — the regex was roughly right"

    counts: dict[str, int] = {}
    for v in p1.values():
        counts[v["label"]] = counts.get(v["label"], 0) + 1

    out = {
        "arm": "evaluation 12 — the literature arm, read rather than grepped",
        "prereg": ("docs/LITERATURE_INFER_PREREG.md, sha256 cd8252ff..., commit "
                   "ae63e18, sealed before any paper was classified. Correction 1 "
                   "appended before the first label existed."),
        "question": ("Of the publications behind the corpus arm's screens, what "
                     "fraction DID anything about gene-set size — adjusted for it "
                     "or measured it — rather than merely mentioning it?"),
        "n_in_population": len(p1),
        "n_unretrieved": len(unretrieved),
        "n_scored": n,
        "label_counts_pass1": counts,
        "acted_band": {
            "lower": round(lower, 4),
            "upper": round(upper, 4),
            "width": round(width, 4),
            "n_lower": len(both),
            "n_upper": len(either),
            "rule": ("lower = both models called it ACTED; upper = either did. "
                     "Never averaged, never broken by a third vote."),
            "point_estimate_withheld": bool(width > BAND_REFUSAL_WIDTH),
        },
        "verdict": verdict,
        "second_pass": {
            "n_re_read": len(p2),
            "n_confirmed": len(both),
            "n_overturned": len(acted_p1 - acted_p2),
            "asymmetry": ("Only pass-1 positives were re-read. A paper pass 1 "
                          "wrongly called NONE is never rescued, so the LOWER "
                          "bound is a genuine lower bound and the UPPER bound is "
                          "not a genuine upper bound."),
        },
        "against_the_regex_arm": {
            "regex_tier_a_of_resolved": regex_tier_a,
            "regex_union_either_tier_of_resolved": regex_union,
            "model_acted_lower": round(lower, 4),
            "model_acted_upper": round(upper, 4),
            "note": ("The two arms measure DIFFERENT things and the gap is not a "
                     "correction of one by the other. The regex counted MENTION "
                     "over thirteen patterns; this counts ACTION over a wider "
                     "recall set read in context. A paper can mention and not act, "
                     "or act and never use a matched word."),
        },
        "positive_control": {
            "docs": ctrl, "n_acted": ctrl_ok, "required": len(POSITIVE_CONTROLS)},
        "what_this_does_not_show": (
            "That any adjustment was CORRECT. This arm establishes that a method "
            "accounting for set size was used or that its effect was quantified, "
            "not that either was done well. That is evaluation 11's limitation "
            "moved one step out, and this arm does not fix it."),
        "recall_bound": (
            "The classifier read context windows returned by a 25-term recall "
            "pattern set, not whole documents — paperclip's parallel LLM reader is "
            "gated on this account and its `cat` truncates near 1000 characters. "
            "A paper that adjusts in language none of the 25 terms touches is "
            "still invisible. The window is much wider than evaluation 11's "
            "thirteen patterns and it is still a window."),
        "denominator_warning": (
            "Every fraction is a fraction of the publications evaluation 11 "
            "resolved in PubMed Central, not of the literature. Open access is "
            "not a random sample of publishing."),
        "scope": ("Aggregate counts only. No publication is named on any rendered "
                  "surface. Writes results/literature_infer/ only and never "
                  "results/frozen/: no headline changes because a model said so."),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "literature_infer.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({k: out[k] for k in
                      ("n_scored", "label_counts_pass1", "acted_band", "verdict")},
                     indent=2))
    print(f"\nwrote {(OUT / 'literature_infer.json').relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
