# SPDX-License-Identifier: Apache-2.0
"""§4.8 — composition + federated audit profile gates (composition-adequacy,
composition-sufficiency, qualified-audit-per-scope). Plus a unit assertion
that the 3 new attestation subclasses inherit the approver shape via
``rdfs:subClassOf rtm:Attestation``.
"""

from __future__ import annotations

from pathlib import Path

import pyshacl
from oracle.composition import (
    CertificationLevel,
    count_signers,
    scope_certification_level,
)
from rdflib import RDF, RDFS, Graph, URIRef

from tests.conftest import ONTOLOGY_DIR

PROFILES = ONTOLOGY_DIR / "profiles"
ASSEMBLED: Path = ONTOLOGY_DIR / "rtm.ttl"

RTM = "https://flexo-rtm.dev/ontology#"

SCOPE_WITH_CERT = f"""
@prefix rtm: <{RTM}> .
<https://rtm.example/scope/A> a rtm:Scope .
<https://rtm.example/att/audit-A>
    a rtm:ScopeCertificationAttestation ;
    rtm:approvedBy <https://rtm.example/person/auditor> ;
    rtm:attests <https://rtm.example/scope/A> ;
    rtm:auditMode rtm:audit-mode-reproducibility-full ;
    rtm:status rtm:pass .
"""

SCOPE_WITHOUT_CERT = f"""
@prefix rtm: <{RTM}> .
<https://rtm.example/scope/B> a rtm:Scope .
"""

COMPOSED_WITH_COVERAGE = f"""
@prefix rtm: <{RTM}> .

<https://rtm.example/scope/A> a rtm:Scope .
<https://rtm.example/scope/B> a rtm:Scope .

<https://rtm.example/scope/composed>
    a rtm:Scope ;
    rtm:union <https://rtm.example/scope/A>, <https://rtm.example/scope/B> .

<https://rtm.example/att/coverage>
    a rtm:CompositionCoverageAttestation ;
    rtm:approvedBy <https://rtm.example/person/sos-certifier> ;
    rtm:attests <https://rtm.example/scope/composed> ;
    rtm:status rtm:pass .

<https://rtm.example/att/sufficiency>
    a rtm:CompositionSufficiencyAttestation ;
    rtm:approvedBy <https://rtm.example/person/sos-certifier> ;
    rtm:attests <https://rtm.example/scope/composed> ;
    rtm:status rtm:pass .
"""

COMPOSED_WITHOUT_COVERAGE = f"""
@prefix rtm: <{RTM}> .
<https://rtm.example/scope/A> a rtm:Scope .
<https://rtm.example/scope/composed>
    a rtm:Scope ;
    rtm:union <https://rtm.example/scope/A> .
"""


def _validate(turtle: str, profile_path: Path) -> tuple[bool, str]:
    data = Graph()
    data.parse(data=turtle, format="turtle")
    shapes = Graph()
    shapes.parse(profile_path, format="turtle")
    ont = Graph()
    ont.parse(ASSEMBLED, format="turtle")
    conforms, _, text = pyshacl.validate(
        data_graph=data, shacl_graph=shapes, ont_graph=ont, inference="none", advanced=True
    )
    return conforms, text


def test_qualified_audit_per_scope_passes_when_attestation_present() -> None:
    conforms, report = _validate(SCOPE_WITH_CERT, PROFILES / "qualified-audit-per-scope.shacl.ttl")
    assert conforms, report


def test_qualified_audit_per_scope_fails_when_scope_uncertified() -> None:
    conforms, _ = _validate(SCOPE_WITHOUT_CERT, PROFILES / "qualified-audit-per-scope.shacl.ttl")
    assert not conforms


def test_composition_adequacy_passes_when_coverage_attestation_present() -> None:
    conforms, report = _validate(
        COMPOSED_WITH_COVERAGE, PROFILES / "composition-adequacy.shacl.ttl"
    )
    assert conforms, report


def test_composition_adequacy_fails_when_coverage_absent() -> None:
    conforms, _ = _validate(COMPOSED_WITHOUT_COVERAGE, PROFILES / "composition-adequacy.shacl.ttl")
    assert not conforms


def test_composition_sufficiency_passes_when_sufficiency_attestation_present() -> None:
    conforms, report = _validate(
        COMPOSED_WITH_COVERAGE, PROFILES / "composition-sufficiency.shacl.ttl"
    )
    assert conforms, report


def test_new_attestation_subclasses_inherit_attestation_parent() -> None:
    """Every composition subclass is rdfs:subClassOf rtm:Attestation, so the
    approver-shape (slice 1's AttestationShape) automatically targets them."""
    g = Graph()
    g.parse(ASSEMBLED, format="turtle")
    attestation = URIRef(RTM + "Attestation")
    for subclass_name in (
        "ScopeCertificationAttestation",
        "CompositionCoverageAttestation",
        "CompositionSufficiencyAttestation",
    ):
        subclass = URIRef(RTM + subclass_name)
        assert (subclass, RDFS.subClassOf, attestation) in g, (
            f"{subclass_name} must declare rdfs:subClassOf rtm:Attestation"
        )
        assert (subclass, RDF.type, None) in g


def test_certification_level_reads_attestation_graph() -> None:
    """The composition helper enumerates per-scope L1-L4 from the attestation graph."""
    g = Graph()
    g.parse(data=SCOPE_WITH_CERT, format="turtle")
    level = scope_certification_level(URIRef("https://rtm.example/scope/A"), attestations=g)
    assert level == CertificationLevel.REPRODUCIBILITY_AUDIT


def test_count_signers_counts_distinct_approvers() -> None:
    g = Graph()
    g.parse(data=SCOPE_WITH_CERT, format="turtle")
    n = count_signers(URIRef("https://rtm.example/scope/A"), attestations=g)
    assert n == 1
