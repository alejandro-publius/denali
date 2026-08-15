# Sponsor tool status — verified 2026-08-15

Every row below was checked against this machine, not recalled. The column that
matters is the last one: whether anything in `results/frozen/` would differ if
the tool had not run. For all but two the answer is no, and that is the point of
the table rather than something to pad around.

| Tool | Installed | Auth | Verified how | Touched a number |
|---|:--:|:--:|---|:--:|
| **Claude Code** | ✅ `2.1.233` | ✅ | `claude --version` | yes, as the author |
| **Paperclip** | ✅ `0.7.37` | ✅ account authenticated | `paperclip config`; 113/113 gene queries stored; hosted MCP registered | yes, as the audited object |
| **Anthropic MCP** | ✅ `mcp 1.29.0` | n/a | `src/mcp_server.py` started over stdio, 2 tools listed, 3 calls returned non-empty | ships the result |
| **Modal** | ✅ `1.5.4` | ✅ workspace `alejandro-publius` | `modal app list` answered live — 0 apps ever deployed | no |
| **CZ Biohub / ESMC** | ✅ `esm 3.2.3` | ✅ hosted API key | verified twice — local weights **and** the hosted Biohub Platform API, both returning `(1, 67, 960)` | no |
| **Proto — Evo Design** | ✅ `proto-tools 0.1.0` | ✅ via Modal | installed from git; 140 tools / 17 categories; `proto-tools doctor` exits 0 | no |
| **Benchling** | ⚠ MCP endpoint live | ⏳ OAuth pending | `hackathon.mcp.bnchdev.org/mcp` returns 401 — up and gated | no |
| **Benchflow** | ✅ `0.6.7` | not required | `bench --help` runs; scaffolded a task to size the work | no — **declined** |
| **Tamarind Bio** | — | ✅ key authenticates | `GET /api/jobs` → 200, 0 jobs submitted | no — **declined** |
| **Boltz** | ❌ standalone | n/a | reachable through Proto | no — **declined** |
| **Sundial** | ❌ | ❌ | no discoverable install path | no |

## Declined on purpose, with the reason

A tool we could have run and chose not to is a different fact from one that would
not install. Collapsing the two is how a tool count stops meaning anything.

- **Benchflow — 4–6 hours, out of scope today.** The fit is real: their framing is
  that *a benchmark is just a frozen environment*, and ours is already frozen with
  pre-registered pass/fail thresholds, so each `verifier/test.sh` would be a
  threshold comparison rather than a judgment call. The cost is container work —
  one shared Dockerfile, four task dirs, and a `bench eval run` per task.
- **Tamarind Bio — nothing to submit.** The key authenticates (`GET /api/jobs`
  returns 200) and the account is live. It is a job runner for structure and
  docking workloads and we have no job of that kind, so it has run nothing.
- **Boltz — no structural claim.** Reachable via Proto and still declined. At
  −0.019 guide-pair concordance this project cannot make a gene-level claim, let
  alone a structural one, and running it would put a structure on the page that no
  result depends on.

## Notes that will otherwise be rediscovered the hard way

- **The venv has no `pip`.** It was built with `uv`. Install with
  `uv pip install --python .venv/bin/python <pkg>`.
- **`modal`, `bench` and `proto-tools` are not on PATH** — they live in `.venv/bin/`.
- **ESMC weights redirect.** `EvolutionaryScale/esmc-300m-2024-12` on HuggingFace
  now resolves to **`biohub/esmc-300m-2024-12`** — that redirect *is* the CZ Biohub
  integration. The local path is not gated — MIT, no HF token, first load
  downloads ~4 files. The hosted Biohub Platform API is a separate path and does
  need a key; both were tested and agree on output shape.
- **Proto runs on Modal by design.** `proto-tools doctor` reports auth, workspace,
  environment `proto-env`, and `0 of 56` apps deployed. Nothing was deployed.
- **Benchling: tenant provisioned, MCP gated.** The event tenant at
  `hackathon.bnchdev.org` has AI credits applied and needs no API key; the hosted
  MCP server at `hackathon.mcp.bnchdev.org/mcp` uses OAuth in the browser. An
  earlier note calling Benchling blocked was about a personal free account and is
  superseded. **We still did not use it: there is nothing in this pipeline to
  register.** Available and unused is the honest status.
- **Paperclip's MCP server is registered and deliberately unqueried.** Its index is
  live, and FIG 4 cites stored counts from 2026-08-15. Re-running the queries would
  move numbers the figure already reports.

## Three name collisions, all caught here

All the same failure mode: a PyPI name that looks like a sponsor tool and is not
one. The second was **our own published error** and is recorded in
`LIMITATIONS.md` §7.

- **`sundial` on PyPI is NOT the sponsor tool** — v0.0.1, a hobbyist progress-bar
  library. Do not install it and do not call it an integration.
- **`proto-language` on PyPI is NOT Proto.** We previously recorded Proto as
  "installs, then fails at import" on the strength of that package. Proto is Evo
  Design's generative-biology infrastructure and does not publish it. The real
  install is
  `pip install git+https://github.com/evo-design/proto-tools.git`, and it
  **succeeds**. We had already caught the `sundial` collision and warned about it
  in this file, then made the identical mistake one row down.
- **`tamarind` on PyPI is NOT Tamarind Bio** — it resolves to `tamarind==0.2.1` and
  pulls in `py2neo`, a Neo4j driver. Tamarind Bio is a REST API with an
  `x-api-key` header; `data2code/tamarind` on GitHub is a third-party wrapper, not
  official.
- **`benchflow` on PyPI IS the right package** — benchflow.ai, "the universal
  environment framework". No key needed for local use; the key references inside
  it are for LLM providers via litellm, not for BenchFlow itself.

## One question left for the organisers

**What is Sundial and where is it distributed?** No public presence found.
