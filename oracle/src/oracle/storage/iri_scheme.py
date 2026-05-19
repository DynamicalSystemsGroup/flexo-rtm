# SPDX-License-Identifier: Apache-2.0
"""Named-graph IRI scheme + branch conventions — Flexo REST Binding §4 + §6.

Stable, prefix-based names so adopters can identify graph kind from the IRI
alone. Tests (F3, F6) consume these constants.
"""

from __future__ import annotations

import re

# §4.1 — per-partition graphs
PARTITION_GRAPHS: dict[str, str] = {
    "model": "urn:rtm:model",
    "requirements": "urn:rtm:requirements",
    "guidance": "urn:rtm:guidance",
    "attestations": "urn:rtm:attestations",
    "transcripts": "urn:rtm:transcripts",
    "audit": "urn:rtm:audit",
    "identity-projection": "urn:rtm:identity-projection",
    "scopes": "urn:rtm:scopes",
    "lifecycle": "urn:rtm:lifecycle",
}

# §4.2 — per-resource source graphs (Layer C carry-through)
SOURCE_GRAPH_PREFIX: dict[str, str] = {
    "oslc-rm": "urn:rtm:source/oslc-rm/",
    "oslc-qm": "urn:rtm:source/oslc-qm/",
    "sysmlv2": "urn:rtm:source/sysmlv2/",
}

# §4.3 — run-scoped graphs
RUN_SCOPED_PREFIX: dict[str, str] = {
    "transcript": "urn:rtm:transcript/",
    "attestation-graph": "urn:rtm:attestation-graph/",
    "audit": "urn:rtm:audit/",
}

# §6 — branch model
MAIN_BRANCH = "main"
ENGINEERING_BRANCH_PREFIX = "engineering/"
CERT_BRANCH_PREFIX = "cert/"

# Branch-name validation. Letters, digits, hyphen, underscore, and the
# slash-separators that the engineering/<team> and cert/<run-id> patterns
# require. No spaces, no leading/trailing slash, no double-slash.
_BRANCH_NAME_RE = re.compile(r"^(?!.*//)[A-Za-z0-9](?:[A-Za-z0-9_/-]*[A-Za-z0-9])?$")


def is_main_branch(branch: str) -> bool:
    return branch == MAIN_BRANCH


def is_valid_branch_name(branch: str) -> bool:
    """Branch matches the §6 patterns: main, engineering/{team}, or cert/{run-id}."""
    if not _BRANCH_NAME_RE.match(branch):
        return False
    if is_main_branch(branch):
        return True
    return branch.startswith(ENGINEERING_BRANCH_PREFIX) or branch.startswith(CERT_BRANCH_PREFIX)


__all__ = [
    "CERT_BRANCH_PREFIX",
    "ENGINEERING_BRANCH_PREFIX",
    "MAIN_BRANCH",
    "PARTITION_GRAPHS",
    "RUN_SCOPED_PREFIX",
    "SOURCE_GRAPH_PREFIX",
    "is_main_branch",
    "is_valid_branch_name",
]
