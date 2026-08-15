"""Timed throughput probe for Track B feasibility. Measurement, not estimate.

20 genes we already scored: 10 canonical (well-studied), 10 drawn deterministically
from the screen by sha256 rank. Records wall-clock, papers returned, and the
one-line claim summaries so testability can be judged by hand.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import time
from pathlib import Path

import pandas as pd

ANSI = re.compile(r"\x1b\[[0-9;]*m")
OUT = Path("/private/tmp/claude-501/-Users-alexvintera/"
           "7dc2189b-1701-4701-beee-bcd03999de85/scratchpad/probe_paperclip.json")

CANONICAL = ["SREBF2", "SCAP", "INSIG1", "HMGCR", "LDLR",
             "ATF4", "XBP1", "ERN1", "EIF2AK3", "HSPA5"]


def sample_random(n=10):
    b = pd.read_csv("results/frozen/program_b_scores.csv")
    genes = sorted(b.gene_symbol.dropna().astype(str).unique())
    return sorted(genes, key=lambda g: hashlib.sha256(g.encode()).hexdigest())[:n]


def probe(gene: str) -> dict:
    q = f'"{gene}" gene function required for regulates knockdown knockout phenotype'
    t = time.time()
    r = subprocess.run(["paperclip", "search", "-s", "pmc", q],
                       capture_output=True, text=True, timeout=180)
    dt = time.time() - t
    txt = ANSI.sub("", r.stdout)
    m = re.search(r"Found (\d+) paper", txt)
    n = int(m.group(1)) if m else 0
    # one-line summaries are the quoted lines under each hit
    claims = re.findall(r'^\s+"(.+?)"\s*$', txt, re.M)
    return {"gene": gene, "seconds": round(dt, 2), "papers": n,
            "claims": claims[:8], "n_claims": len(claims)}


def main():
    genes = [(g, "canonical") for g in CANONICAL] + \
            [(g, "random") for g in sample_random(10)]
    rows = []
    t0 = time.time()
    for g, kind in genes:
        try:
            d = probe(g)
        except Exception as e:
            d = {"gene": g, "seconds": -1, "papers": -1, "claims": [], "n_claims": 0,
                 "error": f"{type(e).__name__}"}
        d["kind"] = kind
        rows.append(d)
        print(f"  {kind:9s} {g:10s} {d['seconds']:6.2f}s  papers={d['papers']:>6}  "
              f"claim-lines={d['n_claims']}")
    total = time.time() - t0
    OUT.write_text(json.dumps(rows, indent=2))

    ok = [r for r in rows if r["seconds"] > 0]
    per = sum(r["seconds"] for r in ok) / max(len(ok), 1)
    print(f"\ntotal wall-clock      : {total:.1f}s for {len(rows)} genes")
    print(f"mean per gene (query) : {per:.2f}s")
    print(f"genes with 0 papers   : {sum(1 for r in ok if r['papers']==0)}")
    print(f"mean claim-lines/gene : {sum(r['n_claims'] for r in ok)/max(len(ok),1):.1f}")
    print(f"\n=> 6 h of pure querying = {int(6*3600/per):,} gene queries")
    print(f"   (query cost only; extraction cost NOT included)")


if __name__ == "__main__":
    main()
