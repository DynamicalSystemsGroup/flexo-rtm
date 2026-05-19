# SPDX-License-Identifier: Apache-2.0
"""Audit-mode fetchers — External URI Rules §6.2.

Each fetcher is opt-in (the default cert run is offline, per §6.1). When
enabled, the fetcher consults the external authoritative source and returns
a :class:`FetchResult` describing whether the recorded reference resolves
correctly.

Slice 5 implements:
- ``verify_content_hash`` with an injectable byte source (no network required
  for the offline test path).
- ``check_git_commit_exists`` via ``git fetch --depth=1`` into a temporary
  bare repo (protocol v2's commit-fetch capability).
- ``check_oci_digest_exists`` via OCI Distribution Specification HTTPS GET.

The git / OCI helpers always need network; tests covering them are marked
``@pytest.mark.network`` and auto-skipped without the FLEXO_RTM_NETWORK_TESTS
env var set.
"""

from __future__ import annotations

import hashlib
import subprocess
import tempfile
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
    """Probe ``repo`` for ``commit`` via ``git fetch --depth=1 <repo> <commit>``.

    Initializes a temporary bare repo and asks the remote to deliver exactly
    the named commit (and nothing reachable from it beyond depth 1). Git
    protocol v2 (default since git 2.26) supports fetching by commit SHA when
    the server permits ``uploadpack.allowReachableSHA1InWant``; github.com and
    gitlab.com enable it by default. Self-hosted servers without this setting
    will report the commit as not found.

    Returns :class:`FetchResult` with ``ok=True`` when the remote delivers the
    commit, ``ok=False`` otherwise (network failure, server refusal, missing
    git binary, or commit unreachable on the remote).

    Requires network and the ``git`` binary on PATH.
    """
    try:
        with tempfile.TemporaryDirectory(prefix="flexo-rtm-git-probe-") as tmp:
            init = subprocess.run(
                ["git", "init", "--bare", "--quiet"],
                cwd=tmp,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if init.returncode != 0:
                return FetchResult(
                    ok=False,
                    detail=f"git init failed: {init.stderr.strip()[:200]}",
                )
            proc = subprocess.run(
                ["git", "fetch", "--quiet", "--depth=1", repo, commit],
                cwd=tmp,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return FetchResult(ok=False, detail=f"git probe failed: {exc}")
    if proc.returncode != 0:
        stderr = proc.stderr.strip()[:200] or "no error output"
        return FetchResult(
            ok=False, detail=f"commit {commit} not found on {repo}: {stderr}"
        )
    return FetchResult(ok=True, detail=f"commit {commit} reachable on {repo}")


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
