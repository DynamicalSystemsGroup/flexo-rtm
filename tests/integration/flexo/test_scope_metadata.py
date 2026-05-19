# SPDX-License-Identifier: Apache-2.0
"""F4 — commit metadata captures the active rtm:Scope IRI; round-trip via
``read_commit_scope`` recovers it.
"""

from __future__ import annotations

from oracle.storage import (
    InMemoryFlexoBackend,
    commit_atomic_batch,
    read_commit_scope,
)
from oracle.storage.iri_scheme import PARTITION_GRAPHS
from rdflib import Graph, Literal, URIRef


def _seed_graph() -> Graph:
    g = Graph()
    g.add(
        (
            URIRef("https://rtm.example/req/r1"),
            URIRef("https://rtm.example/p/title"),
            Literal("r1"),
        )
    )
    return g


def test_scope_iri_round_trips_through_commit_metadata() -> None:
    backend = InMemoryFlexoBackend(seed_branches=("main",))
    scope = "https://rtm.example/scope/adcs-attitude-control"
    result = commit_atomic_batch(
        backend,
        branch="main",
        writes={PARTITION_GRAPHS["model"]: _seed_graph()},
        scope_iri=scope,
    )
    recovered = read_commit_scope(backend, branch="main", activity_iri=result.activity_iri)
    assert recovered == scope


def test_commit_without_scope_returns_none() -> None:
    backend = InMemoryFlexoBackend(seed_branches=("main",))
    result = commit_atomic_batch(
        backend, branch="main", writes={PARTITION_GRAPHS["model"]: _seed_graph()}
    )
    recovered = read_commit_scope(backend, branch="main", activity_iri=result.activity_iri)
    assert recovered is None
