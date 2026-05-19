# SPDX-License-Identifier: Apache-2.0
"""F7 — ``@pytest.mark.live`` auto-skips without ``FLEXO_TOKEN``.

This test is itself marked ``live`` and asserts that when it runs, the
environment variable is set. In CI without ``FLEXO_TOKEN`` the conftest hook
skips it; with ``FLEXO_TOKEN`` it would actually exercise the Flexo HTTPS
client (which is not part of this file — slice 11 wires the live smoke test).
"""
from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.live


def test_live_marker_skips_without_flexo_token() -> None:
    """If we got here, ``FLEXO_TOKEN`` was set — the conftest hook lets us run.
    The assertion is structural: live tests must not silently no-op when the
    token IS set; they must assert their precondition explicitly."""
    assert os.environ.get("FLEXO_TOKEN"), (
        "live test executed without FLEXO_TOKEN — conftest skip logic is broken"
    )
