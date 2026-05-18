# SPDX-License-Identifier: Apache-2.0
"""Acceptance criterion I5: the three reference adapters (GitHub, generic OIDC,
GitHub Actions OIDC) take sample claim payloads and produce projection triples
that conform to the SHACL identity-projection shape.
"""

from __future__ import annotations

from pathlib import Path

import pyshacl
from oracle.identity.adapters.gha_oidc import project_gha_oidc_token
from oracle.identity.adapters.github import project_github_user
from oracle.identity.adapters.oidc import ClaimMapping, project_oidc_user
from rdflib import FOAF, RDF, Graph

from tests.conftest import ONTOLOGY_DIR

SHAPE_PATH: Path = ONTOLOGY_DIR / "shapes" / "identity_projection.shacl.ttl"
ASSEMBLED: Path = ONTOLOGY_DIR / "rtm.ttl"


def _conforms(g: Graph) -> tuple[bool, str]:
    shapes = Graph()
    shapes.parse(SHAPE_PATH, format="turtle")
    ont = Graph()
    ont.parse(ASSEMBLED, format="turtle")
    conforms, _, report_text = pyshacl.validate(
        data_graph=g,
        shacl_graph=shapes,
        ont_graph=ont,
        inference="none",
        advanced=False,
    )
    return conforms, report_text


def test_github_adapter_emits_conforming_projection() -> None:
    g = project_github_user(
        {
            "login": "zargham",
            "name": "Michael Zargham",
            "email": "michael@example.org",
            "teams": [
                {
                    "organization": "dynamicalsystemsgroup",
                    "slug": "safety",
                    "attributes": {"clearance": "SECRET"},
                }
            ],
        }
    )
    persons = list(g.subjects(RDF.type, FOAF.Person))
    assert len(persons) == 1
    conforms, report = _conforms(g)
    assert conforms, f"github projection failed shape:\n{report}"


def test_oidc_adapter_emits_conforming_projection_with_custom_mapping() -> None:
    payload = {
        "iss": "https://idp.example.org",
        "sub": "user-123",
        "name": "Engineer A",
        "email": "engineer@example.org",
        "groups": ["safety-engineer"],
        "clearance_level": "SECRET",
    }
    g = project_oidc_user(
        payload,
        mapping=ClaimMapping(
            organization_iri="https://rtm.example/org/idp",
            attribute_claims={"clearance_level": "clearance"},
        ),
    )
    conforms, report = _conforms(g)
    assert conforms, f"oidc projection failed shape:\n{report}"


def test_gha_oidc_adapter_emits_projection_with_workflow_attributes() -> None:
    g = project_gha_oidc_token(
        {
            "sub": "repo:dynamicalsystemsgroup/flexo-rtm:ref:refs/heads/main",
            "repository": "dynamicalsystemsgroup/flexo-rtm",
            "workflow": "ci",
            "ref": "refs/heads/main",
            "job_workflow_ref": "dynamicalsystemsgroup/flexo-rtm/.github/workflows/ci.yml@SHA",
        }
    )
    # GHA OIDC projection emits an ephemeral identity + attributes (no foaf:Person
    # because the keyless signer is not a human). It conforms via emptiness of the
    # foaf:Person target class.
    conforms, report = _conforms(g)
    assert conforms, f"GHA OIDC projection failed shape:\n{report}"
    assert len(list(g.triples((None, None, None)))) > 0
