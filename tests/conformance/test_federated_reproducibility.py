# SPDX-License-Identifier: Apache-2.0
"""X8 — federated reproducibility composes: multiple parties with
non-overlapping permission subsets each reproduce their permitted fact-set;
union of per-fact PASSes = global PASS over the union.
"""

from __future__ import annotations

from uuid import UUID

from oracle.analysis.emit.transcript import (
    TranscriptRecorder,
    replay_subchain,
    replay_transcript,
)
from rdflib import Graph

RUN_ID = UUID("00000000-0000-4000-8000-000000000011")
TURTLE = """
@prefix rtm: <https://flexo-rtm.dev/ontology#> .
@prefix ex:  <https://rtm.example/> .
ex:r1 a rtm:Requirement .
ex:r2 a rtm:Requirement .
ex:r3 a rtm:Requirement .
ex:a1 a rtm:Artifact ; rtm:addresses ex:r1 .
ex:a2 a rtm:Artifact ; rtm:addresses ex:r2 .
ex:a3 a rtm:Artifact ; rtm:addresses ex:r3 .
"""

QUERIES = (
    "PREFIX rtm: <https://flexo-rtm.dev/ontology#> SELECT ?r WHERE { ?r a rtm:Requirement }",
    "PREFIX rtm: <https://flexo-rtm.dev/ontology#> SELECT ?a WHERE { ?a a rtm:Artifact }",
    "PREFIX rtm: <https://flexo-rtm.dev/ontology#> SELECT ?a ?r WHERE { ?a rtm:addresses ?r }",
)


def _build():
    g = Graph()
    g.parse(data=TURTLE, format="turtle")
    recorder = TranscriptRecorder(run_id=RUN_ID, input_graph=g)
    for q in QUERIES:
        recorder.record_sparql(query_text=q)
    recorder.record_canonicalize()
    return g, recorder.transcript()


def test_two_parties_with_disjoint_permission_subsets_each_pass() -> None:
    g, transcript = _build()
    all_seqs = {step.seq for step in transcript.steps}
    midpoint = max(all_seqs) // 2
    party_a = {seq for seq in all_seqs if seq <= midpoint}
    party_b = {seq for seq in all_seqs if seq > midpoint}

    assert party_a and party_b, "test setup error: parties must be non-empty"
    assert not (party_a & party_b), "parties must have non-overlapping permission subsets"
    assert party_a | party_b == all_seqs, "parties must cover every transcript step"

    result_a = replay_subchain(transcript, step_seqs=party_a, input_graph=g)
    result_b = replay_subchain(transcript, step_seqs=party_b, input_graph=g)

    assert result_a.passed, f"party A failed: {result_a.diverged_field}"
    assert result_b.passed, f"party B failed: {result_b.diverged_field}"


def test_union_of_partial_passes_equals_global_pass() -> None:
    g, transcript = _build()
    all_seqs = {step.seq for step in transcript.steps}
    midpoint = max(all_seqs) // 2
    party_a = {seq for seq in all_seqs if seq <= midpoint}
    party_b = {seq for seq in all_seqs if seq > midpoint}

    # Per-party verifications
    assert replay_subchain(transcript, step_seqs=party_a, input_graph=g).passed
    assert replay_subchain(transcript, step_seqs=party_b, input_graph=g).passed

    # Union (the global replay)
    assert replay_transcript(transcript, input_graph=g).passed


def test_tampering_a_party_step_fails_only_that_party() -> None:
    g, transcript = _build()
    all_seqs = {step.seq for step in transcript.steps}
    midpoint = max(all_seqs) // 2
    party_a = {seq for seq in all_seqs if seq <= midpoint}
    party_b = {seq for seq in all_seqs if seq > midpoint}

    target_seq = max(party_a)
    tampered = next(s for s in transcript.steps if s.seq == target_seq).model_copy(
        update={"result_hash": "deadbeef" * 8}
    )
    other_steps = tuple(s for s in transcript.steps if s.seq != target_seq)
    poisoned = transcript.model_copy(update={"steps": (*other_steps, tampered)})

    res_a = replay_subchain(poisoned, step_seqs=party_a, input_graph=g)
    res_b = replay_subchain(poisoned, step_seqs=party_b, input_graph=g)

    assert not res_a.passed
    assert res_a.diverged_at_seq == target_seq
    # Party B's permitted subchain is independent of party A's tampered step;
    # the subchain's first step's recorded inputs_hash is the chain anchor
    # within party B's permission slice.
    assert res_b.passed
