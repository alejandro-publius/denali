"""Makes the vendored product importable to the study, once, here.

`packages/denali-audit/` is committed in this repository rather than installed, so
that `make judge-check` needs no network and a clean clone can run the tool with no
install step. That means something has to put it on the path, and before this the
answer was "each module that needs it, separately" -- src/audit_screen.py,
src/corpus_rerank.py and src/mcp_server.py were each about to carry their own copy
of the same two lines, which is the small version of exactly the duplication the
package was extracted to remove.

Any `python -m src.<module>` invocation imports this package first, so every study
module can `from denali_audit... import ...` and get the in-repo copy. An installed
denali-audit would shadow it only if it came earlier on sys.path; the insert is at
position 0 so the vendored copy wins, which is what reproduction requires.
"""
from __future__ import annotations

import sys
from pathlib import Path

_VENDORED = Path(__file__).resolve().parents[1] / "packages" / "denali-audit"
if str(_VENDORED) not in sys.path:
    sys.path.insert(0, str(_VENDORED))
