# SPDX-License-Identifier: Apache-2.0
"""RDFC-1.0 canonicalization + suite-derived hashing.

Design Spec §4.7 (bit-exact regime) and ADR-026 (cryptographic agility via algorithm profiles).
The active cryptosuite supplies both the canonicalization algorithm and the digest. v0.1 ships
one suite: ``urn:rtm:suite/rdfc-1.0+sha256``.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from rdflib import Graph
from rdflib.compare import to_canonical_graph

SUITE_RDFC_1_0_SHA256 = "urn:rtm:suite/rdfc-1.0+sha256"


@dataclass(frozen=True)
class CanonicalizeResult:
    canonical_bytes: bytes
    sha256_hex: str
    suite_id: str


def canonicalize_graph(graph: Graph) -> CanonicalizeResult:
    """Return RDFC-1.0 canonical bytes + sha256 of a single-graph input.

    Slice 1 handles a single (non-context-aware) graph and emits sorted N-Triples lines.
    When transcript canonicalization extends to named-graph datasets (slice 2+),
    switch to N-Quads with an explicit Dataset wrapper.
    """
    canon = to_canonical_graph(graph)
    nt_serialization = canon.serialize(format="nt")
    lines = [line for line in nt_serialization.splitlines() if line.strip()]
    canonical_bytes = b"\n".join(sorted(line.encode("utf-8") for line in lines))
    sha256_hex = hashlib.sha256(canonical_bytes).hexdigest()
    return CanonicalizeResult(
        canonical_bytes=canonical_bytes,
        sha256_hex=sha256_hex,
        suite_id=SUITE_RDFC_1_0_SHA256,
    )


__all__ = ["CanonicalizeResult", "SUITE_RDFC_1_0_SHA256", "canonicalize_graph"]
