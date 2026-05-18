# SPDX-License-Identifier: Apache-2.0
"""Policy authorization helper — Identity Adapter Contract §5.

Wraps pyshacl with the policy_authorization.shacl.ttl shape and packages the
result into a small dataclass. Used at attestation-write time and by the
acceptance tests for I2, I3, I4.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pyshacl
from rdflib import Graph

ONTOLOGY_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "ontology"
POLICY_SHAPE_PATH = ONTOLOGY_DIR / "shapes" / "policy_authorization.shacl.ttl"
ASSEMBLED_ONTOLOGY = ONTOLOGY_DIR / "rtm.ttl"


@dataclass(frozen=True)
class AuthorizationResult:
    authorized: bool
    report_text: str


def check_attestation_authorization(
    *,
    attestation_graph: Graph,
    projection_graph: Graph,
    policy_graph: Graph,
) -> AuthorizationResult:
    """Validate attestations in ``attestation_graph`` against policies in
    ``policy_graph``, evaluating ``projection_graph`` for approver role +
    attribute matching. Returns whether every attestation is authorized.
    """
    data = Graph()
    for triple in attestation_graph:
        data.add(triple)
    for triple in projection_graph:
        data.add(triple)
    for triple in policy_graph:
        data.add(triple)

    shapes = Graph()
    shapes.parse(POLICY_SHAPE_PATH, format="turtle")

    ontology = Graph()
    ontology.parse(ASSEMBLED_ONTOLOGY, format="turtle")

    conforms, _, report_text = pyshacl.validate(
        data_graph=data,
        shacl_graph=shapes,
        ont_graph=ontology,
        inference="none",
        advanced=True,
    )
    return AuthorizationResult(authorized=conforms, report_text=report_text)


__all__ = ["AuthorizationResult", "check_attestation_authorization"]
