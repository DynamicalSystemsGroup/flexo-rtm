# SPDX-License-Identifier: Apache-2.0
"""Signed envelopes — Design Spec §4.5, Signed Envelope Shapes contract.

Five composable profiles (all off by default), one verification surface per:

- ``signed-commits`` — git GPG/SSH approver binding (S1 + I7).
- ``data-integrity-attestations`` — W3C VC-DI proofs on attestations (S2).
- ``dsse-activities`` — DSSE-enveloped in-toto attestations on activities (S3).
- ``cosign-images`` — Sigstore cosign bundles on OCI image references (S4).
- ``rekor-transparency`` — Sigstore Rekor log entries on attestations (S5).

The verification helpers lazy-import their optional dependencies; if an adopter
hasn't installed the relevant extra (``flexo-rtm[dsse]``, ``flexo-rtm[cosign]``),
calls raise :class:`OptionalDependencyMissing` with the install instruction.
"""

from oracle.signing.cryptosuites import (
    CRYPTOSUITES,
    CryptoSuite,
    is_known_cryptosuite,
)
from oracle.signing.errors import OptionalDependencyMissing, VerificationError
from oracle.signing.vc_di import sign_and_attach, verify_data_integrity_proof

__all__ = [
    "CRYPTOSUITES",
    "CryptoSuite",
    "OptionalDependencyMissing",
    "VerificationError",
    "is_known_cryptosuite",
    "sign_and_attach",
    "verify_data_integrity_proof",
]
