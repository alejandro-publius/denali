# MCP server — wiring and tool reference

**Wiring it into a client.** An MCP client launches the server from its own
working directory, not from this repository, so both paths below are absolute
and `PYTHONPATH` is set explicitly. Replace `/abs/path/to/denali` with wherever
you cloned it and nothing else needs changing:

```json
{
  "mcpServers": {
    "denali": {
      "command": "/abs/path/to/denali/.venv/bin/python",
      "args": ["-m", "src.mcp_server"],
      "env": { "PYTHONPATH": "/abs/path/to/denali" }
    }
  }
}
```

Tested by starting the server from `/tmp` the way a client actually does. Until
2026-08-16 that failed: `results/frozen/` was resolved against the caller's
working directory, so anyone wiring this into an agent got a `FileNotFoundError`
rather than a server. Both modules now anchor to their own file location, and
the failure is recorded in `docs/LIMITATIONS.md` §7 rather than quietly fixed —
we had been demonstrating this server by running it from the repo root, which is
the one directory where the bug is invisible.

| Tool | Argument | Returns |
|---|---|---|
| `reversibility` | `program` (MSigDB name) | Measured result if the program is in the frozen 50 — rank, hits, tier, predicted vs. observed, residual — plus the generated next-experiment proposal. Held-out result if it was one of the ten. Otherwise an explicit `UNSCORED` response. |
| `provenance` | — | Hashes, the deciding statistic, gap numbers, evidence concentration, and the scope limit. |
| `audit` | `sizes` + `hits` (+ optional `corr`), or `table_path` | **Your** ranking, not ours: what share of it is predicted by set size alone, with a verdict of `CONFOUNDED`, `PARTIALLY CONFOUNDED`, `NOT SIZE-DOMINATED`, or `UNDETERMINED` when every set is the same size and the question cannot be asked. Where a reference applies, where your screen sits against 1,272 published ones. |
| `rerank` | `sizes` + `hits` (+ optional `names`, `top`), or `table_path` | Applies the size correction to **your** ranking and returns which of your top entries left the top, and how far each fell. The inverse of a candidate list. |
| `baseline` | `sizes` + `hits` + `predicted` + `metric`, or `table_path` + `predicted_column` | What a predictor that sees **only set size** scores on **your** evaluation, next to your model's score, and the difference. The metric is named by the caller and never inferred. A measurement, not a verdict on any model. |
| `floor` | `screen_id` | The published no-biology floor for one of the 1,272 screens in the atlas, with the method, the content hash and the citation string. Looked up, never recomputed, so every caller gets the identical number. A screen outside the atlas returns `NOT_IN_ATLAS` with the inclusion rule, never a guess. |

`table_path` accepts the file your enrichment tool already wrote — g:Profiler,
DAVID, clusterProfiler, Enrichr, fgsea, GSEA desktop, MAGeCK, drugZ and BAGEL are
recognised with no flags. Pointed at our own g:Profiler-shaped export, `audit`
returns 0.4649 and `rerank` returns 3 of 10 surviving: the same two numbers on the
page, through the same code path an outside agent gets.

Every response carries the scope limit. The `UNSCORED` branch reports the predictor's own failure verbatim:

> `"predictor_validation": "FAILED on held-out data: balanced accuracy 0.4375, worse than chance, zero true positives. The predictor is reported, not endorsed."`

A caller cannot mistake a prediction for a validated one.
