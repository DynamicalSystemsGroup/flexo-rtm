# SPDX-License-Identifier: Apache-2.0
"""SysMLv2 mapping table conformance — SysMLv2 Ingestion Contract §5."""

from __future__ import annotations

from oracle.adapters.sysmlv2.mapping import SYSMLV2_CLASSES, SYSMLV2_LINK_TYPES


def test_sysmlv2_classes_cover_published_set() -> None:
    expected = {
        "RequirementUsage",
        "RequirementDefinition",
        "PartUsage",
        "PartDefinition",
        "Action",
        "Constraint",
        "VerificationCaseUsage",
    }
    assert expected.issubset(set(SYSMLV2_CLASSES.keys()))


def test_sysmlv2_link_types_include_satisfies_and_verifies() -> None:
    assert "satisfies" in SYSMLV2_LINK_TYPES
    assert "verifies" in SYSMLV2_LINK_TYPES


def test_satisfies_and_verifies_both_map_to_addresses() -> None:
    """Slice-3 epistemic precedent: both SysMLv2 verification edges map to
    rtm:addresses. The SysMLv2 design-time vs verification-time distinction is
    preserved in the source graph, not in the analysis layer's predicate."""
    assert SYSMLV2_LINK_TYPES["satisfies"] == "addresses"
    assert SYSMLV2_LINK_TYPES["verifies"] == "addresses"


def test_requirement_usage_maps_to_rtm_requirement() -> None:
    assert SYSMLV2_CLASSES["RequirementUsage"] == "Requirement"
    assert SYSMLV2_CLASSES["VerificationCaseUsage"] == "TestCase"
