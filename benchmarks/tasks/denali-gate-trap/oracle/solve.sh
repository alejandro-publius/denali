#!/bin/bash
# Reference solution. Not the naive gate -- the naive gate scores 0.6981 and
# this task exists because that is not good enough.
#
# The insight the task is testing: measurability predicts how MUCH signal a
# program shows, not WHETHER it shows any. Almost everything returns something;
# only the smallest, least-measured programs return nothing at all. So predict
# "no result" only at the genuine floor, rather than wherever quality is poor.
set -eu
mkdir -p /logs/artifacts
python3 - <<'PY'
import csv, json
rows = list(csv.DictReader(open("/app/data/programs.csv")))
out = {}
for r in rows:
    n = float(r["n_present"])
    frac = float(r["frac_present"])
    # the floor: too few measured members for a rank test to resolve anything
    out[r["program"]] = not (n < 32 or frac < 0.34)
json.dump(out, open("/logs/artifacts/answer.json", "w"), indent=2, sort_keys=True)
print(f"wrote {len(out)} predictions, {sum(out.values())} positive")
PY
