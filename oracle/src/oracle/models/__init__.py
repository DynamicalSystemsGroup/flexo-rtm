# SPDX-License-Identifier: Apache-2.0
"""Pydantic surface (Design Spec §7.4). These models become OpenAPI schemas in v0.2."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import AnyUrl, AwareDatetime, BaseModel, Field

GapCode = Literal["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10"]
AttestationStatus = Literal["pass", "fail", "deferred", "deprecated"]
AttestationClass = Literal[
    "SatisfactionAttestation",
    "AdequacyAttestation",
    "SufficiencyAttestation",
    "ScopeCertificationAttestation",
    "CompositionCoverageAttestation",
    "CompositionSufficiencyAttestation",
]
TranscriptStepKind = Literal[
    "sparql", "shacl", "canonicalize", "kc-operation", "delegated-numerical"
]


class Scope(BaseModel):
    iri: AnyUrl
    label: str
    asot_held_by: AnyUrl | None = None
    includes_graphs: list[AnyUrl]
    scope_filter: str | None = None
    extends: AnyUrl | None = None
    intersects_with: list[AnyUrl] = Field(default_factory=list)
    lifecycle_stage: AnyUrl | None = None


class TranscriptStep(BaseModel):
    seq: int
    step_kind: TranscriptStepKind
    query_text: str | None = None
    shape_iri: AnyUrl | None = None
    inputs_hash: str
    result_hash: str
    cryptosuite: str | None = None
    prov_activity: AnyUrl
    was_informed_by: AnyUrl | None = None


class Transcript(BaseModel):
    """Linear chain of TranscriptStep records over a single cert run.

    Per Transcript Replay Semantics §1+§5: the chain's hash sequence is a Merkle
    commitment to the entire cert computation. ``genesis_inputs_hash`` is the
    active-suite hash over the canonical input dataset; ``steps[0].inputs_hash``
    MUST equal ``genesis_inputs_hash``; ``steps[k].inputs_hash`` MUST equal
    ``steps[k-1].result_hash`` for ``k ≥ 1``.
    """

    run_id: UUID
    genesis_inputs_hash: str
    steps: tuple[TranscriptStep, ...]
    cryptosuite: str


class GapRecord(BaseModel):
    code: GapCode
    vertex_iri: AnyUrl | None = None
    aspect: AnyUrl | None = None
    detail: str


class AttestationRecord(BaseModel):
    iri: AnyUrl
    approved_by: AnyUrl
    subject: tuple[AnyUrl, AnyUrl, AnyUrl] | AnyUrl
    attestation_class: AttestationClass
    status: AttestationStatus
    invalidated_by: AnyUrl | None = None
    timestamp: AwareDatetime
    transcript_ref: AnyUrl | None = None


class CoverageStats(BaseModel):
    """Per-dimension coverage. X4 forbids any rolled-up '% certified' number."""

    forward_percent: float = Field(ge=0.0, le=100.0)
    backward_percent: float = Field(ge=0.0, le=100.0)
    per_aspect: dict[str, float] = Field(default_factory=dict)
    per_attestation_class: dict[str, float] = Field(default_factory=dict)


class AuditReport(BaseModel):
    run_id: UUID
    scope: AnyUrl
    profile: list[AnyUrl] = Field(default_factory=list)
    input_hash: str
    transcript_iri: AnyUrl
    attestation_graph_iri: AnyUrl
    coverage: CoverageStats
    gaps: list[GapRecord] = Field(default_factory=list)
    reproducibility_manifest_iri: AnyUrl
    certified: bool


__all__ = [
    "AttestationClass",
    "AttestationRecord",
    "AttestationStatus",
    "AuditReport",
    "CoverageStats",
    "GapCode",
    "GapRecord",
    "Scope",
    "Transcript",
    "TranscriptStep",
    "TranscriptStepKind",
]
