# SPDX-License-Identifier: Apache-2.0
"""Storage layer — Design Spec §5.4, Flexo REST Binding.

A narrow Protocol (:class:`FlexoBackend`) defines the surface that the rest of
the oracle consumes. Two implementations:

- :class:`InMemoryFlexoBackend` — fake backend for non-live tests; behaves
  like Flexo's atomic-transaction semantics without a network.
- :class:`FlexoHttpClient` — HTTPS client against a real Flexo MMS Layer 1 API
  endpoint, used by ``@pytest.mark.live`` tests when ``FLEXO_TOKEN`` is set.

High-level commit/read/merge operations live in :mod:`oracle.storage.adapter`
on top of either backend.
"""

from oracle.storage.adapter import (
    CommitResult,
    commit_atomic_batch,
    read_commit_scope,
    request_merge,
)
from oracle.storage.backend import (
    FlexoBackend,
    MergePolicyHints,
    MergeResult,
)
from oracle.storage.flexo_client import FlexoConfig, FlexoHttpClient
from oracle.storage.in_memory import InMemoryFlexoBackend
from oracle.storage.iri_scheme import (
    CERT_BRANCH_PREFIX,
    ENGINEERING_BRANCH_PREFIX,
    MAIN_BRANCH,
    PARTITION_GRAPHS,
    RUN_SCOPED_PREFIX,
    SOURCE_GRAPH_PREFIX,
    is_main_branch,
    is_valid_branch_name,
)

__all__ = [
    "CERT_BRANCH_PREFIX",
    "CommitResult",
    "ENGINEERING_BRANCH_PREFIX",
    "FlexoBackend",
    "FlexoConfig",
    "FlexoHttpClient",
    "InMemoryFlexoBackend",
    "MAIN_BRANCH",
    "MergePolicyHints",
    "MergeResult",
    "PARTITION_GRAPHS",
    "RUN_SCOPED_PREFIX",
    "SOURCE_GRAPH_PREFIX",
    "commit_atomic_batch",
    "is_main_branch",
    "is_valid_branch_name",
    "read_commit_scope",
    "request_merge",
]
