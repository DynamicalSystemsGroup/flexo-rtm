# SPDX-License-Identifier: Apache-2.0
"""Audit-side: attestations carrying prov:wasInvalidatedBy MUST be excluded
from coverage / certification-level computations.

This closes the loop on the constructor's deprecate flow — emitting the
prov:wasInvalidatedBy triple is meaningful only if the audit side honors it.
"""

from __future__ import annotations

from rdflib import Graph, Namespace, URIRef

from oracle.composition.levels import (
    CertificationLevel,
    count_signers,
    scope_certification_level,
)

RTM = Namespace("https://flexo-rtm.dev/ontology#")
PROV = Namespace("http://www.w3.org/ns/prov#")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")

SCOPE = URIRef("https://rtm.example/scope/s1")


def _live_attestation(att: URIRef) -> Graph:
    g = Graph()
    g.add((att, RDF.type, RTM.ScopeCertificationAttestation))
    g.add((att, RTM.attests, SCOPE))
    g.add((att, RTM.approvedBy, URIRef("https://example.org/alice")))
    g.add((att, RTM.auditMode, URIRef(str(RTM) + "audit-mode-reproducibility-full")))
    return g


def _deprecated_attestation(att: URIRef, activity: URIRef) -> Graph:
    g = _live_attestation(att)
    g.add((att, PROV.wasInvalidatedBy, activity))
    return g


def test_deprecated_attestation_does_not_lift_certification_level() -> None:
    """A scope with one deprecated reproducibility attestation and no live
    ones must remain at SELF_CERT_ONLY (not REPRODUCIBILITY_AUDIT)."""
    attestations = _deprecated_attestation(
        URIRef("urn:rtm:attest/old"),
        URIRef("urn:rtm:commit/c1"),
    )
    assert (
        scope_certification_level(SCOPE, attestations=attestations)
        == CertificationLevel.SELF_CERT_ONLY
    )


def test_live_attestation_lifts_certification_level() -> None:
    """Control: a single live attestation does lift the level."""
    attestations = _live_attestation(URIRef("urn:rtm:attest/live"))
    assert (
        scope_certification_level(SCOPE, attestations=attestations)
        == CertificationLevel.REPRODUCIBILITY_AUDIT
    )


def test_deprecated_attestations_not_counted_as_signers() -> None:
    """count_signers must skip deprecated attestations."""
    g = _deprecated_attestation(URIRef("urn:rtm:attest/old"), URIRef("urn:rtm:commit/c1"))
    g += _live_attestation(URIRef("urn:rtm:attest/live"))
    # The live attestation has a different approvedBy
    g.set(
        (
            URIRef("urn:rtm:attest/live"),
            RTM.approvedBy,
            URIRef("https://example.org/bob"),
        )
    )
    assert count_signers(SCOPE, attestations=g) == 1


def test_mixed_live_and_deprecated_certification_uses_only_live() -> None:
    """A scope with a deprecated reproducibility attestation plus a live one
    still gets REPRODUCIBILITY_AUDIT (the live one carries the level)."""
    g = _deprecated_attestation(URIRef("urn:rtm:attest/old"), URIRef("urn:rtm:commit/c1"))
    g += _live_attestation(URIRef("urn:rtm:attest/live"))
    assert (
        scope_certification_level(SCOPE, attestations=g) == CertificationLevel.REPRODUCIBILITY_AUDIT
    )
