# SPDX-License-Identifier: Apache-2.0
"""Live interop: W3C VC Data Integrity 2.0 eddsa-rdfc-2022 test vector.

Sister test to ``tests/integration/flexo/test_live_smoke.py`` — adapter
divergences only surface against real upstream. This fetches the canonical
eddsa-rdfc-2022 signed credential and key pair from the W3C VC-DI EdDSA
spec's TestVectors and runs them through our
:func:`oracle.signing.vc_di.verify_data_integrity_proof`.

Source:
- https://github.com/w3c/vc-di-eddsa/tree/main/TestVectors/eddsa-rdfc-2022
- https://github.com/w3c/vc-di-eddsa/blob/main/TestVectors/keyPair.json

A failure here is a real cross-implementation divergence — see
flexo-rtm-research issue tracker.
"""

from __future__ import annotations

import json
import urllib.request

import pytest
from oracle.signing.vc_di import verify_data_integrity_proof
from rdflib import Graph

pytestmark = [
    pytest.mark.network,
    pytest.mark.xfail(
        strict=True,
        reason=(
            "v0.1 vc_di diverges from W3C VC-DI 2.0 in three ways "
            "(multibase proofValue, JSON-LD 1.1 @graph proof container, "
            "hash-concat signing payload); tracked at flexo-rtm-research#27"
        ),
    ),
]

VECTOR_URL = (
    "https://raw.githubusercontent.com/w3c/vc-di-eddsa/main/"
    "TestVectors/eddsa-rdfc-2022/signedDataInt.json"
)
KEYPAIR_URL = (
    "https://raw.githubusercontent.com/w3c/vc-di-eddsa/main/TestVectors/keyPair.json"
)

_B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def _b58decode(s: str) -> bytes:
    n = 0
    for ch in s:
        n = n * 58 + _B58_ALPHABET.index(ch)
    body = n.to_bytes((n.bit_length() + 7) // 8, "big") if n else b""
    pad = len(s) - len(s.lstrip("1"))
    return b"\x00" * pad + body


def _multibase_base58btc_decode(s: str) -> bytes:
    assert s.startswith("z"), f"expected multibase-base58btc 'z' prefix; got {s[:3]!r}"
    return _b58decode(s[1:])


def _multikey_to_raw_ed25519_pub(public_key_multibase: str) -> bytes:
    """Decode a Multikey-encoded ed25519 public key to the raw 32-byte form."""
    decoded = _multibase_base58btc_decode(public_key_multibase)
    assert decoded[0:2] == b"\xed\x01", (
        f"expected ed25519-pub multicodec prefix 0xED01; got {decoded[0:2].hex()}"
    )
    return decoded[2:]


def _fetch(url: str) -> str:
    req = urllib.request.Request(  # noqa: S310 — fixed raw.githubusercontent.com URL
        url, headers={"User-Agent": "flexo-rtm-live-test"}
    )
    with urllib.request.urlopen(req, timeout=15) as r:  # noqa: S310
        return r.read().decode("utf-8")


def test_w3c_eddsa_rdfc_2022_reference_vector_verifies() -> None:
    """The W3C VC-DI eddsa-rdfc-2022 reference vector verifies through our impl.

    If this fails, the divergence between our v0.1 implementation and the W3C
    spec is one (or both) of:

    1. **proofValue encoding** — W3C mandates multibase-base58btc with ``z``
       prefix; our :mod:`oracle.signing.vc_di` emits and consumes base64.
    2. **Signing payload** — W3C signs
       ``SHA-256(canonicalize(doc-without-proof)) || SHA-256(canonicalize(proof-config))``;
       our impl signs the raw RDFC-1.0 canonical bytes of the proof-stripped
       graph.
    """
    signed_jsonld = json.loads(_fetch(VECTOR_URL))
    keypair = json.loads(_fetch(KEYPAIR_URL))

    public_key_raw = _multikey_to_raw_ed25519_pub(keypair["publicKeyMultibase"])
    verification_method = signed_jsonld["proof"]["verificationMethod"]

    g = Graph()
    g.parse(data=json.dumps(signed_jsonld), format="json-ld")

    verified = verify_data_integrity_proof(
        graph=g,
        public_key_bytes=public_key_raw,
        verification_method=verification_method,
    )
    assert verified, (
        "W3C eddsa-rdfc-2022 reference vector did not verify — see docstring "
        "for likely divergences"
    )
