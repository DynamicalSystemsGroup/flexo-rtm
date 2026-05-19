# SPDX-License-Identifier: Apache-2.0
"""DSSE + in-toto stub verifier — Signed Envelope Shapes §6 + S3.

The real verifier needs the ``in-toto-attestation`` + ``securesystemslib``
packages, which are NOT installed by default. Install via
``pip install 'flexo-rtm[dsse]'``. v0.1 ships the entry point; the full
verification pipeline lands when an adopter exercises the extra.
"""

from __future__ import annotations

from dataclasses import dataclass

from oracle.signing.errors import OptionalDependencyMissing


@dataclass(frozen=True)
class DSSEEnvelope:
    payload_type: str
    payload_b64: str
    signatures: tuple[dict[str, str], ...]


def verify_dsse_envelope(envelope_iri: str) -> bool:
    """Verify a DSSE-enveloped in-toto attestation referenced by IRI.

    Raises :class:`OptionalDependencyMissing` until ``flexo-rtm[dsse]`` is
    installed.
    """
    try:
        import in_toto_attestation  # noqa: F401
    except ImportError as exc:
        raise OptionalDependencyMissing(
            f"verify_dsse_envelope({envelope_iri!r}) needs flexo-rtm[dsse]: "
            "pip install 'flexo-rtm[dsse]'"
        ) from exc
    raise NotImplementedError(  # pragma: no cover - lands when [dsse] is wired
        "DSSE verification pipeline lands when an adopter activates the dsse-activities profile"
    )


__all__ = ["DSSEEnvelope", "verify_dsse_envelope"]
