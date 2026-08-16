#!/bin/bash
# Reference solution. The denali size correction -- denali_audit.core.rerank --
# reimplemented standalone so the container needs nothing from the repository.
# Verified to reproduce the answer key exactly on all seven screens (balanced
# accuracy 1.0000).
#
# Two choices decide the answer and both are stated in task.md rather than left
# to be guessed, because guessing them is not the skill under test:
#
#   fit over ALL sets in the screen, not just the ten being judged. A line fit
#   on ten points is a different and much noisier line, and it moves entries.
#
#   y = log10(1 + hits)   a hit count lives on that scale -- 0 to 10 hits matters
#                         more than 500 to 510.
#   x = size              RAW, not logged. A set with twice the genes gets roughly
#                         twice the chances, which is linear in size. Logging the
#                         x-axis too looks tidier and measures a weaker, different
#                         thing.
#
# stdlib only: the residual rank is an ordinary least-squares line and a sort.
set -eu
mkdir -p /logs/artifacts
python3 - <<'PY'
import csv, json, math

TOP = 10
ranked = json.load(open("/app/data/ranked_top10.json"))
answer = {}

for screen, entries in sorted(ranked.items()):
    sizes, hits = [], []
    with open(f"/app/data/{screen}.csv") as fh:
        for row in csv.DictReader(fh):
            sizes.append(float(row["size"]))
            hits.append(float(row["hits"]))

    n = len(sizes)
    y = [math.log10(1.0 + h) for h in hits]
    mx, my = sum(sizes) / n, sum(y) / n
    sxx = sum((x - mx) ** 2 for x in sizes)
    sxy = sum((x - mx) * (v - my) for x, v in zip(sizes, y))
    slope = sxy / sxx if sxx else 0.0
    intercept = my - slope * mx
    resid = [v - (slope * x + intercept) for x, v in zip(sizes, y)]

    # Rank 1 = largest residual. Stable order on ties, matching the packaged
    # tool, which breaks ties by input order.
    order = sorted(range(n), key=lambda i: (-resid[i], i))
    size_aware_rank = [0] * n
    for place, i in enumerate(order, 1):
        size_aware_rank[i] = place

    # Size-carried: in the top 10 by hits, not in the top 10 by residual.
    answer[screen] = [e["rank"] for e in entries
                      if size_aware_rank[e["row"]] > TOP]

json.dump(answer, open("/logs/artifacts/answer.json", "w"), indent=2, sort_keys=True)
print(json.dumps(answer, indent=2, sort_keys=True))
PY
