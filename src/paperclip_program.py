"""Pipeline step 1, REAL — proteostasis (UPR) gene set, one Paperclip citation per gene.

This replaces the Europe PMC substitute used before Paperclip was authenticated.
Both are kept side by side in the output:

  paperclip_*  : curated semantic retrieval -- the EVIDENCE for each gene
  epmc_*       : Europe PMC counts -- the literature-WEIGHT metric

They answer different questions and neither replaces the other. Paperclip does
not expose a citation count in `search`, so ranking by citation count still uses
the Europe PMC column, which is labelled as such.

    .venv/bin/python -m src.paperclip_program
"""
from __future__ import annotations

import csv
import re
import subprocess
from pathlib import Path

import pandas as pd

GMT = Path("data/genesets/h.all.v2026.1.Hs.symbols.gmt")
SET = "HALLMARK_UNFOLDED_PROTEIN_RESPONSE"
EPMC = Path("results/discovery/upr_program_citations.csv")
OUT = Path("results/discovery/upr_program_paperclip.csv")

ANSI = re.compile(r"\x1b\[[0-9;]*m")


def genes() -> list[str]:
    for line in GMT.read_text().splitlines():
        p = line.split("\t")
        if p[0] == SET:
            return p[2:]
    raise SystemExit(f"{SET} not found")


def search(gene: str) -> dict:
    """Top Paperclip PMC hit for this gene in a UPR/proteostasis context."""
    q = f"{gene} unfolded protein response ER stress proteostasis"
    r = subprocess.run(["paperclip", "search", "-s", "pmc", q],
                       capture_output=True, text=True, timeout=120)
    txt = ANSI.sub("", r.stdout)
    n = 0
    m = re.search(r"Found (\d+) paper", txt)
    if m:
        n = int(m.group(1))
    # first result block: "  1. <title>" then authors, then "PMCxxxxx · PMC · YYYY-MM-DD"
    title = pmcid = date = ""
    tm = re.search(r"^\s+1\.\s+(.+)$", txt, re.M)
    if tm:
        title = tm.group(1).strip()
    im = re.search(r"(PMC\d+)\s+·\s+\S+\s+·\s+(\d{4})-(\d{2})-(\d{2})", txt)
    if im:
        pmcid, date = im.group(1), f"{im.group(2)}-{im.group(3)}-{im.group(4)}"
    return {"paperclip_n_papers": n, "paperclip_pmcid": pmcid,
            "paperclip_year": date[:4], "paperclip_date": date,
            "paperclip_title": title.replace(",", ";")[:150]}


def main() -> None:
    gs = genes()
    print(f"{SET}: {len(gs)} genes -> Paperclip PMC")
    rows = []
    for i, g in enumerate(gs, 1):
        try:
            rows.append({"gene": g, **search(g)})
        except Exception as e:
            rows.append({"gene": g, "paperclip_n_papers": -1, "paperclip_pmcid": "",
                         "paperclip_year": "", "paperclip_date": "",
                         "paperclip_title": f"ERROR {type(e).__name__}"})
        if i % 25 == 0:
            print(f"  {i}/{len(gs)}")

    pc = pd.DataFrame(rows)
    ep = pd.read_csv(EPMC, dtype={"pmid": "string"}).rename(columns={
        "pmid": "epmc_pmid", "year": "epmc_year", "cited_by": "epmc_cited_by",
        "hits": "epmc_hits", "title": "epmc_title"})
    out = pc.merge(ep, on="gene", how="left")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False, quoting=csv.QUOTE_MINIMAL)

    got = int((pc.paperclip_pmcid != "").sum())
    err = int((pc.paperclip_n_papers < 0).sum())
    zero = int((pc.paperclip_n_papers == 0).sum())
    print(f"\nwrote {OUT}")
    print(f"  genes with a Paperclip citation : {got}/{len(pc)}")
    print(f"  genes with ZERO Paperclip hits  : {zero}   <- literature gap, report it")
    print(f"  errors                          : {err}")
    print(f"  distinct PMC IDs                : {pc[pc.paperclip_pmcid!=''].paperclip_pmcid.nunique()}"
          f"   <- compare: Europe PMC gave 75 distinct PMIDs for 113 genes")


if __name__ == "__main__":
    main()
