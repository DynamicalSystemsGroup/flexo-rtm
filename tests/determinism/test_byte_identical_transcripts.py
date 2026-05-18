# SPDX-License-Identifier: Apache-2.0
"""Acceptance criterion X1: same canonical input → byte-identical transcript across runs.

Determinism is the precondition for replay (X3). Times and process IDs are excluded
from the canonical transcript bytes per Transcript Replay Semantics §4.
"""

from __future__ import annotations

from uuid import UUID

from oracle.analysis.emit.transcript import TranscriptRecorder, transcript_canonical_bytes
from rdflib import Graph

RUN_ID = UUID("00000000-0000-4000-8000-000000000001")
QUERY = "PREFIX rtm: <https://flexo-rtm.dev/ontology#> SELECT ?r WHERE { ?r a rtm:Requirement }"
TURTLE = """
@prefix rtm: <https://flexo-rtm.dev/ontology#> .
@prefix ex:  <https://rtm.example/> .
ex:r1 a rtm:Requirement .
ex:r2 a rtm:Requirement .
ex:a1 a rtm:Artifact ; rtm:satisfies ex:r1 .
"""


def _build_transcript():
    g = Graph()
    g.parse(data=TURTLE, format="turtle")
    recorder = TranscriptRecorder(run_id=RUN_ID, input_graph=g)
    recorder.record_sparql(query_text=QUERY)
    recorder.record_canonicalize()
    return recorder.transcript()


def test_transcripts_from_identical_input_are_byte_identical() -> None:
    a = transcript_canonical_bytes(_build_transcript())
    b = transcript_canonical_bytes(_build_transcript())
    assert a == b


EXTRA_REQ = (
    "@prefix ex: <https://rtm.example/> . ex:r3 a <https://flexo-rtm.dev/ontology#Requirement> ."
)


def test_transcripts_from_different_input_diverge() -> None:
    a = transcript_canonical_bytes(_build_transcript())

    g = Graph()
    g.parse(data=TURTLE + "\n" + EXTRA_REQ, format="turtle")
    recorder = TranscriptRecorder(run_id=RUN_ID, input_graph=g)
    recorder.record_sparql(query_text=QUERY)
    recorder.record_canonicalize()
    b = transcript_canonical_bytes(recorder.transcript())
    assert a != b
