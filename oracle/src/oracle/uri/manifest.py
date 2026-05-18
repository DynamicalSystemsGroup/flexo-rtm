# SPDX-License-Identifier: Apache-2.0
"""Reproducibility manifest emitter — External URI Rules §8.

Walks an audit graph and produces an ``rtm:ReproducibilityManifest`` graph
enumerating every external URI reference the cert depends on, with counts
per category and back-references to the resources that cited each URI.
"""

from __future__ import annotations

from collections import defaultdict
from uuid import uuid4

from rdflib import RDF, XSD, BNode, Graph, Literal, Namespace, URIRef

RTM = Namespace("https://flexo-rtm.dev/ontology#")
PROV = Namespace("http://www.w3.org/ns/prov#")


def emit_manifest(audit_graph: Graph, *, manifest_iri: URIRef | None = None) -> Graph:
    """Build a reproducibility manifest from URI references in ``audit_graph``.

    The manifest is itself an RDF graph that can be embedded inside the audit
    report or stored alongside it. Per External URI Rules §8 it enumerates
    git refs, content hashes, and OCI image digests with counts and
    back-references.
    """
    manifest = Graph()
    manifest.bind("rtm", RTM)
    manifest.bind("prov", PROV)

    if manifest_iri is None:
        manifest_iri = URIRef(f"https://flexo-rtm.dev/manifest/{uuid4()}")

    manifest.add((manifest_iri, RDF.type, RTM.ReproducibilityManifest))

    git_users: dict[tuple[str, str, str], list[URIRef]] = defaultdict(list)
    hash_users: dict[str, list[URIRef]] = defaultdict(list)
    oci_users: dict[str, list[URIRef]] = defaultdict(list)

    for subject, _, repo in audit_graph.triples((None, RTM.hasGitRepo, None)):
        commit = audit_graph.value(subject, RTM.hasGitCommit)
        path = audit_graph.value(subject, RTM.hasGitPath)
        if commit is None:
            continue
        key = (str(repo), str(commit), str(path) if path else "")
        git_users[key].append(URIRef(str(subject)))

    for subject, _, content_hash in audit_graph.triples((None, RTM.hasContentHash, None)):
        hash_users[str(content_hash)].append(URIRef(str(subject)))

    for subject, _, image in audit_graph.triples((None, RTM.hasOCIImage, None)):
        oci_users[str(image)].append(URIRef(str(subject)))

    manifest.add(
        (
            manifest_iri,
            RTM.totalGitRefs,
            Literal(len(git_users), datatype=XSD.integer),
        )
    )
    manifest.add(
        (
            manifest_iri,
            RTM.totalContentHashes,
            Literal(len(hash_users), datatype=XSD.integer),
        )
    )
    manifest.add(
        (
            manifest_iri,
            RTM.totalOCIImages,
            Literal(len(oci_users), datatype=XSD.integer),
        )
    )

    for git_key, git_user_list in sorted(git_users.items()):
        repo_str, commit_str, path_str = git_key
        entry = BNode()
        manifest.add((manifest_iri, RTM.gitRefs, entry))
        manifest.add((entry, RTM.hasGitRepo, Literal(repo_str)))
        manifest.add((entry, RTM.hasGitCommit, Literal(commit_str)))
        if path_str:
            manifest.add((entry, RTM.hasGitPath, Literal(path_str)))
        for user in git_user_list:
            manifest.add((entry, RTM.referencedBy, user))

    for hash_key, hash_user_list in sorted(hash_users.items()):
        entry = BNode()
        manifest.add((manifest_iri, RTM.contentHashes, entry))
        manifest.add((entry, RTM.hasContentHash, Literal(hash_key)))
        for user in hash_user_list:
            manifest.add((entry, RTM.referencedBy, user))

    for oci_key, oci_user_list in sorted(oci_users.items()):
        entry = BNode()
        manifest.add((manifest_iri, RTM.ociImages, entry))
        manifest.add((entry, RTM.hasOCIImage, Literal(oci_key)))
        for user in oci_user_list:
            manifest.add((entry, RTM.referencedBy, user))

    return manifest


__all__ = ["emit_manifest"]
