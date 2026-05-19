# SPDX-License-Identifier: Apache-2.0
"""Resolve the engineer's approver IRI for `rtm:approvedBy` claims.

v0.1 keeps this minimal: the engineer either supplies an explicit override
(``--engineer-iri https://…``) or we derive a deterministic IRI from
``git config user.email`` via a stable hash. We don't reach into the
GitHub adapter here — the constructor's job is to write data; full
identity projection (FOAF, org membership) happens at audit time per
the identity adapter contract.

Adopters with a richer identity story override via the flag; otherwise
the email-hash IRI satisfies the SHACL approver shape (which only
demands the predicate's object be an IRI).
"""

from __future__ import annotations

import hashlib
import subprocess

from rdflib import URIRef


class IdentityError(RuntimeError):
    """Raised when no engineer identity can be resolved."""


_VALID_IRI_PREFIXES = ("http://", "https://", "urn:", "did:", "mailto:")


def _validate_iri(iri: str) -> URIRef:
    if not iri.startswith(_VALID_IRI_PREFIXES):
        raise IdentityError(
            f"engineer IRI {iri!r} is not absolute "
            "(must start with http(s)://, urn:, did:, mailto:)"
        )
    return URIRef(iri)


def _mint_from_email(email: str) -> URIRef:
    digest = hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()[:16]
    return URIRef(f"urn:rtm:engineer/{digest}")


def _read_git_email() -> str | None:
    try:
        proc = subprocess.run(  # noqa: S603 — fixed argv, no shell
            ["git", "config", "--get", "user.email"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    email = proc.stdout.strip()
    return email or None


def resolve_engineer_iri(
    *,
    override: str | None = None,
    email: str | None = None,
) -> URIRef:
    """Resolve the current engineer's approver IRI.

    Resolution order:

    1. ``override`` — if non-empty, treated as an explicit IRI.
    2. ``email`` — explicit email argument; minted as a stable urn:.
    3. ``git config --get user.email`` — same minting as (2).
    """
    if override is not None:
        return _validate_iri(override)
    if email:
        return _mint_from_email(email)
    git_email = _read_git_email()
    if git_email:
        return _mint_from_email(git_email)
    raise IdentityError(
        "no engineer IRI resolvable: pass --engineer-iri, --email, or set git config user.email"
    )


__all__ = ["IdentityError", "resolve_engineer_iri"]
