"""The corpus rerank, fanned across Modal containers.

POST-HOC, exploratory. Not pre-registered. Names no screen and no publication:
the unit of inference is the distribution.

WHAT THIS COMPUTES, AND WHY IT NEEDS A CLOUD. `src/corpus_rerank.py` asks how
many of a published screen's top 10 sets keep a top-10 place once set size is
regressed out, and it asks it of every screen in BioGRID ORCS that meets
evaluation 10's inclusion rule. That is 1,952 files, a 752 MB archive and a
few minutes of single-threaded parsing on a laptop -- for a question whose
answer is a distribution over screens, where every screen is independent of
every other. It is the one genuinely embarrassingly-parallel workload in this
project, and it is the reason a second Modal entry point exists at all.

THIS IS NOT A SECOND IMPLEMENTATION. The per-screen function is
`src.corpus_rerank.screen_row`, imported verbatim, which in turn calls the
packaged `denali_audit.core.rerank` -- the same code path the CLI ships and the
local arm runs. If the numbers here differed from the local run, the cause would
be the environment, not the maths, and the join gate below would catch it.

THE SANITY GATES ARE THE SAME TWO, AND THEY RUN BEFORE ANYTHING IS WRITTEN:
  1. JOIN GATE. The screens audited here must match `results/corpus/` -- the
     committed evaluation 10 output -- row for row, and the per-screen size-alone
     R^2 must equal the committed value for every screen. If the join drifts,
     the substrate or the parse differs and everything downstream is noise.
  2. OWN-SCREEN GATE. denali's own screen, read through the same adapters, must
     land at or above the corpus 90th percentile on size-alone R^2 (matching
     evaluation 10) and reproduce the published 3-of-10 survivors.
  3. AGREEMENT GATE, added because this run has something the local one does not
     -- a committed answer to compare against. Every per-screen survivor count
     must equal the committed local result. A distributed run that quietly
     disagreed with the single-process run would be the most dangerous output
     this repository could produce.

    modal run src/modal_corpus_rerank.py                  # 1,952 files, 32 shards
    modal run src/modal_corpus_rerank.py --shards 64      # more parallelism
    modal run src/modal_corpus_rerank.py --limit 200      # smoke test, no gates

The first run uploads the ORCS archive into a Modal Volume and every run after
it reuses the Volume. See the substrate note below for why it uploads rather
than downloading in the container.

Writes results/corpus_rerank/modal_agreement.json and modal_per_screen.csv.
It does NOT overwrite corpus_rerank.json: the local arm owns that file, this one
reproduces it and says whether it agreed. results/frozen/ is untouched, and this
module is not a `make all` step.
"""
from __future__ import annotations

import modal

app = modal.App("denali-corpus-rerank")

# Same pins as requirements.txt, for the same reason modal_sweep pins them: a
# distributed run that used different numeric libraries would be comparing two
# things at once.
image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("numpy==2.5.2", "pandas==3.0.5")
    .add_local_dir("src", remote_path="/root/src")
    .add_local_dir("packages/denali-audit", remote_path="/root/packages/denali-audit")
    .add_local_dir("data/genesets", remote_path="/root/data/genesets")
)

corpus = modal.Volume.from_name("denali-orcs", create_if_missing=True)

# THE SUBSTRATE IS UPLOADED, NOT FETCHED, AND THAT IS A FINDING ABOUT THE HOST.
# The pinned release archive lives at
#   downloads.thebiogrid.org/Download/BioGRID-ORCS/Release-Archive/
#   BIOGRID-ORCS-2.0.18/BIOGRID-ORCS-ALL-homo_sapiens-2.0.18.screens.tar.gz
# and the obvious design was to have each container fetch it. It does not work:
# the first attempt died with `IncompleteRead(1036550 bytes read)` after about a
# megabyte, which is the same truncation docs/CORPUS.md records for curl over
# HTTP/2 (there it stops near 70 MB and exits 92). The host also ignores `Range`
# -- a ranged GET returns 200 with the whole body and no `Accept-Ranges` -- so a
# resumable download is not available either. So the local archive is uploaded to
# the Volume once and its sha256 is ENFORCED in the container. That is the
# stronger arrangement anyway: the bytes on the containers are provably the bytes
# that produced the committed evaluation 10 output, rather than whatever the host
# served today.
ARCHIVE_SHA256 = "39222a9650eed083edf193debe45eedc4aabc779ca04ea70107b6bd1efd9b8d7"

