# SPDX-License-Identifier: Apache-2.0
"""S2 — data-integrity-attestations profile: SHACL gate plus an actual sign +
verify cycle using the eddsa-rdfc-2022 cryptosuite over a generated keypair.
"""

from __future__ import annotations

from pathlib import Path

import pyshacl
from oracle.signing import (
    OptionalDependencyMissing,
    sign_and_attach,
    verify_data_integrity_proof,
)
from rdflib import Graph, Literal, URIRef

from tests.conftest import ONTOLOGY_DIR

PROFILE: Path = ONTOLOGY_DIR / "profiles" / "data-integrity-attestations.shacl.ttl"
ASSEMBLED: Path = ONTOLOGY_DIR / "rtm.ttl"

ATT = URIRef("https://rtm.example/attest/1")
PRED_APPROVED_BY = URIRef("https://flexo-rtm.dev/ontology#approvedBy")
PRED_STATUS = URIRef("https://flexo-rtm.dev/ontology#status")
RTM_PASS = URIRef("https://flexo-rtm.dev/ontology#pass")
RDF_TYPE = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
SATISFACTION = URIRef("https://flexo-rtm.dev/ontology#SatisfactionAttestation")
APPROVER = URIRef("https://rtm.example/person/zargham")
VERIFICATION_METHOD = "https://rtm.example/person/zargham/keys/1"


def _bare_attestation() -> Graph:
    g = Graph()
    g.add((ATT, RDF_TYPE, SATISFACTION))
    g.add((ATT, PRED_APPROVED_BY, APPROVER))
    g.add((ATT, PRED_STATUS, RTM_PASS))
    return g


def _ed25519_keypair() -> tuple[bytes, bytes]:
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ed25519
    except ImportError as exc:
        raise OptionalDependencyMissing("test needs [signing] extra") from exc
    sk = ed25519.Ed25519PrivateKey.generate()
    sk_bytes = sk.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pk_bytes = sk.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return sk_bytes, pk_bytes


def _validate(turtle: str) -> tuple[bool, str]:
    data = Graph()
    data.parse(data=turtle, format="turtle")
    shapes = Graph()
    shapes.parse(PROFILE, format="turtle")
    ont = Graph()
    ont.parse(ASSEMBLED, format="turtle")
    conforms, _, text = pyshacl.validate(
        data_graph=data, shacl_graph=shapes, ont_graph=ont, inference="none", advanced=False
    )
    return conforms, text


def test_attestation_without_proof_fails_profile() -> None:
    bare = _bare_attestation()
    conforms, report = _validate(bare.serialize(format="turtle"))
    assert not conforms
    assert "sec:proof" in report or "proof" in report.lower()


def test_sign_and_verify_round_trip() -> None:
    sk, pk = _ed25519_keypair()
    signed = sign_and_attach(
        attestation_iri=ATT,
        graph=_bare_attestation(),
        private_key_bytes=sk,
        verification_method=VERIFICATION_METHOD,
    )
    assert verify_data_integrity_proof(
        graph=signed,
        public_key_bytes=pk,
        verification_method=VERIFICATION_METHOD,
    )


def test_tampered_payload_fails_verification() -> None:
    sk, pk = _ed25519_keypair()
    signed = sign_and_attach(
        attestation_iri=ATT,
        graph=_bare_attestation(),
        private_key_bytes=sk,
        verification_method=VERIFICATION_METHOD,
    )
    signed.add((ATT, URIRef("https://rtm.example/p/title"), Literal("tampered")))
    assert not verify_data_integrity_proof(
        graph=signed,
        public_key_bytes=pk,
        verification_method=VERIFICATION_METHOD,
    )


def test_signed_attestation_passes_profile() -> None:
    sk, _ = _ed25519_keypair()
    signed = sign_and_attach(
        attestation_iri=ATT,
        graph=_bare_attestation(),
        private_key_bytes=sk,
        verification_method=VERIFICATION_METHOD,
    )
    conforms, report = _validate(signed.serialize(format="turtle"))
    assert conforms, report


def test_random_keypair_independence() -> None:
    """Two independently generated keypairs cannot verify each other's signatures."""
    sk1, _ = _ed25519_keypair()
    _, pk2 = _ed25519_keypair()
    signed = sign_and_attach(
        attestation_iri=ATT,
        graph=_bare_attestation(),
        private_key_bytes=sk1,
        verification_method=VERIFICATION_METHOD,
    )
    assert not verify_data_integrity_proof(
        graph=signed,
        public_key_bytes=pk2,
        verification_method=VERIFICATION_METHOD,
    )
