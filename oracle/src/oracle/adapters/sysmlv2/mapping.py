# SPDX-License-Identifier: Apache-2.0
"""SysMLv2 → rtm: mapping tables — SysMLv2 Ingestion Contract §5.

Both ``satisfies`` and ``verifies`` map to ``rtm:addresses`` per the slice-3
epistemic rename (see CLAUDE.md §Research-repo divergences and
flexo-rtm-research#16). The SysMLv2 design-time vs verification-time distinction
is preserved in the source graph; the analysis layer treats both as addressing
edges and looks at the source graph if the SysMLv2-level distinction matters.
"""

from __future__ import annotations

SYSMLV2_NAMESPACE = "https://www.omg.org/spec/SysML/20240801/SysML#"

SYSMLV2_CLASSES: dict[str, str] = {
    "RequirementUsage": "Requirement",
    "RequirementDefinition": "RequirementDefinition",
    "PartUsage": "Artifact",
    "PartDefinition": "Artifact",
    "Action": "Activity",
    "Constraint": "Constraint",
    "VerificationCaseUsage": "TestCase",
}

SYSMLV2_LINK_TYPES: dict[str, str] = {
    "satisfies": "addresses",
    "verifies": "addresses",
    "owner": "owner",
}


__all__ = ["SYSMLV2_CLASSES", "SYSMLV2_LINK_TYPES", "SYSMLV2_NAMESPACE"]
