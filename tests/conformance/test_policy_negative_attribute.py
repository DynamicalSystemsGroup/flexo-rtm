# SPDX-License-Identifier: Apache-2.0
"""Acceptance criterion I3: same approver lacking the required attribute MUST FAIL
even if role matches.
"""

from __future__ import annotations

from oracle.identity.policy import check_attestation_authorization
from rdflib import Graph

# Person has the role but NO clearance attribute → not authorized.
PROJECTION_NO_CLEARANCE = """
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

POLICY = """
@prefix rtm: <https://flexo-rtm.dev/ontology#> .

<https://rtm.example/policy/safety-suff>
    a rtm:Policy ;
    rtm:appliesToRole          <https://rtm.example/role/safety-engineer> ;
    rtm:permitsAttestationType rtm:SatisfactionAttestation ;
    rtm:permitsAspect          <https://rtm.example/aspect/safety> ;
    rtm:withinScope            <https://rtm.example/scope/adcs> ;
    rtm:requiresAttribute      <https://rtm.example/policy/safety-suff/req-clearance> .

<https://rtm.example/policy/safety-suff/req-clearance>
    rtm:attributeKey "clearance" ;
    rtm:attributeValue "SECRET" .
"""

ATTESTATION = """
@prefix rtm:  <https://flexo-rtm.dev/ontology#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .

<https://rtm.example/req/r1>
    rtm:hasAspect <https://rtm.example/aspect/safety> ;
    rtm:inScope   <https://rtm.example/scope/adcs> .

<https://rtm.example/attest/1>
    a rtm:SatisfactionAttestation ;
    rtm:approvedBy <https://rtm.example/person/zargham> ;
    rtm:appliesTo  <https://rtm.example/req/r1> ;
    rtm:status     rtm:pass ;
    prov:atTime    "2026-05-18T12:00:00Z"^^xsd:dateTime .
"""


def _g(turtle: str) -> Graph:
    g = Graph()
    g.parse(data=turtle, format="turtle")
    return g


def test_missing_required_attribute_rejects_attestation() -> None:
    result = check_attestation_authorization(
        attestation_graph=_g(ATTESTATION),
        projection_graph=_g(PROJECTION_NO_CLEARANCE),
        policy_graph=_g(POLICY),
    )
    assert not result.authorized
    assert "not authorized" in result.report_text.lower()
