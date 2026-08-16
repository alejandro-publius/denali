"""Read the table your enrichment tool already gave you.

The check itself needs three columns: a set name, how many members that set had, and
how many came back significant. No enrichment tool on earth calls them that, which is
the single largest reason a check like this does not get run. So this module knows the
output shapes of the tools people actually use and maps them itself.

WHERE A TOOL DOES NOT REPORT A HIT COUNT, THIS SAYS SO rather than substituting
something and hoping. fgsea and GSEA desktop report an enrichment score per set, not a
count of significant members; the closest honest stand-in is the leading-edge subset,
and an adapter that uses it flags `approximate=True` so the caller can decide. Silently
inventing the input to a check about silently invented inputs would be a poor joke.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import pandas as pd


@dataclass
class Mapping:
    fmt: str
    set_col: str
    size: pd.Series
    hits: pd.Series
    approximate: bool = False
    note: str = ""
    corr: pd.Series | None = field(default=None)


def _has(df: pd.DataFrame, *cols: str) -> bool:
    lower = {c.lower().strip() for c in df.columns}
    return all(c.lower() in lower for c in cols)


def _col(df: pd.DataFrame, name: str) -> str:
    for c in df.columns:
        if c.lower().strip() == name.lower():
            return c
    raise KeyError(name)


def _ratio_num(series: pd.Series) -> pd.Series:
    """'5/200' -> 5 ; also tolerates '5 / 200'."""
    return series.astype(str).str.extract(r"^\s*(\d+)\s*/", expand=False).astype(float)


def _ratio_den(series: pd.Series) -> pd.Series:
    """'5/200' -> 200."""
    return series.astype(str).str.extract(r"/\s*(\d+)\s*$", expand=False).astype(float)


def _denali(df):
    if not _has(df, "set", "size", "hits"):
        return None
    return Mapping("denali", _col(df, "set"), df[_col(df, "size")], df[_col(df, "hits")])


def _gprofiler(df):
    if not _has(df, "term_size", "intersection_size"):
        return None
    name = "term_name" if _has(df, "term_name") else "term_id"
    return Mapping("g:Profiler", _col(df, name),
                   df[_col(df, "term_size")], df[_col(df, "intersection_size")],
                   note="term_size and intersection_size map exactly onto size and hits")


def _david(df):
    if not _has(df, "term", "count", "pop hits"):
        return None
    return Mapping("DAVID", _col(df, "term"),
                   df[_col(df, "pop hits")], df[_col(df, "count")],
                   note="'Pop Hits' is the set size in the background; 'Count' is the overlap")


def _clusterprofiler(df):
    if not _has(df, "bgratio", "count"):
        return None
    name = "description" if _has(df, "description") else "id"
    return Mapping("clusterProfiler", _col(df, name),
                   _ratio_num(df[_col(df, "bgratio")]), df[_col(df, "count")],
                   note="size parsed from the numerator of BgRatio; hits is Count")


def _enrichr(df):
    if not _has(df, "term", "overlap"):
        return None
    ov = df[_col(df, "overlap")]
    return Mapping("Enrichr / GSEApy", _col(df, "term"),
                   _ratio_den(ov), _ratio_num(ov),
                   note="size and hits parsed from the Overlap column ('5/200')")


def _fgsea(df):
    if not _has(df, "pathway", "size"):
        return None
    if _has(df, "leadingedge"):
        le = df[_col(df, "leadingedge")].astype(str)
        hits = le.str.count(r"[,\s]+").add(1).where(le.str.strip().ne(""), 0)
        return Mapping("fgsea", _col(df, "pathway"), df[_col(df, "size")], hits,
                       approximate=True,
                       note="fgsea reports no count of significant members; the "
                            "leading-edge subset size is used as the closest honest "
                            "stand-in. Treat the number as indicative, not exact.")
    return None


def _outlier_note(size: pd.Series) -> str:
    """Flag a single set that dwarfs the rest.

    Found on a real screen, not imagined: MAGeCKFlute's published RRA output has
    19,325 genes with 1-4 guides and one row, `NO_CURRENT`, with 979 -- a control
    pseudo-gene pooling every non-targeting guide. It is 245x a normal gene and
    sits alone at the far end of the x axis, which is the definition of a
    high-leverage point in a straight-line fit. On that screen it barely moves
    the answer (0.0067 vs 0.0099 without it, both NOT SIZE-DOMINATED); on a
    smaller or noisier one it could carry the fit by itself.

    It is reported, never dropped. Silently deleting rows from a check about
    silently invented inputs would be the same sin twice.
    """
    s = pd.to_numeric(size, errors="coerce").dropna()
    if len(s) < 3:
        return ""
    med = s.median()
    top = s.max()
    if med > 0 and top >= 10 * med:
        n = int((s >= 10 * med).sum())
        return (f". NOTE: {n} of {len(s)} entries are 10x the median size or more "
                f"(largest {int(top)} vs median {int(med)}). In a pooled library that "
                "is usually the non-targeting control pseudo-gene, and it is a "
                "high-leverage point in this fit. Nothing is dropped -- rerun with "
                "that row removed and see whether the verdict holds")
    return ""


def _mageck(df):
    """MAGeCK `mageck test` gene_summary.txt — the file a screener is actually
    holding when the screen finishes, before any enrichment step has run.

    Each GENE is treated as a set of its sgRNAs: `num` is guides per gene (size)
    and `neg|goodsgrna` is MAGeCK's own count of guides passing its cutoff (hits).
    Both are exact counts, so this mapping is not approximate. The question the
    audit answers becomes: how much of this gene ranking is explained by how many
    guides each gene had?
    """
    if not _has(df, "id", "num", "neg|goodsgrna"):
        return None
    note = ("each gene is read as a set of its sgRNAs: 'num' is guides per gene, "
            "'neg|goodsgrna' the count passing MAGeCK's cutoff. This audits the "
            "depletion (neg) direction; for enrichment rerun with "
            "--set id --size num --hits 'pos|goodsgrna'")
    size = pd.to_numeric(df[_col(df, "num")], errors="coerce")
    if size.nunique(dropna=True) == 1:
        note += (". Guides-per-gene is constant in this library, so guide count "
                 "cannot explain this ranking — the audit will say so")
    note += _outlier_note(size)
    return Mapping("MAGeCK (gene_summary)", _col(df, "id"),
                   size, pd.to_numeric(df[_col(df, "neg|goodsgrna")], errors="coerce"),
                   note=note)


def _drugz(df):
    if not _has(df, "gene", "numobs", "normz", "fdr_synth"):
        return None
    size = pd.to_numeric(df[_col(df, "numobs")], errors="coerce")
    q = pd.to_numeric(df[_col(df, "fdr_synth")], errors="coerce")
    return Mapping("drugZ", _col(df, "gene"), size, (q < 0.05).astype(int) * size,
                   approximate=True,
                   note="each gene is read as a set of its guide observations; numObs "
                        "counts guide x replicate observations, not distinct guides. "
                        "drugZ reports no per-gene count of significant guides, so "
                        "genes below fdr_synth 0.05 are credited their full numObs — "
                        "the same coarse stand-in as GSEA desktop. This audits the "
                        "synthetic-lethal (synth) direction only; the suppressor "
                        "(supp) columns are present in your file but not audited.")


def _bagel(df):
    if not _has(df, "gene", "bf", "numobs") or _has(df, "rna"):
        return None
    size = pd.to_numeric(df[_col(df, "numobs")], errors="coerce")
    bf = pd.to_numeric(df[_col(df, "bf")], errors="coerce")
    return Mapping("BAGEL2", _col(df, "gene"), size, (bf > 0).astype(int) * size,
                   approximate=True,
                   note="each gene is read as a set of its guide observations; NumObs "
                        "counts guide x replicate observations, not distinct guides. "
                        "BAGEL reports no per-gene count of significant guides and no "
                        "FDR at this step, so genes with BF > 0 (evidence favours the "
                        "essential model) are credited their full NumObs — a coarse "
                        "stand-in. For a calibrated cutoff, take an FDR threshold from "
                        "`BAGEL.py pr`, join it to this file, and name the columns "
                        "yourself.")


def _gsea_desktop(df):
    if not _has(df, "name", "size"):
        return None
    for cand in ("fdr q-val", "nom p-val"):
        if _has(df, cand):
            q = pd.to_numeric(df[_col(df, cand)], errors="coerce")
            return Mapping("GSEA desktop", _col(df, "name"), df[_col(df, "size")],
                           (q < 0.05).astype(int) * df[_col(df, "size")],
                           approximate=True,
                           note="GSEA desktop reports no per-set hit count; sets below "
                                f"{cand} 0.05 are credited their full size, which is a "
                                "coarse stand-in. Prefer a tool that reports an overlap.")
    return None


ADAPTERS = (_denali, _gprofiler, _david, _clusterprofiler, _enrichr, _mageck,
            _fgsea, _gsea_desktop, _drugz, _bagel)

SUPPORTED = ("denali", "g:Profiler", "DAVID", "clusterProfiler",
             "Enrichr / GSEApy", "MAGeCK (gene_summary)", "fgsea", "GSEA desktop",
             "drugZ (approximate — flagged)", "BAGEL2 bf with NumObs (approximate — flagged)")


def _near_miss(df: pd.DataFrame) -> str | None:
    """Files we recognise but honestly cannot audit. Naming what is missing beats
    a generic failure, and beats inventing the missing column by a wide margin."""
    if _has(df, "sgrna", "gene") and not _has(df, "num"):
        return ("This looks like MAGeCK's per-guide file (sgrna_summary.txt). The "
                "audit reads the per-gene file: point it at gene_summary.txt from "
                "the same `mageck test` run.")
    if _has(df, "gene", "bf") and not _has(df, "numobs"):
        return ("This looks like BAGEL output, but without a NumObs column there is "
                "no set size to audit. `BAGEL.py bf` with the default bootstrap "
                "training writes GENE, BF, STD, NumObs — use that file. (The `pr` "
                "output reports FDR but no size, so it cannot be audited either.) "
                "Alternatively, join guides-per-gene from your library file and name "
                "the columns yourself.")
    if _has(df, "rna", "gene", "bf"):
        return ("This looks like BAGEL's per-guide (RNA-level) output. The audit "
                "reads the per-gene file: rerun `BAGEL.py bf` without the RNA-level "
                "flag.")
    return None


def detect(df: pd.DataFrame) -> Mapping | None:
    """First adapter whose required columns are all present. Exact formats win."""
    for fn in ADAPTERS:
        m = fn(df)
        if m is not None:
            return m
    return None


def describe_failure(df: pd.DataFrame) -> str:
    miss = _near_miss(df)
    if miss:
        return miss
    return (
        "Could not recognise this table.\n\n"
        f"  columns found: {list(df.columns)}\n\n"
        f"  formats understood: {', '.join(SUPPORTED)}\n\n"
        "  Name the columns yourself instead:\n"
        "      denali audit FILE --set <col> --size <col> --hits <col>\n\n"
        "  size = how many members that set had.  hits = how many were significant."
    )
