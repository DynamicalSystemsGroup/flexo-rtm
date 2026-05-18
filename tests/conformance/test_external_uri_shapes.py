# SPDX-License-Identifier: Apache-2.0
"""Acceptance criterion U1: external URI format validation (External URI Rules §3)."""

from __future__ import annotations

from pathlib import Path

import pyshacl
from rdflib import Graph

from tests.conftest import ONTOLOGY_DIR

SHAPE_PATH: Path = ONTOLOGY_DIR / "shapes" / "external_uri.shacl.ttl"
ASSEMBLED: Path = ONTOLOGY_DIR / "rtm.ttl"


def _validate(turtle: str) -> tuple[bool, str]:
    data = Graph()
    data.parse(data=turtle, format="turtle")
    shapes = Graph()
    shapes.parse(SHAPE_PATH, format="turtle")
    ont = Graph()
    ont.parse(ASSEMBLED, format="turtle")
    conforms, _, text = pyshacl.validate(
        data_graph=data, shacl_graph=shapes, ont_graph=ont, inference="none", advanced=False
    )
    return conforms, text


# fmt: off
VALID = """
@prefix rtm: <https://flexo-rtm.dev/ontology#> .
<https://rtm.example/activity/run-1>
    rtm:hasGitRepo   "https://github.com/dynamicalsystemsgroup/flexo-rtm" ;
    rtm:hasGitCommit "0123456789abcdef0123456789abcdef01234567" ;
    rtm:hasContentHash "sha256:abc1234567890abc1234567890abc1234567890abc1234567890abc1234567890abc" ;
    rtm:hasOCIImage  "ghcr.io/dynamicalsystemsgroup/oracle@sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef" .
"""  # noqa: E501
# fmt: on

BAD_GIT_REPO_SSH = """
@prefix rtm: <https://flexo-rtm.dev/ontology#> .
<https://rtm.example/a> rtm:hasGitRepo "git@github.com:dynamicalsystemsgroup/flexo-rtm.git" .
"""

BAD_GIT_COMMIT = """
@prefix rtm: <https://flexo-rtm.dev/ontology#> .
<https://rtm.example/a> rtm:hasGitCommit "not-a-sha" .
"""

BAD_CONTENT_HASH_UNKNOWN_ALGO = """
@prefix rtm: <https://flexo-rtm.dev/ontology#> .
<https://rtm.example/a> rtm:hasContentHash "md5:9e107d9d372bb6826bd81d3542a419d6" .
"""

BAD_OCI_NO_DIGEST = """
@prefix rtm: <https://flexo-rtm.dev/ontology#> .
<https://rtm.example/a> rtm:hasOCIImage "ghcr.io/dynamicalsystemsgroup/oracle:latest" .
"""


def test_valid_uri_references_pass() -> None:
    conforms, report = _validate(VALID)
    assert conforms, report


def test_ssh_git_url_rejected() -> None:
    conforms, _ = _validate(BAD_GIT_REPO_SSH)
    assert not conforms


def test_non_sha_git_commit_rejected() -> None:
    conforms, _ = _validate(BAD_GIT_COMMIT)
    assert not conforms


def test_md5_content_hash_rejected() -> None:
    conforms, _ = _validate(BAD_CONTENT_HASH_UNKNOWN_ALGO)
    assert not conforms


def test_oci_image_without_digest_rejected() -> None:
    conforms, _ = _validate(BAD_OCI_NO_DIGEST)
    assert not conforms
