# SPDX-License-Identifier: Apache-2.0
"""Sigstore cosign stub verifier — Signed Envelope Shapes §7 + S4.

Verification uses the ``sigstore`` package, which is NOT installed by default.
Install via ``pip install 'flexo-rtm[cosign]'``.
"""

from __future__ import annotations

from oracle.signing.errors import OptionalDependencyMissing


def verify_cosign_bundle(bundle_iri: str, *, image_digest: str) -> bool:
    """Verify a cosign signature bundle for an OCI image digest.

    Raises :class:`OptionalDependencyMissing` until ``flexo-rtm[cosign]`` is
    installed.
    """
    try:
        import sigstore  # noqa: F401
    except ImportError as exc:
        raise OptionalDependencyMissing(
            f"verify_cosign_bundle({bundle_iri!r}, image={image_digest!r}) needs "
            "flexo-rtm[cosign]: pip install 'flexo-rtm[cosign]'"
        ) from exc
    raise NotImplementedError(  # pragma: no cover - lands when [cosign] is wired
        "cosign verification pipeline lands when an adopter activates cosign-images"
    )


__all__ = ["verify_cosign_bundle"]
