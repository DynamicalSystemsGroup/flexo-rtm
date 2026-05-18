# SPDX-License-Identifier: Apache-2.0
"""Generic OIDC identity adapter — Identity Adapter Contract §7.2.

Input: OIDC ID-token claims + UserInfo payload (merged). Output: projection RDF.

The claim-mapping is configurable so adopters can adapt to their IdP's custom
claims without code changes (§7.2 'Configuration: YAML mapping file').
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from rdflib import FOAF, RDF, Graph, Literal, Namespace, URIRef

RTM = Namespace("https://flexo-rtm.dev/ontology#")
ORG = Namespace("http://www.w3.org/ns/org#")


@dataclass(frozen=True)
class ClaimMapping:
    """Adopter-supplied mapping from OIDC claim names to projection predicates."""

    name_claim: str = "name"
    email_claim: str = "email"
    groups_claim: str = "groups"
    issuer_claim: str = "iss"
    subject_claim: str = "sub"
    organization_iri: str | None = None
    attribute_claims: dict[str, str] = field(default_factory=dict)


def _person_iri(issuer: str, sub: str) -> URIRef:
    safe = sub.replace("/", "-").replace(":", "-")
    return URIRef(f"https://flexo-rtm.dev/identity/oidc/{safe}")


def project_oidc_user(
    payload: dict[str, Any],
    *,
    mapping: ClaimMapping | None = None,
) -> Graph:
    m = mapping or ClaimMapping()
    g = Graph()
    g.bind("rtm", RTM)
    g.bind("foaf", FOAF)
    g.bind("org", ORG)

    issuer = payload[m.issuer_claim]
    sub = payload[m.subject_claim]
    person = _person_iri(issuer, sub)
    g.add((person, RDF.type, FOAF.Person))
    g.add(
        (
            person,
            RTM.hasExternalIdentity,
            Literal(f"oidc:{issuer}#{sub}"),
        )
    )
    if name := payload.get(m.name_claim):
        g.add((person, FOAF.name, Literal(name)))
    if email := payload.get(m.email_claim):
        g.add((person, FOAF.mbox, URIRef(f"mailto:{email}")))

    org_iri = URIRef(m.organization_iri) if m.organization_iri else URIRef(issuer)
    g.add((org_iri, RDF.type, ORG.Organization))

    for group in payload.get(m.groups_claim, []):
        membership = URIRef(f"{person}/membership/{group}")
        role = URIRef(f"https://flexo-rtm.dev/role/{group}")
        g.add((person, ORG.hasMembership, membership))
        g.add((membership, RDF.type, ORG.Membership))
        g.add((membership, ORG.organization, org_iri))
        g.add((membership, ORG.role, role))

    for claim_name, attr_key in m.attribute_claims.items():
        if claim_name in payload:
            attr = URIRef(f"{person}/attribute/{attr_key}")
            g.add((person, RTM.hasAttribute, attr))
            g.add((attr, RDF.type, RTM.Attribute))
            g.add((attr, RTM.attributeKey, Literal(attr_key)))
            g.add((attr, RTM.attributeValue, Literal(payload[claim_name])))

    return g


__all__ = ["ClaimMapping", "project_oidc_user"]
