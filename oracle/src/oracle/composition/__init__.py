# SPDX-License-Identifier: Apache-2.0
"""Composition + federated audit — Design Spec §4.8, Federated Audit and Composition.

Helpers that consume an attestation graph and report per-scope certification
levels (L1 self-cert only → L4 composition-certified). The SHACL profiles in
``ontology/profiles/{composition-adequacy, composition-sufficiency,
qualified-audit-per-scope}.shacl.ttl`` enforce structural presence; this module
adds the SPARQL-based counts and level enumeration the audit report consumes.
"""

from oracle.composition.levels import (
    SCOPE_CERTIFICATION_LEVELS,
    CertificationLevel,
    count_signers,
    enumerate_signer_orgs,
    scope_certification_level,
)

__all__ = [
    "SCOPE_CERTIFICATION_LEVELS",
    "CertificationLevel",
    "count_signers",
    "enumerate_signer_orgs",
    "scope_certification_level",
]
