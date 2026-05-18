# SPDX-License-Identifier: Apache-2.0
"""Composition predicates form a DAG. Cycles fail fast with the offending IRI named.

Analysis Layer Scope Algebra §Scope resolution algorithm, step 7.
"""

from __future__ import annotations

import pytest
from oracle.analysis.scope import ScopeCycleError, resolve_scope
from rdflib import Dataset, URIRef

CYCLE_TURTLE = """
@prefix rtm: <https://flexo-rtm.dev/ontology#> .

<https://rtm.example/scope/a>
    a rtm:Scope ;
    rtm:extends <https://rtm.example/scope/b> ;
    rtm:includesGraph <https://rtm.example/g/a> .

<https://rtm.example/scope/b>
    a rtm:Scope ;
    rtm:extends <https://rtm.example/scope/c> ;
    rtm:includesGraph <https://rtm.example/g/b> .

<https://rtm.example/scope/c>
    a rtm:Scope ;
    rtm:extends <https://rtm.example/scope/a> ;
    rtm:includesGraph <https://rtm.example/g/c> .
"""


def test_cycle_detected_with_offending_iri() -> None:
    ds = Dataset()
    ds.parse(data=CYCLE_TURTLE, format="turtle")
    with pytest.raises(ScopeCycleError) as exc:
        resolve_scope(URIRef("https://rtm.example/scope/a"), ds)
    msg = str(exc.value)
    assert "https://rtm.example/scope/a" in msg
