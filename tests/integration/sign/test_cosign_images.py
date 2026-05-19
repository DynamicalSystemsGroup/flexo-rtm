# SPDX-License-Identifier: Apache-2.0
"""S4 — cosign-images profile gate + stub-verifier lazy-import check."""

from __future__ import annotations

import importlib
from pathlib import Path

import pyshacl
import pytest
from oracle.signing.cosign import verify_cosign_bundle
from oracle.signing.errors import OptionalDependencyMissing
from rdflib import Graph

from tests.conftest import ONTOLOGY_DIR

PROFILE: Path = ONTOLOGY_DIR / "profiles" / "cosign-images.shacl.ttl"
ASSEMBLED: Path = ONTOLOGY_DIR / "rtm.ttl"

# fmt: off
WITH_BUNDLE = """
@prefix rtm: <https://flexo-rtm.dev/ontology#> .
<https://rtm.example/activity/sim-1>
    a rtm:Activity ;
    rtm:hasOCIImage "ghcr.io/x/y@sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef" ;
    rtm:cosignBundle <https://archive.example.org/cosign/x-y.bundle.json> .
"""  # noqa: E501

WITHOUT_BUNDLE = """
@prefix rtm: <https://flexo-rtm.dev/ontology#> .
<https://rtm.example/activity/sim-1>
    a rtm:Activity ;
    rtm:hasOCIImage "ghcr.io/x/y@sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef" .
"""  # noqa: E501
# fmt: on


def _validate(turtle: str) -> tuple[bool, str]:
    data = Graph()
    data.parse(data=turtle, format="turtle")
    shapes = Graph()
    shapes.parse(PROFILE, format="turtle")
    ont = Graph()
    ont.parse(ASSEMBLED, format="turtle")
    conforms, _, text = pyshacl.validate(
        data_graph=data, shacl_graph=shapes, ont_graph=ont, inference="none", advanced=True
    )
    return conforms, text


def test_image_with_cosign_bundle_passes_profile() -> None:
    conforms, report = _validate(WITH_BUNDLE)
    assert conforms, report


def test_image_without_cosign_bundle_fails_profile() -> None:
    conforms, _ = _validate(WITHOUT_BUNDLE)
    assert not conforms


def test_verify_cosign_bundle_reports_missing_extra_when_dep_absent() -> None:
    if importlib.util.find_spec("sigstore") is not None:
        pytest.skip("flexo-rtm[cosign] is installed; lazy-import path not exercised")
    with pytest.raises(OptionalDependencyMissing) as exc:
        verify_cosign_bundle(
            "https://archive.example.org/cosign/x-y.bundle.json",
            image_digest="sha256:" + "0" * 64,
        )
    assert "flexo-rtm[cosign]" in str(exc.value)
