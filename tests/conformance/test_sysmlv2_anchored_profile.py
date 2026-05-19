# SPDX-License-Identifier: Apache-2.0
"""sysmlv2-anchored profile conformance — SysMLv2 Ingestion Contract §4."""

from __future__ import annotations

from pathlib import Path

import pyshacl
from rdflib import Graph

from tests.conftest import ONTOLOGY_DIR

PROFILE_PATH: Path = ONTOLOGY_DIR / "profiles" / "sysmlv2-anchored.shacl.ttl"
ASSEMBLED: Path = ONTOLOGY_DIR / "rtm.ttl"


def _validate(turtle: str) -> tuple[bool, str]:
    data = Graph()
    data.parse(data=turtle, format="turtle")
    shapes = Graph()
    shapes.parse(PROFILE_PATH, format="turtle")
    ont = Graph()
    ont.parse(ASSEMBLED, format="turtle")
    conforms, _, text = pyshacl.validate(
        data_graph=data,
        shacl_graph=shapes,
        ont_graph=ont,
        inference="none",
        advanced=False,
    )
    return conforms, text


WELL_FORMED = """
@prefix omg-sysml: <https://www.omg.org/spec/SysML/20240801/SysML#> .
<https://rtm.example/req/r1>
    a omg-sysml:RequirementUsage ;
    omg-sysml:elementId "R1" ;
    omg-sysml:qualifiedName "ADCS::R1" .
"""

MISSING_ELEMENT_ID = """
@prefix omg-sysml: <https://www.omg.org/spec/SysML/20240801/SysML#> .
<https://rtm.example/req/r1>
    a omg-sysml:RequirementUsage ;
    omg-sysml:qualifiedName "ADCS::R1" .
"""

MISSING_QUALIFIED_NAME = """
@prefix omg-sysml: <https://www.omg.org/spec/SysML/20240801/SysML#> .
<https://rtm.example/req/r1>
    a omg-sysml:RequirementUsage ;
    omg-sysml:elementId "R1" .
"""

TWO_OWNERS = """
@prefix omg-sysml: <https://www.omg.org/spec/SysML/20240801/SysML#> .
<https://rtm.example/req/r1>
    a omg-sysml:RequirementUsage ;
    omg-sysml:elementId "R1" ;
    omg-sysml:qualifiedName "ADCS::R1" ;
    omg-sysml:owner <https://rtm.example/o1> , <https://rtm.example/o2> .
"""


def test_well_formed_element_passes() -> None:
    conforms, report = _validate(WELL_FORMED)
    assert conforms, report


def test_missing_element_id_fails() -> None:
    conforms, report = _validate(MISSING_ELEMENT_ID)
    assert not conforms
    assert "elementId" in report


def test_missing_qualified_name_fails() -> None:
    conforms, report = _validate(MISSING_QUALIFIED_NAME)
    assert not conforms
    assert "qualifiedName" in report


def test_two_owners_fails_containment_invariant() -> None:
    conforms, _ = _validate(TWO_OWNERS)
    assert not conforms
