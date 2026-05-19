# SPDX-License-Identifier: Apache-2.0
"""Pure-function RDF builders for the constructor.

Each builder takes typed inputs and returns an :class:`rdflib.Graph` of
triples ready to be staged into the local session backend. Descriptive
text uses ``rdfs:label`` (titles) and ``rdfs:comment`` (statements,
reasoning) to match the parsimony manifest's existing imports — no new
namespace footprint.

Six v0.1 attestation classes are accepted, three for the constructor's
primary write path (Satisfaction, Adequacy, Sufficiency) and three for
composition-context writes done by audit tooling. Each builder is a
single-purpose mapping from kwargs to a Graph; orchestration belongs in
``constructor/cli.py``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from rdflib import PROV, RDF, RDFS, Graph, Namespace, URIRef
from rdflib import Literal as RdfLiteral
from rdflib.namespace import XSD

RTM = Namespace("https://flexo-rtm.dev/ontology#")

AttestationClass = Literal[
    "SatisfactionAttestation",
    "AdequacyAttestation",
    "SufficiencyAttestation",
]
AttestationStatus = Literal["pass", "fail", "deferred", "deprecated"]


def build_requirement(*, iri: URIRef, title: str, statement: str | None = None) -> Graph:
    g = Graph()
    g.add((iri, RDF.type, RTM.Requirement))
    g.add((iri, RDFS.label, RdfLiteral(title)))
    if statement:
        g.add((iri, RDFS.comment, RdfLiteral(statement)))
    return g


def build_artifact(
    *,
    iri: URIRef,
    title: str,
    content_hash: str | None = None,
    git_commit: str | None = None,
) -> Graph:
    g = Graph()
    g.add((iri, RDF.type, RTM.Artifact))
    g.add((iri, RDFS.label, RdfLiteral(title)))
    if content_hash:
        g.add((iri, RTM.hasContentHash, RdfLiteral(content_hash)))
    if git_commit:
        g.add((iri, RTM.hasGitCommit, RdfLiteral(git_commit)))
    return g


def build_addresses_edge(*, artifact: URIRef, requirement: URIRef) -> Graph:
    g = Graph()
    g.add((artifact, RTM.addresses, requirement))
    return g


def build_attestation(
    *,
    iri: URIRef,
    attestation_class: AttestationClass,
    approved_by: URIRef,
    applies_to: URIRef,
    status: AttestationStatus,
    timestamp: datetime,
    reason: str | None = None,
) -> Graph:
    g = Graph()
    g.add((iri, RDF.type, URIRef(str(RTM) + attestation_class)))
    g.add((iri, RTM.approvedBy, approved_by))
    g.add((iri, RTM.status, URIRef(str(RTM) + status)))
    g.add((iri, RTM.appliesTo, applies_to))
    g.add(
        (
            iri,
            PROV.atTime,
            RdfLiteral(timestamp.isoformat(), datatype=XSD.dateTime),
        )
    )
    if reason:
        g.add((iri, RDFS.comment, RdfLiteral(reason)))
    return g


def build_deprecation(
    *,
    target_attestation: URIRef,
    invalidating_activity: URIRef,
    reason: str | None = None,
) -> Graph:
    """Emit deprecation triples for an existing attestation.

    Flexo branches are immutable, so we never mutate the original
    attestation's triples. Instead we add a single ``prov:wasInvalidatedBy``
    triple linking the attestation (a ``prov:Entity``) to the activity
    that invalidated it. The reason — if any — attaches to the activity,
    not the attestation, so a later reader can distinguish the original
    attestation's commentary from the deprecation explanation.
    """
    g = Graph()
    g.add((target_attestation, PROV.wasInvalidatedBy, invalidating_activity))
    if reason:
        g.add((invalidating_activity, RDFS.comment, RdfLiteral(reason)))
    return g


__all__ = [
    "AttestationClass",
    "AttestationStatus",
    "build_addresses_edge",
    "build_artifact",
    "build_attestation",
    "build_deprecation",
    "build_requirement",
]
