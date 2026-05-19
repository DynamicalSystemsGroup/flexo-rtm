# SPDX-License-Identifier: Apache-2.0
"""S1 — when the signed-commits profile is active, every rtm:Attestation must
cite its introducing commit + signature key, and that signature key must match
a public key declared on rtm:approvedBy.
"""

from __future__ import annotations

from pathlib import Path

import pyshacl
from rdflib import Graph

from tests.conftest import ONTOLOGY_DIR

PROFILE: Path = ONTOLOGY_DIR / "profiles" / "signed-commits.shacl.ttl"
ASSEMBLED: Path = ONTOLOGY_DIR / "rtm.ttl"

ATT_FPR = "ABC123DEADBEEF0987"

WELL_FORMED = f"""
@prefix rtm:  <https://flexo-rtm.dev/ontology#> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .

<https://rtm.example/person/zargham>
    a foaf:Person ;
    rtm:hasExternalIdentity "github:zargham" ;
    rtm:hasPublicKey <https://rtm.example/person/zargham/key/1> .

<https://rtm.example/person/zargham/key/1>
    rtm:keyType "openpgp" ;
    rtm:keyFingerprint "{ATT_FPR}" .

<https://rtm.example/commit/abc>
    rtm:signedByKey "{ATT_FPR}" .

<https://rtm.example/attest/1>
    a rtm:SatisfactionAttestation ;
    rtm:approvedBy <https://rtm.example/person/zargham> ;
    rtm:introducedByCommit <https://rtm.example/commit/abc> ;
    rtm:status rtm:pass ;
    prov:atTime "2026-05-18T12:00:00Z"^^xsd:dateTime .
"""

MISSING_COMMIT = """
@prefix rtm:  <https://flexo-rtm.dev/ontology#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .

<https://rtm.example/attest/1>
    a rtm:SatisfactionAttestation ;
    rtm:approvedBy <https://rtm.example/person/zargham> ;
    rtm:status rtm:pass ;
    prov:atTime "2026-05-18T12:00:00Z"^^xsd:dateTime .
"""

UNRECOGNIZED_KEY = """
@prefix rtm:  <https://flexo-rtm.dev/ontology#> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .

<https://rtm.example/person/zargham>
    a foaf:Person ;
    rtm:hasPublicKey <https://rtm.example/person/zargham/key/1> .

<https://rtm.example/person/zargham/key/1>
    rtm:keyFingerprint "EXPECTED-KEY-FINGERPRINT" .

<https://rtm.example/commit/abc>
    rtm:signedByKey "DIFFERENT-KEY-FINGERPRINT" .

<https://rtm.example/attest/1>
    a rtm:SatisfactionAttestation ;
    rtm:approvedBy <https://rtm.example/person/zargham> ;
    rtm:introducedByCommit <https://rtm.example/commit/abc> ;
    rtm:status rtm:pass ;
    prov:atTime "2026-05-18T12:00:00Z"^^xsd:dateTime .
"""


def _validate(turtle: str) -> tuple[bool, str]:
    data = Graph()
    data.parse(data=turtle, format="turtle")
    shapes = Graph()
    shapes.parse(PROFILE, format="turtle")
    ont = Graph()
    ont.parse(ASSEMBLED, format="turtle")
    conforms, _, text = pyshacl.validate(
        data_graph=data, shacl_graph=shapes, ont_graph=ont, inference="none", advanced=True
    )
    return conforms, text


def test_well_formed_signed_commit_attestation_passes() -> None:
    conforms, report = _validate(WELL_FORMED)
    assert conforms, report


def test_attestation_without_commit_link_fails() -> None:
    conforms, report = _validate(MISSING_COMMIT)
    assert not conforms
    assert "introducedByCommit" in report or "introducing commit" in report


def test_unrecognized_signing_key_fails() -> None:
    conforms, report = _validate(UNRECOGNIZED_KEY)
    assert not conforms
    assert "approver" in report.lower() or "fingerprint" in report.lower()
