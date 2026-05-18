# SPDX-License-Identifier: Apache-2.0
"""Pydantic surface (Design Spec §7.4). v0.2 promotes these to OpenAPI schemas."""

from __future__ import annotations

from uuid import uuid4

import pytest
from oracle.models import (
    AttestationRecord,
    AuditReport,
    CoverageStats,
    GapRecord,
    Scope,
    TranscriptStep,
)
from pydantic import ValidationError


def test_scope_minimal() -> None:
    s = Scope(
        iri="https://rtm.example/scope/adcs",
        label="ADCS attitude control",
        includes_graphs=["https://rtm.example/g/adcs-structural"],
    )
    assert str(s.iri) == "https://rtm.example/scope/adcs"
    assert s.asot_held_by is None
    assert s.intersects_with == []
    assert s.lifecycle_stage is None


def test_scope_with_composition() -> None:
    s = Scope(
        iri="https://rtm.example/scope/safety",
        label="safety-critical extension",
        asot_held_by="https://example.org/orgs/safety-board",
        includes_graphs=[],
        extends="https://rtm.example/scope/adcs",
        intersects_with=["https://rtm.example/scope/qual"],
    )
    assert str(s.extends) == "https://rtm.example/scope/adcs"
    assert len(s.intersects_with) == 1


def test_transcript_step_sparql() -> None:
    step = TranscriptStep(
        seq=1,
        step_kind="sparql",
        query_text="SELECT ?r WHERE { ?r a rtm:Requirement }",
        inputs_hash="sha256:abcd",
        result_hash="sha256:efgh",
        prov_activity="https://rtm.example/activity/run-1",
    )
    assert step.step_kind == "sparql"
    assert step.shape_iri is None


def test_transcript_step_rejects_invalid_kind() -> None:
    with pytest.raises(ValidationError):
        TranscriptStep(
            seq=1,
            step_kind="not-a-step-kind",  # type: ignore[arg-type]
            inputs_hash="sha256:abcd",
            result_hash="sha256:efgh",
            prov_activity="https://rtm.example/activity/run-1",
        )


def test_gap_record_codes() -> None:
    for code in ("T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10"):
        g = GapRecord(code=code, detail=f"example {code}")  # type: ignore[arg-type]
        assert g.code == code


def test_gap_record_rejects_unknown_code() -> None:
    with pytest.raises(ValidationError):
        GapRecord(code="T11", detail="not a real code")  # type: ignore[arg-type]


def test_attestation_record() -> None:
    a = AttestationRecord(
        iri="https://rtm.example/attest/1",
        approved_by="https://github.com/zargham",
        subject=(
            "https://rtm.example/artifact/a1",
            "https://flexo-rtm.dev/ontology#addresses",
            "https://rtm.example/req/r1",
        ),
        attestation_class="SatisfactionAttestation",
        status="pass",
        timestamp="2026-05-18T12:00:00Z",
    )
    assert a.status == "pass"
    assert a.invalidated_by is None


def test_attestation_record_rejects_unknown_class() -> None:
    with pytest.raises(ValidationError):
        AttestationRecord(
            iri="https://rtm.example/attest/1",
            approved_by="https://github.com/zargham",
            subject="https://rtm.example/scope/adcs",
            attestation_class="HeresyAttestation",  # type: ignore[arg-type]
            status="pass",
            timestamp="2026-05-18T12:00:00Z",
        )


def test_audit_report() -> None:
    r = AuditReport(
        run_id=uuid4(),
        scope="https://rtm.example/scope/adcs",
        input_hash="sha256:1234",
        transcript_iri="https://rtm.example/transcript/1",
        attestation_graph_iri="https://rtm.example/g/attestations",
        coverage=CoverageStats(
            forward_percent=100.0,
            backward_percent=100.0,
        ),
        gaps=[],
        reproducibility_manifest_iri="https://rtm.example/manifest/1",
        certified=True,
    )
    assert r.certified is True
    assert r.gaps == []
    assert r.profile == []
