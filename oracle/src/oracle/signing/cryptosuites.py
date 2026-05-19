# SPDX-License-Identifier: Apache-2.0
"""Cryptosuite registry — Signed Envelope Shapes §3 + ADR-026.

The active cryptosuite supplies the algorithm; flexo-rtm never picks an
algorithm directly. The registry below enumerates the v0.1 suites and the
hashlib / cryptography primitives each one binds to.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class CryptoSuite:
    identifier: str
    digest_name: str
    signature_name: str
    digest_factory: Callable[[], hashlib._Hash]


CRYPTOSUITES: dict[str, CryptoSuite] = {
    "eddsa-rdfc-2022": CryptoSuite(
        identifier="eddsa-rdfc-2022",
        digest_name="SHA-256",
        signature_name="Ed25519",
        digest_factory=hashlib.sha256,
    ),
    "ecdsa-rdfc-2019": CryptoSuite(
        identifier="ecdsa-rdfc-2019",
        digest_name="SHA-256",
        signature_name="ECDSA-P256",
        digest_factory=hashlib.sha256,
    ),
    "ecdsa-rdfc-2019-p384": CryptoSuite(
        identifier="ecdsa-rdfc-2019-p384",
        digest_name="SHA-384",
        signature_name="ECDSA-P384",
        digest_factory=hashlib.sha384,
    ),
    "cosign-v1": CryptoSuite(
        identifier="cosign-v1",
        digest_name="SHA-256",
        signature_name="ECDSA-P256",
        digest_factory=hashlib.sha256,
    ),
    "dsse-v1": CryptoSuite(
        identifier="dsse-v1",
        digest_name="payload-defined",
        signature_name="per-envelope",
        digest_factory=hashlib.sha256,
    ),
    "gpg-default": CryptoSuite(
        identifier="gpg-default",
        digest_name="SHA-256",
        signature_name="per-key",
        digest_factory=hashlib.sha256,
    ),
    "ssh-default": CryptoSuite(
        identifier="ssh-default",
        digest_name="SHA-256",
        signature_name="per-key",
        digest_factory=hashlib.sha256,
    ),
}


def is_known_cryptosuite(identifier: str) -> bool:
    return identifier in CRYPTOSUITES


__all__ = ["CRYPTOSUITES", "CryptoSuite", "is_known_cryptosuite"]
