# SPDX-License-Identifier: Apache-2.0
"""Acceptance criterion I6: adding a new adapter requires only conforming to the
input/output schema. The IdentityAdapter Protocol is the conformance contract.
"""

from __future__ import annotations

from typing import Any

from oracle.identity.adapters import IdentityAdapter
from oracle.identity.adapters.gha_oidc import project_gha_oidc_token
from oracle.identity.adapters.github import project_github_user
from oracle.identity.adapters.oidc import project_oidc_user
from rdflib import RDF, Graph, Literal, Namespace, URIRef


def _runtime_protocol_check(adapter: IdentityAdapter, payload: dict[str, Any]) -> Graph:
    """Returns the projection graph if the adapter satisfies the protocol."""
    return adapter(payload)


def test_reference_adapters_satisfy_protocol() -> None:
    # GitHub
    g = _runtime_protocol_check(
        project_github_user,
        {"login": "u", "teams": [{"organization": "o", "slug": "t"}]},
    )
    assert isinstance(g, Graph)

    # OIDC
    g = _runtime_protocol_check(
        project_oidc_user,
        {
            "iss": "https://idp.example.org",
            "sub": "u",
            "name": "u",
            "groups": ["t"],
        },
    )
    assert isinstance(g, Graph)

    # GHA OIDC
    g = _runtime_protocol_check(
        project_gha_oidc_token,
        {"sub": "repo:o/r:ref:refs/heads/main"},
    )
    assert isinstance(g, Graph)


def test_new_adapter_with_no_core_changes_works() -> None:
    """A hypothetical SAML adapter, written in user code, plugs in by satisfying
    the IdentityAdapter Protocol. No oracle/ change is required.
    """
    RTM = Namespace("https://flexo-rtm.dev/ontology#")
    FOAF = Namespace("http://xmlns.com/foaf/0.1/")

    def project_saml_user(payload: dict[str, Any]) -> Graph:
        g = Graph()
        person = URIRef(f"https://rtm.example/person/saml/{payload['nameid']}")
        g.add((person, RDF.type, FOAF.Person))
        g.add((person, RTM.hasExternalIdentity, Literal(f"saml:{payload['nameid']}")))
        return g

    # Runtime structural conformance check — the host application can swap adapters
    # behind this Protocol without changing any framework code.
    adapter: IdentityAdapter = project_saml_user
    g = adapter({"nameid": "user-123"})
    assert isinstance(g, Graph)
    assert len(g) == 2
