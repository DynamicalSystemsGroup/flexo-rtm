<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# flexo-rtm

A verifiable self-certification oracle for **bidirectional requirements traceability** of SysMLv2 models, anchored in open source and self-hostable on Flexo MMS, with lossless I/O to OSLC-based RM tools.

`flexo-rtm` proves that a model satisfies forward + backward traceability — or pinpoints the gaps — and emits a layered, replayable certification artifact (transcript → attestation graph → audit report).

## Status

**Pre-v0.1.** Engineering substrate, scope+coverage analysis, transcript record/replay, identity adapters + policy SHACL, external URI references + reproducibility manifest, OSLC-RM/QM source-preserving adapter, and the SHACL-enforced named-approver constraint are in place. Subsequent slices add SysMLv2 ingestion, Flexo storage, signed envelopes, and federated audit composition.

The design is fully specified in the companion research repo: [`flexo-rtm-research`](https://github.com/dynamicalsystemsgroup/flexo-rtm-research). The canonical [Design Spec](https://github.com/dynamicalsystemsgroup/flexo-rtm-research/wiki/Design-Spec) §6 defines the 45 binary acceptance criteria this codebase targets.

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
│   ├── operational/, storage/, analysis/, identity/, adapters/
│   └── cli.py                        # Typer entry
├── examples/{adcs-corpus,oslc-fixtures}/
└── tests/{unit,conformance,determinism,integration,regression,property}/
```

## Development

```bash
make test         # uv run pytest -q
make parsimony    # build ontology/rtm.ttl + report triple count (≤2000)
make lint         # ruff + mypy
make all          # parsimony + lint + test
```

## License

Three-license split — see [LICENSE.md](LICENSE.md). Code: Apache-2.0. Docs: CC-BY-4.0. Ontology: CC0-1.0.
