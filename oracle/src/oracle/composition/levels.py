# SPDX-License-Identifier: Apache-2.0
"""Per-scope certification level enumeration — Federated Audit and Composition.

Four levels stack:

- **Level 1** — Self-certification only. The scope carries internal
  ``rtm:Satisfaction/Adequacy/SufficiencyAttestation`` instances; no external
  party has signed.
- **Level 2** — Reproducibility audit. ≥ 1 external party has attested a
  ``rtm:ScopeCertificationAttestation`` with ``rtm:auditMode`` of
  ``reproducibility-partial`` or ``reproducibility-full``.
- **Level 3** — Qualified-role audit. ≥ 1 attestation with audit-mode
  ``qualified-role-review`` from an organization bearing
  ``rtm:hasQualifiedRole``.
- **Level 4** — Composition certification. The scope is composed and carries
  both ``rtm:CompositionCoverageAttestation`` and
  ``rtm:CompositionSufficiencyAttestation``.

A scope at Level N inherits levels 1..N-1; the helper returns the highest level
the scope satisfies. Slice 10 ships per-scope enumeration; slice 11 wires this
into the audit report.
"""

from __future__ import annotations

from enum import IntEnum

from rdflib import RDF, Graph, Namespace, URIRef

RTM = Namespace("https://flexo-rtm.dev/ontology#")


class CertificationLevel(IntEnum):
    SELF_CERT_ONLY = 1
    REPRODUCIBILITY_AUDIT = 2
    QUALIFIED_ROLE_AUDIT = 3
    COMPOSITION_CERTIFIED = 4


SCOPE_CERTIFICATION_LEVELS: tuple[CertificationLevel, ...] = tuple(CertificationLevel)

_REPRODUCIBILITY_MODES = frozenset(
    {
        URIRef(str(RTM) + "audit-mode-reproducibility-partial"),
        URIRef(str(RTM) + "audit-mode-reproducibility-full"),
    }
)
_QUALIFIED_ROLE_MODE = URIRef(str(RTM) + "audit-mode-qualified-role-review")


def _attestations_targeting(scope: URIRef, attestations: Graph, *, of_type: URIRef) -> set[URIRef]:
    """Subjects of attestations of ``of_type`` whose ``rtm:attests`` is ``scope``."""
    candidates: set[URIRef] = {URIRef(str(s)) for s in attestations.subjects(RDF.type, of_type)}
    return {s for s in candidates if (s, RTM.attests, scope) in attestations}


def _has_mode(att: URIRef, attestations: Graph, *, mode: URIRef | frozenset[URIRef]) -> bool:
    modes = {mode} if isinstance(mode, URIRef) else set(mode)
    for _, _, value in attestations.triples((att, RTM.auditMode, None)):
        if URIRef(str(value)) in modes:
            return True
    return False


def _approver_org_has_qualified_role(att: URIRef, attestations: Graph) -> bool:
    for _, _, org in attestations.triples((att, RTM.approverOrganization, None)):
        if (URIRef(str(org)), RTM.hasQualifiedRole, None) in attestations:
            return True
        if any(attestations.triples((URIRef(str(org)), RTM.hasQualifiedRole, None))):
            return True
    return False


def scope_certification_level(
    scope: URIRef,
    *,
    attestations: Graph,
) -> CertificationLevel:
    """Return the highest level the scope satisfies given ``attestations``."""
    scope_certs = _attestations_targeting(
        scope, attestations, of_type=RTM.ScopeCertificationAttestation
    )
    composition_coverage = _attestations_targeting(
        scope, attestations, of_type=RTM.CompositionCoverageAttestation
    )
    composition_sufficiency = _attestations_targeting(
        scope, attestations, of_type=RTM.CompositionSufficiencyAttestation
    )

    if composition_coverage and composition_sufficiency:
        return CertificationLevel.COMPOSITION_CERTIFIED

    if any(
        _has_mode(att, attestations, mode=_QUALIFIED_ROLE_MODE)
        and _approver_org_has_qualified_role(att, attestations)
        for att in scope_certs
    ):
        return CertificationLevel.QUALIFIED_ROLE_AUDIT

    if any(_has_mode(att, attestations, mode=_REPRODUCIBILITY_MODES) for att in scope_certs):
        return CertificationLevel.REPRODUCIBILITY_AUDIT

    return CertificationLevel.SELF_CERT_ONLY


def count_signers(scope: URIRef, *, attestations: Graph) -> int:
    """Count distinct ``rtm:approvedBy`` values on rtm:ScopeCertificationAttestation
    instances that target ``scope``. Used by composition-sufficiency thresholds.
    """
    signers: set[URIRef] = set()
    for att in _attestations_targeting(
        scope, attestations, of_type=RTM.ScopeCertificationAttestation
    ):
        for _, _, approver in attestations.triples((att, RTM.approvedBy, None)):
            signers.add(URIRef(str(approver)))
    return len(signers)


def enumerate_signer_orgs(scope: URIRef, *, attestations: Graph) -> set[URIRef]:
    """Return the set of organizations that have attested over ``scope``."""
    orgs: set[URIRef] = set()
    for att in _attestations_targeting(
        scope, attestations, of_type=RTM.ScopeCertificationAttestation
    ):
        for _, _, org in attestations.triples((att, RTM.approverOrganization, None)):
            orgs.add(URIRef(str(org)))
    return orgs


__all__ = [
    "SCOPE_CERTIFICATION_LEVELS",
    "CertificationLevel",
    "count_signers",
    "enumerate_signer_orgs",
    "scope_certification_level",
]
