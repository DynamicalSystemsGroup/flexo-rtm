# SPDX-License-Identifier: Apache-2.0
"""Constructor identity resolver — engineer IRI from git config or override."""

from __future__ import annotations

from typing import Any

import pytest
from rdflib import URIRef

from oracle.constructor.identity import IdentityError, resolve_engineer_iri


def test_override_wins_when_provided() -> None:
    iri = resolve_engineer_iri(override="https://example.org/me")
    assert iri == URIRef("https://example.org/me")


def test_email_arg_mints_deterministic_iri() -> None:
    a = resolve_engineer_iri(email="z@example.org")
    b = resolve_engineer_iri(email="z@example.org")
    other = resolve_engineer_iri(email="x@example.org")
    assert a == b
    assert a != other
    assert str(a).startswith("urn:rtm:engineer/")


def test_falls_back_to_git_config(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(cmd: list[str], **kw: Any) -> Any:
        assert cmd[:3] == ["git", "config", "--get"]

        class _Proc:
            returncode = 0
            stdout = "z@example.org\n"
            stderr = ""

        return _Proc()

    monkeypatch.setattr("subprocess.run", fake_run)
    iri = resolve_engineer_iri()
    assert str(iri).startswith("urn:rtm:engineer/")


def test_raises_when_no_email_resolvable(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(cmd: list[str], **kw: Any) -> Any:
        class _Proc:
            returncode = 1
            stdout = ""
            stderr = "fatal: no config user.email"

        return _Proc()

    monkeypatch.setattr("subprocess.run", fake_run)
    with pytest.raises(IdentityError):
        resolve_engineer_iri()


def test_explicit_iri_must_be_absolute() -> None:
    """If the user passes a relative or empty override, raise — don't silently
    construct a malformed approver IRI that would fail SHACL at audit time."""
    with pytest.raises(IdentityError):
        resolve_engineer_iri(override="")
    with pytest.raises(IdentityError):
        resolve_engineer_iri(override="not-an-iri")
