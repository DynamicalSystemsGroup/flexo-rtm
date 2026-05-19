<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# CLAUDE.md — `flexo-rtm`

## What this repo is

The **implementation** of `flexo-rtm` — a verifiable self-certification oracle for bidirectional requirements traceability of SysMLv2 models. The companion [`flexo-rtm-research`](/Users/z/Documents/GitHub/flexo-rtm-research) holds principles, design spec, ADRs, normative contracts, and the research issue tracker. **Design lives there; code lives here.**

## Double-loop architecture

`flexo-rtm` development pairs two loops, one per repo, plus a coupling loop between them. This repo runs the **development loop**; the research repo runs the **research loop**; the coupling loop is what keeps them honest.

```
   RESEARCH LOOP                          DEVELOPMENT LOOP (this repo)
   (flexo-rtm-research)
   ─────────────────                      ─────────────────────────────
   principles ─→ design spec ─→ ADRs ─→   spec ─→ code ─→ CI ─→ behavior
                                                                  │
                                                       (verification)
                                                                  │
   ←─── coupling loop ────────────────────────────────────────────┘
   (observed behavior challenges assumptions; research issues filed; spec amends)
```

| Loop | Question | Repo | Activity |
|---|---|---|---|
| Research | "Are we building the right thing?" (**validation**) | `flexo-rtm-research` | Principles; design; ADRs; ontology choices |
| Development (this one) | "Are we building it right?" (**verification**) | `flexo-rtm` | CLI; SHACL; tests; CI gates; observable behavior |
| Coupling | "What did we learn that changes the question?" | both | Filing research-repo issues when implementation surfaces spec gaps |

### Direction of information flow

