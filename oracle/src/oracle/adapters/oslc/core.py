# SPDX-License-Identifier: Apache-2.0
"""Source-preserving OSLC parse + emit — OSLC Roundtrip Acceptance §3.

Layer A lossless-by-construction strategy: the parse step groups all triples
about each subject into a per-resource source graph; the emit step flattens
those source graphs back to a single OSLC RDF document. No remapping, no
normalization — what comes in goes out.

The internal analysis layer can derive ``rtm:*`` triples from the source graphs
on demand (slice 7+); those derivations live in separate named graphs and are
NOT emitted by ``emit_oslc``.
"""

from __future__ import annotations

from urllib.parse import quote

from rdflib import Dataset, Graph, URIRef
from rdflib.compare import to_canonical_graph

SOURCE_GRAPH_PREFIX = "urn:rtm:oslc-source:"

OSLC_CORE_NAMESPACES: frozenset[str] = frozenset(
    {
        "http://open-services.net/ns/rm#",
        "http://open-services.net/ns/qm#",
        "http://open-services.net/ns/core#",
        "http://purl.org/dc/terms/",
        "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "http://www.w3.org/2000/01/rdf-schema#",
        "http://www.w3.org/2002/07/owl#",
        "http://www.w3.org/2001/XMLSchema#",
    }
)


def _source_graph_iri(resource_iri: URIRef) -> URIRef:
    return URIRef(f"{SOURCE_GRAPH_PREFIX}{quote(str(resource_iri), safe='')}")


def parse_oslc(rdf_data: str | bytes, *, format: str = "turtle") -> Dataset:
    """Parse an OSLC RDF document into a Dataset with one source graph per subject."""
    flat = Graph()
    flat.parse(data=rdf_data, format=format)

    ds = Dataset()
    subjects = {triple[0] for triple in flat.triples((None, None, None))}
    for subject in subjects:
        if not isinstance(subject, URIRef):
            continue
        named = ds.graph(_source_graph_iri(subject))
        for triple in flat.triples((subject, None, None)):
            named.add(triple)
    return ds


def emit_oslc(ds: Dataset, *, format: str = "turtle") -> str:
    """Flatten every source graph back to a single OSLC RDF document."""
    flat = Graph()
    for ctx in ds.contexts():
        if str(ctx.identifier).startswith(SOURCE_GRAPH_PREFIX):
            for triple in ctx:
                flat.add(triple)
    return flat.serialize(format=format)


def extract_core_triples(graph: Graph) -> Graph:
    """Triples whose predicate is in an OSLC-core namespace."""
    out = Graph()
    for s, p, o in graph:
        if any(str(p).startswith(ns) for ns in OSLC_CORE_NAMESPACES):
            out.add((s, p, o))
    return out


def extract_carry_through_triples(graph: Graph) -> Graph:
    """Triples whose predicate is outside the OSLC-core namespaces (Layer C)."""
    out = Graph()
    for s, p, o in graph:
        if not any(str(p).startswith(ns) for ns in OSLC_CORE_NAMESPACES):
            out.add((s, p, o))
    return out


def canonical_triple_set(graph: Graph) -> bytes:
    """RDFC-1.0 canonical N-Triples bytes for triple-set equivalence checks."""
    canon = to_canonical_graph(graph)
    nt = canon.serialize(format="nt")
    lines = [line for line in nt.splitlines() if line.strip()]
    return b"\n".join(sorted(line.encode("utf-8") for line in lines))


def flatten_to_graph(ds: Dataset) -> Graph:
    """Union of every source graph (utility for tests)."""
    flat = Graph()
    for ctx in ds.contexts():
        if str(ctx.identifier).startswith(SOURCE_GRAPH_PREFIX):
            for triple in ctx:
                flat.add(triple)
    return flat


__all__ = [
    "OSLC_CORE_NAMESPACES",
    "SOURCE_GRAPH_PREFIX",
    "canonical_triple_set",
    "emit_oslc",
    "extract_carry_through_triples",
    "extract_core_triples",
    "flatten_to_graph",
    "parse_oslc",
]
