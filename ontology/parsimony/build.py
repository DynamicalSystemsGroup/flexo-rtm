# SPDX-License-Identifier: Apache-2.0
"""Deterministic ontology assembler. Reads manifest.yaml, validates the declared
extracts exist, and emits ``ontology/rtm.ttl`` as Core + Alignment + extracts.

Acceptance criterion X6: assembled ``rtm.ttl`` ≤ 2000 triples. The build fails
loudly if the budget is exceeded. Per ADR-014 the manifest is the audit trail
for every imported triple.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from rdflib import Graph

ONTOLOGY_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = ONTOLOGY_DIR.parent
MANIFEST_PATH = ONTOLOGY_DIR / "parsimony" / "manifest.yaml"
CORE_TTL = ONTOLOGY_DIR / "core" / "rtm-core.ttl"
ALIGNMENT_TTL = ONTOLOGY_DIR / "alignment" / "rtm-alignment.ttl"
OUTPUT_TTL = ONTOLOGY_DIR / "rtm.ttl"

SUPPORTED_EXTRACT_METHODS = {"hand-curated", "MIREOT", "SLME", "SPARQL_CONSTRUCT"}


def _resolve_extract_path(target: str) -> Path:
    candidate = Path(target)
    if candidate.is_absolute():
        return candidate
    return (ONTOLOGY_DIR / target).resolve()


def assemble() -> tuple[Graph, dict[str, int]]:
    manifest = yaml.safe_load(MANIFEST_PATH.read_text())
    budget: int = manifest["target_triple_budget"]
    counts: dict[str, int] = {}

    assembled = Graph()
    assembled.parse(CORE_TTL, format="turtle")
    counts["core"] = len(assembled)

    if ALIGNMENT_TTL.exists():
        before = len(assembled)
        assembled.parse(ALIGNMENT_TTL, format="turtle")
        counts["alignment"] = len(assembled) - before
    else:
        counts["alignment"] = 0

    for vocab in manifest["vocabularies"]:
        method = vocab["extract_method"]
        if method not in SUPPORTED_EXTRACT_METHODS:
            raise ValueError(f"vocabulary {vocab['name']!r}: unsupported extract_method {method!r}")
        if method != "hand-curated":
            # Slice 1 only ships hand-curated extracts. SLME / MIREOT / SPARQL_CONSTRUCT
            # land in later slices; skip silently when no terms are declared so the
            # manifest schema can be exercised end-to-end.
            terms = (
                vocab.get("extracted_classes", [])
                + vocab.get("extracted_properties", [])
                + vocab.get("extracted_individuals", [])
            )
            if terms:
                raise NotImplementedError(
                    f"vocabulary {vocab['name']!r}: extract_method {method!r} "
                    "is not implemented yet (slice 1 ships hand-curated only)"
                )
            counts[vocab["name"]] = 0
            continue

        extract_target = vocab.get("target_extract_file")
        if not extract_target:
            raise ValueError(f"vocabulary {vocab['name']!r}: missing target_extract_file")
        extract_path = _resolve_extract_path(extract_target)
        if not extract_path.exists():
            raise FileNotFoundError(
                f"vocabulary {vocab['name']!r}: declared extract {extract_path} is missing"
            )
        before = len(assembled)
        assembled.parse(extract_path, format="turtle")
        counts[vocab["name"]] = len(assembled) - before

    total = len(assembled)
    counts["TOTAL"] = total
    if total > budget:
        raise SystemExit(
            f"rtm.ttl assembled to {total} triples; budget {budget} exceeded "
            "(see Parsimony Manifest §4)"
        )
    return assembled, counts


def write() -> int:
    assembled, counts = assemble()
    assembled.serialize(destination=OUTPUT_TTL, format="turtle")
    width = max(len(k) for k in counts)
    for name, count in counts.items():
        print(f"  {name:<{width}}  {count:>5}")
    print(f"\nWrote {OUTPUT_TTL.relative_to(REPO_ROOT)} ({counts['TOTAL']} triples)")
    return 0


if __name__ == "__main__":
    sys.exit(write())
