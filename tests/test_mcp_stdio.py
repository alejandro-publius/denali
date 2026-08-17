"""Start the MCP server as a real subprocess and call all three tools.

Every other check on the server imports `src.mcp_server` and calls the functions
directly, which proves the maths and proves nothing about the server. A client
does not import this module -- it launches a process, speaks stdio to it, and
does so **from its own working directory**. That distinction is not academic
here: until 2026-08-16 the server resolved `results/frozen/` against the
caller's cwd, so anyone wiring it into an agent got a `FileNotFoundError`
instead of a server, and every in-process check stayed green throughout. This
runs with `cwd="/"` for exactly that reason -- the repo root is the one
directory where that class of bug is invisible.

    make mcp-check          # or: .venv/bin/python tests/test_mcp_stdio.py

Skips cleanly (exit 0, loudly) when the optional `mcp` package is absent: the
study reproduces without it, so its absence must not fail the build.
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = ROOT / ".venv" / "bin" / "python"

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ModuleNotFoundError:
    print("SKIP  the `mcp` package is not installed. The study reproduces "
          "without it; `uv pip install --python .venv/bin/python mcp` to run "
          "this check.")
    raise SystemExit(0)

# A table that is size-driven by construction: hits track size closely, so the
# correction has something to find. Not our data and not anyone's real screen --
# the point is that the server accepts a stranger's table at all.
ROWS = [{"name": f"PATHWAY_{i}", "size": s, "hits": h}
        for i, (s, h) in enumerate(
            [(200, 5700), (190, 5600), (180, 5200), (175, 1700), (160, 1750),
             (150, 2400), (60, 900), (55, 1200), (40, 700), (35, 1100),
             (30, 400), (25, 800)])]

EXPECTED_TOOLS = ["audit", "baseline", "floor", "provenance", "rerank",
                  "reversibility"]

# The same rows with a prediction column. `pred_sizeish` is deliberately little
# more than set size with noise on it -- a model that knows nothing -- so the
# server must NOT report it as beating a size-only baseline.
PRED_SIZEISH = [s * 30.0 + (i % 5) * 40 for i, s in enumerate(
    [200, 190, 180, 175, 160, 150, 60, 55, 40, 35, 30, 25])]
ROWS_WITH_PRED = [dict(r, predicted=p) for r, p in zip(ROWS, PRED_SIZEISH)]

passed: list[str] = []
failed: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    (passed if cond else failed).append(f"{name}{'  --  ' + detail if detail else ''}")


async def run() -> None:
    params = StdioServerParameters(
        command=str(PY), args=["-m", "src.mcp_server"],
        env={"PYTHONPATH": str(ROOT), "PATH": "/usr/bin:/bin"},
        cwd="/",
    )
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()

            listed = sorted(t.name for t in (await s.list_tools()).tools)
            check("the server lists exactly the six documented tools",
                  listed == EXPECTED_TOOLS, f"listed {listed}")

            async def call(tool, args):
                return json.loads((await s.call_tool(tool, args)).content[0].text)

            d = await call("reversibility",
                           {"program": "HALLMARK_CHOLESTEROL_HOMEOSTASIS"})
            check("reversibility returns a measured program over stdio",
                  d.get("status") == "MEASURED" and d.get("knockdowns_that_moved_it", 0) > 0,
                  f"status {d.get('status')}")
            check("every reversibility answer carries the scope limit",
                  "scope_limit" in d)

            p = await call("provenance", {})
            check("provenance returns the frozen provenance record", bool(p),
                  f"{len(p)} keys")

            rr = await call("rerank", {"sets": ROWS, "top": 5})
            check("rerank accepts the caller's own table and corrects it",
                  rr.get("n_sets") == len(ROWS) and "survived_top_n" in rr,
                  f"n_sets {rr.get('n_sets')}")
            check("rerank reports what LEFT the top, not what held",
                  "left_the_top" in rr and "survivors" not in rr)
            check("rerank attaches the audit verdict for the caller's table",
                  rr.get("your_ranking", {}).get("verdict") in (
                      "MORE SIZE-CARRIED THAN ITS OWN NULL",
                      "INDISTINGUISHABLE FROM ITS OWN NULL",
                      "LESS SIZE-CARRIED THAN ITS OWN NULL"),
                  str(rr.get("your_ranking", {}).get("verdict")))
            check("rerank refuses to be read as a candidate list",
                  "not a candidate list" in rr.get("what_this_is_not", "").lower())
            check("rerank volunteers the predictor's own failure",
                  "0.4375" in rr.get("predictor_validation", ""),
                  rr.get("predictor_validation", "")[:60])

            # The refusals are the reason this server is safe to hand an agent.
            g = await call("reversibility", {"program": "TP53"})
            check("a bare gene symbol is refused", g.get("status") == "REFUSED")
            n = await call("reversibility", {"program": "top candidates to chase"})
            check("a request for a candidate ranking is refused",
                  n.get("status") == "REFUSED")
            check("the nomination refusal cites the held-out failure",
                  "0.4375" in n.get("reason", ""))

            small = await call("rerank", {"sets": ROWS[:4]})
            check("rerank refuses a table too small to say anything about",
                  small.get("status") == "REFUSED",
                  str(small.get("reason", ""))[:60])
            bad = await call("rerank", {"sets": [{"name": "x"}] * 12})
            check("rerank refuses rows missing size/hits rather than guessing",
                  bad.get("status") == "REFUSED")

            # ---- baseline, over the wire ----------------------------------
            bl = await call("baseline",
                            {"sets": ROWS_WITH_PRED, "metric": "spearman"})
            check("baseline scores the caller's model against size alone",
                  bl.get("your_score") is not None
                  and bl.get("size_only_score") is not None,
                  f"{bl.get('your_score')} vs {bl.get('size_only_score')}")
            check("baseline does not credit a size-only model with beating size",
                  bl.get("beats_size_alone") is False,
                  f"delta {bl.get('delta')}")
            _how = bl.get("how_the_baseline_was_built", "")
            check("baseline's own predictor never saw the row it predicts",
                  ("leave-one-out" in _how or "no fit" in _how)
                  and "IN-SAMPLE" not in _how, _how[:90])
            check("a model that is a monotone function of set size ties the "
                  "size-only baseline exactly",
                  bl.get("delta") == 0.0, f"delta {bl.get('delta')}")
            check("baseline refuses to be read as a verdict on a model",
                  "not a claim that any model is bad"
                  in bl.get("what_this_is_not", "").lower())
            nom = await call("baseline", {"sets": ROWS_WITH_PRED})
            check("baseline refuses to guess the caller's metric",
                  nom.get("status") == "REFUSED"
                  and "name the metric" in nom.get("reason", ""),
                  str(nom.get("reason", ""))[:60])
            unk = await call("baseline",
                             {"sets": ROWS_WITH_PRED, "metric": "auroc"})
            check("baseline refuses a metric it does not implement rather than "
                  "approximating it",
                  unk.get("status") == "REFUSED"
                  and "unrecognised metric" in unk.get("reason", ""))
            nop = await call("baseline",
                             {"sets": ROWS, "metric": "spearman"})
            check("baseline refuses rows with no prediction in them",
                  nop.get("status") == "REFUSED"
                  and "predicted" in nop.get("reason", ""))

            # ---- floor: the atlas lookup ----------------------------------
            fl = await call("floor", {"screen_id": 100})
            check("floor returns a published screen's no-biology floor",
                  fl.get("status") == "IN_ATLAS"
                  and isinstance(fl.get("no_biology_floor"), float),
                  str(fl.get("no_biology_floor")))
            check("floor hands back a citation that pins the source table",
                  "doi:10.1002/pro.3978" in fl.get("cite", "")
                  and len(fl.get("source_sha256", "")) == 64)
            check("floor refuses to be read as a score for the screen",
                  "not a quality score" in fl.get("what_this_is_not", "").lower())
            miss = await call("floor", {"screen_id": 999999999})
            check("floor refuses a screen it does not carry rather than "
                  "inventing a number",
                  miss.get("status") == "NOT_IN_ATLAS"
                  and "no_biology_floor" not in miss)
            check("the refusal states the rule that excluded it",
                  "inclusion_rule" in miss)


def main() -> int:
    if not PY.exists():
        print(f"SKIP  no interpreter at {PY}; run `make setup` first.")
        return 0
    asyncio.run(run())
    for x in passed:
        print(f"PASS  {x}")
    for x in failed:
        print(f"FAIL  {x}")
    print(f"\n{len(passed)}/{len(passed) + len(failed)} MCP stdio checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
