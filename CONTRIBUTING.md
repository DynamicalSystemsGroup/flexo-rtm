<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Contributing

## Engineering principles

`flexo-rtm` is built **test-first**, in **sparse correct slices**, and against the [Design Spec](https://github.com/dynamicalsystemsgroup/flexo-rtm-research/wiki/Design-Spec). The principles below are non-negotiable.

### Sparseness rules

1. Make the named acceptance test file fail with a precise error first.
2. Add the smallest code that makes it green.
3. Refactor only inside the slice; no abstractions for "future flexibility."
4. No private re-implementations of `rdflib`, `pyshacl`, `pydantic`, `cryptography`, `sigstore`, or `in-toto-attestation` (per [ADR-023](https://github.com/dynamicalsystemsgroup/flexo-rtm-research/wiki/ADR-023-Cryptography-by-Composition-of-Battle-Tested-Standards)).
5. No code unattached to a failing test or a stated SHACL invariant in the spec.

### Escalation rule

The Design Spec was written under spec-time assumptions. **Stop and escalate** — do not paper over — when:

- Two design principles are in direct tension (e.g., parsimony vs alignment completeness; ASOT non-ownership vs a test that wants caching; determinism vs a non-replayable external dep).
- An acceptance criterion as written cannot be made true by composing the spec's named tools.
- The "sparsest" path would require building substantial machinery (new algorithm, custom resolver, non-trivial state machine, parser for a format the spec didn't name).
- An ADR's premise is empirically falsified by the prototype, tooling, or upstream standard.
- A SHACL shape or SPARQL query in the spec, applied verbatim, fails on the regression corpus.

The implementation principle is: **compose known tools into the three layers (operational / storage / analysis). Anything more sophisticated is a signal that something is off.**

### Deterministic everything

No clocks, no randomness, no environment-dependent ordering in oracle code paths. Time enters only via signed payloads or transcript `prov:atTime` fields supplied as inputs.

## Workflow

1. Pick a slice from the v0.1 roadmap in [`/Users/z/.claude/plans/harmonic-puzzling-patterson.md`](https://github.com/dynamicalsystemsgroup/flexo-rtm-research/wiki) (local, not yet published).
2. Read its named companion contract page in `flexo-rtm-research/wiki/` before coding.
3. RED: write the slice's failing test(s).
4. GREEN: minimum code.
5. Refactor inside the slice.
6. Update `CLAUDE.md` if the slice changes a load-bearing convention.

## SPDX headers

Every source file declares its license class as the first line:

| File class | Header |
|---|---|
| Python / shell / Makefile | `# SPDX-License-Identifier: Apache-2.0` |
| Markdown | `<!-- SPDX-License-Identifier: CC-BY-4.0 -->` |
| Turtle / SHACL / YAML ontology | `# SPDX-License-Identifier: CC0-1.0` |

## Licensing

By contributing you agree your changes are licensed under the artifact-class terms in [LICENSE.md](LICENSE.md). No CLA required.
