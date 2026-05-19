# SPDX-License-Identifier: Apache-2.0
"""Constructor deprecate command — explicit invalidation of a prior attestation."""

from __future__ import annotations

from pathlib import Path

from rdflib import PROV, RDFS, Dataset, Graph, Literal, URIRef
from typer.testing import CliRunner

from oracle.constructor.cli import constructor_app
from oracle.storage.iri_scheme import PARTITION_GRAPHS

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


def _attest_iri_from_session(state_path: Path) -> str:
    attestations = _read(state_path, "attestations")
    iris = {str(s) for s in attestations.subjects() if str(s).startswith("urn:rtm:attest/")}
    assert len(iris) == 1, f"expected exactly one attestation, got {iris}"
    return next(iter(iris))


def test_deprecate_emits_prov_was_invalidated_by(tmp_path: Path) -> None:
    runner.invoke(
        constructor_app,
        [
            "attest",
            "--applies-to",
            "https://rtm.example/req/r1",
            "--class",
            "SatisfactionAttestation",
            "--outcome",
            "pass",
            "--reason",
            "initial judgement",
            "--engineer-iri",
            "https://example.org/me",
            "--session-dir",
            str(tmp_path),
        ],
    )
    iri = _attest_iri_from_session(tmp_path / "state.trig")

    result = runner.invoke(
        constructor_app,
        [
            "deprecate",
            iri,
            "--reason",
            "evidence superseded by re-simulation",
            "--session-dir",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert "deprecated" in result.stdout.lower()

    attestations = _read(tmp_path / "state.trig", "attestations")
    invalidating = list(attestations.objects(URIRef(iri), PROV.wasInvalidatedBy))
    assert len(invalidating) == 1
    activity = invalidating[0]
    assert (
        activity,
        RDFS.comment,
        Literal("evidence superseded by re-simulation"),
    ) in attestations


def test_deprecate_requires_reason(tmp_path: Path) -> None:
    runner.invoke(
        constructor_app,
        [
            "attest",
            "--applies-to",
            "https://rtm.example/req/r1",
            "--class",
            "AdequacyAttestation",
            "--outcome",
            "pass",
            "--reason",
            "x",
            "--engineer-iri",
            "https://example.org/me",
            "--session-dir",
            str(tmp_path),
        ],
    )
    iri = _attest_iri_from_session(tmp_path / "state.trig")
    result = runner.invoke(
        constructor_app,
        ["deprecate", iri, "--session-dir", str(tmp_path)],
    )
    assert result.exit_code != 0
    assert "reason" in (result.stdout + (result.stderr or "")).lower()


def test_status_marks_deprecated_attestation(tmp_path: Path) -> None:
    runner.invoke(
        constructor_app,
        [
            "attest",
            "--applies-to",
            "https://rtm.example/req/r1",
            "--class",
            "SatisfactionAttestation",
            "--outcome",
            "pass",
            "--reason",
            "x",
            "--engineer-iri",
            "https://example.org/me",
            "--session-dir",
            str(tmp_path),
        ],
    )
    iri = _attest_iri_from_session(tmp_path / "state.trig")
    runner.invoke(
        constructor_app,
        ["deprecate", iri, "--reason", "obsolete", "--session-dir", str(tmp_path)],
    )
    result = runner.invoke(constructor_app, ["status", "--session-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "[DEPRECATED]" in result.stdout
