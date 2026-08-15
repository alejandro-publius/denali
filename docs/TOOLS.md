# Sponsor tool status — verified 2026-08-15

Every row below was checked against this machine, not recalled.

| Tool | Installed | Auth | Verified how |
|---|:--:|:--:|---|
| **Claude Code** | ✅ `2.1.233` | ✅ | `claude --version` |
| **Paperclip** | ✅ `0.7.37` | ✅ `thealexschroeder@gmail.com` | `paperclip config`, 113/113 gene queries run |
| **Modal** | ✅ `1.5.4` | ✅ workspace `alejandro-publius` | token in `~/.modal.toml`, verified against `api.modal.com` |
| **CZ Biohub / ESMC** | ✅ `esm 3.2.3` | n/a — open weights | **real forward pass**: `esmc_300m` → embeddings `(1, 67, 960)` |
| **Benchflow** | ✅ `0.6.7` | not required | `benchflow --help` works; CLIs `bench`, `benchflow` |
| **Benchling** | ⚠ SDK `1.25.0` | ✅ **PROVISIONED** | tenant at `hackathon.bnchdev.org`, AI credits applied, no key needed. **Not used** — nothing in our pipeline to register |
| **Sundial** | ❌ | ❌ | no discoverable install path |
| **Proto (Arc)** | ❌ | ❌ | not attempted; recorded gotcha below |

## Notes that will otherwise be rediscovered the hard way

- **The venv has no `pip`.** It was built with `uv`. Install with
  `uv pip install --python .venv/bin/python <pkg>`.
- **`modal` is not on PATH** — it lives at `.venv/bin/modal`.
- **ESMC weights redirect.** `EvolutionaryScale/esmc-300m-2024-12` on HuggingFace
  now resolves to **`biohub/esmc-300m-2024-12`** — that redirect *is* the CZ Biohub
  integration. **Not gated**, MIT, no HF token needed. First load downloads ~4
  files and took ~3.5 min.
- **Benchling: PROVISIONED, superseding an earlier note.** An event tenant exists
  at `hackathon.bnchdev.org` with AI credits already applied and no key required;
  the same credits cover the MCP server and the API. My earlier finding — that
  `benchling.com/patagoniabear` is a free personal account whose Developer
  Platform 404s — was correct about *that* account and is superseded by the
  provisioned tenant. **We still did not use it: there is nothing in this
  pipeline to register.** Available and unused is the honest status, not blocked.
- **`sundial` on PyPI is NOT the sponsor tool** — v0.0.1, a hobbyist progress-bar
  library. Do not install it and do not call it an integration.
- **`benchflow` on PyPI IS the right package** — benchflow.ai, "universal
  environment framework". No key needed for local use; the key references inside
  it are for LLM providers via litellm, not for BenchFlow itself.
- **Proto:** `pip install proto-language` succeeds then **fails at import** —
  PyPI metadata omits `proto_tools`. Recorded from earlier work; not retried.

## Two questions for the organisers

1. ~~Is there a re:AGENT Benchling tenant?~~ **Answered: yes**, `hackathon.bnchdev.org`.
2. **What is Sundial and where is it distributed?** No public presence found.

## What this changes for the plan

Steps 5–7 are unblocked: **Modal is live and ESMC runs.** Step 8 (Benchling
write-back) is blocked on an organiser tenant. None of this touches the demo
spine — steps 1–4 and 9–10 — which is already done and frozen in
`results/frozen/`.
