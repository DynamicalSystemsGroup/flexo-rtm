<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# flexo-rtm

A verifiable self-certification oracle for **bidirectional requirements traceability** of SysMLv2 models, anchored in open source and self-hostable on Flexo MMS, with lossless I/O to OSLC-based RM tools.

`flexo-rtm` proves that a model satisfies forward + backward traceability — or pinpoints the gaps — and emits a layered, replayable certification artifact (transcript → attestation graph → audit report).

## Status

**v0.1.0-rc1** — all 11 slices of the v0.1 roadmap landed; every named acceptance criterion in [Design Spec §6](https://github.com/dynamicalsystemsgroup/flexo-rtm-research/wiki/Design-Spec) (F1–F7, O1–O7, I1–I8, U1–U6, S1–S5, X1–X8) is covered by either a green conformance test or a `@pytest.mark.{live,network}` test that auto-skips without credentials. **217 tests pass** (225 with `FLEXO_RTM_NETWORK_TESTS=1` exercising the network + live paths; one xfail-marked test pinned to research-repo issue [#27](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/issues/27) for W3C VC-DI conformance). **ruff + mypy --strict clean; assembled `rtm.ttl` = 485 triples (budget 2000).**

**Post-v0.1 development** (continuing toward v0.2) adds three layers on top of the certified-clean v0.1 core:

- **Constructor service** — an engineer-facing CLI under `flexo-rtm constructor` for authoring RDF interactively as engineering work happens, with atomic local commits and explicit push to a remote Flexo branch.
- **Role-scoped Claude skills** — four catechisms (`.claude/skills/flexo-rtm-{engineer,reviewer,auditor,reconcile}.md`) wrap the CLI under a two-gate verbatim-reflection contract, inheriting the MVC pattern from [`flexo-rtm-research`](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/wiki/MVC-Pattern-from-RIME-TRL-ANT).
- **User-acceptance walkthroughs** — versioned scripts at [`tests/acceptance/`](tests/acceptance/) for each skill role, designed to be driven live by a human + LLM through the ADCS reference arc. The first run produced [User Testing Experiment #1](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/wiki/User-Testing-Experiment-1) and surfaced six v0.2 vocabulary gaps (research-repo [#29–#34](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/issues?q=is%3Aissue+is%3Aopen+number%3A29..34)).

The design is fully specified in the companion research repo: [`flexo-rtm-research`](https://github.com/dynamicalsystemsgroup/flexo-rtm-research). The canonical [Design Spec](https://github.com/dynamicalsystemsgroup/flexo-rtm-research/wiki/Design-Spec) §6 enumerates the 45 binary acceptance criteria this codebase targets; the open issues at [Open Issues — Research](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/wiki/Open-Issues---Research) + [Open Issues — Implementation](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/wiki/Open-Issues---Implementation) are the live status board for v0.2.

## Usage

```bash
# Rebuild the assembled ontology and report triple count
uv run flexo-rtm parsimony

# Run an audit against an RDF input file
uv run flexo-rtm certify \
    --input examples/adcs-corpus/rtm.ttl \
    --scope https://rtm.example/scope/adcs \
    --out audit-report.json

# Activate SHACL profiles (composable, all off by default)
uv run flexo-rtm certify -i my-model.ttl -s https://my.example/scope/X \
    --profile signed-commits \
    --profile data-integrity-attestations \
    --profile composition-adequacy

# JSON-only output (no file)
uv run flexo-rtm certify -i my-model.ttl -s https://my.example/scope/X
```

`flexo-rtm certify` emits an :class:`oracle.models.AuditReport` JSON document: per-dimension coverage stats, scope IRI, transcript IRI, reproducibility manifest IRI, and a `certified` boolean derived from the coverage thresholds. The exit code is 1 when `certified` is false, 0 otherwise — suitable for CI integration.

### Constructor (engineer-facing authoring)

```bash
# Interactive RDF authoring against a local session
uv run flexo-rtm constructor new-requirement \
    https://rtm.example/req/REQ-001 --title "Pointing accuracy"

uv run flexo-rtm constructor new-artifact \
    https://rtm.example/art/proof-1 --title "Lyapunov proof" \
    --content-hash sha256:abc... --git-commit deadbeef...

uv run flexo-rtm constructor link \
    --artifact https://rtm.example/art/proof-1 \
    --requirement https://rtm.example/req/REQ-001

# Interactive judgement-bearing signoff (adequacy / sufficiency / satisfaction)
uv run flexo-rtm constructor attest \
    --applies-to https://rtm.example/req/REQ-001 \
    --class SatisfactionAttestation

# Review pending session state + push atomically to a remote Flexo branch
uv run flexo-rtm constructor status
uv run flexo-rtm constructor push \
    --url $FLEXO_URL --org my-org --repo my-repo --branch engineering/me \
    --scope https://rtm.example/scope/adcs
```

The constructor commands enforce a **two-gate verbatim-reflection contract** when invoked through the role-scoped skills at [`.claude/skills/`](.claude/skills/): the user reviews proposed writes BEFORE they run and confirms what landed AFTER. See [`tests/acceptance/01-engineer-walkthrough.md`](tests/acceptance/01-engineer-walkthrough.md) for the canonical scripted walkthrough.

## Asymmetric audit semantics (vs OSLC)

flexo-rtm's audit bar is strictly higher than OSLC's: we distinguish evidence (`rtm:addresses`) from judgment (`rtm:SatisfactionAttestation`). A graph that passes OSLC's traceability bar may fail a flexo-rtm audit because we flag missing explicit human attestations. **Roundtrips through OSLC are not identity** — exporting a flexo-rtm cert artifact to OSLC drops attestation structure (or carries it as opaque Layer C extensions that other OSLC clients can't interpret). flexo-rtm strictly *extends* OSLC; OSLC is a strict semantic subset. See [CLAUDE.md §Asymmetric audit semantics](CLAUDE.md) and [research-repo issue #15](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/issues/15).

## Install

```bash
uv sync                    # dev setup
uv pip install flexo-rtm   # once published (pre-v0.1: not yet)
```

Default install is PyPI-only, no proprietary deps. Signing-verification extras (`pip install flexo-rtm[signing]`) lazy-load only when a signed-envelope profile activates.

## Layout

```
flexo-rtm/
├── ontology/
│   ├── core/, alignment/, profiles/, shapes/, lifecycle/, parsimony/
│   └── rtm.ttl                       # deterministic build output (git-tracked)
├── oracle/src/oracle/
│   ├── models/                       # Pydantic surface (Design Spec §7.4)
│   ├── canonicalize/                 # RDFC-1.0 + suite-derived hashing
│   ├── constructor/                  # engineer-facing authoring CLI (post-v0.1)
│   ├── storage/, analysis/, identity/, signing/, composition/, adapters/, uri/
│   └── cli.py                        # Typer entry (certify, parsimony, constructor sub-app)
├── .claude/skills/                   # 4 role-scoped catechisms (engineer/reviewer/auditor/reconcile)
├── examples/{adcs-corpus,oslc-fixtures}/
└── tests/
    ├── {unit,conformance,determinism,integration,regression,property}/   # automated (217 tests)
    └── acceptance/                   # human-driven UAT walkthroughs (1 per skill role)
```

## Development

```bash
make test         # uv run pytest -q
make parsimony    # build ontology/rtm.ttl + report triple count (≤2000)
make lint         # ruff check + ruff format --check + mypy --strict (matches CI)
make all          # parsimony + lint + test
```

Pre-commit hooks (`.pre-commit-config.yaml`) chain the same ruff + ruff-format + mypy gates; install once with `uv run pre-commit install`.

## Working with SysMLv2 sources (openCAESAR is an external dependency)

`flexo-rtm` is RDF-native. Its SysMLv2 adapter reads and writes **`omg-sysml:` RDF only** — the canonical [openCAESAR OWL rendering](https://github.com/dynamicalsystemsgroup/flexo-rtm-research/wiki/OMG-SysMLv2) of OMG SysMLv2 1.0. Converting between `omg-sysml:` RDF and SysMLv2's native formats (`.kerml`, `.sysml`, `.sysml.json`) is **not** in flexo-rtm's scope; that's openCAESAR's `owl-adapter` (MOF2OML + OWL) toolchain's job in both directions.

| Adopter source-of-truth | What you need | What flexo-rtm does |
|---|---|---|
| `omg-sysml:` RDF already (`.ttl`, `.nt`, `.jsonld`) | nothing extra | reads/writes the RDF directly |
| SysMLv2 native (`.kerml` / `.sysml` / `.sysml.json`) | openCAESAR's `owl-adapter` toolchain | reads converted RDF; emits per-file RDF for re-conversion |

Bidirectional adopter workflow:

```
Ingest:        SysMLv2 source → openCAESAR owl-adapter → omg-sysml: RDF → flexo-rtm
Write-back:    flexo-rtm → omg-sysml: RDF → openCAESAR owl-adapter → SysMLv2 source
```

flexo-rtm pins to **OMG SysMLv2 1.0** (formal/2024-08-01) and **openCAESAR rendering v1.x** per [SysMLv2 Ingestion Contract](https://github.com/dynamicalsystemsgroup/flexo-rtm-research/wiki/SysMLv2-Ingestion-Contract) §2. The openCAESAR toolchain is **not** installed by `pip install flexo-rtm` or `uv sync` — it's a separate JVM-based dependency adopters install only if their source-of-truth is SysMLv2 native rather than pre-converted RDF. The research wiki's [OMG SysMLv2 page](https://github.com/dynamicalsystemsgroup/flexo-rtm-research/wiki/OMG-SysMLv2) has the rendering details and version-skew policy; the canonical project location is openCAESAR (see research-repo [issue #19](https://github.com/DynamicalSystemsGroup/flexo-rtm-research/issues/19) tracking the addition of a concrete URL to the contract).

## License

Three-license split — see [LICENSE.md](LICENSE.md). Code: Apache-2.0. Docs: CC-BY-4.0. Ontology: CC0-1.0.
