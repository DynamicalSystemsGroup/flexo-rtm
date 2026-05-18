# SPDX-License-Identifier: Apache-2.0
"""Identity adapter Protocol — Identity Adapter Contract §1+§8.

Each adapter is a callable taking a provider-specific claim payload and
returning an rdflib.Graph of projection triples that conform to the SHACL
shapes in ``ontology/shapes/identity_projection.shacl.ttl``.

Adapters are thin: no authentication, no credential storage, no business
logic, no provider-side writes. They translate claim payloads to RDF.
"""

from __future__ import annotations

from typing import Any, Protocol

from rdflib import Graph


class IdentityAdapter(Protocol):
    """The new-provider contract (acceptance criterion I6).

    Any callable matching this signature plugs in to the oracle by
    configuration alone — no core code changes per Identity Adapter Contract §8.
    """

    def __call__(self, payload: dict[str, Any]) -> Graph: ...


__all__ = ["IdentityAdapter"]
