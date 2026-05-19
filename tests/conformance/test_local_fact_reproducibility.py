# SPDX-License-Identifier: Apache-2.0
"""X7 — a verifier with read access to a fact's local neighborhood + dereference
access to its external URIs re-executes the recorded steps and confirms hashes.

The slice 2 transcript machinery records every step's inputs+result hashes; here
we verify that ANY single recorded step can be replayed in isolation against the
same input graph and produce the same result hash — without needing the whole
transcript.
"""

from __future__ import annotations

from uuid import UUID

from oracle.analysis.emit.transcript import TranscriptRecorder, replay_subchain
from rdflib import Graph

RUN_ID = UUID("00000000-0000-4000-8000-000000000010")
TURTLE = """
@prefix rtm: <https://flexo-rtm.dev/ontology#> .
@prefix ex:  <https://rtm.example/> .
ex:r1 a rtm:Requirement .
ex:r2 a rtm:Requirement .
ex:a1 a rtm:Artifact ; rtm:addresses ex:r1 .
"""

QUERIES = (
    "PREFIX rtm: <https://flexo-rtm.dev/ontology#> SELECT ?r WHERE { ?r a rtm:Requirement }",
    "PREFIX rtm: <https://flexo-rtm.dev/ontology#> SELECT ?a WHERE { ?a a rtm:Artifact }",
)


def _build():
    g = Graph()
    g.parse(data=TURTLE, format="turtle")
    recorder = TranscriptRecorder(run_id=RUN_ID, input_graph=g)
    for q in QUERIES:
        recorder.record_sparql(query_text=q)
    recorder.record_canonicalize()
    return g, recorder.transcript()


def test_each_individual_step_can_be_replayed_in_isolation() -> None:
    g, transcript = _build()
    for step in transcript.steps:
        result = replay_subchain(transcript, step_seqs={step.seq}, input_graph=g)
        assert result.passed, (
            f"step {step.seq} ({step.step_kind}) failed isolated replay: {result.diverged_field}"
        )


def test_first_step_subchain_passes_against_genesis_state() -> None:
    g, transcript = _build()
    first = min(transcript.steps, key=lambda s: s.seq)
    result = replay_subchain(transcript, step_seqs={first.seq}, input_graph=g)
    assert result.passed


def test_empty_subchain_passes_vacuously() -> None:
    g, transcript = _build()
    result = replay_subchain(transcript, step_seqs=(), input_graph=g)
    assert result.passed
