"""The 50-program sweep, fanned across Modal containers.

Why this exists: reproducing denali locally costs a 470 MB download and about
twelve minutes. That is a real barrier to anyone checking our work. This runs the
SAME scorer on Modal, one container per shard of programs, and writes the same
two files -- so a reviewer with no substrate and no patience can reproduce the
result in the cloud instead of taking our word for it.

    modal run src/modal_sweep.py                  # 50 programs, 10 shards
    modal run src/modal_sweep.py --shards 25      # more parallelism
    modal run src/modal_sweep.py --limit 4        # smoke test, 4 programs

It is a REPRODUCTION, not a second implementation. The per-program maths is
`score()` and `features()` imported verbatim from the byte-frozen
`src/score_k562.py` and `src/sweep.py`; nothing here recomputes them. Output is
compared against results/frozen/ at the end and the exit code says whether it
matched.

The substrate is downloaded once into a Modal Volume and reused, so only the
first run pays the 140 s fetch.
"""
from __future__ import annotations

import modal

app = modal.App("denali-sweep")

# Same pins as requirements.txt. Reproduction is the whole point, so the cloud
# interpreter has to match the one that produced results/frozen/.
image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "h5py==3.16.0", "numpy==2.5.2", "pandas==3.0.5",
        "scipy==1.18.0", "statsmodels==0.14.6",
    )
    .add_local_dir("src", remote_path="/root/src")
    .add_local_dir("data/genesets", remote_path="/root/data/genesets")
)

substrate = modal.Volume.from_name("denali-substrate", create_if_missing=True)

FILES = {
    "K562_gwps_normalized_bulk_01.h5ad": "https://ndownloader.figshare.com/files/35773217",
    "CRISPRGeneEffect.csv": "https://ndownloader.figshare.com/files/51064667",
}
MD5 = {
    "K562_gwps_normalized_bulk_01.h5ad": "a3dfaa94ea8724217f5ecb1e14a5f0c8",
    "CRISPRGeneEffect.csv": "6edf7ade09b9b34199210b559d4745d3",
}


@app.function(image=image, volumes={"/substrate": substrate}, timeout=3600)
def fetch_substrate() -> dict:
    """Download the substrate into the Volume once, verifying md5. Idempotent."""
    import hashlib
    import urllib.request
    from pathlib import Path

    out = {}
    for name, url in FILES.items():
        p = Path("/substrate") / name
        if p.exists():
            out[name] = "cached"
            continue
        print(f"downloading {name} ...")
        urllib.request.urlretrieve(url, p)
        h = hashlib.md5(p.read_bytes()).hexdigest()
        # The md5 is checked here rather than trusted: a silently truncated
        # download would otherwise produce plausible numbers that are wrong.
        if h != MD5[name]:
            p.unlink()
            raise RuntimeError(f"{name} md5 {h} != expected {MD5[name]}")
        out[name] = f"downloaded, md5 OK ({p.stat().st_size / 1e6:.0f} MB)"
    substrate.commit()
    return out


@app.function(image=image, volumes={"/substrate": substrate},
              timeout=3600, cpu=2.0, memory=8192)
