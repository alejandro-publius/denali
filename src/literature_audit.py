"""Evaluation 11 — do the publications behind the corpus arm discuss set size?

Pre-registered in docs/LITERATURE_PREREG.md, sha256 165d91a2..., committed at
b0c5e35 BEFORE this file produced anything. Search terms, both tiers, the power
rule and both branches of the claim were fixed there and are read from here
unchanged.

The corpus arm measured 1,272 screens from 187 publications and found a field
median size-confound of 0.224. It could not ask whether the field knows. This
asks that, and only that.

Writes results/literature/ only. Never touches results/frozen/.

    .venv/bin/python -m src.literature_audit

Live index: Paperclip over PubMed Central / bioRxiv / medRxiv / arXiv. Like
src/probe_retrieval.py this is a dated observation, not a reproducible step --
the index moves. It is deliberately NOT in `make all`.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "results" / "corpus" / "corpus_per_screen.csv"
OUT = ROOT / "results" / "literature"
PAPERCLIP = Path.home() / ".local" / "bin" / "paperclip"

# --- FIXED IN THE PRE-REGISTRATION. Do not edit after seeing a result. -------
TIER_A = [
    r"gene[- ]set size",
    r"pathway size",
    r"set size",
    r"size bias",
    r"size[- ]dependent",
    r"larger gene sets",
    r"number of genes in the (gene )?set",
]
TIER_B = [
    r"CAMERA",
    r"competitive (gene set )?test",
    r"self[- ]contained test",
    r"inter[- ]gene correlation",
    r"variance inflation",
]
POWER_FLOOR = 60          # below this many resolved, NO VERDICT
CLAIM_A_THRESHOLD = 0.50  # Tier A at or above this => our framing is wrong
TIER_B_UNINFORMATIVE = 0.90
# -----------------------------------------------------------------------------


def _run(args: list[str], timeout: int = 120) -> str:
    try:
        r = subprocess.run([str(PAPERCLIP), *args], capture_output=True,
                           text=True, timeout=timeout)
        return r.stdout
    except (subprocess.TimeoutExpired, OSError):
        return ""


_PMC = re.compile(r"\b(PMC\d+)\b")


def resolve(pmid: str) -> str | None:
    """PMID -> PMC id, or None when PubMed Central does not carry it."""
    out = _run(["lookup", "pmid", str(pmid)])
    if "No documents found" in out:
        return None
    m = _PMC.search(out)
    return m.group(1) if m else None


def tier_hits(doc: str, patterns: list[str]) -> list[str]:
    """Which patterns in this tier match anywhere in the full text."""
    hit = []
    for p in patterns:
        args = ["grep", "-i", "-c", "-e", p, f"/papers/{doc}/content.lines"]
        out = _run(args).strip()
        n = 0
        for line in out.splitlines():
            line = line.strip()
            if line.isdigit():
                n = int(line)
                break
        if n > 0:
            hit.append(p)
    return hit


def main() -> int:
    if not CORPUS.exists():
        print(f"missing {CORPUS}", file=sys.stderr)
        return 1
    pmids = sorted({str(x) for x in pd.read_csv(CORPUS).source_id.dropna()})
    print(f"query set: {len(pmids)} unique publications behind the corpus arm")
    print(f"pre-registered power floor: {POWER_FLOOR} resolved\n")

    rows, resolved = [], 0
    for i, pmid in enumerate(pmids, 1):
        doc = resolve(pmid)
        if doc is None:
            rows.append({"pmid": pmid, "resolved": False, "doc": None,
                         "tier_a": [], "tier_b": []})
            print(f"  [{i:>3}/{len(pmids)}] {pmid}  not in PMC")
            continue
        resolved += 1
        a, b = tier_hits(doc, TIER_A), tier_hits(doc, TIER_B)
        rows.append({"pmid": pmid, "resolved": True, "doc": doc,
                     "tier_a": a, "tier_b": b})
        flag = ("A" if a else "-") + ("B" if b else "-")
        print(f"  [{i:>3}/{len(pmids)}] {pmid}  {doc:<12} {flag}")

    n_a = sum(1 for r in rows if r["tier_a"])
    n_b = sum(1 for r in rows if r["tier_b"])
    n_u = sum(1 for r in rows if r["tier_a"] or r["tier_b"])

    # The power rule fires before any fraction is interpreted.
    underpowered = resolved < POWER_FLOOR
    frac_a = (n_a / resolved) if resolved else 0.0
    frac_b = (n_b / resolved) if resolved else 0.0
    frac_u = (n_u / resolved) if resolved else 0.0

    if underpowered:
        verdict = "NO VERDICT — underpowered"
        claim = ("Fewer than the pre-registered floor of "
                 f"{POWER_FLOOR} publications resolved to full text "
                 f"({resolved}). The fractions below carry no verdict.")
    elif frac_a >= CLAIM_A_THRESHOLD:
        verdict = "CLAIM (a) — the field does discuss it"
        claim = ("Tier A reached or exceeded 50% of resolved publications, so "
                 "the pre-registered branch (a) fires: set size is discussed in "
                 "the literature and our 'unacknowledged' framing is WRONG. The "
                 "corpus arm quantifies a known problem rather than a new one.")
    else:
        verdict = "CLAIM (b) — mostly unacknowledged"
        claim = ("Tier A fell below 50% of resolved publications, so the "
                 "pre-registered branch (b) fires: most of the publications "
                 "whose screens we audited do not mention set size anywhere in "
                 "their full text.")

    result = {
        "arm": "evaluation 11 — literature audit",
        "labelling": ("PRE-REGISTERED as to claim, power rule and search terms "
                      "(docs/LITERATURE_PREREG.md, sha256 165d91a2..., commit "
                      "b0c5e35, committed before this ran). The ARM is "
                      "post-freeze and says so, as evaluations 6, 8 and 10 do."),
        "question": ("Of the publications behind the corpus arm's 1,272 "
                     "screens, how many discuss gene-set size or set-level "
                     "statistical confounding anywhere in their full text?"),
        "index": "Paperclip — PubMed Central / bioRxiv / medRxiv / arXiv",
        "n_publications_queried": len(pmids),
        "n_resolved_to_full_text": resolved,
        "resolution_rate": round(resolved / len(pmids), 4) if pmids else 0.0,
        "power_floor": POWER_FLOOR,
        "underpowered": underpowered,
        "verdict": verdict,
        "claim": claim,
        "tier_a_explicit_size": {
            "n": n_a, "of_resolved": round(frac_a, 4),
            "patterns": TIER_A,
        },
        "tier_b_competitive_test": {
            "n": n_b, "of_resolved": round(frac_b, 4),
            "patterns": TIER_B,
            "uninformative": frac_b >= TIER_B_UNINFORMATIVE,
            "note": ("Pre-registered: above 90% this tier is reported as "
                     "uninformative, because it would be matching boilerplate "
                     "rather than engagement."),
        },
        "union_either_tier": {"n": n_u, "of_resolved": round(frac_u, 4)},
        "what_this_does_not_show": (
            "A regex match is evidence a topic is MENTIONED, not that it is "
            "handled correctly. This measures mention, not understanding, and "
            "claiming otherwise would be the overreach this project exists to "
            "detect."),
        "denominator_warning": (
            "Every fraction is a fraction of what resolved in PubMed Central "
            f"({resolved} of {len(pmids)}), not of the literature. Open access "
            "is not a random sample of publishing."),
        "scope": ("Aggregate counts only. No publication is named here or on "
                  "any rendered surface; the corpus scope invariant already "
                  "fails the build if a PMID appears."),
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "literature_audit.json").write_text(
        json.dumps(result, indent=2) + "\n")
    pd.DataFrame([{"pmid": r["pmid"], "resolved": r["resolved"],
                   "doc": r["doc"] or "",
                   "tier_a_n": len(r["tier_a"]), "tier_b_n": len(r["tier_b"]),
                   "tier_a": "|".join(r["tier_a"]),
                   "tier_b": "|".join(r["tier_b"])} for r in rows]
                 ).to_csv(OUT / "literature_per_publication.csv", index=False)

    print(f"\n{'='*66}")
    print(f"queried            {len(pmids)}")
    print(f"resolved to text   {resolved}  ({result['resolution_rate']:.1%})")
    print(f"Tier A (size)      {n_a}  ({frac_a:.1%} of resolved)")
    print(f"Tier B (competitive){n_b}  ({frac_b:.1%} of resolved)")
    print(f"either tier        {n_u}  ({frac_u:.1%} of resolved)")
    print(f"\nVERDICT: {verdict}")
    print(claim)
    print(f"\nwrote {OUT}/literature_audit.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
