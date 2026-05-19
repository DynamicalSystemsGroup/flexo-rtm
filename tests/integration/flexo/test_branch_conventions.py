# SPDX-License-Identifier: Apache-2.0
"""F6 — branch model: main / engineering/<team> / cert/<run-id>."""

from __future__ import annotations

import pytest
from oracle.storage import InMemoryFlexoBackend
from oracle.storage.backend import TransactionError
from oracle.storage.iri_scheme import (
    CERT_BRANCH_PREFIX,
    ENGINEERING_BRANCH_PREFIX,
    MAIN_BRANCH,
    is_main_branch,
    is_valid_branch_name,
)


def test_main_branch_constant() -> None:
    assert MAIN_BRANCH == "main"
    assert is_main_branch("main")
    assert not is_main_branch("engineering/adcs")


def test_engineering_branch_pattern() -> None:
    assert is_valid_branch_name("engineering/adcs-team")
    assert is_valid_branch_name("engineering/safety")
    assert ENGINEERING_BRANCH_PREFIX == "engineering/"


def test_cert_branch_pattern() -> None:
    assert is_valid_branch_name("cert/01234567-89ab-cdef-0123-456789abcdef")
    assert CERT_BRANCH_PREFIX == "cert/"


def test_invalid_branch_names_rejected() -> None:
    assert not is_valid_branch_name("feature/x")  # not one of the three families
    assert not is_valid_branch_name("engineering//double-slash")
    assert not is_valid_branch_name("engineering/with space")
    assert not is_valid_branch_name("/leading-slash")
    assert not is_valid_branch_name("trailing-slash/")


def test_backend_rejects_invalid_branch_creation() -> None:
    backend = InMemoryFlexoBackend()
    with pytest.raises(TransactionError):
        backend.create_branch("feature/x")


def test_backend_creates_and_lists_valid_branches() -> None:
    backend = InMemoryFlexoBackend()
    backend.create_branch("engineering/adcs", from_branch="main")
    backend.create_branch("cert/run-1", from_branch="main")
    assert set(backend.list_branches()) == {"main", "engineering/adcs", "cert/run-1"}
