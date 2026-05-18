<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# CLAUDE.md — `flexo-rtm`

## What this repo is

The implementation of `flexo-rtm` — a verifiable self-certification oracle for bidirectional requirements traceability of SysMLv2 models. The design is finished and frozen in [`flexo-rtm-research`](/Users/z/Documents/GitHub/flexo-rtm-research). This repo is the code.

## Load-bearing documents

| Where | What |
|---|---|
| [Design Spec](/Users/z/Documents/GitHub/flexo-rtm-research/wiki/Design Spec.md) | §6 = the 45 normative acceptance criteria; §7 = oracle structure; §7.4 = Pydantic surface; §8.3 = test categories |
| [Parsimony Manifest](/Users/z/Documents/GitHub/flexo-rtm-research/wiki/Parsimony Manifest.md) | The 9 vocabularies extracted into `rtm.ttl`; budget ≤ 2000 triples |
| [ADCS Prototype Lessons](/Users/z/Documents/GitHub/flexo-rtm-research/wiki/ADCS Prototype Lessons.md) | What lifts from the prototype vs stays |
| [Identity Adapter Contract](/Users/z/Documents/GitHub/flexo-rtm-research/wiki/Identity Adapter Contract.md), [External URI Rules](/Users/z/Documents/GitHub/flexo-rtm-research/wiki/External URI Rules.md), [Signed Envelope Shapes](/Users/z/Documents/GitHub/flexo-rtm-research/wiki/Signed Envelope Shapes.md), [OSLC Roundtrip Acceptance](/Users/z/Documents/GitHub/flexo-rtm-research/wiki/OSLC Roundtrip Acceptance.md), [SysMLv2 Ingestion Contract](/Users/z/Documents/GitHub/flexo-rtm-research/wiki/SysMLv2 Ingestion Contract.md), [Flexo REST Binding](/Users/z/Documents/GitHub/flexo-rtm-research/wiki/Flexo REST Binding.md) | Slice-specific normative contracts; read before coding the corresponding slice |
| [`/Users/z/.claude/plans/harmonic-puzzling-patterson.md`](/Users/z/.claude/plans/harmonic-puzzling-patterson.md) | The v0.1 build roadmap; 11 slices; this is the working plan |
| ADCS prototype: [/Users/z/Documents/GitHub/ADCS-lifecycle-demo](/Users/z/Documents/GitHub/ADCS-lifecycle-demo) | Regression corpus source (slice 3); ontology framework half lifts here |

## Engineering rules (from [CONTRIBUTING.md](CONTRIBUTING.md))

**Sparseness:** minimum code per failing test; no abstractions for hypothetical future use; no reimplementing `rdflib` / `pyshacl` / `pydantic` / `cryptography` / `sigstore` / `in-toto-attestation`.

**Escalation:** when the Design Spec and dev-time reality diverge — design principles in direct tension, sophisticated machinery would be required, an ADR's premise is falsified, or a spec'd SHACL / SPARQL fails on the regression corpus — **stop and escalate**, do not silently work around it.

**Deterministic:** no clocks, no randomness, no env-dependent ordering in oracle paths.

## Slice in progress

Slice 1 — engineering substrate + ontology core skeleton. Acceptance: X6 (parsimony ≤ 2000 triples), I1 (approver shape), X5 (minimal install), partial X1 (canonicalization byte-identical).

When slice 1 lands, the next slice is selected from the roadmap in the plan file; each slice gets its own `/writing-plans` cycle before coding.

## Style

- Python ≥ 3.11; type hints everywhere in `oracle/`; `mypy --strict`.
- `ruff` for lint+format.
- SPDX headers per [CONTRIBUTING.md](CONTRIBUTING.md).
- Default to writing no comments. Only add one when the *why* is non-obvious — a hidden invariant, a spec citation, a workaround for a specific bug.
- Reference Design-Spec sections by their §-anchor in commit messages and PRs; e.g., `feat(canonicalize): RDFC-1.0 + sha256 wrapper (Design Spec §4.7, X1)`.
