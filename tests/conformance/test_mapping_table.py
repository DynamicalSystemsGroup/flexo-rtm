# SPDX-License-Identifier: Apache-2.0
"""Acceptance criterion O3: the enumerated core class set + link-type table is
normative. Adding a row requires updating the manifest, the SHACL profile, a
fixture, and this test together (OSLC Roundtrip Acceptance §10)."""

from __future__ import annotations

from oracle.adapters.oslc.qm import QM_CLASSES, QM_LINK_TYPES
from oracle.adapters.oslc.rm import RM_CLASSES, RM_LINK_TYPES


def test_rm_mapping_covers_published_link_types() -> None:
    expected = {
        "elaboratedBy",
        "elaborates",
        "specifiedBy",
        "specifies",
        "satisfiedBy",
        "satisfies",
        "tracedTo",
        "affectedBy",
        "constrainedBy",
        "constrains",
        "decomposedBy",
        "decomposes",
        "implementedBy",
        "trackedBy",
        "validatedBy",
    }
    assert set(RM_LINK_TYPES.keys()) == expected
    assert set(RM_CLASSES.keys()) == {"Requirement", "RequirementCollection"}


def test_qm_mapping_covers_published_link_types() -> None:
    expected = {
        "usesTestCase",
        "executesTestScript",
        "producedByTestExecutionRecord",
        "reportsOnTestCase",
        "reportsOnTestPlan",
        "runsTestCase",
        "runsOnTestEnvironment",
        "validatesRequirement",
        "blocksTestExecutionRecord",
        "relatedChangeRequest",
    }
    assert set(QM_LINK_TYPES.keys()) == expected
    assert set(QM_CLASSES.keys()) == {
        "TestPlan",
        "TestCase",
        "TestScript",
        "TestExecutionRecord",
        "TestResult",
    }


def test_oslc_satisfies_maps_to_rtm_addresses() -> None:
    """The slice-3 epistemic rename applies here: OSLC's 'satisfies' is
    evidence-level addressing in flexo-rtm's vocabulary."""
    assert RM_LINK_TYPES["satisfies"] == "addresses"
    assert QM_LINK_TYPES["validatesRequirement"] == "addresses"
