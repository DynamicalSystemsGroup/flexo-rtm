# SPDX-License-Identifier: Apache-2.0
"""GitHub identity adapter — Identity Adapter Contract §7.1.

Input: GitHub user payload (REST/GraphQL response). Output: projection RDF.
"""

from __future__ import annotations

from typing import Any

from rdflib import FOAF, RDF, Graph, Literal, Namespace, URIRef

RTM = Namespace("https://flexo-rtm.dev/ontology#")
ORG = Namespace("http://www.w3.org/ns/org#")
GH = Namespace("https://github.com/")


def _person_iri(login: str) -> URIRef:
    return URIRef(f"https://flexo-rtm.dev/identity/github/{login}")


def _membership_iri(login: str, team: str) -> URIRef:
    return URIRef(f"https://flexo-rtm.dev/identity/github/{login}/membership/{team}")


def _team_org_iri(org: str) -> URIRef:
    return URIRef(f"https://flexo-rtm.dev/identity/github/org/{org}")


def _role_iri(team: str) -> URIRef:
    return URIRef(f"https://flexo-rtm.dev/role/{team}")


def project_github_user(payload: dict[str, Any]) -> Graph:
    """Map a GitHub user payload to projection triples.

    The payload shape we accept (subset of the REST + GraphQL responses):

    .. code-block:: json

        {
          "login": "zargham",
          "name": "Michael Zargham",
          "email": "michael@example.org",
          "teams": [
            {"organization": "dynamicalsystemsgroup", "slug": "adcs",
             "attributes": {"clearance": "SECRET"}}
          ]
        }
    """
    g = Graph()
    g.bind("rtm", RTM)
    g.bind("foaf", FOAF)
    g.bind("org", ORG)

    login = payload["login"]
    person = _person_iri(login)
    g.add((person, RDF.type, FOAF.Person))
    g.add((person, RTM.hasExternalIdentity, Literal(f"github:{login}")))
    if name := payload.get("name"):
        g.add((person, FOAF.name, Literal(name)))
    if email := payload.get("email"):
        g.add((person, FOAF.mbox, URIRef(f"mailto:{email}")))

    for team in payload.get("teams", []):
        organization = team["organization"]
        slug = team["slug"]
        membership = _membership_iri(login, f"{organization}-{slug}")
        org_iri = _team_org_iri(organization)
        role = _role_iri(slug)

        g.add((person, ORG.hasMembership, membership))
        g.add((membership, RDF.type, ORG.Membership))
        g.add((membership, ORG.organization, org_iri))
        g.add((membership, ORG.role, role))
        g.add((org_iri, RDF.type, ORG.Organization))
        g.add(
            (
                org_iri,
                RTM.hasExternalIdentity,
                Literal(f"github-org:{organization}"),
            )
        )

        for key, value in team.get("attributes", {}).items():
            attr = URIRef(f"{membership}/attribute/{key}")
            g.add((membership, RTM.hasAttribute, attr))
            g.add((attr, RDF.type, RTM.Attribute))
            g.add((attr, RTM.attributeKey, Literal(key)))
            g.add((attr, RTM.attributeValue, Literal(value)))

    return g


__all__ = ["project_github_user"]
