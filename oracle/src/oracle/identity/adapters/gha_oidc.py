# SPDX-License-Identifier: Apache-2.0
"""GitHub Actions OIDC adapter (CI keyless) — Identity Adapter Contract §7.3.

Input: Fulcio-issued OIDC token claims from a GitHub Actions workflow.
Output: ephemeral projection scoped to the workflow run (short TTL).
"""

from __future__ import annotations

from typing import Any

from rdflib import RDF, Graph, Literal, Namespace, URIRef

RTM = Namespace("https://flexo-rtm.dev/ontology#")


def _identity_iri(sub: str) -> URIRef:
    safe = sub.replace("/", "-").replace(":", "-")
    return URIRef(f"https://flexo-rtm.dev/identity/fulcio/{safe}")


def project_gha_oidc_token(claims: dict[str, Any]) -> Graph:
    """Map a GitHub Actions Fulcio-issued OIDC token to projection triples.

    Sample claim shape (subset of what Fulcio exposes):

    .. code-block:: json

        {
          "sub": "repo:dynamicalsystemsgroup/flexo-rtm:ref:refs/heads/main",
          "repository": "dynamicalsystemsgroup/flexo-rtm",
          "workflow": "ci",
          "ref": "refs/heads/main",
          "job_workflow_ref": "dynamicalsystemsgroup/flexo-rtm/.github/workflows/ci.yml@SHA"
        }
    """
    g = Graph()
    g.bind("rtm", RTM)

    sub = claims["sub"]
    identity = _identity_iri(sub)
    g.add(
        (
            identity,
            RTM.hasExternalIdentity,
            Literal(f"fulcio:{sub}"),
        )
    )

    for claim_name, attr_key in (
        ("repository", "ci-repository"),
        ("workflow", "ci-workflow"),
        ("ref", "ci-ref"),
        ("job_workflow_ref", "ci-job-workflow-ref"),
    ):
        if claim_name in claims:
            attr = URIRef(f"{identity}/attribute/{attr_key}")
            g.add((identity, RTM.hasAttribute, attr))
            g.add((attr, RDF.type, RTM.Attribute))
            g.add((attr, RTM.attributeKey, Literal(attr_key)))
            g.add((attr, RTM.attributeValue, Literal(claims[claim_name])))

    return g


__all__ = ["project_gha_oidc_token"]
