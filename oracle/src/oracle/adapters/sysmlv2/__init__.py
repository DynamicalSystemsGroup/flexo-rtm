# SPDX-License-Identifier: Apache-2.0
"""SysMLv2 ingestion adapter — Design Spec §3, SysMLv2 Ingestion Contract.

v0.1 ships READ ingestion only (write-back to .kerml / .sysml.json is v0.2+).
The adapter consumes pre-converted ``omg-sysml:`` RDF (via the openCAESAR
toolchain or the SysMLv2 Pilot Implementation's JSON exporter). Ingestion is
source-preserving: the input RDF lands verbatim in ``urn:rtm:source/sysmlv2/{path-hash}``
per Flexo REST Binding §4.2, and internal augmentations (attestations,
transcripts, audit graphs) live in separate named graphs that reference
``omg-sysml:elementId`` for stable identity across re-ingestions.

**Asymmetric audit semantics still apply.** SysMLv2's ``omg-sysml:satisfies``
and ``omg-sysml:verifies`` both map to ``rtm:addresses`` (evidence linkage);
satisfaction in flexo-rtm requires a named-approver ``rtm:SatisfactionAttestation``
that no SysMLv2 source graph carries on its own. Tracked upstream as
flexo-rtm-research#16 (omg-sysml:satisfies/verifies → rtm:addresses).
"""

from oracle.adapters.sysmlv2.core import (
    SOURCE_GRAPH_PREFIX,
    SYSMLV2_NAMESPACE,
    canonical_triple_set,
    emit_sysmlv2,
    parse_sysmlv2,
    source_graph_iri_for_path,
)
from oracle.adapters.sysmlv2.mapping import (
    SYSMLV2_CLASSES,
    SYSMLV2_LINK_TYPES,
)

__all__ = [
    "SOURCE_GRAPH_PREFIX",
    "SYSMLV2_CLASSES",
    "SYSMLV2_LINK_TYPES",
    "SYSMLV2_NAMESPACE",
    "canonical_triple_set",
    "emit_sysmlv2",
    "parse_sysmlv2",
    "source_graph_iri_for_path",
]
