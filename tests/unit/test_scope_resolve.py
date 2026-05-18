# SPDX-License-Identifier: Apache-2.0
"""Scope resolution algorithm — Analysis Layer Scope Algebra §Scope resolution.

Resolves an rtm:Scope IRI against an rdflib Dataset into (graph_set, filter_expr).
"""

from __future__ import annotations

from oracle.analysis.scope import resolve_scope
from rdflib import Dataset, URIRef

SCOPE_TURTLE = """
@prefix rtm: <https://flexo-rtm.dev/ontology#> .

<https://rtm.example/scope/base>
    a rtm:Scope ;
    rtm:includesGraph <https://rtm.example/g/a>, <https://rtm.example/g/b> ;
    rtm:scopeFilter "FILTER(?aspect IN (rtm:functional))" .

<https://rtm.example/scope/aspect-safety>
    a rtm:Scope ;
    rtm:includesGraph <https://rtm.example/g/b>, <https://rtm.example/g/c> ;
    rtm:scopeFilter "FILTER(?aspect = rtm:safety)" .

<https://rtm.example/scope/extended>
    a rtm:Scope ;
    rtm:extends <https://rtm.example/scope/base> ;
    rtm:includesGraph <https://rtm.example/g/d> .

<https://rtm.example/scope/intersected>
    a rtm:Scope ;
    rtm:extends <https://rtm.example/scope/base> ;
    rtm:intersectsWith <https://rtm.example/scope/aspect-safety> .
"""


def _dataset_with_scopes() -> Dataset:
    ds = Dataset()
    ds.parse(data=SCOPE_TURTLE, format="turtle")
    return ds


def test_resolve_base_scope_returns_direct_graphs_and_filter() -> None:
    ds = _dataset_with_scopes()
    resolved = resolve_scope(URIRef("https://rtm.example/scope/base"), ds)
    assert resolved.graph_set == frozenset(
        {URIRef("https://rtm.example/g/a"), URIRef("https://rtm.example/g/b")}
    )
    assert "rtm:functional" in resolved.filter_expr


def test_resolve_extends_unions_graphs_and_conjoins_filters() -> None:
    ds = _dataset_with_scopes()
    resolved = resolve_scope(URIRef("https://rtm.example/scope/extended"), ds)
    assert resolved.graph_set == frozenset(
        {
            URIRef("https://rtm.example/g/a"),
            URIRef("https://rtm.example/g/b"),
            URIRef("https://rtm.example/g/d"),
        }
    )
    assert "rtm:functional" in resolved.filter_expr


def test_resolve_intersects_intersects_graphs_and_conjoins_filters() -> None:
    ds = _dataset_with_scopes()
    resolved = resolve_scope(URIRef("https://rtm.example/scope/intersected"), ds)
    assert resolved.graph_set == frozenset({URIRef("https://rtm.example/g/b")})
    assert "rtm:functional" in resolved.filter_expr
    assert "rtm:safety" in resolved.filter_expr


def test_resolve_unknown_scope_raises() -> None:
    ds = _dataset_with_scopes()
    import pytest
    from oracle.analysis.scope import ScopeNotFoundError

    with pytest.raises(ScopeNotFoundError):
        resolve_scope(URIRef("https://rtm.example/scope/does-not-exist"), ds)
