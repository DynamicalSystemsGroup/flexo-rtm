# SPDX-License-Identifier: Apache-2.0
"""Acceptance criterion U6 (proxy): URI references persist verbatim through a
parse→serialize→parse roundtrip. The full Flexo round-trip lands in slice 8;
this test is the structural antecedent — if rdflib normalises URI strings
across serialization, slice 8 cannot rely on bit-exact persistence."""

from __future__ import annotations

from rdflib import Graph, Namespace

RTM = Namespace("https://flexo-rtm.dev/ontology#")

# fmt: off
ORIGINAL = """
@prefix rtm: <https://flexo-rtm.dev/ontology#> .

<https://rtm.example/activity/sim-1>
    a rtm:Activity ;
    rtm:hasGitRepo   "https://github.com/dynamicalsystemsgroup/adcs-sim" ;
    rtm:hasGitCommit "0123456789abcdef0123456789abcdef01234567" ;
    rtm:hasGitPath   "scripts/slew.py" ;
    rtm:hasContentHash "sha256:abc1234567890abc1234567890abc1234567890abc1234567890abc1234567890abc" ;
    rtm:hasOCIImage  "ghcr.io/dynamicalsystemsgroup/oracle@sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef" .
"""  # noqa: E501
# fmt: on


def test_uri_string_values_survive_roundtrip() -> None:
    g = Graph()
    g.parse(data=ORIGINAL, format="turtle")
    recorded = {
        str(p): str(o) for _, p, o in g.triples((None, None, None)) if str(p).startswith(str(RTM))
    }

    serialized = g.serialize(format="turtle")
    reparsed = Graph()
    reparsed.parse(data=serialized, format="turtle")
    reparsed_strings = {
        str(p): str(o)
        for _, p, o in reparsed.triples((None, None, None))
        if str(p).startswith(str(RTM))
    }

    assert recorded == reparsed_strings
