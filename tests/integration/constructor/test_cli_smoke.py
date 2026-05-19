# SPDX-License-Identifier: Apache-2.0
"""Constructor CLI integration tests — non-interactive (flags-only).

Each command is exercised via Typer's CliRunner. The session-dir is
isolated under tmp_path so the tests don't touch ~/.flexo-rtm/.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from oracle.constructor.cli import constructor_app
from oracle.storage.iri_scheme import PARTITION_GRAPHS
from rdflib import PROV, RDF, RDFS, Graph, Literal, Namespace, URIRef
from typer.testing import CliRunner

RTM = Namespace("https://flexo-rtm.dev/ontology#")

runner = CliRunner()


def _read_partition(state_path: Path, partition: str) -> Graph:
    from rdflib import Dataset

    ds = Dataset()
    ds.parse(source=str(state_path), format="trig")
    out = Graph()
    target_iri = URIRef(PARTITION_GRAPHS[partition])
    for graph in ds.graphs():
        if graph.identifier == target_iri:
            for triple in graph:
                out.add(triple)
    return out


def test_new_requirement(tmp_path: Path) -> None:
    result = runner.invoke(
        constructor_app,
        [
            "new-requirement",
            "https://rtm.example/req/REQ-001",
            "--title",
            "Attitude pointing accuracy",
            "--statement",
            "The ADCS shall maintain pointing accuracy ≤ 0.1°.",
            "--session-dir",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert "created Requirement" in result.stdout

    model = _read_partition(tmp_path / "state.trig", "model")
    req = URIRef("https://rtm.example/req/REQ-001")
    assert (req, RDF.type, RTM.Requirement) in model
    assert (req, RDFS.label, Literal("Attitude pointing accuracy")) in model
    assert any(
        str(o) == "The ADCS shall maintain pointing accuracy ≤ 0.1°."
        for _, _, o in model.triples((req, RDFS.comment, None))
    )


def test_new_artifact(tmp_path: Path) -> None:
    result = runner.invoke(
        constructor_app,
        [
            "new-artifact",
            "https://rtm.example/art/proof-1",
            "--title",
            "Lyapunov stability proof",
            "--content-hash",
            "sha256:abc123",
            "--session-dir",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.stdout
    model = _read_partition(tmp_path / "state.trig", "model")
    art = URIRef("https://rtm.example/art/proof-1")
    assert (art, RDF.type, RTM.Artifact) in model
    assert (art, RTM.hasContentHash, Literal("sha256:abc123")) in model


def test_link(tmp_path: Path) -> None:
    runner.invoke(
        constructor_app,
        [
            "new-requirement",
            "https://rtm.example/req/r1",
            "--title",
            "R1",
            "--session-dir",
            str(tmp_path),
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
            str(tmp_path),
        ],
    )
    result = runner.invoke(
        constructor_app,
        [
            "link",
            "--artifact",
            "https://rtm.example/art/a1",
            "--requirement",
            "https://rtm.example/req/r1",
            "--session-dir",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.stdout
    model = _read_partition(tmp_path / "state.trig", "model")
    assert (
        URIRef("https://rtm.example/art/a1"),
        RTM.addresses,
        URIRef("https://rtm.example/req/r1"),
    ) in model


def test_attest_non_interactive(tmp_path: Path) -> None:
    result = runner.invoke(
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
            "All adequacy + sufficiency criteria met.",
            "--engineer-iri",
            "https://example.org/me",
            "--session-dir",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert "created SatisfactionAttestation" in result.stdout

    attestations = _read_partition(tmp_path / "state.trig", "attestations")
    types = {str(o) for _, _, o in attestations.triples((None, RDF.type, None))}
    assert "https://flexo-rtm.dev/ontology#SatisfactionAttestation" in types
    approvers = {str(o) for _, _, o in attestations.triples((None, RTM.approvedBy, None))}
    assert approvers == {"https://example.org/me"}


@pytest.mark.parametrize(
    "cls",
    ["SatisfactionAttestation", "AdequacyAttestation", "SufficiencyAttestation"],
)
def test_attest_accepts_three_classes(tmp_path: Path, cls: str) -> None:
    result = runner.invoke(
        constructor_app,
        [
            "attest",
            "--applies-to",
            "https://rtm.example/x",
            "--class",
            cls,
            "--outcome",
            "pass",
            "--reason",
            "ok",
            "--engineer-iri",
            "https://example.org/me",
            "--session-dir",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.stdout


def test_attest_interactive_prompts(tmp_path: Path) -> None:
    """REPL flow: answer 'y' to the class question, then provide a reason."""
    result = runner.invoke(
        constructor_app,
        [
            "attest",
            "--applies-to",
            "https://rtm.example/req/r1",
            "--class",
            "AdequacyAttestation",
            "--engineer-iri",
            "https://example.org/me",
            "--session-dir",
            str(tmp_path),
        ],
        input="y\nthe rigid-body abstraction captures the regime of interest\n",
    )
    assert result.exit_code == 0, result.stdout
    attestations = _read_partition(tmp_path / "state.trig", "attestations")
    types = {str(o) for _, _, o in attestations.triples((None, RDF.type, None))}
    assert "https://flexo-rtm.dev/ontology#AdequacyAttestation" in types
    statuses = {str(o) for _, _, o in attestations.triples((None, RTM.status, None))}
    assert "https://flexo-rtm.dev/ontology#pass" in statuses


def test_status_lists_requirements_and_artifacts(tmp_path: Path) -> None:
    runner.invoke(
        constructor_app,
        [
            "new-requirement",
            "https://rtm.example/req/r1",
            "--title",
            "R1",
            "--session-dir",
            str(tmp_path),
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
            str(tmp_path),
        ],
    )
    result = runner.invoke(constructor_app, ["status", "--session-dir", str(tmp_path)])
    assert result.exit_code == 0, result.stdout
    assert "Requirement" in result.stdout
    assert "Artifact" in result.stdout


def test_show_dumps_triples_for_iri(tmp_path: Path) -> None:
    runner.invoke(
        constructor_app,
        [
            "new-requirement",
            "https://rtm.example/req/r1",
            "--title",
            "R1",
            "--session-dir",
            str(tmp_path),
        ],
    )
    result = runner.invoke(
        constructor_app,
        ["show", "https://rtm.example/req/r1", "--session-dir", str(tmp_path)],
    )
    assert result.exit_code == 0
    assert "Requirement" in result.stdout or "rtm:" in result.stdout


# silence rdflib's PROV import linter — not used in this test module directly
_ = PROV
