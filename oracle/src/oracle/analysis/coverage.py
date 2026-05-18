# SPDX-License-Identifier: Apache-2.0
"""Addresses coverage stats — Quantitative Outcomes §v0.1 coverage metrics.

Operates over a materialised scope (an rdflib Graph). Forward = % of requirements
that have at least one addressing artifact; backward = % of artifacts that address
at least one requirement. ADDRESSES is the structural per-edge claim; SATISFACTION
is a separate human-attested judgment recorded via rtm:SatisfactionAttestation
(profile-gated, slice 9). Per X4, coverage is reported per-dimension; no rolled-up
"% certified" number is produced here. Empty populations report 100% as the
vacuous-truth convention so absent dimensions do not erode the PASS bar.
"""

from __future__ import annotations

from rdflib import RDF, Graph, URIRef

from oracle.models import CoverageStats

RTM = "https://flexo-rtm.dev/ontology#"
RTM_REQUIREMENT = URIRef(RTM + "Requirement")
RTM_ARTIFACT = URIRef(RTM + "Artifact")
RTM_ADDRESSES = URIRef(RTM + "addresses")


def compute_coverage(graph: Graph) -> CoverageStats:
    requirements = set(graph.subjects(RDF.type, RTM_REQUIREMENT))
    artifacts = set(graph.subjects(RDF.type, RTM_ARTIFACT))

    if requirements:
        covered_requirements = {
            r for r in requirements if any(graph.triples((None, RTM_ADDRESSES, r)))
        }
        forward_percent = 100.0 * len(covered_requirements) / len(requirements)
    else:
        forward_percent = 100.0

    if artifacts:
        covered_artifacts = {a for a in artifacts if any(graph.triples((a, RTM_ADDRESSES, None)))}
        backward_percent = 100.0 * len(covered_artifacts) / len(artifacts)
    else:
        backward_percent = 100.0

    return CoverageStats(
        forward_percent=forward_percent,
        backward_percent=backward_percent,
    )


__all__ = ["compute_coverage"]
