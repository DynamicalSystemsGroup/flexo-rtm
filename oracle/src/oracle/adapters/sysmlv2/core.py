# SPDX-License-Identifier: Apache-2.0
"""Source-preserving SysMLv2 ingestion — SysMLv2 Ingestion Contract §6.

The whole input file lands in one source graph keyed by the SHA-256 of the
input path (or content, when no path is available). On write-back (v0.2+),
flatten the source graph back to RDF; the openCAESAR converter then renders
it as ``.sysml.json`` for re-import into the adopter's SysMLv2 tooling.

v0.1 ships read-only ingest; ``emit_sysmlv2`` exists for the source-preservation
roundtrip test and for the v0.2 write-back path.
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

    The path-hash makes re-ingestions of the same file land in the same graph
    (idempotent), while distinct files get distinct graphs.
    """
    digest = hashlib.sha256(path_or_id.encode("utf-8")).hexdigest()
    return URIRef(f"{SOURCE_GRAPH_PREFIX}{quote(digest, safe='')}")


def parse_sysmlv2(
    rdf_data: str | bytes,
    *,
    path: str,
    format: str = "turtle",
) -> Dataset:
    """Ingest a SysMLv2 RDF document into a source-preserving Dataset.

    The whole input file lands in one named graph keyed by ``source_graph_iri_for_path(path)``;
    internal augmentations land in *other* named graphs and are not touched here.
    """
    flat = Graph()
    flat.parse(data=rdf_data, format=format)

    ds = Dataset()
    source_graph = ds.graph(source_graph_iri_for_path(path))
    for triple in flat:
        source_graph.add(triple)
    return ds


def emit_sysmlv2(ds: Dataset, *, format: str = "turtle") -> str:
    """Flatten every SysMLv2 source graph back to a single RDF document.

    Multiple source graphs in the dataset (e.g., several ingested files) are
    serialized together; callers who want per-file output filter the dataset
    by source-graph IRI before calling.
    """
    flat = Graph()
    for ctx in ds.contexts():
        if str(ctx.identifier).startswith(SOURCE_GRAPH_PREFIX):
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
    "parse_sysmlv2",
    "source_graph_iri_for_path",
]
