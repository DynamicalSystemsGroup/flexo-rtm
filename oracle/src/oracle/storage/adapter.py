# SPDX-License-Identifier: Apache-2.0
"""High-level atomic-batch commit + scope round-trip + merge — Flexo REST Binding §5+§7.

This module is the only place the rest of the oracle calls into the storage
layer. It builds the §5.2 commit-provenance Activity, writes the per-partition
graphs in one transaction, and either commits or aborts atomically. Backends
are injected (in-memory for tests, HTTPS for live).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from rdflib import RDF, XSD, Graph, Literal, Namespace, URIRef

from oracle.storage.backend import (
    FlexoBackend,
    MergePolicyHints,
    MergeResult,
    TransactionError,
)
from oracle.storage.iri_scheme import is_valid_branch_name

RTM = Namespace("https://flexo-rtm.dev/ontology#")
PROV = Namespace("http://www.w3.org/ns/prov#")


@dataclass(frozen=True)
class CommitResult:
    commit_iri: str
    activity_iri: str
    transaction_id: str


def _commit_activity_iri(run_id: str | None = None) -> URIRef:
    run = run_id or str(uuid4())
    return URIRef(f"urn:rtm:commit/{run}")


def _build_activity_graph(
    *,
    activity_iri: URIRef,
    branch: str,
    scope_iri: str | None,
    parent_commit: str | None,
    associated_with: str | None,
    started_at: datetime,
) -> Graph:
    g = Graph()
    g.add((activity_iri, RDF.type, PROV.Activity))
    g.add(
        (
            activity_iri,
            PROV.startedAtTime,
            Literal(started_at.isoformat(), datatype=XSD.dateTime),
        )
    )
    g.add((activity_iri, RTM.onBranch, Literal(branch)))
    if scope_iri is not None:
        g.add((activity_iri, RTM.writesScope, URIRef(scope_iri)))
    if parent_commit is not None:
        g.add((activity_iri, RTM.parentCommit, URIRef(parent_commit)))
    if associated_with is not None:
        g.add((activity_iri, PROV.wasAssociatedWith, URIRef(associated_with)))
    return g


def commit_atomic_batch(
    backend: FlexoBackend,
    *,
    branch: str,
    writes: Mapping[str, Graph],
    activity_graph_iri: str = "urn:rtm:audit",
    scope_iri: str | None = None,
    parent_commit: str | None = None,
    associated_with: str | None = None,
    started_at: datetime | None = None,
) -> CommitResult:
    """F1 + F2 + F4 — write ``writes`` (graph IRI → triples) in one transaction,
    with a single ``prov:Activity`` IRI threading every triple via
    ``prov:wasGeneratedBy``. The activity itself lands in
    ``activity_graph_iri`` (default ``urn:rtm:audit``).

    ``scope_iri`` records the active ``rtm:Scope`` for F4 round-trip recovery.

    If any sub-write or the final commit fails, the transaction is aborted and
    ``TransactionError`` is raised — partial commits are forbidden.
    """
    if not is_valid_branch_name(branch):
        raise TransactionError(f"branch name {branch!r} does not match the §6 conventions")
    if not writes:
        raise TransactionError("commit_atomic_batch requires at least one graph to write")

    activity_iri = _commit_activity_iri()
    activity = _build_activity_graph(
        activity_iri=activity_iri,
        branch=branch,
        scope_iri=scope_iri,
        parent_commit=parent_commit,
        associated_with=associated_with,
        started_at=started_at or datetime.now(UTC),
    )

    tx_id = backend.begin_transaction(branch)
    try:
        for graph_iri, graph in writes.items():
            tagged = Graph()
            for triple in graph:
                tagged.add(triple)
            for subject in {s for s, _, _ in graph}:
                tagged.add((subject, PROV.wasGeneratedBy, activity_iri))
            backend.write_graph(tx_id, branch, graph_iri, tagged)

        existing_activity_graph = backend.read_graph(branch, activity_graph_iri)
        merged_activity = Graph()
        for triple in existing_activity_graph:
            merged_activity.add(triple)
        for triple in activity:
            merged_activity.add(triple)
        backend.write_graph(tx_id, branch, activity_graph_iri, merged_activity)

        commit_iri = backend.commit_transaction(tx_id, branch)
    except Exception:
        backend.abort_transaction(tx_id, branch)
        raise

    return CommitResult(
        commit_iri=commit_iri,
        activity_iri=str(activity_iri),
        transaction_id=tx_id,
    )


def read_commit_scope(
    backend: FlexoBackend,
    *,
    branch: str,
    activity_iri: str,
    activity_graph_iri: str = "urn:rtm:audit",
) -> str | None:
    """F4 — recover the scope IRI an activity was authored under."""
    g = backend.read_graph(branch, activity_graph_iri)
    for _, _, scope in g.triples((URIRef(activity_iri), RTM.writesScope, None)):
        return str(scope)
    return None


def request_merge(
    backend: FlexoBackend,
    *,
    source: str,
    target: str,
    policy: MergePolicyHints | None = None,
) -> MergeResult:
    """F5 — request a merge with the constraint-aware policy hints."""
    return backend.merge(
        source=source,
        target=target,
        policy=policy or MergePolicyHints(),
    )


__all__ = [
    "CommitResult",
    "commit_atomic_batch",
    "read_commit_scope",
    "request_merge",
]