SCREENS = "/corpus/screens"
ARCHIVE = "/corpus/orcs.tar.gz"
# Relative to the repo root, or an absolute path in DENALI_ORCS_ARCHIVE. The
# override exists because data/raw/ is git-ignored, so a git worktree or a second
# clone has the code without the substrate and would otherwise need the file
# copied or symlinked into place.
LOCAL_ARCHIVE = "data/raw/orcs/orcs_human.tar.gz"


@app.function(image=image, volumes={"/corpus": corpus}, timeout=3600)
def corpus_status() -> dict:
    """What is in the Volume, and is it the right bytes?

    The hash is checked HERE rather than only at extract time because the first
    run of this module left a truncated archive in the Volume -- the in-container
    download died at `IncompleteRead(1036550 bytes read)` after writing a partial
    file -- and a status check that only asked "does the archive exist?" would
    have skipped the upload forever and failed at the same gate every run. A
    cache that can be poisoned by a failed write has to be able to notice.
    """
    import hashlib
    from pathlib import Path

    root = Path(SCREENS)
    n = len(sorted(root.glob("*screen.tab.txt"))) if root.exists() else 0
    tgz = Path(ARCHIVE)
    if not tgz.exists():
        return {"n_screen_files": n, "archive_present": False, "archive_mb": 0,
                "archive_ok": False}
    h = hashlib.sha256()
    with tgz.open("rb") as f:
        while chunk := f.read(1 << 22):
            h.update(chunk)
    sha = h.hexdigest()
    return {"n_screen_files": n, "archive_present": True,
            "archive_mb": round(tgz.stat().st_size / 1e6, 1),
            "archive_sha256": sha, "archive_ok": sha == ARCHIVE_SHA256}


@app.function(image=image, volumes={"/corpus": corpus}, timeout=600)
def drop_archive() -> str:
    """Remove a truncated archive so the verified local copy can replace it."""
    from pathlib import Path
    p = Path(ARCHIVE)
    if p.exists():
        p.unlink()
        corpus.commit()
        return "removed"
    return "absent"


@app.function(image=image, volumes={"/corpus": corpus}, timeout=3600)
def extract_corpus() -> dict:
    """Verify the uploaded archive against its sha256, then extract it. Idempotent.

    The hash is ENFORCED, not recorded. This archive is the one that produced the
    committed evaluation 10 output, so a mismatch means the distributed run is
    about to measure a different corpus than the number it will be compared to.
    """
    import hashlib
    import tarfile
    from pathlib import Path

    tgz = Path(ARCHIVE)
    if not tgz.exists():
        raise RuntimeError(f"no archive at {ARCHIVE}; the local entrypoint uploads it")
    h = hashlib.sha256()
    with tgz.open("rb") as f:
        while chunk := f.read(1 << 22):
            h.update(chunk)
    sha = h.hexdigest()
    if sha != ARCHIVE_SHA256:
        raise RuntimeError(f"archive sha256 {sha} != expected {ARCHIVE_SHA256}. "
                           "This is not the substrate evaluation 10 was computed "
                           "against; refusing to run.")
    root = Path(SCREENS)
    root.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tgz, "r:gz") as t:
        t.extractall(root, filter="data")
    n = len(sorted(root.glob("*screen.tab.txt")))
    corpus.commit()
    return {"status": "extracted", "n_screen_files": n, "sha256_verified": sha}


@app.function(image=image, volumes={"/corpus": corpus}, timeout=3600,
              cpu=2.0, memory=8192)
