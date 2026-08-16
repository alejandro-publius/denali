"""Test THIS checkout, not whatever `denali-audit` happens to be installed.

Found the hard way: an editable install left pointing at a different clone meant
`make judge-check` was importing that clone's `denali_audit` and reporting it as
this repository's result. The suite passed while testing code nobody was editing.
Putting the package root first on sys.path makes the import unambiguous.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
