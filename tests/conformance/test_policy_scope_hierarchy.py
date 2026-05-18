# SPDX-License-Identifier: Apache-2.0
"""Acceptance criterion I4: an approver scoped to rtm:scope/adcs is authorized for
sub-scopes (via rtm:extends), but NOT for sibling scopes.
"""

from __future__ import annotations

from oracle.identity.policy import check_attestation_authorization
from rdflib import Graph

PROJECTION = """
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

<https://rtm.example/policy/adcs-safety>
    a rtm:Policy ;
    rtm:appliesToRole          <https://rtm.example/role/safety-engineer> ;
    rtm:permitsAttestationType rtm:SatisfactionAttestation ;
    rtm:permitsAspect          <https://rtm.example/aspect/safety> ;
    rtm:withinScope            <https://rtm.example/scope/adcs> .
"""

# adcs-attitude-control extends adcs; safety-only extends adcs.
# adcs-comms does NOT extend adcs (sibling scope).
SCOPES = """
@prefix rtm: <https://flexo-rtm.dev/ontology#> .

<https://rtm.example/scope/adcs-attitude-control>
    a rtm:Scope ;
    rtm:extends <https://rtm.example/scope/adcs> .

<https://rtm.example/scope/adcs-comms> a rtm:Scope .
"""


def _req_attestation_in_scope(scope_iri: str) -> str:
    return f"""
@prefix rtm:  <https://flexo-rtm.dev/ontology#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .

<https://rtm.example/req/r1>
    rtm:hasAspect <https://rtm.example/aspect/safety> ;
    rtm:inScope   <{scope_iri}> .

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


def test_subscope_authorization_extends_via_rtm_extends() -> None:
    attestation = _g(_req_attestation_in_scope("https://rtm.example/scope/adcs-attitude-control"))
    # The scope hierarchy lives in the projection graph (any graph the SPARQL
    # sees; we colocate it with the projection for the test).
    projection = _g(PROJECTION)
    projection.parse(data=SCOPES, format="turtle")
    result = check_attestation_authorization(
        attestation_graph=attestation,
        projection_graph=projection,
        policy_graph=_g(POLICY),
    )
    assert result.authorized, f"sub-scope must inherit, got:\n{result.report_text}"


def test_sibling_scope_authorization_rejected() -> None:
    attestation = _g(_req_attestation_in_scope("https://rtm.example/scope/adcs-comms"))
    projection = _g(PROJECTION)
    projection.parse(data=SCOPES, format="turtle")
    result = check_attestation_authorization(
        attestation_graph=attestation,
        projection_graph=projection,
        policy_graph=_g(POLICY),
    )
    assert not result.authorized
