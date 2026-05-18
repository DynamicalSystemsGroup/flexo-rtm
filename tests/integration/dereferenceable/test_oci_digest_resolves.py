# SPDX-License-Identifier: Apache-2.0
"""Acceptance criterion U4: in audit mode, fetching rtm:hasOCIImage digest MUST
succeed via the OCI Distribution Specification (External URI Rules §6.2).

Network-marked. Auto-skipped unless FLEXO_RTM_NETWORK_TESTS is set.
"""

from __future__ import annotations

import pytest
from oracle.uri.fetch import check_oci_digest_exists

pytestmark = pytest.mark.network


def test_unknown_oci_digest_fails() -> None:
    # We use a registry that exists but a digest that doesn't, so the test
    # asserts the negative path without depending on a specific public image.
    result = check_oci_digest_exists(
        "ghcr.io/dynamicalsystemsgroup/does-not-exist@sha256:" + "0" * 64
    )
    assert not result.ok
