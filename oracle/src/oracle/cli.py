# SPDX-License-Identifier: Apache-2.0
"""flexo-rtm CLI — Design Spec §7.2 (oracle/cli.py).

Subcommands:

- ``flexo-rtm --version`` / ``--help`` — info only.
- ``flexo-rtm parsimony`` — rebuild the assembled ontology and report triple count.
- ``flexo-rtm certify`` — run an audit against a single input RDF file: compute
  addresses coverage, emit a JSON :class:`oracle.models.AuditReport`. Profiles
  and audit-mode fetches are CLI flags that map to the per-slice runtime paths.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated
from uuid import uuid4

import typer
from rdflib import Graph

from oracle import __version__
from oracle.analysis.coverage import compute_coverage
from oracle.analysis.emit.transcript import TranscriptRecorder
from oracle.canonicalize import canonicalize_graph
from oracle.constructor.cli import constructor_app
from oracle.models import AuditReport
from oracle.uri.manifest import emit_manifest

app = typer.Typer(
    name="flexo-rtm",
    help="Verifiable self-certification oracle for bidirectional requirements traceability.",
    no_args_is_help=True,
)
app.add_typer(constructor_app, name="constructor")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show version and exit.",
        ),
    ] = False,
) -> None:
    """flexo-rtm root command."""


@app.command()
def parsimony() -> None:
    """Rebuild the assembled ontology (ontology/rtm.ttl) and report triple count.

    Equivalent to ``uv run python ontology/parsimony/build.py`` from the repo
    root; the CLI form is the user-facing entry point.
    """
    repo_root = Path.cwd()
    build_script = repo_root / "ontology" / "parsimony" / "build.py"
    if not build_script.exists():
        typer.echo(
            f"error: {build_script} not found. Run from the flexo-rtm repo root.",
            err=True,
        )
        raise typer.Exit(code=2)
    import runpy

    runpy.run_path(str(build_script), run_name="__main__")


@app.command()
def certify(
    input_path: Annotated[
        Path,
        typer.Option("--input", "-i", exists=True, help="Path to an RDF input file."),
    ],
    scope: Annotated[
        str,
        typer.Option("--scope", "-s", help="Active rtm:Scope IRI for this run."),
    ],
    profile: Annotated[
        list[str] | None,
        typer.Option("--profile", "-p", help="Profile name(s) to activate."),
    ] = None,
    out: Annotated[
        Path | None,
        typer.Option("--out", "-o", help="Where to write the JSON audit report."),
    ] = None,
    rdf_format: Annotated[
        str,
        typer.Option("--format", help="Input RDF format (turtle, nt, xml, json-ld)."),
    ] = "turtle",
    audit_fetch: Annotated[
        bool,
        typer.Option(
            "--audit-fetch",
            help="Enable audit-mode network fetches (default: offline structural check).",
        ),
    ] = False,
) -> None:
    """Run an audit: addresses coverage + transcript + reproducibility manifest."""
    graph = Graph()
    graph.parse(input_path, format=rdf_format)

    canon = canonicalize_graph(graph)
    coverage = compute_coverage(graph)

    run_id = uuid4()
    recorder = TranscriptRecorder(run_id=run_id, input_graph=graph)
    recorder.record_canonicalize()
    transcript = recorder.transcript()

    manifest = emit_manifest(graph)
    manifest_iri = next(iter(manifest.subjects()), None)

    report = AuditReport(
        run_id=run_id,
        scope=scope,  # type: ignore[arg-type]
        profile=[p for p in (profile or [])],  # type: ignore[misc]
        input_hash=canon.sha256_hex,
        transcript_iri=f"https://flexo-rtm.dev/transcript/{run_id}",  # type: ignore[arg-type]
        attestation_graph_iri=f"https://flexo-rtm.dev/attestation-graph/{run_id}",  # type: ignore[arg-type]
        coverage=coverage,
        gaps=[],
        reproducibility_manifest_iri=str(manifest_iri)  # type: ignore[arg-type]
        if manifest_iri
        else f"https://flexo-rtm.dev/manifest/{run_id}",
        certified=coverage.forward_percent >= 100.0 and coverage.backward_percent >= 100.0,
    )

    payload = report.model_dump_json(indent=2)
    if out is not None:
        out.write_text(payload + "\n")
        typer.echo(f"Wrote audit report → {out}")
    else:
        typer.echo(payload)

    # Stash transcript for offline downstream tooling (slice 11+ scope)
    _ = audit_fetch  # reserved for slice 11 polish — wires to oracle.uri.fetch
    _ = transcript  # available for callers that import this command directly
    if not report.certified:
        sys.exit(1)


if __name__ == "__main__":
    app()
