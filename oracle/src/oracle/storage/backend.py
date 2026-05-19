# SPDX-License-Identifier: Apache-2.0
"""Backend protocol — Flexo REST Binding §9.

A narrow Protocol that both :class:`InMemoryFlexoBackend` (non-live tests)
and :class:`FlexoHttpClient` (live tests) implement. The rest of the oracle
codebase consumes this Protocol; concrete backends are injected at the edges.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from rdflib import Graph


@dataclass(frozen=True)
class MergePolicyHints:
    """§7 — constraint-aware merge policy.

    ``verification_scope`` covers SHACL-resolvable structural conflicts.
    ``validation_scope`` covers attestation conflicts that require a named
    approver to resolve (per ADR-031).
    """

    verification_scope: str = "auto-resolve-via-shacl"
    validation_scope: str = "escalate-to-named-approver"


@dataclass(frozen=True)
class MergeResult:
    ok: bool
    detail: str
    conflicts: tuple[str, ...] = ()


class TransactionError(RuntimeError):
    """Raised when an atomic-batch commit fails. The caller already aborted."""


class FlexoBackend(Protocol):
    """Atomic-transaction surface for Flexo storage (read + write + merge)."""

    def begin_transaction(self, branch: str) -> str: ...

    def write_graph(
        self,
        tx_id: str,
        branch: str,
        graph_iri: str,
        graph: Graph,
    ) -> None: ...

    def commit_transaction(self, tx_id: str, branch: str) -> str: ...

    def abort_transaction(self, tx_id: str, branch: str) -> None: ...

    def read_graph(self, branch: str, graph_iri: str) -> Graph: ...

    def list_graphs(self, branch: str) -> list[str]: ...

    def create_branch(self, name: str, *, from_branch: str = "main") -> None: ...

    def list_branches(self) -> list[str]: ...

    def merge(self, *, source: str, target: str, policy: MergePolicyHints) -> MergeResult: ...


__all__ = [
    "FlexoBackend",
    "MergePolicyHints",
    "MergeResult",
    "TransactionError",
]
