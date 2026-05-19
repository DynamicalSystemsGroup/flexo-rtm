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

### Spec amendments (`flexo-rtm-research`)

Entries below name what diverged at slice time, the chosen resolution (already in code), and the research-repo wiki section that should be reconciled. None of these are pending code work in this repo.

- **`TranscriptStep.step_kind` enum** ([#12](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/issues/12)). [`Design Spec`](/Users/z/Documents/GitHub/flexo-rtm-research/wiki/Design Spec.md) §7.4 lists `"sparql", "shacl", "canonicalize", "fetch", "verify-signature"`; [`Transcript Replay Semantics`](/Users/z/Documents/GitHub/flexo-rtm-research/wiki/Transcript Replay Semantics.md) §2 + §4a lists `"sparql", "shacl", "canonicalize", "kc-operation", "delegated-numerical"` (the latter wired to [`ADR-027`](/Users/z/Documents/GitHub/flexo-rtm-research/wiki/ADR-027 Bit-Exactness vs Numerical Tolerances Are Both First-Class.md)). Resolution chosen 2026-05-18: companion wins; [`oracle/models`](oracle/src/oracle/models/__init__.py) uses the companion's five.
- **`TranscriptStep.was_informed_by` field** ([#13](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/issues/13)). Design Spec §7.4 omits the prov-chain pointer; companion §2 makes `prov:wasInformedBy` mandatory and §3 builds the replay algorithm on it. Resolution chosen 2026-05-18 (same precedent: companion wins): [`oracle/models`](oracle/src/oracle/models/__init__.py) adds `was_informed_by: AnyUrl | None` and a new `Transcript` chain wrapper.
- **`rtm:satisfies` → `rtm:addresses` (epistemic correction)** ([#11](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/issues/11)). [`Design Spec`](/Users/z/Documents/GitHub/flexo-rtm-research/wiki/Design Spec.md) §4.1 names the artifact→requirement edge `rtm:satisfies`, but no individual artifact can satisfy a requirement — satisfaction is a synthesizing human judgment over multiple pieces of evidence (Hawkins-Habli ACP split; consistent with the ADCS prototype's `rtm:addresses`). Resolution chosen 2026-05-18: rename the core predicate to `rtm:addresses`; satisfaction is recorded strictly via `rtm:SatisfactionAttestation` (whose subject is an `rtm:addresses` triple).
- **OSLC `satisfies` / `validatesRequirement` mapping (slice-3 precedent applied)** ([#14](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/issues/14)). [`OSLC Roundtrip Acceptance`](/Users/z/Documents/GitHub/flexo-rtm-research/wiki/OSLC Roundtrip Acceptance.md) §4.2 and §5.2 still map `oslc_rm:satisfies` and `oslc_qm:validatesRequirement` to `rtm:satisfies`. After the slice-3 rename, both map to `rtm:addresses` instead (recorded in [`oracle/adapters/oslc/{rm,qm}.py`](oracle/src/oracle/adapters/oslc/) and the corresponding extracts).
- **SysMLv2 `omg-sysml:satisfies` / `omg-sysml:verifies` mapping (slice-3 precedent applied)** ([#16](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/issues/16)). [`SysMLv2 Ingestion Contract`](/Users/z/Documents/GitHub/flexo-rtm-research/wiki/SysMLv2 Ingestion Contract.md) §5.1 maps `omg-sysml:satisfies` to `rtm:satisfies` and `omg-sysml:verifies` to `rtm:verifies`. Both are evidence-linkage edges and should map to `rtm:addresses`; the SysMLv2 design-time vs verification-time distinction is preserved in the source graph. Recorded in [`oracle/adapters/sysmlv2/mapping.py`](oracle/src/oracle/adapters/sysmlv2/mapping.py).
- **SysMLv2 contract uses `rtm:subject` instead of `rtm:appliesTo`** ([#17](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/issues/17)). §8.2 references `rtm:subject` for the attestation-subject pointer; slice 4 standardized on `rtm:appliesTo` per the policy SPARQL in Identity Adapter Contract §5. The ontology declares only `rtm:appliesTo`.
- **SysMLv2 write-back pulled into v0.1** ([#18](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/issues/18)). [`SysMLv2 Ingestion Contract`](/Users/z/Documents/GitHub/flexo-rtm-research/wiki/SysMLv2 Ingestion Contract.md) §9 defers write-back to v0.2. After implementing slice 7's read path, we pulled per-file RDF write-back into v0.1 because the same-format roundtrip test (`parse → emit → parse → canonical-equality`) is the read step's correctness proof — without it, `parse()` could silently lose triples and the audit would still "pass" on the diminished graph. Per-format JSON emission stays out of scope (openCAESAR's job, symmetric to ingest).
- **Flexo Layer-1 has no transaction endpoints** ([#20](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/issues/20)). [`Flexo REST Binding`](/Users/z/Documents/GitHub/flexo-rtm-research/wiki/Flexo REST Binding.md) §3.2 lists `POST /transactions`, `POST /transactions/{tx-id}/commit`, etc. Live-testing against `try-layer1.starforge.app` confirms these endpoints don't exist. The real atomic-batch semantics use PUT-then-SPARQL-INSERT-DATA: idempotent PUTs to `/orgs/{org}` + `/repos/{repo}` + `/branches/{branch}` create resources; one `POST .../branches/{branch}/update` with combined `INSERT DATA` body IS the atomic commit. Reconciled in [`oracle/storage/flexo_client.py`](oracle/src/oracle/storage/flexo_client.py).
- **Flexo's default branch is `master`, not `main`** ([#21](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/issues/21)). Contract §6 lists `main` as the published-baselines branch; Flexo MMS Layer-1 auto-creates `master` on repo PUT. [`is_valid_branch_name`](oracle/src/oracle/storage/iri_scheme.py) now accepts both.
- **Flexo Layer-1 branches ARE named graphs** ([#22](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/issues/22)). Contract §4.1 envisions multiple partition graphs per branch (`urn:rtm:model`, `urn:rtm:attestations`, etc.). Real Flexo raises `QuadsNotAllowedException` on `GRAPH <iri> { ... }` inside `INSERT DATA` — one branch holds one named graph (the ADCS prototype maps each partition to its own branch). `FlexoHttpClient` now emits bare triples; adopters who need partition graphs map them to per-partition branches.

**Live-test-point decisions:** Sanctioned live test points are pending for OSLC-RM/QM ([#23](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/issues/23)), openCAESAR SysMLv2 ingestion end-to-end ([#24](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/issues/24)), OIDC + GHA OIDC identity adapters ([#25](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/issues/25)), and Cosign + DSSE + Rekor signing profiles ([#26](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/issues/26)). The corresponding `Flexo REST Binding` / `OSLC Roundtrip Acceptance` / `SysMLv2 Ingestion Contract` / `Identity Adapter Contract` / `Signed Envelope Shapes` wiki pages need to designate the chosen point; impl-side tickets above are blocked on these.

**VC-DI W3C conformance (Option A/B/C):** [#27](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/issues/27) — pick whether v0.1 conforms to W3C VC-DI 2.0 verbatim, ships a private `flexo-rtm-eddsa-rdfc-2022` cryptosuite, or both. `Signed Envelope Shapes` §5 needs an update either way. Impl-side tracked at flexo-rtm#3.

## Style

- Python ≥ 3.11; type hints everywhere in `oracle/`; `mypy --strict`.
- `ruff` for lint+format.
- SPDX headers per [CONTRIBUTING.md](CONTRIBUTING.md).
- Default to writing no comments. Only add one when the *why* is non-obvious — a hidden invariant, a spec citation, a workaround for a specific bug.
- Reference Design-Spec sections by their §-anchor in commit messages and PRs; e.g., `feat(canonicalize): RDFC-1.0 + sha256 wrapper (Design Spec §4.7, X1)`.
