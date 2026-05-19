# SPDX-License-Identifier: Apache-2.0
"""OSLC-RM 2.1 + OSLC-QM 2.1 adapter — Design Spec §6.2, OSLC Roundtrip Acceptance.

Source-preserving design: an imported OSLC graph lands verbatim in per-resource
source graphs (``<urn:rtm:oslc-source:{escaped-iri}>``) inside an rdflib Dataset.
On write-back, those source graphs are flattened back to a single OSLC RDF
graph — Layer A roundtrip is lossless by construction; Layer C carry-through
is automatic (vendor extensions live in the same source graphs and serialize
back verbatim).

**Asymmetric audit semantics.** flexo-rtm's audit bar is strictly higher than
OSLC's because we distinguish evidence (``rtm:addresses``) from judgment
(``rtm:SatisfactionAttestation``). A graph that passes OSLC's traceability bar
may fail a flexo-rtm audit — we flag missing explicit human attestations.

Roundtrip directions:

- **OSLC → flexo-rtm**: faithful (source-preserving). The result has no
  attestations; any ``attested-*`` profile would fail at re-audit.
- **flexo-rtm → OSLC**: lossy. Attestation triples drop (default) or ride
  as Layer C extensions other OSLC clients can't interpret.
- **flexo-rtm → OSLC → flexo-rtm**: NOT identity. The intermediate OSLC form
  loses attestation structure; re-ingesting yields the bare addresses-graph.

This is intentional — flexo-rtm strictly extends OSLC. The asymmetry is at
the semantic-bar level, not the syntactic-fidelity level. Tracked upstream as
flexo-rtm-research#15.
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
