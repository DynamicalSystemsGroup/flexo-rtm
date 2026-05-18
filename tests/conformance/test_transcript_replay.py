# SPDX-License-Identifier: Apache-2.0
"""Acceptance criterion X3: replay re-executes recorded steps and produces byte-identical
hashes. The first divergent step pinpoints tampering. Transcript Replay Semantics §3+§5.
"""

from __future__ import annotations

from uuid import UUID

from oracle.analysis.emit.transcript import (
    ReplayResult,
    TranscriptRecorder,
    replay_transcript,
)
from rdflib import Graph

RUN_ID = UUID("00000000-0000-4000-8000-000000000002")
QUERY = "PREFIX rtm: <https://flexo-rtm.dev/ontology#> SELECT ?r WHERE { ?r a rtm:Requirement }"
TURTLE = """
@prefix rtm: <https://flexo-rtm.dev/ontology#> .
@prefix ex:  <https://rtm.example/> .
ex:r1 a rtm:Requirement .
ex:r2 a rtm:Requirement .
ex:a1 a rtm:Artifact ; rtm:addresses ex:r1 .
"""


def _build():
    g = Graph()
    g.parse(data=TURTLE, format="turtle")
    recorder = TranscriptRecorder(run_id=RUN_ID, input_graph=g)
    recorder.record_sparql(query_text=QUERY)
    recorder.record_canonicalize()
    return g, recorder.transcript()


def test_replay_passes_on_unmodified_transcript() -> None:
    g, transcript = _build()
    result = replay_transcript(transcript, input_graph=g)
    assert isinstance(result, ReplayResult)
    assert result.passed is True
    assert result.diverged_at_seq is None


def test_replay_detects_tampered_result_hash_at_correct_step() -> None:
    g, transcript = _build()
    tampered_step = transcript.steps[0].model_copy(update={"result_hash": "deadbeef" * 8})
    tampered = transcript.model_copy(update={"steps": (tampered_step, *transcript.steps[1:])})
    result = replay_transcript(tampered, input_graph=g)
    assert result.passed is False
    assert result.diverged_at_seq == 1
    assert "result" in result.diverged_field


def test_replay_detects_broken_chain_at_correct_step() -> None:
    g, transcript = _build()
    bad_step2 = transcript.steps[1].model_copy(update={"inputs_hash": "deadbeef" * 8})
    tampered = transcript.model_copy(update={"steps": (transcript.steps[0], bad_step2)})
    result = replay_transcript(tampered, input_graph=g)
    assert result.passed is False
    assert result.diverged_at_seq == 2
    assert "inputs" in result.diverged_field
