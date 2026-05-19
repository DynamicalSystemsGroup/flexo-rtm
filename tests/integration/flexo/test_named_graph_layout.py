# SPDX-License-Identifier: Apache-2.0
"""F3 — named-graph layout per Flexo REST Binding §4."""

from __future__ import annotations

from oracle.storage.iri_scheme import (
    PARTITION_GRAPHS,
    RUN_SCOPED_PREFIX,
    SOURCE_GRAPH_PREFIX,
)


def test_partition_graph_iris_match_contract() -> None:
    assert PARTITION_GRAPHS["model"] == "urn:rtm:model"
    assert PARTITION_GRAPHS["requirements"] == "urn:rtm:requirements"
    assert PARTITION_GRAPHS["guidance"] == "urn:rtm:guidance"
    assert PARTITION_GRAPHS["attestations"] == "urn:rtm:attestations"
    assert PARTITION_GRAPHS["transcripts"] == "urn:rtm:transcripts"
    assert PARTITION_GRAPHS["audit"] == "urn:rtm:audit"
    assert PARTITION_GRAPHS["identity-projection"] == "urn:rtm:identity-projection"
    assert PARTITION_GRAPHS["scopes"] == "urn:rtm:scopes"
    assert PARTITION_GRAPHS["lifecycle"] == "urn:rtm:lifecycle"


def test_source_graph_prefixes_match_contract() -> None:
    assert SOURCE_GRAPH_PREFIX["oslc-rm"] == "urn:rtm:source/oslc-rm/"
    assert SOURCE_GRAPH_PREFIX["oslc-qm"] == "urn:rtm:source/oslc-qm/"
    assert SOURCE_GRAPH_PREFIX["sysmlv2"] == "urn:rtm:source/sysmlv2/"


def test_run_scoped_prefixes_match_contract() -> None:
    assert RUN_SCOPED_PREFIX["transcript"] == "urn:rtm:transcript/"
    assert RUN_SCOPED_PREFIX["attestation-graph"] == "urn:rtm:attestation-graph/"
    assert RUN_SCOPED_PREFIX["audit"] == "urn:rtm:audit/"
