# SPDX-License-Identifier: Apache-2.0
"""OSLC-RM 2.1 + OSLC-QM 2.1 adapter — Design Spec §6.2, OSLC Roundtrip Acceptance.

Source-preserving design: an imported OSLC graph lands verbatim in per-resource
source graphs (``<urn:rtm:oslc-source:{escaped-iri}>``) inside an rdflib Dataset.
On write-back, those source graphs are flattened back to a single OSLC RDF
graph — Layer A roundtrip is lossless by construction; Layer C carry-through
is automatic (vendor extensions live in the same source graphs and serialize
back verbatim).
"""

from oracle.adapters.oslc.core import (
    OSLC_CORE_NAMESPACES,
    SOURCE_GRAPH_PREFIX,
    canonical_triple_set,
    emit_oslc,
    extract_carry_through_triples,
    extract_core_triples,
    parse_oslc,
)

__all__ = [
    "OSLC_CORE_NAMESPACES",
    "SOURCE_GRAPH_PREFIX",
    "canonical_triple_set",
    "emit_oslc",
    "extract_carry_through_triples",
    "extract_core_triples",
    "parse_oslc",
]
