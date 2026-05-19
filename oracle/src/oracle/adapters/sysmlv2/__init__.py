# SPDX-License-Identifier: Apache-2.0
"""SysMLv2 ingestion + per-file RDF write-back — Design Spec §3, SysMLv2 Ingestion Contract.

The adapter consumes and emits **``omg-sysml:`` RDF only** — the canonical
openCAESAR OWL rendering of OMG SysMLv2 1.0. Converting between this RDF and
SysMLv2's native formats (``.kerml`` / ``.sysml`` / ``.sysml.json``) is
**not** in flexo-rtm's scope; that's openCAESAR's ``owl-adapter`` (MOF2OML +
OWL) toolchain's job in both directions. flexo-rtm pins to OMG SysMLv2 1.0
(formal/2024-08-01) and openCAESAR rendering v1.x per
``SysMLv2 Ingestion Contract`` §2.

**Adopter workflow**:

- Ingest: SysMLv2 source → openCAESAR owl-adapter → omg-sysml: RDF → flexo-rtm.
- Write-back: flexo-rtm → omg-sysml: RDF → openCAESAR owl-adapter → SysMLv2 source.

The openCAESAR toolchain is a separate JVM-based dependency NOT installed by
``pip install flexo-rtm`` or ``uv sync``. Adopters whose source-of-truth is
already ``omg-sysml:`` RDF (``.ttl`` / ``.nt`` / ``.jsonld``) don't need it.

Ingestion is source-preserving: the input RDF lands verbatim in
``urn:rtm:source/sysmlv2/{sha256(path)}`` per Flexo REST Binding §4.2.
Internal augmentations (attestations, transcripts, audit graphs) live in
separate named graphs and reference ``omg-sysml:elementId`` for stable
identity across re-ingestions.

**Read + write are both in v0.1.** Carrying the write path lets the same-format
roundtrip test (``parse → emit → parse → canonical-equality``) be the read
step's correctness proof. See ``flexo-rtm-research#18``.

**Asymmetric audit semantics still apply.** SysMLv2's ``omg-sysml:satisfies``
and ``omg-sysml:verifies`` both map to ``rtm:addresses`` (evidence linkage);
satisfaction in flexo-rtm requires a named-approver ``rtm:SatisfactionAttestation``
that no SysMLv2 source graph carries on its own. Tracked upstream as
``flexo-rtm-research#16``.
"""

from oracle.adapters.sysmlv2.core import (
    SOURCE_GRAPH_PREFIX,
    SYSMLV2_NAMESPACE,
    canonical_triple_set,
    emit_sysmlv2,
    list_source_files,
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
    "list_source_files",
    "parse_sysmlv2",
    "source_graph_iri_for_path",
]