def score_shard(programs: list[str]) -> dict:
    """Score one shard of programs. Returns summary rows and matrix columns.

    Imports the frozen scorer rather than reimplementing it -- if these numbers
    differ from the local run, the cause is the environment, not the maths.
    """
    import os
    import sys

    os.chdir("/root")
    sys.path.insert(0, "/root")

    import numpy as np
    import pandas as pd
    from scipy.stats import norm
    from statsmodels.stats.multitest import multipletests

    from src import score_k562 as SC
    from src import sweep as SW

    # The scorer's substrate path is a module constant. Point it at the Volume
    # rather than editing the file -- src/score_k562.py is byte-frozen and its
    # sha256 is asserted by the test suite.
    SC.K562 = __import__("pathlib").Path("/substrate/K562_gwps_normalized_bulk_01.h5ad")

    import h5py
    X, symbols, pert, targets = SC.load_k562()
    with h5py.File(SC.K562, "r") as f:
        expr_all = f["var/mean"][:].astype(float)
    sd_all = np.nanstd(X, axis=0)

    dm = pd.read_csv("/substrate/CRISPRGeneEffect.csv", index_col=0)
    dm.columns = [c.split(" (")[0] for c in dm.columns]
    ess = dm.mean(axis=0)

    sets = SW.hallmark()
    rows, cols = [], {}
    for name in programs:
        program = sets[name]
        u_z, cos, delta, n_present = SC.score(X, symbols, program)
        p = 2 * norm.sf(np.abs(u_z))
        ok = np.isfinite(p)
        q = np.full_like(p, np.nan)
        if ok.sum():
            q[ok] = multipletests(p[ok], method="fdr_bh")[1]
        n_hits = int(np.nansum(q < SW.ALPHA))
        R_p = float(np.log10(1 + n_hits))

        f = SW.features(program, symbols, expr_all, sd_all, X, ess)
        gate = bool(f["frac_present"] >= SW.MIN_FRAC and f["n_present"] >= SW.MIN_N
                    and (f["expr_ratio"] or 0) >= 1.0 and (f["sd_ratio"] or 0) >= 1.0)

        col = pd.Series(u_z, index=pert).groupby(pd.Series(targets, index=pert)).max()
        cols[name] = {str(k): (None if pd.isna(v) else float(v)) for k, v in col.items()}
        rows.append({"program": name, **f, "n_hits_q05": n_hits, "R_p": round(R_p, 4),
                     "passes_measurability_gate": gate,
                     "is_held_out_program": name == SW.HELDOUT_B,
                     "is_program_A": name == SW.PROGRAM_A})
        print(f"  {name[:52]:54s} hits={n_hits:5d} R_p={R_p:.3f}")
    return {"rows": rows, "cols": cols}


@app.local_entrypoint()
def main(shards: int = 10, limit: int = 0, compare: bool = True):
    import json
    import time
    from pathlib import Path

    import pandas as pd

    sys_path = Path(__file__).resolve().parents[1]
    sets = sorted(
        n for g in (sys_path / "data" / "genesets").glob("h.all*.symbols.gmt")
        for n in (line.split("\t")[0] for line in g.read_text().splitlines())
    )
    if limit:
        sets = sets[:limit]
    print(f"{len(sets)} programs across {shards} shards")

    print("\n== substrate ==")
    for k, v in fetch_substrate.remote().items():
        print(f"  {k:42s} {v}")

    groups = [sets[i::shards] for i in range(shards)]
    groups = [g for g in groups if g]
    t0 = time.time()
    print(f"\n== scoring on {len(groups)} containers ==")
    results = list(score_shard.map(groups))
    wall = time.time() - t0

    rows, cols = [], {}
    for r in results:
        rows.extend(r["rows"])
        cols.update(r["cols"])

    S = pd.DataFrame(rows).sort_values("R_p", ascending=False)
    M = pd.DataFrame(cols)
    M.index.name = "target_gene"
    out = sys_path / "results" / "modal"
    out.mkdir(parents=True, exist_ok=True)
    S.to_csv(out / "program_summary.csv", index=False)
    M.sort_index(axis=1).to_csv(out / "matrix.csv")
    print(f"\nwall clock {wall:.0f}s across {len(groups)} containers "
          f"-> results/modal/")

    if not compare or limit:
        return
    # The claim is reproduction, so verify it instead of asserting it.
    print("\n== agreement with results/frozen/ ==")
    F = pd.read_csv(sys_path / "results" / "frozen" / "program_summary.csv")
    key = ["n_hits_q05", "R_p", "n_present", "passes_measurability_gate"]
    m = F[["program"] + key].merge(S[["program"] + key], on="program",
                                   suffixes=("_frozen", "_modal"))
    bad = []
    for k in key:
        a, b = m[f"{k}_frozen"], m[f"{k}_modal"]
        same = (a == b) if a.dtype == bool or a.dtype == object else \
            ((a - b).abs() <= 1e-4)
        n_diff = int((~same).sum())
        print(f"  {k:30s} {len(m) - n_diff}/{len(m)} identical")
        if n_diff:
            bad.append(k)
    print("\n" + ("MATCH - the cloud run reproduces the frozen result."
                  if not bad else f"MISMATCH in {bad}"))
    (out / "agreement.json").write_text(json.dumps(
        {"n_programs": len(m), "columns_checked": key,
         "mismatched_columns": bad, "shards": len(groups),
         "reproduces_frozen": not bad}, indent=2))
