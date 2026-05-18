# SPDX-License-Identifier: Apache-2.0
"""Acceptance criterion U1 (strict mode): under strict-provenance, every
rtm:Activity MUST carry rtm:hasGitCommit OR rtm:hasOCIImage. Default mode
without the profile is silent (warning surfaced at the runtime layer, not by
SHACL)."""

from __future__ import annotations

from pathlib import Path

import pyshacl
from rdflib import Graph

from tests.conftest import ONTOLOGY_DIR

PROFILE_PATH: Path = ONTOLOGY_DIR / "profiles" / "strict_provenance.shacl.ttl"
ASSEMBLED: Path = ONTOLOGY_DIR / "rtm.ttl"


def _validate(turtle: str, *, with_profile: bool) -> tuple[bool, str]:
    data = Graph()
    data.parse(data=turtle, format="turtle")
    shapes = Graph()
    if with_profile:
        shapes.parse(PROFILE_PATH, format="turtle")
    ont = Graph()
    ont.parse(ASSEMBLED, format="turtle")
    conforms, _, text = pyshacl.validate(
        data_graph=data, shacl_graph=shapes, ont_graph=ont, inference="none", advanced=False
    )
    return conforms, text


ACTIVITY_WITH_GIT = """
@prefix rtm: <https://flexo-rtm.dev/ontology#> .
<https://rtm.example/activity/a>
    a rtm:Activity ;
    rtm:hasGitCommit "0123456789abcdef0123456789abcdef01234567" .
"""

# fmt: off
ACTIVITY_WITH_OCI = """
@prefix rtm: <https://flexo-rtm.dev/ontology#> .
<https://rtm.example/activity/a>
    a rtm:Activity ;
    rtm:hasOCIImage "ghcr.io/x/y@sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef" .
"""  # noqa: E501
# fmt: on

ACTIVITY_WITHOUT_PROVENANCE = """
@prefix rtm: <https://flexo-rtm.dev/ontology#> .
<https://rtm.example/activity/a> a rtm:Activity .
"""


def test_strict_profile_passes_when_git_present() -> None:
    conforms, report = _validate(ACTIVITY_WITH_GIT, with_profile=True)
    assert conforms, report


def test_strict_profile_passes_when_oci_present() -> None:
    conforms, report = _validate(ACTIVITY_WITH_OCI, with_profile=True)
    assert conforms, report


def test_strict_profile_fails_when_neither_present() -> None:
    conforms, _ = _validate(ACTIVITY_WITHOUT_PROVENANCE, with_profile=True)
    assert not conforms


def test_default_mode_passes_even_without_provenance() -> None:
    """Without the strict-provenance profile, the activity is allowed; the
    SHOULD is enforced as a warning at the runtime layer."""
    conforms, _ = _validate(ACTIVITY_WITHOUT_PROVENANCE, with_profile=False)
    assert conforms
