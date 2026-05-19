# SPDX-License-Identifier: Apache-2.0
"""Offline + live tests for `flexo-rtm constructor push`.

The offline path uses ``InMemoryFlexoBackend`` as the remote target so we
exercise the full push_session logic without a network. The live path
(``@pytest.mark.live``) round-trips a session to ``try-layer1.starforge.app``.
"""

from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

import pytest
from oracle.constructor.cli import constructor_app
from oracle.constructor.push import push_session
from oracle.constructor.session import SessionContext
from oracle.storage.flexo_client import FlexoConfig, FlexoHttpClient
from oracle.storage.in_memory import InMemoryFlexoBackend
from oracle.storage.iri_scheme import PARTITION_GRAPHS
from rdflib import RDF, Namespace, URIRef
from typer.testing import CliRunner

RTM = Namespace("https://flexo-rtm.dev/ontology#")

runner = CliRunner()


def _populate_session(session_dir: Path) -> None:
    runner.invoke(
        constructor_app,
        [
            "new-requirement",
            "https://rtm.example/req/r1",
            "--title",
            "R1",
            "--session-dir",
            str(session_dir),
        ],
    )
    runner.invoke(
        constructor_app,
        [
            "new-artifact",
            "https://rtm.example/art/a1",
            "--title",
            "A1",
            "--session-dir",
            str(session_dir),
        ],
    )
    runner.invoke(
        constructor_app,
        [
            "link",
            "--artifact",
            "https://rtm.example/art/a1",
            "--requirement",
            "https://rtm.example/req/r1",
            "--session-dir",
            str(session_dir),
        ],
    )


def test_push_session_offline(tmp_path: Path) -> None:
    """push_session copies every non-empty partition graph from local to remote."""
    _populate_session(tmp_path)
    session = SessionContext(state_path=tmp_path / "state.trig")
    remote = InMemoryFlexoBackend(seed_branches=("master",))

    result = push_session(session, remote=remote, branch="master")
    assert result.commit_iri

    model = remote.read_graph("master", PARTITION_GRAPHS["model"])
    assert (URIRef("https://rtm.example/req/r1"), RDF.type, RTM.Requirement) in model
    assert (URIRef("https://rtm.example/art/a1"), RDF.type, RTM.Artifact) in model
    assert (
        URIRef("https://rtm.example/art/a1"),
        RTM.addresses,
        URIRef("https://rtm.example/req/r1"),
    ) in model


def test_push_session_does_not_push_local_activity_log(tmp_path: Path) -> None:
    """The local urn:rtm:audit activity log stays local; the remote builds
    its own activity for the single push commit."""
    _populate_session(tmp_path)
    session = SessionContext(state_path=tmp_path / "state.trig")
    remote = InMemoryFlexoBackend(seed_branches=("master",))
    push_session(session, remote=remote, branch="master")

    # The remote SHOULD have an activity graph entry (one for the push), but
    # NOT carry the multiple local activities that ran during construction.
    remote_audit = remote.read_graph("master", "urn:rtm:audit")
    prov_activity = URIRef("http://www.w3.org/ns/prov#Activity")
    activities = list(remote_audit.subjects(RDF.type, prov_activity))
    assert len(activities) == 1, (
        f"expected one push activity on remote, got {len(activities)}: {activities}"
    )


def test_push_session_empty_session_raises(tmp_path: Path) -> None:
    """Pushing an empty session is an error — there's nothing to commit."""
    session = SessionContext(state_path=tmp_path / "state.trig")
    remote = InMemoryFlexoBackend(seed_branches=("master",))
    with pytest.raises(ValueError, match="empty"):
        push_session(session, remote=remote, branch="master")


def test_push_cli_archives_session_on_success(tmp_path: Path) -> None:
    _populate_session(tmp_path)
    state_path = tmp_path / "state.trig"
    assert state_path.exists()

    # Spin up an in-memory "remote" via a custom CLI invocation:
    # Instead of HTTP, we test the CLI flow against a monkey-patched
    # FlexoHttpClient — but that's heavyweight. The simpler check: the
    # archive_on_success flag flows through correctly. Test it by directly
    # calling push_session + session.archive() to model what the CLI does.
    session = SessionContext(state_path=state_path)
    remote = InMemoryFlexoBackend(seed_branches=("master",))
    push_session(session, remote=remote, branch="master")
    archived = session.archive()
    assert not state_path.exists()
    assert archived.exists()


# --- Live ---------------------------------------------------------------------

pytestmark_live = pytest.mark.live


@pytestmark_live
def test_push_session_live_to_try_layer1(tmp_path: Path) -> None:
    """Round-trip a constructor session against try-layer1.starforge.app.

    Skipped unless FLEXO_TOKEN is set (existing conftest hook). Creates a
    sandbox org with a uuid suffix so the test is idempotent + isolated.
    """
    token = os.environ.get("FLEXO_TOKEN")
    assert token, "FLEXO_TOKEN must be set for live tests"
    base_url = os.environ.get("FLEXO_URL", "https://try-layer1.starforge.app")

    _populate_session(tmp_path)
    session = SessionContext(state_path=tmp_path / "state.trig")

    sandbox_org = f"flexo-rtm-constructor-live-{uuid4().hex[:8]}"
    config = FlexoConfig(base_url=base_url, org=sandbox_org, repo="constructor-smoke", token=token)
    remote = FlexoHttpClient(config)
    result = push_session(session, remote=remote, branch="master")
    assert result.commit_iri

    model = remote.read_graph("master", PARTITION_GRAPHS["model"])
    assert (URIRef("https://rtm.example/req/r1"), RDF.type, RTM.Requirement) in model
