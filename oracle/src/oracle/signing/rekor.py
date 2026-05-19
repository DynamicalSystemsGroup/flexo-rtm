# SPDX-License-Identifier: Apache-2.0
"""Sigstore Rekor stub verifier — Signed Envelope Shapes §8 + S5.

Verification uses the ``sigstore`` package (shared with cosign). Install via
``pip install 'flexo-rtm[cosign]'``.
"""

from __future__ import annotations

from oracle.signing.errors import OptionalDependencyMissing


def verify_rekor_inclusion_proof(entry_iri: str) -> bool:
    """Verify a Rekor transparency-log entry's Merkle inclusion proof.

    Raises :class:`OptionalDependencyMissing` until ``flexo-rtm[cosign]`` is
    installed (the cosign extra carries the sigstore client used here).
    """
    try:
        import sigstore  # noqa: F401
    except ImportError as exc:
        raise OptionalDependencyMissing(
            f"verify_rekor_inclusion_proof({entry_iri!r}) needs flexo-rtm[cosign]: "
            "pip install 'flexo-rtm[cosign]'"
        ) from exc
    raise NotImplementedError(  # pragma: no cover - lands when [cosign] is wired
        "Rekor verification pipeline lands when an adopter activates rekor-transparency"
    )


__all__ = ["verify_rekor_inclusion_proof"]
