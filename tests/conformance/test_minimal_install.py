# SPDX-License-Identifier: Apache-2.0
"""Acceptance criterion X5: no proprietary deps in the default install."""

from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path

from tests.conftest import REPO_ROOT

PYPROJECT: Path = REPO_ROOT / "pyproject.toml"

ALLOWED_OPTIONAL_EXTRAS = {"signing", "dsse", "cosign", "analysis", "viz"}


def test_no_non_pypi_default_deps() -> None:
    data = tomllib.loads(PYPROJECT.read_text())
    deps: list[str] = data["project"]["dependencies"]
    for d in deps:
        spec = d.strip()
        assert "@" not in spec, f"non-PyPI source in default dep: {spec!r}"
        assert "file://" not in spec, f"local-path dep forbidden: {spec!r}"
        assert "git+" not in spec, f"git source forbidden: {spec!r}"


def test_optional_extras_are_known() -> None:
    data = tomllib.loads(PYPROJECT.read_text())
    extras = set(data["project"].get("optional-dependencies", {}).keys())
    unknown = extras - ALLOWED_OPTIONAL_EXTRAS
    assert not unknown, f"unexpected optional-dependency groups: {unknown}"


def test_cli_help_exits_zero() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "oracle.cli", "--help"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"--help exited {result.returncode}\nstdout:{result.stdout}\nstderr:{result.stderr}"
    )
    assert "flexo-rtm" in result.stdout.lower() or "usage" in result.stdout.lower()


def test_cli_version_exits_zero() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "oracle.cli", "--version"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0
    assert "0.0.1" in result.stdout
