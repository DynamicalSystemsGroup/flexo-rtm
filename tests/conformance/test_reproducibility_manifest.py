# SPDX-License-Identifier: Apache-2.0
"""Acceptance criterion U5: every audit report MUST include the manifest
enumerating every external URI the cert depends on (External URI Rules §8)."""

from __future__ import annotations

from oracle.uri.manifest import emit_manifest
from rdflib import RDF, Graph, Namespace

RTM = Namespace("https://flexo-rtm.dev/ontology#")

# fmt: off
AUDIT_GRAPH = """
@prefix rtm: <https://flexo-rtm.dev/ontology#> .

<https://rtm.example/activity/sim-1>
    a rtm:Activity ;
    rtm:hasGitRepo   "https://github.com/dynamicalsystemsgroup/adcs-sim" ;
    rtm:hasGitCommit "0123456789abcdef0123456789abcdef01234567" ;
    rtm:hasGitPath   "scripts/slew.py" .

<https://rtm.example/artifact/r1>
    rtm:hasContentHash "sha256:abc1234567890abc1234567890abc1234567890abc1234567890abc1234567890abc" .

<https://rtm.example/artifact/r2>
    rtm:hasContentHash "sha256:abc1234567890abc1234567890abc1234567890abc1234567890abc1234567890abc" .

<https://rtm.example/activity/sim-2>
    a rtm:Activity ;
    rtm:hasOCIImage "ghcr.io/x/y@sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef" .
"""  # noqa: E501
# fmt: on


def _load() -> Graph:
    g = Graph()
    g.parse(data=AUDIT_GRAPH, format="turtle")
    return g


def test_manifest_counts_categories_correctly() -> None:
    manifest = emit_manifest(_load())
    manifests = list(manifest.subjects(RDF.type, RTM.ReproducibilityManifest))
    assert len(manifests) == 1
    m = manifests[0]
    assert int(manifest.value(m, RTM.totalGitRefs)) == 1
    # Two artifacts share the same content hash → counted once.
    assert int(manifest.value(m, RTM.totalContentHashes)) == 1
    assert int(manifest.value(m, RTM.totalOCIImages)) == 1


def test_manifest_back_references_resources_that_cite_each_uri() -> None:
    manifest = emit_manifest(_load())
    referenced = set()
    for _s, _, o in manifest.triples((None, RTM.referencedBy, None)):
        referenced.add(str(o))
    assert "https://rtm.example/activity/sim-1" in referenced
    assert "https://rtm.example/artifact/r1" in referenced
    assert "https://rtm.example/artifact/r2" in referenced
    assert "https://rtm.example/activity/sim-2" in referenced


def test_manifest_is_deterministic_across_runs() -> None:
    """Re-running emit_manifest with the same input yields the same triple
    counts (X1 sympathy: per-run nondeterminism would break the audit chain)."""
    a = emit_manifest(_load())
    b = emit_manifest(_load())
    # IRIs of the two manifests differ (uuid4); but the structural triple
    # counts and the URIs they enumerate should be identical.
    a_counts = sorted(
        (str(p), str(o))
        for s, p, o in a
        if p in {RTM.totalGitRefs, RTM.totalContentHashes, RTM.totalOCIImages}
    )
    b_counts = sorted(
        (str(p), str(o))
        for s, p, o in b
        if p in {RTM.totalGitRefs, RTM.totalContentHashes, RTM.totalOCIImages}
    )
    assert a_counts == b_counts
