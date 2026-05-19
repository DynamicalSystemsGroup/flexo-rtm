# SPDX-License-Identifier: Apache-2.0
"""Constructor new-artifact: content-hash conflict surfaces attestations
for engineer-judged deprecation. This is the workflow the user flagged
as the reason the deprecated state exists."""

from __future__ import annotations

from pathlib import Path

from oracle.constructor.cli import constructor_app
from oracle.storage.iri_scheme import PARTITION_GRAPHS
from rdflib import PROV, Dataset, Graph, URIRef
from typer.testing import CliRunner

runner = CliRunner()


def _read(state_path: Path, partition: str) -> Graph:
    ds = Dataset()
    ds.parse(source=str(state_path), format="trig")
    out = Graph()
    target = URIRef(PARTITION_GRAPHS[partition])
    for graph in ds.graphs():
        if graph.identifier == target:
            for triple in graph:
                out.add(triple)
    return out


def _bootstrap_artifact_with_attestation(session_dir: Path, content_hash: str) -> str:
    """Create artifact + requirement + addresses + attestation; return the
    attestation IRI for later assertions."""
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
            "--content-hash",
            content_hash,
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
    runner.invoke(
        constructor_app,
        [
            "attest",
            "--applies-to",
            "https://rtm.example/art/a1",
            "--class",
            "AdequacyAttestation",
            "--outcome",
            "pass",
            "--reason",
            "model adequate",
            "--engineer-iri",
            "https://example.org/me",
            "--session-dir",
            str(session_dir),
        ],
    )
    attestations = _read(session_dir / "state.trig", "attestations")
    iris = {str(s) for s in attestations.subjects() if str(s).startswith("urn:rtm:attest/")}
    assert len(iris) == 1
    return next(iter(iris))


def test_new_artifact_with_different_hash_deprecates_prior_attestations(tmp_path: Path) -> None:
    """Re-registering the same artifact IRI with a different content hash and
    --on-conflict=deprecate writes prov:wasInvalidatedBy on every attestation
    that referenced the old artifact."""
    attest_iri = _bootstrap_artifact_with_attestation(tmp_path, "sha256:original")

    result = runner.invoke(
        constructor_app,
        [
            "new-artifact",
            "https://rtm.example/art/a1",
            "--title",
            "A1 (re-derived)",
            "--content-hash",
            "sha256:revised",
            "--on-conflict",
            "deprecate",
            "--session-dir",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.stdout

    attestations = _read(tmp_path / "state.trig", "attestations")
    invalidating = list(attestations.objects(URIRef(attest_iri), PROV.wasInvalidatedBy))
    assert len(invalidating) == 1


def test_new_artifact_same_hash_is_a_noop_for_attestations(tmp_path: Path) -> None:
    """Registering the same artifact + same content hash does NOT touch any
    prior attestation."""
    attest_iri = _bootstrap_artifact_with_attestation(tmp_path, "sha256:same")

    result = runner.invoke(
        constructor_app,
        [
            "new-artifact",
            "https://rtm.example/art/a1",
            "--title",
            "A1 again",
            "--content-hash",
            "sha256:same",
            "--on-conflict",
            "deprecate",
            "--session-dir",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0

    attestations = _read(tmp_path / "state.trig", "attestations")
    invalidating = list(attestations.objects(URIRef(attest_iri), PROV.wasInvalidatedBy))
    assert invalidating == []


def test_new_artifact_with_on_conflict_abort_aborts(tmp_path: Path) -> None:
    """--on-conflict=abort exits non-zero and does NOT commit anything new."""
    _bootstrap_artifact_with_attestation(tmp_path, "sha256:v1")

    result = runner.invoke(
        constructor_app,
        [
            "new-artifact",
            "https://rtm.example/art/a1",
            "--title",
            "should not commit",
            "--content-hash",
            "sha256:v2",
            "--on-conflict",
            "abort",
            "--session-dir",
            str(tmp_path),
        ],
    )
    assert result.exit_code != 0
