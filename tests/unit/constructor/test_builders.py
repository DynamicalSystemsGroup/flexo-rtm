# SPDX-License-Identifier: Apache-2.0
"""Constructor builders — pure-function unit tests.

Each builder takes typed inputs and returns an ``rdflib.Graph`` of triples
ready to be staged into the local session. Descriptive text uses ``rdfs:label``
(titles) and ``rdfs:comment`` (statements / reasoning) to match the
parsimony manifest's existing imports — no new namespace footprint.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from oracle.constructor.builders import (
    build_addresses_edge,
    build_artifact,
    build_attestation,
    build_deprecation,
    build_requirement,
)
from rdflib import PROV, RDF, RDFS, Literal, Namespace, URIRef
from rdflib.namespace import XSD

RTM = Namespace("https://flexo-rtm.dev/ontology#")


def test_build_requirement_emits_typed_labelled_resource() -> None:
    iri = URIRef("https://rtm.example/req/REQ-001")
    g = build_requirement(iri=iri, title="Attitude pointing accuracy")

    assert (iri, RDF.type, RTM.Requirement) in g
    assert (iri, RDFS.label, Literal("Attitude pointing accuracy")) in g
    assert len(g) == 2


def test_build_requirement_attaches_statement_as_rdfs_comment() -> None:
    iri = URIRef("https://rtm.example/req/REQ-002")
    g = build_requirement(
        iri=iri,
        title="Pointing accuracy",
        statement="The ADCS shall maintain pointing accuracy ≤ 0.1°.",
    )
    assert (
        iri,
        RDFS.comment,
        Literal("The ADCS shall maintain pointing accuracy ≤ 0.1°."),
    ) in g


def test_build_artifact_minimal() -> None:
    iri = URIRef("https://rtm.example/art/proof-1")
    g = build_artifact(iri=iri, title="Lyapunov stability proof")

    assert (iri, RDF.type, RTM.Artifact) in g
    assert (iri, RDFS.label, Literal("Lyapunov stability proof")) in g
    assert len(g) == 2


def test_build_artifact_with_content_hash_and_git_commit() -> None:
    iri = URIRef("https://rtm.example/art/proof-2")
    g = build_artifact(
        iri=iri,
        title="Sim run",
        content_hash="sha256:abc123",
        git_commit="deadbeef" * 5,
    )
    assert (iri, RTM.hasContentHash, Literal("sha256:abc123")) in g
    assert (iri, RTM.hasGitCommit, Literal("deadbeef" * 5)) in g


def test_build_addresses_edge_is_a_single_triple() -> None:
    a = URIRef("https://rtm.example/art/proof-1")
    r = URIRef("https://rtm.example/req/REQ-001")
    g = build_addresses_edge(artifact=a, requirement=r)

    assert (a, RTM.addresses, r) in g
    assert len(g) == 1


def test_build_attestation_satisfaction_pass() -> None:
    iri = URIRef("urn:rtm:attest/abc")
    approver = URIRef("https://flexo-rtm.dev/identity/github/octocat")
    subject = URIRef("https://rtm.example/req/REQ-001")
    ts = datetime(2026, 5, 19, 12, 0, 0, tzinfo=UTC)

    g = build_attestation(
        iri=iri,
        attestation_class="SatisfactionAttestation",
        approved_by=approver,
        applies_to=subject,
        status="pass",
        timestamp=ts,
    )

    assert (iri, RDF.type, RTM.SatisfactionAttestation) in g
    assert (iri, RTM.approvedBy, approver) in g
    assert (iri, RTM.status, RTM.pass_) not in g  # use rtm:pass IRI, NOT rtm:pass_
    assert (iri, RTM.status, URIRef(str(RTM) + "pass")) in g
    assert (iri, RTM.appliesTo, subject) in g
    assert (
        iri,
        PROV.atTime,
        Literal("2026-05-19T12:00:00+00:00", datatype=XSD.dateTime),
    ) in g


def test_build_attestation_attaches_reason_as_rdfs_comment() -> None:
    iri = URIRef("urn:rtm:attest/abc")
    approver = URIRef("https://flexo-rtm.dev/identity/github/octocat")
    subject = URIRef("https://rtm.example/req/REQ-001")
    ts = datetime(2026, 5, 19, 12, 0, 0, tzinfo=UTC)

    g = build_attestation(
        iri=iri,
        attestation_class="AdequacyAttestation",
        approved_by=approver,
        applies_to=subject,
        status="pass",
        timestamp=ts,
        reason="The simplified rigid-body model captures the dynamics of interest.",
    )
    assert (
        iri,
        RDFS.comment,
        Literal("The simplified rigid-body model captures the dynamics of interest."),
    ) in g


@pytest.mark.parametrize(
    "cls",
    ["SatisfactionAttestation", "AdequacyAttestation", "SufficiencyAttestation"],
)
def test_build_attestation_accepts_three_v01_classes(cls: str) -> None:
    iri = URIRef("urn:rtm:attest/x")
    g = build_attestation(
        iri=iri,
        attestation_class=cls,  # type: ignore[arg-type]
        approved_by=URIRef("https://flexo-rtm.dev/identity/github/octocat"),
        applies_to=URIRef("https://rtm.example/req/r"),
        status="pass",
        timestamp=datetime(2026, 5, 19, tzinfo=UTC),
    )
    assert (iri, RDF.type, URIRef(str(RTM) + cls)) in g


def test_build_deprecation_emits_prov_was_invalidated_by() -> None:
    target = URIRef("urn:rtm:attest/old")
    activity = URIRef("urn:rtm:commit/activity-1")

    g = build_deprecation(target_attestation=target, invalidating_activity=activity)
    assert (target, PROV.wasInvalidatedBy, activity) in g
    assert len(g) == 1


def test_build_deprecation_with_reason_attaches_to_activity() -> None:
    """The reason describes WHY the activity invalidated the attestation —
    it belongs on the activity, not the (immutable) attestation."""
    target = URIRef("urn:rtm:attest/old")
    activity = URIRef("urn:rtm:commit/activity-1")
    reason = "Artifact content hash changed; prior judgement no longer covers the new artifact."

    g = build_deprecation(
        target_attestation=target,
        invalidating_activity=activity,
        reason=reason,
    )
    assert (target, PROV.wasInvalidatedBy, activity) in g
    assert (activity, RDFS.comment, Literal(reason)) in g
    assert len(g) == 2
