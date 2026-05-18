<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# flexo-rtm

A verifiable self-certification oracle for **bidirectional requirements traceability** of SysMLv2 models, anchored in open source and self-hostable on Flexo MMS, with lossless I/O to OSLC-based RM tools.

`flexo-rtm` proves that a model satisfies forward + backward traceability — or pinpoints the gaps — and emits a layered, replayable certification artifact (transcript → attestation graph → audit report).

## Status

**Pre-v0.1, slice 1.** Engineering substrate, ontology core skeleton, and the SHACL-enforced named-approver constraint are in place. Subsequent slices add analysis, identity, external URI references, OSLC adapters, SysMLv2 ingestion, Flexo storage, signed envelopes, and federated audit composition.

The design is fully specified in the companion research repo: [`flexo-rtm-research`](https://github.com/dynamicalsystemsgroup/flexo-rtm-research). The canonical [Design Spec](https://github.com/dynamicalsystemsgroup/flexo-rtm-research/wiki/Design-Spec) §6 defines the 45 binary acceptance criteria that this codebase targets.

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
