# SPDX-License-Identifier: Apache-2.0
"""Acceptance criterion O6: --profile=oslc-rm-roundtrip / oslc-qm-roundtrip
PASSes only when every profile shape passes against the graph being certified."""

from __future__ import annotations

from pathlib import Path

import pyshacl
from rdflib import Graph

from tests.conftest import ONTOLOGY_DIR

RM_PROFILE: Path = ONTOLOGY_DIR / "profiles" / "oslc-rm-roundtrip.shacl.ttl"
QM_PROFILE: Path = ONTOLOGY_DIR / "profiles" / "oslc-qm-roundtrip.shacl.ttl"

WELL_FORMED_RM = """
@prefix oslc_rm: <http://open-services.net/ns/rm#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
<https://rtm.example/req/r1>
    a oslc_rm:Requirement ;
    dcterms:identifier "r1" ;
    dcterms:title "well-formed" .
"""

MISSING_TITLE_RM = """
@prefix oslc_rm: <http://open-services.net/ns/rm#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
<https://rtm.example/req/r1> a oslc_rm:Requirement ; dcterms:identifier "r1" .
"""

WELL_FORMED_QM = """
@prefix oslc_qm: <http://open-services.net/ns/qm#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
<https://rtm.example/tc/t1>
    a oslc_qm:TestCase ;
    dcterms:identifier "t1" ;
    dcterms:title "well-formed" .
"""


def _validate(turtle: str, profile_path: Path) -> tuple[bool, str]:
    data = Graph()
    data.parse(data=turtle, format="turtle")
    shapes = Graph()
    shapes.parse(profile_path, format="turtle")
    conforms, _, text = pyshacl.validate(
        data_graph=data, shacl_graph=shapes, inference="none", advanced=False
    )
    return conforms, text


def test_rm_profile_passes_well_formed_requirement() -> None:
    conforms, report = _validate(WELL_FORMED_RM, RM_PROFILE)
    assert conforms, report


def test_rm_profile_rejects_missing_title() -> None:
    conforms, _ = _validate(MISSING_TITLE_RM, RM_PROFILE)
    assert not conforms


def test_qm_profile_passes_well_formed_test_case() -> None:
    conforms, report = _validate(WELL_FORMED_QM, QM_PROFILE)
    assert conforms, report
