"""Pipeline step 1 — proteostasis (UPR) gene set with one citation per gene.

PAPERCLIP IS UNAVAILABLE (not authenticated; `paperclip login` is interactive).
Substituted Europe PMC REST, which requires no auth and returns citedByCount
directly. This is recorded as a substitution, not presented as Paperclip output.
"""
from __future__ import annotations

import json
import subprocess
import time
import urllib.parse
from pathlib import Path

GMT = Path("data/genesets/h.all.v2026.1.Hs.symbols.gmt")
SET = "HALLMARK_UNFOLDED_PROTEIN_RESPONSE"
OUT = Path("results/discovery/upr_program_citations.csv")
EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"


def genes() -> list[str]:
    for line in GMT.read_text().splitlines():
        p = line.split("\t")
        if p[0] == SET:
            return p[2:]
    raise SystemExit(f"{SET} not found")


def query(gene: str) -> dict:
    q = (f'("{gene}") AND ("unfolded protein response" OR "ER stress" OR '
         f'"proteostasis" OR "protein folding")')
    url = (f"{EPMC}?query={urllib.parse.quote(q)}&format=json&pageSize=1"
           f"&sort=CITED%20desc&resultType=core")
    # curl, not urllib: the SSL chain is intercepted on this machine
    r = subprocess.run(["curl", "-sL", "--max-time", "25", url],
                       capture_output=True, text=True)
    try:
        d = json.loads(r.stdout)
        res = d.get("resultList", {}).get("result", [])
        hits = int(d.get("hitCount", 0))
        if not res:
            return {"pmid": "", "year": "", "cited_by": 0, "hits": hits, "title": ""}
        t = res[0]
        return {"pmid": t.get("pmid", t.get("id", "")),
                "year": t.get("pubYear", ""),
                "cited_by": int(t.get("citedByCount", 0) or 0),
                "hits": hits,
                "title": (t.get("title", "") or "").replace(",", ";")[:120]}
    except Exception as e:
        return {"pmid": "", "year": "", "cited_by": -1, "hits": -1, "title": f"ERROR {e}"}


def main() -> None:
    gs = genes()
    print(f"{SET}: {len(gs)} declared members")
    rows = []
    for i, g in enumerate(gs, 1):
        r = query(g)
        rows.append({"gene": g, **r})
        if i % 20 == 0:
            print(f"  {i}/{len(gs)}")
        time.sleep(0.12)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    import csv
    with OUT.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["gene", "pmid", "year", "cited_by", "hits", "title"])
        w.writeheader()
        w.writerows(rows)
    ok = sum(1 for r in rows if r["pmid"])
    print(f"\nwrote {OUT}  ({ok}/{len(rows)} genes got a citation)")
    print(f"errors: {sum(1 for r in rows if r['cited_by'] < 0)}")


if __name__ == "__main__":
    main()
