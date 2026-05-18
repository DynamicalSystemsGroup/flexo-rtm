# SPDX-License-Identifier: Apache-2.0
"""Acceptance criterion X4: audit report carries per-dimension coverage only.

No rolled-up "% certified" anywhere. Gaps enumerated by T-code. The derived binary
"certified" bool (D19) is allowed because it is derivable from coverage + thresholds.
Quantitative Outcomes §The derived binary view.
"""

from __future__ import annotations

from uuid import uuid4

from oracle.models import AuditReport, CoverageStats, GapRecord

FORBIDDEN_FIELD_SUBSTRINGS = (
    "certified_percent",
    "overall_percent",
    "overall_pct",
    "score",
    "rolled_up",
    "summary_pct",
)


def test_audit_report_carries_per_dimension_coverage_only() -> None:
    field_names = set(AuditReport.model_fields.keys())
    for forbidden in FORBIDDEN_FIELD_SUBSTRINGS:
        for fn in field_names:
            assert forbidden not in fn.lower(), (
                f"AuditReport.{fn} contains forbidden rolled-up substring {forbidden!r}"
            )


def test_audit_report_certified_bool_allowed_per_d19() -> None:
    # The derived binary view (D19) is allowed; D4 forbids only rolled-up percentages.
    assert "certified" in AuditReport.model_fields


def test_audit_report_coverage_is_per_dimension() -> None:
    cov_fields = set(CoverageStats.model_fields.keys())
    assert "forward_percent" in cov_fields
    assert "backward_percent" in cov_fields
    assert "per_aspect" in cov_fields
    assert "per_attestation_class" in cov_fields
    for fn in cov_fields:
        assert "overall" not in fn.lower()


def test_audit_report_round_trip_preserves_scope_and_gaps() -> None:
    r = AuditReport(
        run_id=uuid4(),
        scope="https://rtm.example/scope/adcs",
        input_hash="sha256:1234",
        transcript_iri="https://rtm.example/transcript/1",
        attestation_graph_iri="https://rtm.example/g/attestations",
        coverage=CoverageStats(forward_percent=66.667, backward_percent=50.0),
        gaps=[
            GapRecord(code="T1", vertex_iri="https://rtm.example/req/r3", detail="orphan"),
            GapRecord(code="T2", vertex_iri="https://rtm.example/art/a2", detail="dangling"),
        ],
        reproducibility_manifest_iri="https://rtm.example/manifest/1",
        certified=False,
    )
    round_tripped = AuditReport.model_validate(r.model_dump())
    assert round_tripped.scope == r.scope
    assert {g.code for g in round_tripped.gaps} == {"T1", "T2"}
    assert round_tripped.certified is False
