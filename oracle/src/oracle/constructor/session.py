# SPDX-License-Identifier: Apache-2.0
"""Constructor session: a local InMemory backend + on-disk TriG persistence.

A session owns one :class:`InMemoryFlexoBackend` instance and a path on disk
where the backend's state is serialized between commands. Each construction
command (``new-requirement``, ``attest``, …) commits atomically to the
session's backend via the existing ``commit_atomic_batch`` write path; the
session then persists the resulting state to a single TriG file so the
engineer can resume the session in a later invocation.

Single-branch model: v0.1 sessions hold one Flexo branch (default
``master``). Multi-branch construction is out of scope; see the plan for
when (and whether) to lift this.

Session identity: derived from ``git config user.email`` + the absolute
working directory. Stable across runs from the same dir + same email,
distinct otherwise. The default state path lives under
``~/.flexo-rtm/sessions/{session-id}/state.trig`` so that different
projects on the same machine don't collide.
"""

from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from rdflib import Dataset, Graph, URIRef

from oracle.storage.in_memory import InMemoryFlexoBackend
from oracle.storage.iri_scheme import PARTITION_GRAPHS


def derive_session_id(*, email: str, cwd: Path) -> str:
    """Stable 16-char hex slug from (email, absolute cwd)."""
    h = hashlib.sha256(f"{email}::{Path(cwd).resolve()}".encode())
    return h.hexdigest()[:16]


def default_state_path(*, email: str, cwd: Path) -> Path:
    session_id = derive_session_id(email=email, cwd=cwd)
    return Path.home() / ".flexo-rtm" / "sessions" / session_id / "state.trig"


@dataclass
class SessionContext:
    state_path: Path
    branch: str = "master"
    backend: InMemoryFlexoBackend = field(
        default_factory=lambda: InMemoryFlexoBackend(seed_branches=("master",))
    )

    def __post_init__(self) -> None:
        if self.branch not in self.backend.list_branches():
            self.backend.create_branch(self.branch)
        if self.state_path.exists():
            self.load()

    # ------------------------------------------------------------------- I/O

    def load(self) -> None:
        """Load the on-disk TriG into the session's backend.

        No-op if the state file does not exist. Replays each named graph in
        the file into the corresponding partition on the session's branch.
        """
        if not self.state_path.exists():
            return
        ds = Dataset()
        ds.parse(source=str(self.state_path), format="trig")
        for graph in ds.graphs():
            iri = str(graph.identifier)
            if not iri.startswith("urn:rtm:"):
                continue
            payload = Graph()
            for triple in graph:
                payload.add(triple)
            if len(payload) == 0:
                continue
            tx = self.backend.begin_transaction(self.branch)
            self.backend.write_graph(tx, self.branch, iri, payload)
            self.backend.commit_transaction(tx, self.branch)

    def persist(self) -> None:
        """Serialize the session's branch state to ``state_path``.

        Idempotent — writing the same backend state twice produces identical
        bytes. The output is canonical TriG (sorted prefixes; rdflib's
        default ordering).
        """
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        ds = Dataset()
        for partition_name in PARTITION_GRAPHS:
            iri = PARTITION_GRAPHS[partition_name]
            graph = self.backend.read_graph(self.branch, iri)
            if len(graph) == 0:
                continue
            named = ds.graph(URIRef(iri))
            for triple in graph:
                named.add(triple)
        body = ds.serialize(format="trig")
        self.state_path.write_bytes(body.encode("utf-8") if isinstance(body, str) else body)

    def archive(self) -> Path:
        """Move the current state file into ``archive/`` next to it.

        Returned path is the archived copy. The active state file is removed
        so the engineer's next session starts fresh after a push.
        """
        archive_dir = self.state_path.parent / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        target = archive_dir / f"{self.state_path.stem}-{stamp}{self.state_path.suffix}"
        shutil.move(str(self.state_path), str(target))
        return target


__all__ = [
    "SessionContext",
    "default_state_path",
    "derive_session_id",
]
