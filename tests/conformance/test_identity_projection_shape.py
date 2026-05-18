# SPDX-License-Identifier: Apache-2.0
"""Acceptance criterion I1 (extension): identity projections conform to the SHACL
shape in ontology/shapes/identity_projection.shacl.ttl.

The approver-on-Attestation half of I1 is covered by tests/conformance/
test_attestation_shape.py (slice 1). This file covers the projection side:
foaf:Person needs an external identity, org:Membership needs role+org, etc.
"""

from __future__ import annotations

from pathlib import Path

import pyshacl
from rdflib import Graph

from tests.conftest import ONTOLOGY_DIR

SHAPE_PATH: Path = ONTOLOGY_DIR / "shapes" / "identity_projection.shacl.ttl"
ASSEMBLED: Path = ONTOLOGY_DIR / "rtm.ttl"

OK_PROJECTION = """
@prefix rtm:  <https://flexo-rtm.dev/ontology#> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix org:  <http://www.w3.org/ns/org#> .

<https://rtm.example/person/zargham>
    a foaf:Person ;
    rtm:hasExternalIdentity "github:zargham" ;
    org:hasMembership <https://rtm.example/membership/1> .

<https://rtm.example/membership/1>
    a org:Membership ;
    org:role         <https://rtm.example/role/safety-engineer> ;
    org:organization <https://rtm.example/org/adcs> .
"""

PERSON_WITHOUT_EXTERNAL_ID = """
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
<https://rtm.example/person/no-id> a foaf:Person .
"""

MEMBERSHIP_WITHOUT_ROLE = """
@prefix org: <http://www.w3.org/ns/org#> .
<https://rtm.example/membership/no-role>
    a org:Membership ;
    org:organization <https://rtm.example/org/x> .
"""


def _validate(data_turtle: str) -> tuple[bool, str]:
    data = Graph()
    data.parse(data=data_turtle, format="turtle")
    shapes = Graph()
    shapes.parse(SHAPE_PATH, format="turtle")
    ont = Graph()
    ont.parse(ASSEMBLED, format="turtle")
    conforms, _, report_text = pyshacl.validate(
        data_graph=data,
        shacl_graph=shapes,
        ont_graph=ont,
        inference="none",
        advanced=False,
    )
    return conforms, report_text


def test_conforming_projection_passes() -> None:
    conforms, report = _validate(OK_PROJECTION)
    assert conforms, f"expected pass, got:\n{report}"


def test_person_without_external_identity_fails() -> None:
    conforms, report = _validate(PERSON_WITHOUT_EXTERNAL_ID)
    assert not conforms
    assert "rtm:hasExternalIdentity" in report


def test_membership_without_role_fails() -> None:
    conforms, report = _validate(MEMBERSHIP_WITHOUT_ROLE)
    assert not conforms
    assert "org:role" in report
