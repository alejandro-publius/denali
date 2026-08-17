"""The version must have exactly one definition, and it must reach the wheel.

`denali --version` reads denali_audit.__version__. The wheel's metadata used to
be typed separately in pyproject.toml. Both said 0.1.0, so nothing was wrong yet
-- but nothing was checking, and the first release that bumped one and not the
other would have shipped a package whose metadata and whose CLI disagreed.

pyproject now derives its version from the module attribute, and this file is
what makes "derives" checkable rather than asserted.
"""
from __future__ import annotations

import re
from pathlib import Path

import denali_audit

PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"


def test_pyproject_does_not_hardcode_a_second_version():
    """A SOURCE-TREE check. `make package` runs this suite from outside the repo
    against the installed wheel, where pyproject.toml legitimately does not exist
    -- a wheel ships no build config. Skipping there is correct, but skipping
    because a file MOVED would be the vanishing-guard failure, so the two cases are
    distinguished: absent source tree skips, present-but-missing fails.
    """
    if not PYPROJECT.exists():
        import pytest
        pkg_root = PYPROJECT.parent
        assert not (pkg_root / "denali_audit").is_dir(), (
            f"{PYPROJECT} is missing but a source checkout is present at {pkg_root}. "
            "That is a moved or deleted build config, not a wheel-only run.")
        pytest.skip("no source tree here (wheel-only run); this check is in-repo only")
    t = PYPROJECT.read_text()
    assert 'dynamic = ["version"]' in t, "pyproject must derive the version, not restate it"
    assert not re.search(r'(?m)^version\s*=\s*"', t), (
        "a literal version reappeared in pyproject.toml; there must be exactly one "
        "definition and it lives in denali_audit/__init__.py")
    assert 'version = {attr = "denali_audit.__version__"}' in t


def test_version_is_a_sane_release_string():
    assert re.fullmatch(r"\d+\.\d+\.\d+([abrc.\-+\w]*)?", denali_audit.__version__), \
        denali_audit.__version__


def test_installed_metadata_agrees_when_the_package_is_installed():
    """When denali-audit is installed, the wheel's metadata must match the module.

    Asserted rather than gated: if the distribution is not installed this states
    so loudly instead of vanishing, because a check that disappears with its input
    is the failure mode this repository has hit repeatedly.
    """
    from importlib.metadata import PackageNotFoundError, version
    try:
        meta = version("denali-audit")
    except PackageNotFoundError:
        import pytest
        pytest.skip("denali-audit is not installed in this environment; "
                    "`make package` covers the built-wheel case")
        return
    assert meta == denali_audit.__version__, (meta, denali_audit.__version__)
