# SPDX-License-Identifier: Apache-2.0
"""SessionContext — local InMemory backend wrapped with TriG auto-persist."""

from __future__ import annotations

from pathlib import Path

import pytest
from oracle.constructor.session import SessionContext, derive_session_id
from oracle.storage.adapter import commit_atomic_batch
from oracle.storage.iri_scheme import PARTITION_GRAPHS
from rdflib import RDF, Graph, Namespace, URIRef

RTM = Namespace("https://flexo-rtm.dev/ontology#")


def _seed_graph() -> Graph:
    g = Graph()
    g.add((URIRef("https://rtm.example/req/1"), RDF.type, RTM.Requirement))
    return g


def test_derive_session_id_is_stable_for_same_inputs(tmp_path: Path) -> None:
    a = derive_session_id(email="zargham@example.org", cwd=tmp_path)
    b = derive_session_id(email="zargham@example.org", cwd=tmp_path)
    assert a == b


def test_derive_session_id_differs_by_email_or_cwd(tmp_path: Path) -> None:
    base = derive_session_id(email="z@example.org", cwd=tmp_path)
    other_email = derive_session_id(email="x@example.org", cwd=tmp_path)
    other_dir = derive_session_id(email="z@example.org", cwd=tmp_path / "child")
    assert base != other_email
    assert base != other_dir


def test_session_persist_then_load_round_trips(tmp_path: Path) -> None:
    state_path = tmp_path / "state.trig"
    s = SessionContext(state_path=state_path)
    commit_atomic_batch(
        s.backend,
        branch=s.branch,
        writes={PARTITION_GRAPHS["model"]: _seed_graph()},
    )
    s.persist()
    assert state_path.exists()

    reloaded = SessionContext(state_path=state_path)
    reloaded.load()
    read_back = reloaded.backend.read_graph(reloaded.branch, PARTITION_GRAPHS["model"])
    assert (URIRef("https://rtm.example/req/1"), RDF.type, RTM.Requirement) in read_back


def test_session_persist_is_idempotent(tmp_path: Path) -> None:
    s = SessionContext(state_path=tmp_path / "state.trig")
    commit_atomic_batch(
        s.backend,
        branch=s.branch,
        writes={PARTITION_GRAPHS["model"]: _seed_graph()},
    )
    s.persist()
    first = (tmp_path / "state.trig").read_bytes()
    s.persist()
    second = (tmp_path / "state.trig").read_bytes()
    assert first == second


def test_session_load_with_no_file_is_a_noop(tmp_path: Path) -> None:
    s = SessionContext(state_path=tmp_path / "fresh.trig")
    s.load()  # no-op
    assert s.backend.read_graph(s.branch, PARTITION_GRAPHS["model"]) == Graph() or (
        len(s.backend.read_graph(s.branch, PARTITION_GRAPHS["model"])) == 0
    )


def test_session_archive_moves_state_file(tmp_path: Path) -> None:
    state_path = tmp_path / "state.trig"
    s = SessionContext(state_path=state_path)
    commit_atomic_batch(
        s.backend,
        branch=s.branch,
        writes={PARTITION_GRAPHS["model"]: _seed_graph()},
    )
    s.persist()
    assert state_path.exists()

    archive_path = s.archive()
    assert not state_path.exists(), "active state should be cleared after archive"
    assert archive_path.exists(), "archive file should exist after archive()"
    assert archive_path.parent == state_path.parent / "archive"


@pytest.fixture(autouse=True)
def _no_home_pollution(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Keep tests away from ~/.flexo-rtm/."""
    monkeypatch.setenv("HOME", str(tmp_path / "fake-home"))