- **Research → here.** Spec changes and ADR decisions land in the research wiki. Work this repo needs to do is tracked as **impl-repo issues** (often cross-linked from a research-repo issue with `blocked-by`).
- **Here → Research.** Behavior observed during integration tests, UAT walkthroughs, live-test sweeps, or just from coding that **doesn't match the spec's assumptions** must be escalated by **filing a research-repo issue**. Never silently work around a spec gap. Precedent: the slice-time divergences (filed during the v0.1 build as research-repo #11–#22) and the UAT-time divergences (research-repo #29–#34 from Experiment #1) are how this loop has fired so far.

The discipline is the same the engineer skill enforces in its catechism: never paraphrase, never silently resolve, always file when in doubt.

## Issue dashboards (the loop's status board)

Both repos' open issues are mirrored to wiki pages in the research repo:

- [**Open Issues — Research**](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/wiki/Open-Issues---Research) — what's pending in the spec/design side.
- [**Open Issues — Implementation**](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/wiki/Open-Issues---Implementation) — what's pending in this repo.

These auto-regenerate on every issue event in either repo (see `flexo-rtm-research/.github/workflows/sync-issues.yml`). When in doubt about whether work belongs here or in the research repo, check both dashboards first.

## Load-bearing documents

| Where | What |
|---|---|
| [Design Spec](/Users/z/Documents/GitHub/flexo-rtm-research/wiki/Design Spec.md) | §6 = the 45 normative acceptance criteria; §7 = oracle structure; §7.4 = Pydantic surface; §8.3 = test categories |
| [Parsimony Manifest](/Users/z/Documents/GitHub/flexo-rtm-research/wiki/Parsimony Manifest.md) | The 9 vocabularies extracted into `rtm.ttl`; budget ≤ 2000 triples |
| [ADCS Prototype Lessons](/Users/z/Documents/GitHub/flexo-rtm-research/wiki/ADCS Prototype Lessons.md) | What lifts from the prototype vs stays |
| [Identity Adapter Contract](/Users/z/Documents/GitHub/flexo-rtm-research/wiki/Identity Adapter Contract.md), [External URI Rules](/Users/z/Documents/GitHub/flexo-rtm-research/wiki/External URI Rules.md), [Signed Envelope Shapes](/Users/z/Documents/GitHub/flexo-rtm-research/wiki/Signed Envelope Shapes.md), [OSLC Roundtrip Acceptance](/Users/z/Documents/GitHub/flexo-rtm-research/wiki/OSLC Roundtrip Acceptance.md), [SysMLv2 Ingestion Contract](/Users/z/Documents/GitHub/flexo-rtm-research/wiki/SysMLv2 Ingestion Contract.md), [Flexo REST Binding](/Users/z/Documents/GitHub/flexo-rtm-research/wiki/Flexo REST Binding.md) | Slice-specific normative contracts; read before coding the corresponding slice |
| [`/Users/z/.claude/plans/harmonic-puzzling-patterson.md`](/Users/z/.claude/plans/harmonic-puzzling-patterson.md) | The v0.1 build roadmap; 11 slices; this is the working plan |
| ADCS prototype: [/Users/z/Documents/GitHub/ADCS-lifecycle-demo](/Users/z/Documents/GitHub/ADCS-lifecycle-demo) | Regression corpus source (slice 3); ontology framework half lifts here |

## Skill routing

Role-scoped Claude skills wrap the CLI; each translates natural-language requests into correctly-constructed CLI invocations under a **two-gate verbatim-reflection contract** (the user reviews the proposed write before it runs, and reviews what landed after). The skills live under [`.claude/skills/`](.claude/skills/):

| Skill | When to use | Path scope | CLI surface |
|---|---|---|---|
| [`flexo-rtm-engineer`](.claude/skills/flexo-rtm-engineer.md) | Engineer doing primary engineering work — making decisions, recording requirements / artifacts / addresses-edges / attestations. Triggers: "log this", "attest", "new requirement / artifact", "link", "deprecate", "start/stop tandem logging". | `~/.flexo-rtm/sessions/**` | `constructor` (new-requirement, new-artifact, link, attest, deprecate, status, show) — NEVER `push`. |
| [`flexo-rtm-reviewer`](.claude/skills/flexo-rtm-reviewer.md) | Engineer (or designated reviewer) gating the local-session → remote-Flexo boundary. Triggers: "review my session", "ready to push", "what am I about to push", "pre-push check". | `~/.flexo-rtm/sessions/**/archive/**` | `constructor status / show / push`; `certify`. Amendments route to `flexo-rtm-engineer`; drift routes to `flexo-rtm-reconcile`. |
| [`flexo-rtm-auditor`](.claude/skills/flexo-rtm-auditor.md) | Auditor evaluating a scope's coverage, attestation health, deprecation status. Read-only by construction. Triggers: "audit this scope", "coverage of", "certification status", "run the audit report". | `[]` (no writes) | `certify`, `parsimony`, `constructor status / show`. Resolutions route to `flexo-rtm-engineer`; drift to `flexo-rtm-reconcile`. |
| [`flexo-rtm-reconcile`](.claude/skills/flexo-rtm-reconcile.md) | Role-agnostic conflict identification + resolution between local and other sources (remote branch, OSLC-RM, another engineer's session, an audit finding). Surfaces the four exhaustive options (AcceptA / AcceptB / AcceptBoth / Deferred); **never picks**. Triggers: "reconcile", "drift", "conflict between", "merge my session with main". | `~/.flexo-rtm/reconciliation/**` (append-only) | Read-side: `constructor show / status`, `certify`. Writes: only `.trig` records under allowed-paths. Follow-up CLI writes route to `flexo-rtm-engineer`. |

**Inherited from** [`MVC Pattern from RIME TRL ANT`](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/wiki/MVC-Pattern-from-RIME-TRL-ANT). Specifically: the skill never edits RDF directly (the CLI is the sole mutator); the skill walks role-scoped catechisms; the skill orchestrates the commit / push (the CLI doesn't). flexo-rtm tightens the reference pattern's single review-gate to **two gates** because writes touch audit-critical attestation triples — the LLM + CLI are not assumed to faithfully capture the user's intent.

## Permission model

Two tiers, matching the local-vs-remote split in the CLI:

- **Autonomous (locally reversible).** The engineer skill's writes land in `~/.flexo-rtm/sessions/<id>/state.trig` — the local working set. SHACL gates run against an in-memory rdflib graph. Both gates of the verbatim-reflection contract still apply, but the action is reversible (deprecate or amend) and confined to the engineer's machine.
- **Require explicit user authorization (non-local, observable to others).** `flexo-rtm constructor push` is the only action in this tier — it makes the engineer's session state visible to the shared Flexo branch. Always gated by the reviewer skill's two-gate confirmation: GATE 1 confirms what's about to push; GATE 2 reads back what landed on the remote.

The reconcile skill's writes (under `~/.flexo-rtm/reconciliation/**`) are append-only: a mistaken decision is corrected by a new record, never by overwriting. The auditor writes nothing at all.

## Engineering rules (from [CONTRIBUTING.md](CONTRIBUTING.md))

**Sparseness:** minimum code per failing test; no abstractions for hypothetical future use; no reimplementing `rdflib` / `pyshacl` / `pydantic` / `cryptography` / `sigstore` / `in-toto-attestation`.

**Escalation:** when the Design Spec and dev-time reality diverge — design principles in direct tension, sophisticated machinery would be required, an ADR's premise is falsified, or a spec'd SHACL / SPARQL fails on the regression corpus — **stop and escalate**, do not silently work around it. Concretely: **file a research-repo issue** describing the gap (see [Open Issues — Research](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/wiki/Open-Issues---Research) for precedents — #11–#22 from the v0.1 build, #29–#34 from UAT Experiment #1). The coupling loop closes when the research-repo decision lands and a follow-up impl-repo issue captures the spec-aligned implementation work.

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
