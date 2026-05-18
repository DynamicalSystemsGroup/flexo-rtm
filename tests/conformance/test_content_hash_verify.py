# SPDX-License-Identifier: Apache-2.0
"""Acceptance criterion U2: verify_content_hash recomputes the digest under the
recorded algorithm and compares to the recorded hex string. Offline; the
caller is responsible for the transport (HTTPS fetch, IPFS resolution, etc.)."""

from __future__ import annotations

import hashlib

from oracle.uri.fetch import verify_content_hash


def test_sha256_match() -> None:
    payload = b"the quick brown fox jumps over the lazy dog"
    recorded = f"sha256:{hashlib.sha256(payload).hexdigest()}"
    result = verify_content_hash(recorded, payload=payload)
    assert result.ok, result.detail
    assert "sha256" in result.detail


def test_sha256_mismatch_reports_both_hashes() -> None:
    payload = b"actual content"
    bogus_digest = "0" * 64
    result = verify_content_hash(f"sha256:{bogus_digest}", payload=payload)
    assert not result.ok
    assert "mismatch" in result.detail


def test_sha512_match() -> None:
    payload = b"another payload"
    recorded = f"sha512:{hashlib.sha512(payload).hexdigest()}"
    assert verify_content_hash(recorded, payload=payload).ok


def test_unsupported_algorithm_reports_clearly() -> None:
    # ipfs requires an external resolver, not hashlib — verify_content_hash
    # should refuse rather than emit a false-positive.
    result = verify_content_hash(
        "ipfs:bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi",
        payload=b"any",
    )
    assert not result.ok
    assert "ipfs" in result.detail.lower() or "resolver" in result.detail.lower()
