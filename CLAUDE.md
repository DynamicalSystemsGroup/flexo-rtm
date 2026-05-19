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

## Slices landed

| # | What | Acceptance |
|---|---|---|
| 1 | Engineering substrate, Pydantic models, canonicalize, ontology core skeleton, approver shape, parsimony build | I1, X5, X6, partial X1 |
| 2 | Scope materialisation, coverage stats, transcript record + replay | X1, X3, X4, partial F4 |
| 3 | ADCS regression corpus (translated fixture) | §4.1 + partial X7 |
| 4 | Identity adapters + policy SHACL | I1–I6, I8 |
| 5 | External URI refs + reproducibility manifest | U1, U2, U5; U3+U4 network-marked; partial U6 |
| 6 | OSLC-RM/QM source-preserving adapter | O1–O7 |
| 7 | SysMLv2 read ingestion | §3 + SysMLv2-anchored profile |

Next: slice 8 (Flexo storage adapter, F1–F7).

## Asymmetric audit semantics (OSLC ↔ flexo-rtm)

flexo-rtm's audit bar is strictly *higher* than OSLC's, because we distinguish **evidence** (`rtm:addresses`) from **judgment** (`rtm:SatisfactionAttestation`). A graph that passes OSLC's traceability bar may fail a flexo-rtm audit — we flag the missing explicit human attestations.

Consequence: roundtrips through OSLC are NOT identity for non-trivial graphs.

| Direction | Faithful? | Notes |
|---|---|---|
| OSLC → flexo-rtm | Layer A faithful by construction (source-preserving). | The result has no attestations; any `attested-*` profile would fail. |
| flexo-rtm → OSLC | Lossy. | Attestation triples drop (default) or carry as Layer C extensions other OSLC clients can't interpret. |
| flexo-rtm → OSLC → flexo-rtm | NOT identity. | The intermediate OSLC form loses attestation structure; re-ingesting yields the bare addresses-graph. |

The OSLC adapter source-preserves verbatim — the *triple-set* roundtrip is lossless for whatever the input contained. The asymmetry is at the **semantic-bar** level, not the syntactic-fidelity level. flexo-rtm strictly *extends* OSLC; OSLC is a strict semantic subset.

Tracked upstream as [research-repo issue #15](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/issues/15).

## Research-repo divergences

Track inconsistencies between this repo and the canonical research repo. Each entry names what diverged, the chosen resolution, and the research-repo file that should be reconciled. Filed upstream — see linked issues.

- **`TranscriptStep.step_kind` enum** ([#12](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/issues/12)). [`Design Spec`](/Users/z/Documents/GitHub/flexo-rtm-research/wiki/Design Spec.md) §7.4 lists `"sparql", "shacl", "canonicalize", "fetch", "verify-signature"`; [`Transcript Replay Semantics`](/Users/z/Documents/GitHub/flexo-rtm-research/wiki/Transcript Replay Semantics.md) §2 + §4a lists `"sparql", "shacl", "canonicalize", "kc-operation", "delegated-numerical"` (the latter wired to [`ADR-027`](/Users/z/Documents/GitHub/flexo-rtm-research/wiki/ADR-027 Bit-Exactness vs Numerical Tolerances Are Both First-Class.md)). Resolution chosen 2026-05-18: companion wins; [`oracle/models`](oracle/src/oracle/models/__init__.py) uses the companion's five.
- **`TranscriptStep.was_informed_by` field** ([#13](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/issues/13)). Design Spec §7.4 omits the prov-chain pointer; companion §2 makes `prov:wasInformedBy` mandatory and §3 builds the replay algorithm on it. Resolution chosen 2026-05-18 (same precedent: companion wins): [`oracle/models`](oracle/src/oracle/models/__init__.py) adds `was_informed_by: AnyUrl | None` and a new `Transcript` chain wrapper.
- **`rtm:satisfies` → `rtm:addresses` (epistemic correction)** ([#11](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/issues/11)). [`Design Spec`](/Users/z/Documents/GitHub/flexo-rtm-research/wiki/Design Spec.md) §4.1 names the artifact→requirement edge `rtm:satisfies`, but no individual artifact can satisfy a requirement — satisfaction is a synthesizing human judgment over multiple pieces of evidence (Hawkins-Habli ACP split; consistent with the ADCS prototype's `rtm:addresses`). Resolution chosen 2026-05-18: rename the core predicate to `rtm:addresses`; satisfaction is recorded strictly via `rtm:SatisfactionAttestation` (whose subject is an `rtm:addresses` triple).
- **OSLC `satisfies` / `validatesRequirement` mapping (slice-3 precedent applied)** ([#14](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/issues/14)). [`OSLC Roundtrip Acceptance`](/Users/z/Documents/GitHub/flexo-rtm-research/wiki/OSLC Roundtrip Acceptance.md) §4.2 and §5.2 still map `oslc_rm:satisfies` and `oslc_qm:validatesRequirement` to `rtm:satisfies`. After the slice-3 rename, both map to `rtm:addresses` instead (recorded in [`oracle/adapters/oslc/{rm,qm}.py`](oracle/src/oracle/adapters/oslc/) and the corresponding extracts).
- **SysMLv2 `omg-sysml:satisfies` / `omg-sysml:verifies` mapping (slice-3 precedent applied)** ([#16](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/issues/16)). [`SysMLv2 Ingestion Contract`](/Users/z/Documents/GitHub/flexo-rtm-research/wiki/SysMLv2 Ingestion Contract.md) §5.1 maps `omg-sysml:satisfies` to `rtm:satisfies` and `omg-sysml:verifies` to `rtm:verifies`. Both are evidence-linkage edges and should map to `rtm:addresses`; the SysMLv2 design-time vs verification-time distinction is preserved in the source graph. Recorded in [`oracle/adapters/sysmlv2/mapping.py`](oracle/src/oracle/adapters/sysmlv2/mapping.py).
- **SysMLv2 contract uses `rtm:subject` instead of `rtm:appliesTo`** ([#17](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/issues/17)). §8.2 references `rtm:subject` for the attestation-subject pointer; slice 4 standardized on `rtm:appliesTo` per the policy SPARQL in Identity Adapter Contract §5. The ontology declares only `rtm:appliesTo`.

## Style

- Python ≥ 3.11; type hints everywhere in `oracle/`; `mypy --strict`.
- `ruff` for lint+format.
- SPDX headers per [CONTRIBUTING.md](CONTRIBUTING.md).
- Default to writing no comments. Only add one when the *why* is non-obvious — a hidden invariant, a spec citation, a workaround for a specific bug.
- Reference Design-Spec sections by their §-anchor in commit messages and PRs; e.g., `feat(canonicalize): RDFC-1.0 + sha256 wrapper (Design Spec §4.7, X1)`.
