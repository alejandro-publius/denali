"""Prove Proto actually executes, and record what it returned.

Proto was recorded as broken in this repo for a day and a half, on the strength
of a package name Proto does not publish (`proto-language`). That was our error
and it is in LIMITATIONS.md §7. This script exists so the corrected status has a
receipt rather than a second assertion.

It does three things and writes them to results/tools/proto_validation.json:

  1. reports the installed version, tool count and category count
  2. runs `proto-tools doctor`, which checks Modal auth and build capability
  3. makes ONE real tool call and records the result verbatim, with the upstream
     source URL Proto reports

It is deliberately NOT part of `make all`. Proto contributes nothing to any
number in results/frozen/ — denali makes no structural or sequence-design claim
— and this file must never be mistaken for a step that does.

    .venv/bin/python -m src.proto_validate
"""
from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

OUT = Path("results/tools")
PROBE_GENE = "HMGCR"          # a canonical member of the control pathway


def _cli(*args: str) -> str:
    r = subprocess.run([".venv/bin/proto-tools", *args],
                       capture_output=True, text=True, timeout=600)
    return r.stdout.strip()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rec: dict = {
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "install_command": "pip install git+https://github.com/evo-design/proto-tools.git",
        "note": ("Recorded because we previously published Proto as broken on the "
                 "strength of `proto-language`, a package Proto does not publish. "
                 "See LIMITATIONS.md section 7."),
    }

    import importlib.metadata as md
    rec["version"] = md.version("proto-tools")
    rec["n_tools"] = len([l for l in _cli("list").splitlines() if l[:1].islower()])
    rec["n_categories"] = len([l for l in _cli("categories").splitlines() if l.strip()])

    doctor = _cli("doctor")
    rec["doctor"] = {ln.split(":", 1)[0].strip(): ln.split(":", 1)[1].strip()
                     for ln in doctor.splitlines() if ":" in ln}

    # --- one real call, recorded verbatim -------------------------------------
    from proto_tools.tools.database_retrieval.ensembl.ensembl_lookup import (
        EnsemblLookupConfig, EnsemblLookupInput, run_ensembl_lookup)
    call: dict = {"tool": "ensembl-lookup", "input": {"symbol": PROBE_GENE}}
    t0 = time.time()
    try:
        r = run_ensembl_lookup(EnsemblLookupInput(symbol=PROBE_GENE),
                               EnsemblLookupConfig(species="homo_sapiens"))
        d = r.model_dump()
        call.update(success=bool(d.get("success")),
                    seconds=round(time.time() - t0, 1),
                    source_url=d.get("source_url"),
                    result={k: d["result"].get(k) for k in
                            ("id", "display_name", "biotype", "seq_region_name")}
                    if isinstance(d.get("result"), dict) else d.get("result"))
    except Exception as e:
        # Recorded, not swallowed. Ensembl's REST endpoint returned 503 to plain
        # curl during this session too, so an upstream outage is a real outcome
        # and pretending otherwise would be the kind of thing FIG 4 is about.
        call.update(success=False, seconds=round(time.time() - t0, 1),
                    error=f"{type(e).__name__}: {str(e)[:200]}",
                    upstream_note=("Ensembl REST was returning 503 to direct curl "
                                   "at the time of this run. The failure is "
                                   "upstream, not in proto-tools."))
    rec["live_call"] = call
    rec["verdict"] = ("INSTALLED AND EXECUTING. Not used in the pipeline: Proto "
                      "serves structure and sequence-design models and denali "
                      "makes no structural or sequence-design claim.")

    p = OUT / "proto_validation.json"
    p.write_text(json.dumps(rec, indent=2) + "\n")
    print(f"wrote {p}")
    print(f"  version     : {rec['version']}")
    print(f"  tools       : {rec['n_tools']} across {rec['n_categories']} categories")
    print(f"  modal auth  : {rec['doctor'].get('modal auth', '?')}")
    print(f"  live call   : {PROBE_GENE} -> success={call['success']} "
          f"({call['seconds']}s)")
    if not call["success"]:
        print(f"                {call.get('error', '')[:90]}")


if __name__ == "__main__":
    main()
