# SPDX-License-Identifier: Apache-2.0
"""U6 (full path) — external URI references persist verbatim through a
commit + read round-trip (Flexo REST Binding §4 + Design Spec §6.4 U6).

Slice 5 tested the rdflib parse-serialize proxy; this is the real
Flexo-backed test, exercised against the in-memory backend.
"""

from __future__ import annotations

from oracle.storage import InMemoryFlexoBackend, commit_atomic_batch
from oracle.storage.iri_scheme import PARTITION_GRAPHS
from rdflib import Graph, Literal, Namespace, URIRef

RTM = Namespace("https://flexo-rtm.dev/ontology#")

ACTIVITY = URIRef("https://rtm.example/activity/sim-1")
GIT_REPO = "https://github.com/dynamicalsystemsgroup/adcs-sim"
GIT_COMMIT = "0123456789abcdef0123456789abcdef01234567"
GIT_PATH = "scripts/slew.py"
CONTENT_HASH = "sha256:abc1234567890abc1234567890abc1234567890abc1234567890abc1234567890abc"
OCI_IMAGE = (
    "ghcr.io/dynamicalsystemsgroup/oracle@sha256:"
    "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
)


def test_uri_references_persist_verbatim_through_flexo_round_trip() -> None:
    backend = InMemoryFlexoBackend(seed_branches=("main",))
    g = Graph()
    g.add((ACTIVITY, RTM.hasGitRepo, Literal(GIT_REPO)))
    g.add((ACTIVITY, RTM.hasGitCommit, Literal(GIT_COMMIT)))
    g.add((ACTIVITY, RTM.hasGitPath, Literal(GIT_PATH)))
    g.add((ACTIVITY, RTM.hasContentHash, Literal(CONTENT_HASH)))
    g.add((ACTIVITY, RTM.hasOCIImage, Literal(OCI_IMAGE)))

    commit_atomic_batch(backend, branch="main", writes={PARTITION_GRAPHS["model"]: g})

    read = backend.read_graph("main", PARTITION_GRAPHS["model"])
    assert (ACTIVITY, RTM.hasGitRepo, Literal(GIT_REPO)) in read
    assert (ACTIVITY, RTM.hasGitCommit, Literal(GIT_COMMIT)) in read
    assert (ACTIVITY, RTM.hasGitPath, Literal(GIT_PATH)) in read
    assert (ACTIVITY, RTM.hasContentHash, Literal(CONTENT_HASH)) in read
    assert (ACTIVITY, RTM.hasOCIImage, Literal(OCI_IMAGE)) in read
