# SPDX-License-Identifier: Apache-2.0
"""Acceptance criterion U3: in audit mode, fetching rtm:hasGitRepo +
rtm:hasGitCommit MUST succeed (External URI Rules §6.2).

Network-marked. Auto-skipped unless FLEXO_RTM_NETWORK_TESTS is set.
"""

from __future__ import annotations

import pytest
from oracle.uri.fetch import check_git_commit_exists

pytestmark = pytest.mark.network


def test_known_commit_on_public_repo_resolves() -> None:
    result = check_git_commit_exists(
        repo="https://github.com/python/cpython",
        # The 'main' branch's tip changes; instead, use the well-known initial
        # commit which is stable forever.
        commit="7f777ed95a19224294949e1b4ce56bbffcb1fe9f",
    )
    assert result.ok, result.detail


def test_unknown_commit_on_public_repo_fails() -> None:
    result = check_git_commit_exists(
        repo="https://github.com/python/cpython",
        commit="0" * 40,
    )
    assert not result.ok
