# SPDX-License-Identifier: Apache-2.0
"""OSLC-QM 2.1 specific helpers. Mapping tables only; the roundtrip mechanics
live in ``core``.
"""

from __future__ import annotations

OSLC_QM_NAMESPACE = "http://open-services.net/ns/qm#"

# Per OSLC Roundtrip Acceptance §5.2.
QM_LINK_TYPES: dict[str, str] = {
    "usesTestCase": "usesTestCase",
    "executesTestScript": "executesTestScript",
    "producedByTestExecutionRecord": "producedByTestExecutionRecord",
    "reportsOnTestCase": "reportsOnTestCase",
    "reportsOnTestPlan": "reportsOnTestPlan",
    "runsTestCase": "runsTestCase",
    "runsOnTestEnvironment": "runsOnTestEnvironment",
    "validatesRequirement": "addresses",
    "blocksTestExecutionRecord": "blocksTestExecutionRecord",
    "relatedChangeRequest": "relatedChangeRequest",
}

QM_CLASSES: dict[str, str] = {
    "TestPlan": "TestPlan",
    "TestCase": "TestCase",
    "TestScript": "TestScript",
    "TestExecutionRecord": "TestExecutionRecord",
    "TestResult": "TestResult",
}

# Per OSLC Roundtrip Acceptance §5.3.
QM_VERDICT_TO_STATUS: dict[str, str] = {
    "passed": "pass",
    "failed": "fail",
    "inconclusive": "deferred",
    "error": "fail",
    "blocked": "deferred",
}


__all__ = ["OSLC_QM_NAMESPACE", "QM_CLASSES", "QM_LINK_TYPES", "QM_VERDICT_TO_STATUS"]
