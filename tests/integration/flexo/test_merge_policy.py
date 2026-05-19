# SPDX-License-Identifier: Apache-2.0
"""F5 — merge policy: constraint-aware synthesis. Verification-scope conflicts
auto-resolve via SHACL ASK at the real Flexo; validation-scope conflicts are
escalated to a named approver.

Slice 8 verifies the request shape against InMemoryFlexoBackend. The full
SHACL ASK loop is a real-Flexo concern (live tests).
"""

from __future__ import annotations

from oracle.storage import (
    InMemoryFlexoBackend,
    MergePolicyHints,
    request_merge,
)
from oracle.storage.iri_scheme import PARTITION_GRAPHS
from rdflib import Graph, Literal, URIRef


def _seed(branch: str, subject: str, title: str) -> InMemoryFlexoBackend:
    backend = InMemoryFlexoBackend(seed_branches=("main", branch))
    g = Graph()
    g.add((URIRef(subject), URIRef("https://rtm.example/p/title"), Literal(title)))
    tx = backend.begin_transaction(branch)
    backend.write_graph(tx, branch, PARTITION_GRAPHS["model"], g)
    backend.commit_transaction(tx, branch)
    return backend


def test_verification_scope_conflict_auto_resolves() -> None:
    """When two branches add to the same graph and policy is auto-resolve,
    the merge unions the graphs."""
    backend = _seed("engineering/adcs", "https://rtm.example/req/r1", "from-adcs")
    tx = backend.begin_transaction("main")
    g = Graph()
    g.add(
        (
            URIRef("https://rtm.example/req/r2"),
            URIRef("https://rtm.example/p/title"),
            Literal("from-main"),
        )
    )
    backend.write_graph(tx, "main", PARTITION_GRAPHS["model"], g)
    backend.commit_transaction(tx, "main")

    result = request_merge(
        backend,
        source="engineering/adcs",
        target="main",
        policy=MergePolicyHints(verification_scope="auto-resolve-via-shacl"),
    )
    assert result.ok, result.detail
    merged = backend.read_graph("main", PARTITION_GRAPHS["model"])
    titles = {str(o) for _, _, o in merged.triples((None, None, None))}
    assert "from-adcs" in titles
    assert "from-main" in titles


def test_validation_scope_conflict_escalates() -> None:
    backend = _seed("engineering/adcs", "https://rtm.example/req/r1", "from-adcs")
    tx = backend.begin_transaction("main")
    g = Graph()
    g.add(
        (
            URIRef("https://rtm.example/req/r2"),
            URIRef("https://rtm.example/p/title"),
            Literal("from-main"),
        )
    )
    backend.write_graph(tx, "main", PARTITION_GRAPHS["model"], g)
    backend.commit_transaction(tx, "main")

    result = request_merge(
        backend,
        source="engineering/adcs",
        target="main",
        policy=MergePolicyHints(
            verification_scope="escalate-to-named-approver",
            validation_scope="escalate-to-named-approver",
        ),
    )
    assert not result.ok
    assert result.conflicts
    assert "named-approver" in result.detail


def test_self_merge_rejected() -> None:
    backend = InMemoryFlexoBackend(seed_branches=("main",))
    result = request_merge(backend, source="main", target="main")
    assert not result.ok
