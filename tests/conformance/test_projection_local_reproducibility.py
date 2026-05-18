# SPDX-License-Identifier: Apache-2.0
"""Acceptance criterion I8: a verifier with read access to the recorded
projection-at-cert-time re-evaluates authorization locally; identity changes
after cert do NOT invalidate past attestations.
"""

from __future__ import annotations

from oracle.identity.policy import check_attestation_authorization
from rdflib import Graph

PROJECTION_AT_CERT_TIME = """
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

# After cert: the person has left the safety-engineering role.
PROJECTION_AFTER_ROLE_CHANGE = """
@prefix rtm:  <https://flexo-rtm.dev/ontology#> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix org:  <http://www.w3.org/ns/org#> .

<https://rtm.example/person/zargham>
    a foaf:Person ;
    rtm:hasExternalIdentity "github:zargham" ;
    org:hasMembership <https://rtm.example/membership/2> .

<https://rtm.example/membership/2>
    a org:Membership ;
    org:role         <https://rtm.example/role/observer> ;
    org:organization <https://rtm.example/org/adcs> .
"""

POLICY = """
@prefix rtm: <https://flexo-rtm.dev/ontology#> .

<https://rtm.example/policy/adcs-safety>
    a rtm:Policy ;
    rtm:appliesToRole          <https://rtm.example/role/safety-engineer> ;
    rtm:permitsAttestationType rtm:SatisfactionAttestation ;
    rtm:permitsAspect          <https://rtm.example/aspect/safety> ;
    rtm:withinScope            <https://rtm.example/scope/adcs> .
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


def test_authorization_is_a_pure_function_of_recorded_projection() -> None:
    """Same attestation + same recorded projection produces the same verdict
    regardless of present-day identity-provider state."""
    a = check_attestation_authorization(
        attestation_graph=_g(ATTESTATION),
        projection_graph=_g(PROJECTION_AT_CERT_TIME),
        policy_graph=_g(POLICY),
    )
    b = check_attestation_authorization(
        attestation_graph=_g(ATTESTATION),
        projection_graph=_g(PROJECTION_AT_CERT_TIME),
        policy_graph=_g(POLICY),
    )
    assert a.authorized == b.authorized
    assert a.authorized is True


def test_post_cert_role_change_does_not_invalidate_past_attestation() -> None:
    """The verifier evaluates against the recorded projection (not the live one)."""
    cert_time = check_attestation_authorization(
        attestation_graph=_g(ATTESTATION),
        projection_graph=_g(PROJECTION_AT_CERT_TIME),
        policy_graph=_g(POLICY),
    )
    assert cert_time.authorized is True

    # If we ran the live evaluation today (role removed), it would fail —
    # but that's a different question from "was this attestation authorized
    # at the time it was made?"
    after_change = check_attestation_authorization(
        attestation_graph=_g(ATTESTATION),
        projection_graph=_g(PROJECTION_AFTER_ROLE_CHANGE),
        policy_graph=_g(POLICY),
    )
    assert after_change.authorized is False
    # The post-cert evaluation is informational; the recorded projection is
    # the audit-of-record. Both pass and fail are independently computable.
