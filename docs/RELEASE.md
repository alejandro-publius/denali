# Releasing `denali-audit`

Right now a judge, a reviewer or a screener must clone a ~100 MB repository to run a
two-minute check. PyPI fixes that more cheaply than any repository surgery. Everything
below is done except the upload itself, which needs credentials this machine does not
have.

## State

| | |
|---|---|
| name `denali-audit` on PyPI | **free** (404 on the JSON API, checked 2026-08-16) |
| name on TestPyPI | **free** |
| `uv build` | builds both sdist and wheel |
| `twine check` | PASSED on both artifacts |
| clean-venv install | verified on 3.9, 3.11, 3.12 — see below |
| upload | **not done — no credentials on this machine** |

## What the clean-venv check found

The package claimed `requires-python = ">=3.9"` and that claim had never been tested
above 3.9. It was false. `denali audit` crashed on a clean install with:

```
ModuleNotFoundError: No module named 'scipy'
```

`pandas.Series.corr(method="spearman")` imports scipy internally. scipy is not a
declared dependency of this package, so the only reason the tool ever ran was that
scipy happened to be installed for other reasons on every machine it had been tried
on. A first user installing from PyPI into a clean environment would have hit this on
their first command.

Fixed by computing Spearman from its definition — Pearson on average ranks — in
`core.py::_spearman`. Verified to agree with `scipy.stats.spearmanr` to 5.6e-17 over
500 deliberately tie-heavy trials and exactly on the frozen study data. Adding scipy
as a dependency would also have worked, and was rejected: it is a large dependency for
one rank correlation in a tool whose entire argument is that running it should be
trivial.

Verified after the fix, each in a fresh venv with the built wheel and nothing else:

| Python | numpy / pandas resolved | suite | published headline |
|---|---|---|---|
| 3.9 | 2.0.2 / 2.2.3 | 33 passed | 0.4649 ✓ |
| 3.11 | 2.4.6 / 3.0.5 | 33 passed | — |
| 3.12 | 2.5.2 / 3.0.5 | 33 passed | 0.4649 ✓ |

The suite was run from a directory outside the repository, so the imports resolve to
the installed wheel rather than the source tree.

## Upload

```bash
make package                      # build + twine check + clean-venv smoke test

# TestPyPI first — it is a different account and a separate token
uv tool run twine upload --repository testpypi packages/denali-audit/dist/*
uv venv --python 3.12 /tmp/tpv && \
  uv pip install --python /tmp/tpv/bin/python \
    --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ denali-audit && \
  /tmp/tpv/bin/denali audit examples/example_gprofiler.csv

# then real PyPI
uv tool run twine upload packages/denali-audit/dist/*
```

The `--extra-index-url` is not optional: numpy and pandas are not on TestPyPI, so the
install resolves them from real PyPI.

## Immediately after the upload

Add the install line to the top of the main `README.md`. It is deliberately not there
yet — until the upload happens the command fails, and a README that opens with a
broken command is worse than one that opens without it. The line to add, directly
under the title:

```markdown
    pip install denali-audit
```

Then bump `version` in `packages/denali-audit/pyproject.toml` for any subsequent
release: PyPI refuses a re-upload of a version that already exists, and the fix is
always a new version, never a deletion.
