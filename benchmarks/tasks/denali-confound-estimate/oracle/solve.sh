#!/bin/bash
# Reference solution. The denali auditor's own method, reimplemented standalone
# so the container needs nothing from the repository. Verified to reproduce the
# answer key exactly on all seven screens (MAE 0.000000).
#
# The transform is asymmetric and that is deliberate, not an oversight:
#
#   y = log10(1 + hits)   because a hit count lives on that scale -- the
#                         difference between 0 and 10 hits matters more than
#                         between 500 and 510.
#   x = size              RAW, not logged.
#
# Logging the x-axis too looks tidier and is wrong: it scored MAE 0.1474
# against this key, worse than a constant. The confound being measured is that
# a set with twice the genes gets roughly twice the chances, which is linear in
# size. Compressing that axis measures a different, weaker thing.
set -eu
mkdir -p /logs/artifacts
python3 - <<'PY'
import csv, glob, json, math, os

def r2_size_alone(path):
    xs, ys = [], []
    with open(path) as fh:
        for row in csv.DictReader(fh):
            try:
                size, hits = float(row["size"]), float(row["hits"])
            except (KeyError, ValueError):
                continue
            if not (math.isfinite(size) and math.isfinite(hits)):
                continue
            xs.append(size)                      # raw size
            ys.append(math.log10(1.0 + hits))    # log1p hits
    n = len(xs)
    if n < 8:                       # the auditor's own floor
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return 0.0
    return round((sxy * sxy) / (sxx * syy), 4)

out = {}
for p in sorted(glob.glob("/app/data/screen_*.csv")):
    out[os.path.basename(p)[:-4]] = r2_size_alone(p)
json.dump(out, open("/logs/artifacts/answer.json", "w"), indent=2, sort_keys=True)
print(json.dumps(out, indent=2, sort_keys=True))
PY
