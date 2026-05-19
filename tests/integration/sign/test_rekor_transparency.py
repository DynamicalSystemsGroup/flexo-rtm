# SPDX-License-Identifier: Apache-2.0
"""S5 — rekor-transparency profile gate + stub-verifier lazy-import check."""

from __future__ import annotations

import importlib
from pathlib import Path

import pyshacl
import pytest
from oracle.signing.errors import OptionalDependencyMissing
from oracle.signing.rekor import verify_rekor_inclusion_proof
from rdflib import Graph

from tests.conftest import ONTOLOGY_DIR

PROFILE: Path = ONTOLOGY_DIR / "profiles" / "rekor-transparency.shacl.ttl"
ASSEMBLED: Path = ONTOLOGY_DIR / "rtm.ttl"

WITH_REKOR = """
@prefix rtm:  <https://flexo-rtm.dev/ontology#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .

<https://rtm.example/attest/1>
    a rtm:SatisfactionAttestation ;
    rtm:approvedBy <https://rtm.example/person/zargham> ;
    rtm:status rtm:pass ;
    rtm:rekorLogEntry <https://rekor.sigstore.dev/api/v1/log/entries/108e9186e8c5f78c> ;
    prov:atTime "2026-05-18T12:00:00Z"^^xsd:dateTime .
"""

WITHOUT_REKOR = """
@prefix rtm:  <https://flexo-rtm.dev/ontology#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .

<https://rtm.example/attest/1>
    a rtm:SatisfactionAttestation ;
    rtm:approvedBy <https://rtm.example/person/zargham> ;
    rtm:status rtm:pass ;
    prov:atTime "2026-05-18T12:00:00Z"^^xsd:dateTime .
"""

MALFORMED_REKOR_IRI = """
@prefix rtm:  <https://flexo-rtm.dev/ontology#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .

<https://rtm.example/attest/1>
    a rtm:SatisfactionAttestation ;
    rtm:approvedBy <https://rtm.example/person/zargham> ;
    rtm:status rtm:pass ;
    rtm:rekorLogEntry <https://not-rekor.example.com/log/abc> ;
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
        data_graph=data, shacl_graph=shapes, ont_graph=ont, inference="none", advanced=False
    )
    return conforms, text


def test_attestation_with_rekor_entry_passes_profile() -> None:
    conforms, report = _validate(WITH_REKOR)
    assert conforms, report


def test_attestation_without_rekor_entry_fails_profile() -> None:
    conforms, _ = _validate(WITHOUT_REKOR)
    assert not conforms


def test_malformed_rekor_iri_fails_pattern() -> None:
    conforms, _ = _validate(MALFORMED_REKOR_IRI)
    assert not conforms


def test_verify_rekor_inclusion_proof_reports_missing_extra_when_dep_absent() -> None:
    if importlib.util.find_spec("sigstore") is not None:
        pytest.skip("flexo-rtm[cosign] (rekor shares) is installed; lazy-import not exercised")
    with pytest.raises(OptionalDependencyMissing) as exc:
        verify_rekor_inclusion_proof(
            "https://rekor.sigstore.dev/api/v1/log/entries/108e9186e8c5f78c"
        )
    assert "flexo-rtm[cosign]" in str(exc.value)
