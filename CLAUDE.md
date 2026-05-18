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

Slice 2 — scope materialisation + transcript + audit report shape (X1, X3, X4 + partial F4). Slice 1 landed at commit 9268811. The next slice is selected from the roadmap in the plan file; each slice gets its own `/writing-plans` cycle before coding.

## Research-repo divergences

Track inconsistencies between this repo and the canonical research repo. Each entry names what diverged, the chosen resolution, and the research-repo file that should be reconciled in its next normal-course revision.

- **`TranscriptStep.step_kind` enum.** [`Design Spec`](/Users/z/Documents/GitHub/flexo-rtm-research/wiki/Design Spec.md) §7.4 lists `"sparql", "shacl", "canonicalize", "fetch", "verify-signature"`; [`Transcript Replay Semantics`](/Users/z/Documents/GitHub/flexo-rtm-research/wiki/Transcript Replay Semantics.md) §2 + §4a lists `"sparql", "shacl", "canonicalize", "kc-operation", "delegated-numerical"` (the latter wired to [`ADR-027`](/Users/z/Documents/GitHub/flexo-rtm-research/wiki/ADR-027 Bit-Exactness vs Numerical Tolerances Are Both First-Class.md)). Resolution chosen 2026-05-18: companion wins; [`oracle/models`](oracle/src/oracle/models/__init__.py) uses the companion's five. Research repo to reconcile: update Design Spec §7.4 to match the companion in its next revision.
- **`TranscriptStep.was_informed_by` field.** Design Spec §7.4 omits the prov-chain pointer; companion §2 makes `prov:wasInformedBy` mandatory and §3 builds the replay algorithm on it. Resolution chosen 2026-05-18 (same precedent: companion wins): [`oracle/models`](oracle/src/oracle/models/__init__.py) adds `was_informed_by: AnyUrl | None` and a new `Transcript` chain wrapper. Research repo to reconcile: add the field + a `Transcript` chain model to Design Spec §7.4.
- **`rtm:satisfies` → `rtm:addresses` (epistemic correction).** [`Design Spec`](/Users/z/Documents/GitHub/flexo-rtm-research/wiki/Design Spec.md) §4.1 names the artifact→requirement edge `rtm:satisfies`, but no individual artifact can satisfy a requirement — satisfaction is a synthesizing human judgment over multiple pieces of evidence (Hawkins-Habli ACP split; consistent with the ADCS prototype's `rtm:addresses`). Resolution chosen 2026-05-18: rename the core predicate to `rtm:addresses`; satisfaction is recorded strictly via `rtm:SatisfactionAttestation` (whose subject is an `rtm:addresses` triple). Coverage stats become "addresses coverage"; satisfaction is a separate profile-gated metric. Research repo to reconcile: amend Design Spec §4.1 vocabulary and the §4.2 attestation-subject wording in its next revision.

## Style

- Python ≥ 3.11; type hints everywhere in `oracle/`; `mypy --strict`.
- `ruff` for lint+format.
- SPDX headers per [CONTRIBUTING.md](CONTRIBUTING.md).
- Default to writing no comments. Only add one when the *why* is non-obvious — a hidden invariant, a spec citation, a workaround for a specific bug.
- Reference Design-Spec sections by their §-anchor in commit messages and PRs; e.g., `feat(canonicalize): RDFC-1.0 + sha256 wrapper (Design Spec §4.7, X1)`.
