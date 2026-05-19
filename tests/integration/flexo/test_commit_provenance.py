# SPDX-License-Identifier: Apache-2.0
"""F2 — every triple committed in a single transaction shares a single
``prov:Activity`` IRI (via ``prov:wasGeneratedBy``). No orphans.
"""

from __future__ import annotations

from oracle.storage import InMemoryFlexoBackend, commit_atomic_batch
from oracle.storage.iri_scheme import PARTITION_GRAPHS
from rdflib import Graph, Literal, Namespace, URIRef

PROV = Namespace("http://www.w3.org/ns/prov#")


def test_every_committed_subject_links_to_the_commit_activity() -> None:
    backend = InMemoryFlexoBackend(seed_branches=("main",))
    subjects = [URIRef(f"https://rtm.example/req/r{i}") for i in range(1, 4)]
    g = Graph()
    for s in subjects:
        g.add((s, URIRef("https://rtm.example/p/title"), Literal(f"req {s}")))

    result = commit_atomic_batch(
        backend,
        branch="main",
        writes={PARTITION_GRAPHS["model"]: g},
        scope_iri="https://rtm.example/scope/adcs",
    )

    model = backend.read_graph("main", PARTITION_GRAPHS["model"])
    for s in subjects:
        targets = {str(o) for _, _, o in model.triples((s, PROV.wasGeneratedBy, None))}
        assert result.activity_iri in targets, (
            f"subject {s} missing prov:wasGeneratedBy to activity {result.activity_iri}"
        )


def test_commit_activity_lands_in_audit_graph_with_required_metadata() -> None:
    backend = InMemoryFlexoBackend(seed_branches=("main",))
    g = Graph()
    g.add(
        (
            URIRef("https://rtm.example/req/r1"),
            URIRef("https://rtm.example/p/title"),
            Literal("r1"),
        )
    )
    result = commit_atomic_batch(
        backend,
        branch="main",
        writes={PARTITION_GRAPHS["model"]: g},
        scope_iri="https://rtm.example/scope/adcs",
        associated_with="https://github.com/zargham",
    )
    audit = backend.read_graph("main", PARTITION_GRAPHS["audit"])
    activity = URIRef(result.activity_iri)
    assert (activity, PROV.startedAtTime, None) in audit
    assert (activity, PROV.wasAssociatedWith, URIRef("https://github.com/zargham")) in audit
