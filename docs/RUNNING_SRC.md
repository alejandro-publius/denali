# Running things in `src/`

**These are pipeline steps, not command-line tools.** With one exception they do
not parse arguments at all: `python -m src.<anything> --help` **ignores the flag
and runs the step**, which for `src.sweep` means fifteen minutes and for the
`freeze_*` modules means rewriting files in `results/frozen/`. Nothing is
damaged if you do this — every step is deterministic, which is the whole point,
and the outputs land byte-identical — but it is not what you asked for.

| You want | Run |
|---|---|
| the whole pipeline | `make all` |
| the tests | `make test` |
| the page | `make page` |
| **to audit your own screen** | `denali audit` — the packaged CLI, see the top of this file |
| the same check without installing | `python -m src.audit_screen --help` — the in-repo original |
| a next-experiment proposal | `python -m src.next_experiment --demo` |
| the MCP server | `python -m src.mcp_server` |

The reason they are not CLIs is the byte-frozen scorer: `src/score_k562.py` is
pinned at sha256 `2abfdc6f…` and verified on load, so adding argument parsing to
it would invalidate every number in this repository. Rather than make one module
an exception to a rule the rest follow, they all stayed plain. That is a real
cost and it is stated here rather than discovered.