def rerank_shard(names: list[str]) -> dict:
    """Audit and rerank one shard of screens. Same function as the local arm."""
    import os
    import sys

    os.chdir("/root")
    sys.path.insert(0, "/root")

    # Importing `src` runs src/__init__.py, which puts the vendored
    # packages/denali-audit on the path -- mounted at the same relative location
    # it occupies in the repo, so the import resolves identically here.
    from src.corpus_rerank import screen_row
    from src.corpus_audit import load_gmt
    from pathlib import Path

    gmt = next(Path("/root/data/genesets").glob("h.all*.symbols.gmt"))
    sets = load_gmt(gmt)

    rows, parse_failed, excluded = [], 0, 0
    for n in names:
        status, row = screen_row(f"{SCREENS}/{n}", sets)
        if status == "parse_failed":
            parse_failed += 1
        elif status == "excluded":
            excluded += 1
        else:
            rows.append(row)
    print(f"  shard of {len(names)}: {len(rows)} audited, "
          f"{excluded} excluded, {parse_failed} unparseable")
    return {"rows": rows, "parse_failed": parse_failed, "excluded": excluded}


@app.function(image=image, volumes={"/corpus": corpus}, timeout=600)
def list_screens() -> list[str]:
    from pathlib import Path
    return sorted(p.name for p in Path(SCREENS).glob("*screen.tab.txt"))


