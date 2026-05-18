# SPDX-License-Identifier: Apache-2.0
"""Audit-mode fetchers — External URI Rules §6.2.

Each fetcher is opt-in (the default cert run is offline, per §6.1). When
enabled, the fetcher consults the external authoritative source and returns
a :class:`FetchResult` describing whether the recorded reference resolves
correctly.

Slice 5 implements:
- ``verify_content_hash`` with an injectable byte source (no network required
  for the offline test path).
- ``check_git_commit_exists`` via ``git ls-remote`` subprocess.
- ``check_oci_digest_exists`` via OCI Distribution Specification HTTPS GET.

The git / OCI helpers always need network; tests covering them are marked
``@pytest.mark.network`` and auto-skipped without the FLEXO_RTM_NETWORK_TESTS
env var set.
"""

from __future__ import annotations

import hashlib
import subprocess
import urllib.request
from dataclasses import dataclass

from oracle.uri.validation import ContentHash, OCIImageRef

_HASHLIB_ALGORITHMS = {
    "sha256": hashlib.sha256,
    "sha384": hashlib.sha384,
    "sha512": hashlib.sha512,
    "sha3-256": hashlib.sha3_256,
    "sha3-512": hashlib.sha3_512,
}


@dataclass(frozen=True)
class FetchResult:
    ok: bool
    detail: str


def verify_content_hash(recorded: str, *, payload: bytes) -> FetchResult:
    """Compute the hash of ``payload`` under the algorithm declared in
    ``recorded`` and compare to the recorded digest. Returns :class:`FetchResult`.

    No network is performed; the caller is responsible for supplying the bytes
    (typically by fetching ``dcat:downloadURL`` or another mirror). This keeps
    the algorithm in flexo-rtm's control while transport stays at the call site.
    """
    parsed = ContentHash.parse(recorded)
    hasher_factory = _HASHLIB_ALGORITHMS.get(parsed.algorithm)
    if hasher_factory is None:
        return FetchResult(
            ok=False,
            detail=(
                f"algorithm {parsed.algorithm!r} not supported by hashlib in this build; "
                "ipfs/cid require an external resolver"
            ),
        )
    hasher = hasher_factory()
    hasher.update(payload)
    computed = hasher.hexdigest()
    if computed.lower() == parsed.digest.lower():
        return FetchResult(ok=True, detail=f"{parsed.algorithm} match")
    return FetchResult(
        ok=False,
        detail=f"{parsed.algorithm} mismatch: recorded={parsed.digest} computed={computed}",
    )


def check_git_commit_exists(*, repo: str, commit: str) -> FetchResult:
    """Run ``git ls-remote <repo>`` and check whether the recorded commit is
    in the output. Requires network and the ``git`` binary on PATH.
    """
    try:
        proc = subprocess.run(
            ["git", "ls-remote", repo],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return FetchResult(ok=False, detail=f"git ls-remote failed: {exc}")
    if proc.returncode != 0:
        return FetchResult(
            ok=False, detail=f"git ls-remote exit {proc.returncode}: {proc.stderr.strip()}"
        )
    if commit.lower() in proc.stdout.lower():
        return FetchResult(ok=True, detail=f"commit found on remote: {commit}")
    return FetchResult(ok=False, detail=f"commit {commit} not found on {repo}")


def check_oci_digest_exists(image_ref: str, *, accept_header: str | None = None) -> FetchResult:
    """Resolve ``image_ref`` via the OCI Distribution Specification. Requires
    network access to the registry.
    """
    parsed = OCIImageRef.parse(image_ref)
    url = (
        f"https://{parsed.registry}/v2/{parsed.image_path}/manifests/"
        f"{parsed.algorithm}:{parsed.digest}"
    )
    request = urllib.request.Request(url, method="HEAD")
    default_accept = (
        "application/vnd.oci.image.manifest.v1+json,"
        "application/vnd.docker.distribution.manifest.v2+json"
    )
    request.add_header("Accept", accept_header or default_accept)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 — auditor controls URL
            if 200 <= response.status < 300:
                return FetchResult(ok=True, detail=f"OCI digest resolved at {url}")
            return FetchResult(ok=False, detail=f"OCI registry returned {response.status}")
    except Exception as exc:
        return FetchResult(ok=False, detail=f"OCI fetch failed: {exc}")


__all__ = [
    "FetchResult",
    "check_git_commit_exists",
    "check_oci_digest_exists",
    "verify_content_hash",
]
