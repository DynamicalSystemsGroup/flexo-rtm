# SPDX-License-Identifier: Apache-2.0
"""F1 — flexo-rtm commit writes model + evidence + attestation + transcript
fragments in a single Flexo transaction. Partial commits are forbidden.
"""

from __future__ import annotations

import pytest
from oracle.storage import (
    InMemoryFlexoBackend,
    commit_atomic_batch,
)
from oracle.storage.backend import TransactionError
from oracle.storage.iri_scheme import PARTITION_GRAPHS
from rdflib import Graph, Literal, URIRef

MODEL_TRIPLE = (
    URIRef("https://rtm.example/req/r1"),
    URIRef("https://rtm.example/predicate/title"),
    Literal("REQ-1"),
)
ATTESTATION_TRIPLE = (
    URIRef("https://rtm.example/attest/1"),
    URIRef("https://flexo-rtm.dev/ontology#approvedBy"),
    URIRef("https://github.com/zargham"),
)


def _graph_with(*triples: tuple) -> Graph:
    g = Graph()
    for t in triples:
        g.add(t)
    return g


def test_atomic_commit_lands_all_graphs_at_once() -> None:
    backend = InMemoryFlexoBackend(seed_branches=("main", "engineering/adcs"))
    result = commit_atomic_batch(
        backend,
        branch="engineering/adcs",
        writes={
            PARTITION_GRAPHS["model"]: _graph_with(MODEL_TRIPLE),
            PARTITION_GRAPHS["attestations"]: _graph_with(ATTESTATION_TRIPLE),
        },
        scope_iri="https://rtm.example/scope/adcs",
    )
    assert result.commit_iri.startswith("urn:rtm:commit/")
    model_read = backend.read_graph("engineering/adcs", PARTITION_GRAPHS["model"])
    attest_read = backend.read_graph("engineering/adcs", PARTITION_GRAPHS["attestations"])
    assert MODEL_TRIPLE in model_read
    assert ATTESTATION_TRIPLE in attest_read


def test_partial_commit_is_forbidden_on_backend_failure() -> None:
    """If any sub-write raises, the whole transaction is aborted; the branch
    state does not partially mutate."""
    backend = InMemoryFlexoBackend(seed_branches=("main",))
    original = type(backend).write_graph

    def _fail_on_attestations(self, tx_id, branch, graph_iri, graph):  # type: ignore[no-untyped-def]
        if graph_iri == PARTITION_GRAPHS["attestations"]:
            raise RuntimeError("simulated server-side SHACL violation")
        original(self, tx_id, branch, graph_iri, graph)

    type(backend).write_graph = _fail_on_attestations  # type: ignore[method-assign]
    try:
        with pytest.raises(RuntimeError):
            commit_atomic_batch(
                backend,
                branch="main",
                writes={
                    PARTITION_GRAPHS["model"]: _graph_with(MODEL_TRIPLE),
                    PARTITION_GRAPHS["attestations"]: _graph_with(ATTESTATION_TRIPLE),
                },
            )
    finally:
        type(backend).write_graph = original  # type: ignore[method-assign]

    assert len(backend.read_graph("main", PARTITION_GRAPHS["model"])) == 0
    assert len(backend.read_graph("main", PARTITION_GRAPHS["attestations"])) == 0


def test_empty_writes_rejected() -> None:
    backend = InMemoryFlexoBackend()
    with pytest.raises(TransactionError):
        commit_atomic_batch(backend, branch="main", writes={})
