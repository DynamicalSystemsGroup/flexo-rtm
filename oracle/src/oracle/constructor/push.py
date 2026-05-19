# SPDX-License-Identifier: Apache-2.0
"""Push a constructor session to a remote Flexo backend.

Reads every non-empty partition graph from the local session and emits
ONE atomic commit against the remote backend. The local activity log
(``urn:rtm:audit``) is intentionally NOT pushed — the remote tracks its
own activity for the single push commit. Partition graphs (model,
attestations, …) carry the engineer's data and are pushed verbatim.
"""

from __future__ import annotations

from rdflib import Graph

from oracle.constructor.session import SessionContext
from oracle.storage.adapter import CommitResult, commit_atomic_batch
from oracle.storage.backend import FlexoBackend
from oracle.storage.iri_scheme import PARTITION_GRAPHS


def push_session(
    session: SessionContext,
    *,
    remote: FlexoBackend,
    branch: str,
    scope_iri: str | None = None,
    associated_with: str | None = None,
) -> CommitResult:
    """Copy the session's data partitions to ``remote`` via one atomic commit.

    Reads each PARTITION_GRAPHS entry from the local session's branch; any
    partition with at least one triple is included. The activity-tracking
    partition ``urn:rtm:audit`` is skipped — the remote builds its own.

    Raises ``TransactionError`` (via ``commit_atomic_batch``) if the remote
    rejects the write. On failure, the local session is unchanged.
    """
    writes: dict[str, Graph] = {}
    for partition_iri in PARTITION_GRAPHS.values():
        if partition_iri == "urn:rtm:audit":
            continue
        graph = session.backend.read_graph(session.branch, partition_iri)
        if len(graph) == 0:
            continue
        writes[partition_iri] = graph

    if not writes:
        raise ValueError("session is empty; nothing to push")

    return commit_atomic_batch(
        remote,
        branch=branch,
        writes=writes,
        scope_iri=scope_iri,
        associated_with=associated_with,
    )


__all__ = ["push_session"]
