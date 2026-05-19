# SPDX-License-Identifier: Apache-2.0
"""Source-preserving SysMLv2 ingestion + write-back — SysMLv2 Ingestion Contract §6.

Each ingested file lands in its own named graph keyed by ``sha256(path)``.
Multiple files coexist in one Dataset as distinct source graphs; internal
augmentations (attestations, transcripts, audit graphs) live in *other* named
graphs and never contaminate the source.

**Read + write are both in v0.1.** The write path emits per-file RDF that the
openCAESAR converter renders to ``.sysml.json`` for re-import into the adopter's
SysMLv2 tooling — the same external dependency as ingest, used in reverse.
Per-format JSON emission is NOT in flexo-rtm's scope (mirror of how the spec
treats ingest in §3).

Carrying the write path in v0.1 lets the same-format roundtrip test (parse →
emit → parse → byte-identical canonical form) be the read step's correctness
proof: if the read path lost or normalised anything, the roundtrip would
disagree.
"""

from __future__ import annotations

import hashlib
from urllib.parse import quote

from rdflib import Dataset, Graph, URIRef
from rdflib.compare import to_canonical_graph

SOURCE_GRAPH_PREFIX = "urn:rtm:source/sysmlv2/"
SYSMLV2_NAMESPACE = "https://www.omg.org/spec/SysML/20240801/SysML#"


def source_graph_iri_for_path(path_or_id: str) -> URIRef:
    """Build the canonical source-graph IRI for an ingested SysMLv2 file.

    The path-hash makes re-ingestions of the same path land in the same graph
    (idempotent), while distinct paths get distinct graphs.
    """
    digest = hashlib.sha256(path_or_id.encode("utf-8")).hexdigest()
    return URIRef(f"{SOURCE_GRAPH_PREFIX}{quote(digest, safe='')}")


def parse_sysmlv2(
    rdf_data: str | bytes,
    *,
    path: str,
    format: str = "turtle",
    into: Dataset | None = None,
) -> Dataset:
    """Ingest a SysMLv2 RDF document into a source-preserving Dataset.

    The whole input file lands in one named graph keyed by
    ``source_graph_iri_for_path(path)``. When ``into`` is supplied, the new
    source graph is added to that Dataset (allowing multi-file ingestion);
    otherwise a fresh Dataset is created.
    """
    flat = Graph()
    flat.parse(data=rdf_data, format=format)

    ds = into if into is not None else Dataset()
    source_graph = ds.graph(source_graph_iri_for_path(path))
    for triple in flat:
        source_graph.add(triple)
    return ds


def list_source_files(ds: Dataset) -> list[URIRef]:
    """The source-graph IRIs of every SysMLv2 file ingested into ``ds``.

    Useful for round-tripping multi-file projects: iterate the IRIs returned
    here and call ``emit_sysmlv2(ds, source_graph=iri)`` per file.
    """
    return sorted(
        URIRef(str(ctx.identifier))
        for ctx in ds.contexts()
        if str(ctx.identifier).startswith(SOURCE_GRAPH_PREFIX)
    )


def emit_sysmlv2(
    ds: Dataset,
    *,
    source_graph: URIRef | str | None = None,
    path: str | None = None,
    format: str = "turtle",
) -> str:
    """Emit SysMLv2 RDF back from the Dataset's source graphs.

    By default, every source graph is flattened into a single document.
    Supply ``source_graph`` (an IRI from :func:`list_source_files`) or ``path``
    (the original ingest path, re-hashed here) to emit a single file's contents.

    The output is the per-file RDF the openCAESAR converter consumes to render
    ``.sysml.json``.
    """
    target: URIRef | None
    if source_graph is not None:
        target = URIRef(str(source_graph))
    elif path is not None:
        target = source_graph_iri_for_path(path)
    else:
        target = None

    flat = Graph()
    for ctx in ds.contexts():
        ctx_iri = str(ctx.identifier)
        if not ctx_iri.startswith(SOURCE_GRAPH_PREFIX):
            continue
        if target is not None and str(target) != ctx_iri:
            continue
        for triple in ctx:
            flat.add(triple)
    return flat.serialize(format=format)


def canonical_triple_set(graph: Graph) -> bytes:
    """RDFC-1.0 canonical N-Triples bytes (same routine as the OSLC adapter)."""
    canon = to_canonical_graph(graph)
    nt = canon.serialize(format="nt")
    lines = [line for line in nt.splitlines() if line.strip()]
    return b"\n".join(sorted(line.encode("utf-8") for line in lines))


__all__ = [
    "SOURCE_GRAPH_PREFIX",
    "SYSMLV2_NAMESPACE",
    "canonical_triple_set",
    "emit_sysmlv2",
    "list_source_files",
    "parse_sysmlv2",
    "source_graph_iri_for_path",
]
