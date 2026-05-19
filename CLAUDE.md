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
| 7 | SysMLv2 read + per-file RDF write-back | §3 + SysMLv2-anchored profile + roundtrip |
| 8 | Flexo storage adapter (InMemory + HTTPS backends) | F1–F7 |
| 9 | Signed envelopes (5 profiles + VC-DI sign/verify) + git approver binding | S1–S5 + I7 |
| 10 | Composition + federated audit ladder (3 attestation subclasses, 3 profiles, L1-L4 levels, sub-chain replay) | §4.8 + X7 + X8 |
| 11 | CLI (`certify`, `parsimony`) + Hypothesis property tests + GitHub Actions CI + docs polish | smoke + property suite |

**v0.1.0-rc1 reached.** All 11 slices landed; every named acceptance criterion in Design Spec §6 (F1–F7, O1–O7, I1–I8, U1–U6, S1–S5, X1–X8) is covered.

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

## Outstanding work

Two trackers. **Implementation/test work** lives in this repo. **Spec amendments** live in the research repo. Don't conflate — code defects don't need spec edits, and spec edits don't need code work.

### Implementation backlog (`flexo-rtm`)

- [#3](https://github.com/DynamicalSystemsGroup/flexo-rtm/issues/3) — Implement chosen W3C VC-DI 2.0 conformance path. Blocked on research-repo [#27](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/issues/27) A/B/C decision. Test [`test_live_vc_di.py`](tests/integration/sign/test_live_vc_di.py) marked `@pytest.mark.xfail(strict=True)`.
- [#4](https://github.com/DynamicalSystemsGroup/flexo-rtm/issues/4) — Add OSLC-RM/QM live interop test. Blocked on research-repo [#23](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/issues/23) test-point decision.
- [#5](https://github.com/DynamicalSystemsGroup/flexo-rtm/issues/5) — Add openCAESAR end-to-end live test. Blocked on research-repo [#24](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/issues/24).
- [#6](https://github.com/DynamicalSystemsGroup/flexo-rtm/issues/6) — Add OIDC + GHA OIDC live tests. Blocked on research-repo [#25](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/issues/25).
- [#7](https://github.com/DynamicalSystemsGroup/flexo-rtm/issues/7) — Add Cosign + DSSE live tests + implement Rekor verifier. Blocked on research-repo [#26](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/issues/26).

### Open research-repo decisions

Slice-time spec amendments (#11–#22) reconciled in the wiki at research-repo commit [308d563](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/wiki) and closed. What remains are five open design decisions, each blocking an impl-side ticket:

- **Live-test-point picks** — choose sanctioned points for OSLC-RM/QM ([#23](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/issues/23)), openCAESAR SysMLv2 ingestion end-to-end ([#24](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/issues/24)), OIDC + GHA OIDC identity adapters ([#25](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/issues/25)), and Cosign + DSSE + Rekor signing profiles ([#26](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/issues/26)). Impl-side blocked tickets: #4–#7.
- **VC-DI W3C conformance (Option A/B/C)** — [#27](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/issues/27): conform verbatim, ship a private cryptosuite, or both. Impl-side blocked ticket: #3.

## Style

- Python ≥ 3.11; type hints everywhere in `oracle/`; `mypy --strict`.
- `ruff` for lint+format.
- SPDX headers per [CONTRIBUTING.md](CONTRIBUTING.md).
- Default to writing no comments. Only add one when the *why* is non-obvious — a hidden invariant, a spec citation, a workaround for a specific bug.
- Reference Design-Spec sections by their §-anchor in commit messages and PRs; e.g., `feat(canonicalize): RDFC-1.0 + sha256 wrapper (Design Spec §4.7, X1)`.
