# SPDX-License-Identifier: Apache-2.0
"""Acceptance criterion I1: every rtm:Attestation requires rtm:approvedBy <IRI>."""

from __future__ import annotations

from pathlib import Path

import pyshacl
from rdflib import Graph

from tests.conftest import ONTOLOGY_DIR

SHAPE_PATH: Path = ONTOLOGY_DIR / "shapes" / "attestation_shape.ttl"

ATTESTATION_WITH_APPROVER = """
@prefix rtm: <https://flexo-rtm.dev/ontology#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<https://rtm.example/attest/1>
    a rtm:SatisfactionAttestation ;
    rtm:approvedBy <https://github.com/zargham> ;
    rtm:status rtm:pass ;
    prov:atTime "2026-05-18T12:00:00Z"^^xsd:dateTime .
"""

ATTESTATION_WITHOUT_APPROVER = """
@prefix rtm: <https://flexo-rtm.dev/ontology#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<https://rtm.example/attest/1>
    a rtm:SatisfactionAttestation ;
    rtm:status rtm:pass ;
    prov:atTime "2026-05-18T12:00:00Z"^^xsd:dateTime .
"""


def _validate(data_turtle: str) -> tuple[bool, Graph, str]:
    shapes = Graph()
    shapes.parse(SHAPE_PATH, format="turtle")
    ontology = Graph()
    ontology.parse(ONTOLOGY_DIR / "core" / "rtm-core.ttl", format="turtle")
    data = Graph()
    data.parse(data=data_turtle, format="turtle")
    conforms, report_graph, report_text = pyshacl.validate(
        data_graph=data,
        shacl_graph=shapes,
        ont_graph=ontology,
        inference="none",
        advanced=False,
    )
    return conforms, report_graph, report_text


def test_attestation_with_approver_passes() -> None:
    conforms, _, report_text = _validate(ATTESTATION_WITH_APPROVER)
    assert conforms, f"expected pass, got:\n{report_text}"


def test_attestation_without_approver_fails_with_named_message() -> None:
    conforms, _, report_text = _validate(ATTESTATION_WITHOUT_APPROVER)
    assert not conforms
    assert "Every attestation requires a named human approver IRI" in report_text
