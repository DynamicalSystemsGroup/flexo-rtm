# SPDX-License-Identifier: Apache-2.0
"""OSLC-RM 2.1 specific helpers. The roundtrip mechanics live in ``core``;
this module only enumerates the RM core mapping for ``test_mapping_table``.
"""

from __future__ import annotations

OSLC_RM_NAMESPACE = "http://open-services.net/ns/rm#"

# Per OSLC Roundtrip Acceptance §4.2 — every row is a mapping the analysis
# layer can rely on. The right-hand side is the rtm:* peer in the assembled
# rtm.ttl ontology. The OSLC oslc_rm:satisfies edge maps to rtm:addresses
# per the slice-3 epistemic rename (see CLAUDE.md §Research-repo divergences).
RM_LINK_TYPES: dict[str, str] = {
    "elaboratedBy": "elaboratedBy",
    "elaborates": "elaborates",
    "specifiedBy": "specifiedBy",
    "specifies": "specifies",
    "satisfiedBy": "satisfiedBy",
    "satisfies": "addresses",
    "tracedTo": "tracedTo",
    "affectedBy": "affectedBy",
    "constrainedBy": "constrainedBy",
    "constrains": "constrains",
    "decomposedBy": "decomposedBy",
    "decomposes": "decomposes",
    "implementedBy": "implementedBy",
    "trackedBy": "trackedBy",
    "validatedBy": "validatedBy",
}

RM_CLASSES: dict[str, str] = {
    "Requirement": "Requirement",
    "RequirementCollection": "RequirementCollection",
}


__all__ = ["OSLC_RM_NAMESPACE", "RM_CLASSES", "RM_LINK_TYPES"]
