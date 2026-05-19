# SPDX-License-Identifier: Apache-2.0
"""In-memory Flexo backend — non-live test stand-in.

Behaves like Flexo MMS Layer 1's atomic-transaction semantics without a
network. Per-branch state; per-transaction staged writes; commit promotes
staged writes; abort discards them. Conflicts and merge policy hints are
modelled but not deeply exercised at this layer (slice 10 brings federated
composition).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from rdflib import Graph

from oracle.storage.backend import MergePolicyHints, MergeResult, TransactionError
from oracle.storage.iri_scheme import is_valid_branch_name


@dataclass
class _BranchState:
    graphs: dict[str, Graph] = field(default_factory=dict)


@dataclass
class _PendingTransaction:
    branch: str
    staged_writes: dict[str, Graph] = field(default_factory=dict)


class InMemoryFlexoBackend:
    """A fake Flexo backend used by ``tests/integration/flexo/`` non-live tests.

    Stores graphs per-branch in memory. Transactions stage writes; commit
    promotes them; abort discards them. ``commit_transaction`` returns a
    deterministic-ish commit IRI keyed by ``uuid4`` so tests can pin or
    inspect it. The contract surface mirrors :class:`oracle.storage.backend.FlexoBackend`.
    """

    def __init__(self, *, seed_branches: tuple[str, ...] = ("main",)) -> None:
        self._branches: dict[str, _BranchState] = {b: _BranchState() for b in seed_branches}
        self._transactions: dict[str, _PendingTransaction] = {}
        self.commit_log: list[str] = []

    def _branch(self, name: str) -> _BranchState:
        if name not in self._branches:
            raise TransactionError(f"unknown branch: {name!r}")
        return self._branches[name]

    def begin_transaction(self, branch: str) -> str:
        self._branch(branch)
        tx_id = f"tx-{uuid4()}"
        self._transactions[tx_id] = _PendingTransaction(branch=branch)
        return tx_id

    def write_graph(self, tx_id: str, branch: str, graph_iri: str, graph: Graph) -> None:
        if tx_id not in self._transactions:
            raise TransactionError(f"unknown transaction: {tx_id!r}")
        pending = self._transactions[tx_id]
        if pending.branch != branch:
            raise TransactionError(
                f"transaction {tx_id} is for branch {pending.branch!r}, not {branch!r}"
            )
        staged = Graph()
        for triple in graph:
            staged.add(triple)
        pending.staged_writes[graph_iri] = staged

    def commit_transaction(self, tx_id: str, branch: str) -> str:
        if tx_id not in self._transactions:
            raise TransactionError(f"unknown transaction: {tx_id!r}")
        pending = self._transactions.pop(tx_id)
        if pending.branch != branch:
            raise TransactionError(
                f"transaction {tx_id} is for branch {pending.branch!r}, not {branch!r}"
            )
        state = self._branch(branch)
        for graph_iri, staged in pending.staged_writes.items():
            state.graphs[graph_iri] = staged
        commit_iri = f"urn:rtm:commit/{uuid4()}"
        self.commit_log.append(commit_iri)
        return commit_iri

    def abort_transaction(self, tx_id: str, branch: str) -> None:
        if tx_id in self._transactions:
            del self._transactions[tx_id]

    def read_graph(self, branch: str, graph_iri: str) -> Graph:
        state = self._branch(branch)
        existing = state.graphs.get(graph_iri)
        if existing is None:
            return Graph()
        out = Graph()
        for triple in existing:
            out.add(triple)
        return out

    def list_graphs(self, branch: str) -> list[str]:
        return sorted(self._branch(branch).graphs.keys())

    def create_branch(self, name: str, *, from_branch: str = "main") -> None:
        if not is_valid_branch_name(name):
            raise TransactionError(f"branch name {name!r} does not match the §6 conventions")
        if name in self._branches:
            raise TransactionError(f"branch {name!r} already exists")
        source = self._branch(from_branch)
        copy = _BranchState()
        for graph_iri, graph in source.graphs.items():
            cloned = Graph()
            for triple in graph:
                cloned.add(triple)
            copy.graphs[graph_iri] = cloned
        self._branches[name] = copy

    def list_branches(self) -> list[str]:
        return sorted(self._branches.keys())

    def merge(self, *, source: str, target: str, policy: MergePolicyHints) -> MergeResult:
        if source == target:
            return MergeResult(ok=False, detail="cannot merge a branch into itself")
        src = self._branch(source)
        tgt = self._branch(target)
        for graph_iri, graph in src.graphs.items():
            if graph_iri not in tgt.graphs:
                copy = Graph()
                for triple in graph:
                    copy.add(triple)
                tgt.graphs[graph_iri] = copy
            else:
                # In-memory backend doesn't run SHACL itself; the adapter passes
                # policy hints that a real Flexo would consume. Slice 10 brings
                # federation; slice 8 only verifies the request shape.
                if policy.verification_scope == "auto-resolve-via-shacl":
                    merged = Graph()
                    for triple in tgt.graphs[graph_iri]:
                        merged.add(triple)
                    for triple in graph:
                        merged.add(triple)
                    tgt.graphs[graph_iri] = merged
                else:
                    return MergeResult(
                        ok=False,
                        detail="validation-scope conflict requires named-approver escalation",
                        conflicts=(graph_iri,),
                    )
        return MergeResult(ok=True, detail=f"merged {source} → {target}")


__all__ = ["InMemoryFlexoBackend"]
