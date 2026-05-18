# SPDX-License-Identifier: Apache-2.0
"""Programmatic parsers for the URI strings — External URI Rules §3.

SHACL handles the structural format gate. These helpers split a value into
its (algorithm, digest) parts so the fetch path can pick the right hasher.
"""

from __future__ import annotations

from dataclasses import dataclass

CONTENT_HASH_ALGORITHMS = {
    "sha256",
    "sha384",
    "sha512",
    "sha3-256",
    "sha3-512",
    "ipfs",
    "cid",
}


@dataclass(frozen=True)
class ContentHash:
    algorithm: str
    digest: str

    @classmethod
    def parse(cls, value: str) -> ContentHash:
        if ":" not in value:
            raise ValueError(f"content hash missing ':' separator: {value!r}")
        algorithm, digest = value.split(":", 1)
        if algorithm not in CONTENT_HASH_ALGORITHMS:
            raise ValueError(
                f"unsupported content-hash algorithm {algorithm!r}; "
                f"allowed: {sorted(CONTENT_HASH_ALGORITHMS)}"
            )
        if not digest:
            raise ValueError(f"content hash has empty digest: {value!r}")
        return cls(algorithm=algorithm, digest=digest)


@dataclass(frozen=True)
class OCIImageRef:
    """An OCI image reference of the form ``registry[:port]/image-path@algo:digest``."""

    registry: str
    image_path: str
    algorithm: str
    digest: str

    @classmethod
    def parse(cls, value: str) -> OCIImageRef:
        if "@" not in value:
            raise ValueError(f"OCI image ref missing @digest: {value!r}")
        location, hash_part = value.split("@", 1)
        if "/" not in location:
            raise ValueError(f"OCI image ref missing image path: {value!r}")
        registry, image_path = location.split("/", 1)
        if ":" not in hash_part:
            raise ValueError(f"OCI image ref hash missing algo: {value!r}")
        algorithm, digest = hash_part.split(":", 1)
        return cls(
            registry=registry,
            image_path=image_path,
            algorithm=algorithm,
            digest=digest,
        )


__all__ = ["CONTENT_HASH_ALGORITHMS", "ContentHash", "OCIImageRef"]
