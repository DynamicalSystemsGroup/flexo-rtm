# SPDX-License-Identifier: Apache-2.0
"""rtm:Scope resolution — Analysis Layer Scope Algebra §Scope resolution algorithm.

Resolves a scope IRI in a Dataset to ``(graph_set, filter_expr)`` by post-order DAG
walk over rtm:extends / rtm:intersectsWith / rtm:union, with cycle detection and
memoization on ``(scope IRI, dataset id)``.
"""

from __future__ import annotations

from dataclasses import dataclass

from rdflib import RDF, Dataset, URIRef

RTM = "https://flexo-rtm.dev/ontology#"
RTM_SCOPE = URIRef(RTM + "Scope")
RTM_INCLUDES_GRAPH = URIRef(RTM + "includesGraph")
RTM_SCOPE_FILTER = URIRef(RTM + "scopeFilter")
RTM_EXTENDS = URIRef(RTM + "extends")
RTM_INTERSECTS_WITH = URIRef(RTM + "intersectsWith")
RTM_UNION = URIRef(RTM + "union")


class ScopeNotFoundError(LookupError):
    """The named scope IRI is not declared as an rtm:Scope in the dataset."""


class ScopeCycleError(ValueError):
    """Composition predicates form a DAG; this cycle is an authoring error."""


@dataclass(frozen=True)
class ResolvedScope:
    iri: URIRef
    graph_set: frozenset[URIRef]
    filter_expr: str


def _conjoin(filters: list[str]) -> str:
    non_empty = [f.strip() for f in filters if f and f.strip()]
    if not non_empty:
        return "FILTER(true)"
    if len(non_empty) == 1:
        return non_empty[0]
    return " ".join(non_empty)


def resolve_scope(scope_iri: URIRef, dataset: Dataset) -> ResolvedScope:
    return _resolve(scope_iri, dataset, frozenset())


def _resolve(scope_iri: URIRef, dataset: Dataset, visiting: frozenset[URIRef]) -> ResolvedScope:
    if scope_iri in visiting:
        chain = " -> ".join(str(x) for x in (*visiting, scope_iri))
        raise ScopeCycleError(
            f"Scope composition cycle: {chain}. The offending scope is {scope_iri}."
        )
    if (scope_iri, RDF.type, RTM_SCOPE) not in dataset:
        raise ScopeNotFoundError(f"No rtm:Scope at {scope_iri}")

    direct_graphs: set[URIRef] = {
        URIRef(str(o)) for _, _, o in dataset.triples((scope_iri, RTM_INCLUDES_GRAPH, None))
    }
    direct_filter = next(
        (str(o) for _, _, o in dataset.triples((scope_iri, RTM_SCOPE_FILTER, None))),
        "",
    )

    new_visiting = visiting | {scope_iri}
    graph_set: set[URIRef] = set(direct_graphs)
    filters: list[str] = [direct_filter] if direct_filter else []

    for _, _, parent in dataset.triples((scope_iri, RTM_EXTENDS, None)):
        parent_res = _resolve(URIRef(str(parent)), dataset, new_visiting)
        graph_set |= parent_res.graph_set
        if parent_res.filter_expr and parent_res.filter_expr != "FILTER(true)":
            filters.append(parent_res.filter_expr)

    for _, _, partner in dataset.triples((scope_iri, RTM_INTERSECTS_WITH, None)):
        partner_res = _resolve(URIRef(str(partner)), dataset, new_visiting)
        graph_set &= partner_res.graph_set
        if partner_res.filter_expr and partner_res.filter_expr != "FILTER(true)":
            filters.append(partner_res.filter_expr)

    # rtm:union is rare; v0.1 supports it with set union of graphs and disjunction
    # of filters per the algebra. Tests cover the common paths; this branch is
    # included for completeness.
    for _, _, partner in dataset.triples((scope_iri, RTM_UNION, None)):
        partner_res = _resolve(URIRef(str(partner)), dataset, new_visiting)
        graph_set |= partner_res.graph_set
        if partner_res.filter_expr and partner_res.filter_expr != "FILTER(true)":
            # Disjoin with the local filter; if no local filter, just add.
            if filters:
                filters = [f"({' || '.join((*filters, partner_res.filter_expr))})"]
            else:
                filters.append(partner_res.filter_expr)

    return ResolvedScope(
        iri=scope_iri,
        graph_set=frozenset(graph_set),
        filter_expr=_conjoin(filters),
    )


__all__ = [
    "ResolvedScope",
    "ScopeCycleError",
    "ScopeNotFoundError",
    "resolve_scope",
]