@app.local_entrypoint()
def main(shards: int = 32, limit: int = 0):
    import json
    import os
    import sys
    import time
    from pathlib import Path

    import pandas as pd

    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    import src                                          # noqa: F401  (path setup)
    from denali_audit.adapters import detect
    from denali_audit.core import audit, rerank

    TOP = 10
    out = root / "results" / "corpus_rerank"
    committed_csv = root / "results" / "corpus" / "corpus_per_screen.csv"
    committed_rr = out / "corpus_rerank_per_screen.csv"

    print("== substrate ==")
    st = corpus_status.remote()
    print(f"  in the Volume: {st['n_screen_files']} screen files, "
          f"archive {st['archive_mb']} MB, sha256 "
          f"{'OK' if st.get('archive_ok') else 'MISSING/WRONG'}")
    if st["n_screen_files"] == 0 or not st.get("archive_ok"):
        if st["archive_present"] and not st["archive_ok"]:
            print(f"  archive in the Volume hashes to {st.get('archive_sha256')} -- "
                  "truncated or a different release. Dropping it.")
            print(f"  {drop_archive.remote()}")
            st = {**st, "archive_present": False}
        if not st["archive_present"]:
            local_tgz = Path(os.environ.get("DENALI_ORCS_ARCHIVE",
                                            str(root / LOCAL_ARCHIVE)))
            if not local_tgz.exists():
                raise SystemExit(
                    f"no archive in the Volume and none at {local_tgz}. "
                    "Fetch it first -- docs/CORPUS.md has the command and the "
                    "HTTP/1.1 gotcha -- then re-run. It uploads once.")
            mb = local_tgz.stat().st_size / 1e6
            print(f"  uploading {mb:.0f} MB to the Volume (once) ...")
            t_up = time.time()
            with corpus.batch_upload() as batch:
                batch.put_file(local_tgz, "/orcs.tar.gz")
            print(f"  uploaded in {time.time() - t_up:.0f}s")
        for k, v in extract_corpus.remote().items():
            print(f"  {k:24s} {v}")

    names = list_screens.remote()
    if limit:
        names = names[:limit]
    groups = [names[i::shards] for i in range(shards)]
    groups = [g for g in groups if g]
    print(f"\n== {len(names)} screen files across {len(groups)} containers ==")

    t0 = time.time()
    results = list(rerank_shard.map(groups))
    wall = time.time() - t0

    rows, n_parse_failed, n_excluded = [], 0, 0
    for r in results:
        rows.extend(r["rows"])
        n_parse_failed += r["parse_failed"]
        n_excluded += r["excluded"]
    R = pd.DataFrame(rows).sort_values("screen_id").reset_index(drop=True)
    print(f"\nwall clock {wall:.0f}s across {len(groups)} containers")
    print(f"files: {len(names)}  parse-failed: {n_parse_failed}  "
          f"excluded by rule: {n_excluded}  audited: {len(R)}")

    if limit:
        print("\n--limit set: this is a smoke test. Gates skipped, nothing written.")
        return

    # ---- gate 1: the join, against evaluation 10 ----
    committed = pd.read_csv(committed_csv, dtype={"screen_id": str})
    m = R.merge(committed, on="screen_id", suffixes=("", "_committed"))
    same_ids = len(m) == len(R) == len(committed)
    max_dr2 = float((m.r2_size_alone - m.r2_size_alone_committed).abs().max()) \
        if same_ids else float("inf")
    join_ok = same_ids and max_dr2 <= 1e-6
    print(f"\njoin gate: ids match={same_ids}, max |dR2| = {max_dr2}")

    # ---- gate 2: our own screen, through the same packaged code path ----
    own = pd.read_csv(root / "examples" / "example_gprofiler.csv")
    mp = detect(own)
    own_r2 = audit(mp.size, mp.hits)["r2_size_alone"]
    own_surv = rerank(mp.size, mp.hits, names=None, top=TOP)["survived_top_n"]
    p90 = float(R.r2_size_alone.quantile(0.90))
    own_ok = own_r2 >= p90 and own_surv == 3
    print(f"own-screen gate: R2 {own_r2} vs corpus p90 {p90:.4f}; "
          f"survivors {own_surv}/{TOP}")

    # ---- gate 3: agreement with the committed single-process run ----
    agree_ok, n_diff = False, None
    if committed_rr.exists():
        C = pd.read_csv(committed_rr, dtype={"screen_id": str})
        j = R.merge(C[["screen_id", "survivors_top10"]], on="screen_id",
                    suffixes=("", "_local"))
        n_diff = int((j.survivors_top10 != j.survivors_top10_local).sum())
        agree_ok = len(j) == len(R) == len(C) and n_diff == 0
        print(f"agreement gate: {len(j) - (n_diff or 0)}/{len(j)} screens identical "
              f"to the local run")
    else:
        print("agreement gate: SKIPPED, no committed local run to compare against")

    if not (join_ok and own_ok):
        print("\nGATE FAILED. Nothing written -- a distributed result that does not "
              "join to evaluation 10 is noise with a wall-clock time attached.")
        raise SystemExit(1)

    surv = R.survivors_top10
    q = {f"p{int(k * 100)}": round(float(v), 2)
         for k, v in surv.quantile([0.10, 0.25, 0.50, 0.75, 0.90]).items()}
    print(f"\nsurvivors of the top {TOP} across {len(R)} published screens:")
    for k, v in q.items():
        print(f"  {k}  {v}")
    print(f"  mean {surv.mean():.2f}")

    out.mkdir(parents=True, exist_ok=True)
    R.to_csv(out / "modal_per_screen.csv", index=False)
    (out / "modal_agreement.json").write_text(json.dumps({
        "status": "POST-HOC, exploratory. Not pre-registered.",
        "what_this_is": "The corpus rerank run as distributed compute: the same "
                        "src.corpus_rerank.screen_row, imported verbatim, fanned "
                        "across Modal containers. Not a second implementation and "
                        "not an independent check of the maths -- it establishes "
                        "that the arm runs without the 752 MB local archive, and "
                        "that fanning it out does not change the answer.",
        "names_nothing": "No screen, publication or gene set is named. The unit of "
                         "inference is the distribution.",
        "source": "BioGRID ORCS 2.0.18 (pinned release URL), human, MIT licence.",
        "containers": len(groups),
        "wall_clock_s": round(wall, 1),
        "n_screen_files": len(names),
        "n_parse_failed": n_parse_failed,
        "n_excluded_by_rule": n_excluded,
        "n_screens_audited": int(len(R)),
        "gates": {
            "join_vs_evaluation_10": {
                "screens_matched_row_for_row": int(len(m)) if same_ids else 0,
                "max_abs_r2_delta_vs_committed": max_dr2, "passed": bool(join_ok)},
            "own_screen": {
                "r2_size_alone": own_r2, "corpus_p90": round(p90, 4),
                "above_p90": bool(own_r2 >= p90),
                "survivors_top10": int(own_surv),
                "matches_published_3_of_10": bool(own_surv == 3),
                "passed": bool(own_ok)},
            "agreement_with_local_run": {
                "compared": committed_rr.exists(),
                "n_screens_differing": n_diff, "passed": bool(agree_ok)},
        },
        "quantiles": q,
        "mean": round(float(surv.mean()), 2),
    }, indent=2) + "\n")
    print(f"\nwrote {out}/modal_agreement.json and modal_per_screen.csv")
    if not agree_ok and committed_rr.exists():
        print("⚠ The distributed run DISAGREED with the committed local run. "
              "That is reported, not smoothed over.")
        raise SystemExit(1)
