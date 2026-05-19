# SPDX-License-Identifier: Apache-2.0
"""Transcript record + canonical-bytes + replay — Transcript Replay Semantics §1-§5.

Slice 2 ships the bit-exact regime (sparql / shacl / canonicalize / kc-operation).
The delegated-numerical regime (ADR-027) needs tolerance-aware comparison and lands
with the External URI Rules slice (slice 5).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from uuid import UUID

from rdflib import Graph

from oracle.canonicalize import SUITE_RDFC_1_0_SHA256, canonicalize_graph
from oracle.models import Transcript, TranscriptStep, TranscriptStepKind


def _step_iri(run_id: UUID, seq: int) -> str:
    return f"https://flexo-rtm.dev/transcript/{run_id}/step/{seq}"


def _hash_select_result(query_result: object) -> str:
    rows = sorted(
        ",".join(str(binding) for binding in row)
        for row in query_result  # type: ignore[attr-defined]
    )
    return hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()


class TranscriptRecorder:
    """Records steps as the oracle runs them; emits a Transcript on demand."""

    def __init__(self, *, run_id: UUID, input_graph: Graph) -> None:
        self.run_id = run_id
        self._state: Graph = input_graph
        self._steps: list[TranscriptStep] = []
        self.genesis_inputs_hash: str = canonicalize_graph(input_graph).sha256_hex
        self._cryptosuite: str = SUITE_RDFC_1_0_SHA256

    def _next_seq(self) -> int:
        return len(self._steps) + 1

    def _prev_hash(self) -> str:
        return self._steps[-1].result_hash if self._steps else self.genesis_inputs_hash

    def _prev_iri(self) -> str | None:
        return str(self._steps[-1].prov_activity) if self._steps else None

    def _append(
        self,
        *,
        kind: TranscriptStepKind,
        result_hash: str,
        query_text: str | None = None,
        shape_iri: str | None = None,
    ) -> TranscriptStep:
        seq = self._next_seq()
        step = TranscriptStep(
            seq=seq,
            step_kind=kind,
            query_text=query_text,
            shape_iri=shape_iri,  # type: ignore[arg-type]
            inputs_hash=self._prev_hash(),
            result_hash=result_hash,
            cryptosuite=self._cryptosuite,
            prov_activity=_step_iri(self.run_id, seq),  # type: ignore[arg-type]
            was_informed_by=self._prev_iri(),  # type: ignore[arg-type]
        )
        self._steps.append(step)
        return step

    def record_sparql(self, *, query_text: str) -> TranscriptStep:
        result = self._state.query(query_text)
        return self._append(
            kind="sparql",
            query_text=query_text,
            result_hash=_hash_select_result(result),
        )

    def record_canonicalize(self) -> TranscriptStep:
        result_hash = canonicalize_graph(self._state).sha256_hex
        return self._append(kind="canonicalize", result_hash=result_hash)

    def transcript(self) -> Transcript:
        return Transcript(
            run_id=self.run_id,
            genesis_inputs_hash=self.genesis_inputs_hash,
            steps=tuple(self._steps),
            cryptosuite=self._cryptosuite,
        )


def transcript_canonical_bytes(transcript: Transcript) -> bytes:
    """Deterministic line-form: one record per step, fields in stable order.

    The fields included are exactly those needed for replay (X3) and Merkle-chain
    integrity (§5). Wall-clock times and toolchain version metadata are recorded
    elsewhere and intentionally excluded from this canonical form — including them
    would break X1 across machines and process IDs.
    """
    parts: list[str] = [
        f"genesis_inputs_hash={transcript.genesis_inputs_hash}",
        f"cryptosuite={transcript.cryptosuite}",
        f"run_id={transcript.run_id}",
    ]
    for step in sorted(transcript.steps, key=lambda s: s.seq):
        parts.append(
            "|".join(
                (
                    f"seq={step.seq}",
                    f"kind={step.step_kind}",
                    f"query={step.query_text or ''}",
                    f"shape={step.shape_iri or ''}",
                    f"inputs={step.inputs_hash}",
                    f"result={step.result_hash}",
                    f"suite={step.cryptosuite or ''}",
                    f"prov={step.prov_activity}",
                    f"was_informed_by={step.was_informed_by or ''}",
                )
            )
        )
    return "\n".join(parts).encode("utf-8")


@dataclass(frozen=True)
class ReplayResult:
    passed: bool
    diverged_at_seq: int | None
    diverged_field: str | None


def _execute_step(state: Graph, step: TranscriptStep) -> tuple[str | None, str | None]:
    """Re-execute a single step against ``state``. Returns ``(computed_hash, diverged_field)``."""
    if step.step_kind == "sparql":
        if step.query_text is None:
            return None, "query_text"
        return _hash_select_result(state.query(step.query_text)), None
    if step.step_kind == "canonicalize":
        return canonicalize_graph(state).sha256_hex, None
    return None, f"unsupported-step-kind:{step.step_kind}"


def replay_transcript(transcript: Transcript, *, input_graph: Graph) -> ReplayResult:
    state = input_graph
    prev_hash = canonicalize_graph(state).sha256_hex
    if transcript.genesis_inputs_hash != prev_hash:
        return ReplayResult(passed=False, diverged_at_seq=0, diverged_field="genesis")

    for step in sorted(transcript.steps, key=lambda s: s.seq):
        if step.inputs_hash != prev_hash:
            return ReplayResult(passed=False, diverged_at_seq=step.seq, diverged_field="inputs")
        computed, diverged_field = _execute_step(state, step)
        if diverged_field is not None:
            return ReplayResult(
                passed=False, diverged_at_seq=step.seq, diverged_field=diverged_field
            )
        if computed != step.result_hash:
            return ReplayResult(passed=False, diverged_at_seq=step.seq, diverged_field="result")
        prev_hash = step.result_hash

    return ReplayResult(passed=True, diverged_at_seq=None, diverged_field=None)


def replay_subchain(
    transcript: Transcript,
    *,
    step_seqs: list[int] | tuple[int, ...] | frozenset[int],
    input_graph: Graph,
) -> ReplayResult:
    """Replay a contiguous subset of ``transcript.steps`` — Federated Audit + X8.

    Each party with permissions for a non-overlapping permission subset can
    invoke this with the seqs they're authorized to verify. The subchain is
    structurally complete in its local neighborhood: each step's recorded
    ``inputs_hash`` is what we compare against (the chain anchor for the first
    step in the subchain need not be the transcript's genesis).
    """
    requested = frozenset(step_seqs)
    if not requested:
        return ReplayResult(passed=True, diverged_at_seq=None, diverged_field=None)

    state = input_graph
    selected = [s for s in sorted(transcript.steps, key=lambda s: s.seq) if s.seq in requested]
    if not selected:
        return ReplayResult(passed=False, diverged_at_seq=0, diverged_field="no-steps-match-seqs")

    prev_hash: str | None = None
    for step in selected:
        if prev_hash is not None and step.inputs_hash != prev_hash:
            return ReplayResult(passed=False, diverged_at_seq=step.seq, diverged_field="inputs")
        computed, diverged_field = _execute_step(state, step)
        if diverged_field is not None:
            return ReplayResult(
                passed=False, diverged_at_seq=step.seq, diverged_field=diverged_field
            )
        if computed != step.result_hash:
            return ReplayResult(passed=False, diverged_at_seq=step.seq, diverged_field="result")
        prev_hash = step.result_hash

    return ReplayResult(passed=True, diverged_at_seq=None, diverged_field=None)


__all__ = [
    "ReplayResult",
    "TranscriptRecorder",
    "replay_subchain",
    "replay_transcript",
    "transcript_canonical_bytes",
]
