# SPDX-License-Identifier: Apache-2.0
"""S3 — dsse-activities profile gate + stub-verifier lazy-import check."""

from __future__ import annotations

import importlib
from pathlib import Path

import pyshacl
import pytest
from oracle.signing.dsse import verify_dsse_envelope
from oracle.signing.errors import OptionalDependencyMissing
from rdflib import Graph

from tests.conftest import ONTOLOGY_DIR

PROFILE: Path = ONTOLOGY_DIR / "profiles" / "dsse-activities.shacl.ttl"
ASSEMBLED: Path = ONTOLOGY_DIR / "rtm.ttl"

WITH_ENVELOPE = """
@prefix rtm: <https://flexo-rtm.dev/ontology#> .
<https://rtm.example/activity/sim-1>
    a rtm:Activity ;
    rtm:dsseEnvelope <https://archive.example.org/attestations/run-001.dsse.json> .
"""

WITHOUT_ENVELOPE = """
@prefix rtm: <https://flexo-rtm.dev/ontology#> .
<https://rtm.example/activity/sim-1> a rtm:Activity .
"""


def _validate(turtle: str) -> tuple[bool, str]:
    data = Graph()
    data.parse(data=turtle, format="turtle")
    shapes = Graph()
    shapes.parse(PROFILE, format="turtle")
    ont = Graph()
    ont.parse(ASSEMBLED, format="turtle")
    conforms, _, text = pyshacl.validate(
        data_graph=data, shacl_graph=shapes, ont_graph=ont, inference="none", advanced=False
    )
    return conforms, text


def test_activity_with_dsse_envelope_passes_profile() -> None:
    conforms, report = _validate(WITH_ENVELOPE)
    assert conforms, report


def test_activity_without_dsse_envelope_fails_profile() -> None:
    conforms, _ = _validate(WITHOUT_ENVELOPE)
    assert not conforms


def test_verify_dsse_envelope_reports_missing_extra_when_dep_absent() -> None:
    """If in-toto-attestation isn't installed (default), the stub verifier
    surfaces an OptionalDependencyMissing with the install instruction."""
    if importlib.util.find_spec("in_toto_attestation") is not None:
        pytest.skip("flexo-rtm[dsse] is installed; lazy-import path not exercised")
    with pytest.raises(OptionalDependencyMissing) as exc:
        verify_dsse_envelope("https://archive.example.org/attestations/run-001.dsse.json")
    assert "flexo-rtm[dsse]" in str(exc.value)
