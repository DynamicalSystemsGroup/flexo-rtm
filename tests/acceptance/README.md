<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Acceptance walkthroughs — ADCS arc

User-acceptance-style scripts for the four `flexo-rtm` skills. Each
walkthrough is a scenario you can play through in conversation with
Claude (or any LLM-with-skills client). They are NOT automated `pytest`
tests; the pass criterion is "after the walkthrough completes, the
resulting state matches the expected RDF" — verified by running
`flexo-rtm certify` against the session and comparing the audit summary
against a pinned reference in each doc.

## The arc

The four walkthroughs recreate the [ADCS-lifecycle-demo](https://github.com/DynamicalSystemsGroup/ADCS-lifecycle-demo)'s
full traceability lifecycle through skill catechisms:

1. **[01-engineer-walkthrough.md](01-engineer-walkthrough.md)** —
   define 4 ADCS requirements (pointing accuracy / momentum cap /
   stability / disturbance rejection), register 4 proof artifacts +
   3 simulation results, create 7 addresses-edges, and walk
   adequacy / sufficiency / satisfaction attestations for each. One
   deliberately-failed satisfaction attestation on REQ-001 reproduces
   the prototype's "evidence is insufficient" case.

2. **[02-reviewer-walkthrough.md](02-reviewer-walkthrough.md)** —
   pre-push gate: walk the session, run `certify`, present the
   per-dimension coverage, GATE 1 on the push proposal, push, GATE 2
   read-back from the remote.

3. **[03-auditor-walkthrough.md](03-auditor-walkthrough.md)** —
   read-only audit walk: per-class attestation counts, gap findings
   (T1/T2/T3), certification level. Surfaces the failed REQ-001
   attestation as a finding the auditor classifies.

4. **[04-reconcile-walkthrough.md](04-reconcile-walkthrough.md)** —
   synthetic conflict: a re-run simulation with a different content
   hash invalidates the original SimulationResult artifact. Walks the
   four-options decision (AcceptA / AcceptB / AcceptBoth / Deferred)
   with verbatim reasoning capture. Routes resulting deprecation back
   through the engineer skill.

Each walkthrough is self-contained but expects the prior arc step's
state. The chain is engineer → reviewer → auditor → reconcile (if the
audit surfaces a conflict).

## How to run a walkthrough

In a Claude Code session at the `flexo-rtm` repo root:

```
> follow tests/acceptance/01-engineer-walkthrough.md
```

The model reads the walkthrough as a script, invokes the appropriate
skill, and drives you through the catechism. You play the role
(engineer / reviewer / auditor / reconciler) and provide the
judgement-bearing answers.

Each walkthrough has an explicit **pass criteria** section at the
bottom. Verify by running the named commands and comparing against the
pinned expected outputs.

## Reference fixture

The ADCS regression fixture at [`examples/adcs-corpus/rtm.ttl`](../../examples/adcs-corpus/rtm.ttl)
is the structural ground truth (4 requirements + 7 artifacts + 7
addresses-edges). The walkthroughs reproduce this structure exactly,
then add the attestation layer on top — that's the work the original
prototype did via its `request_attestation()` flow.

## What the walkthroughs prove

For the **skills** (configuration markdown, not code):

- That a real engineering arc — not a toy example — can be expressed
  through the catechisms.
- That the two-gate verbatim-reflection contract holds end-to-end:
  every CLI write was reviewed before AND after.
- That role boundaries are respected: the engineer never pushes; the
  reviewer never amends; the auditor never writes; reconcile never
  picks.
- That cross-skill routing works: engineer → reviewer → auditor →
  reconcile flows surface the right next-step at the right boundary.

For the **CLI** (already covered by 221 automated tests):

- That the constructor commands compose into a realistic workflow
  rather than just isolated unit operations.
- That `certify` produces the expected audit verdict against a graph
  the engineer authored interactively rather than file-fed.
- That `push` survives the journey from "engineer's first decision"
  through "remote Flexo has the cert artifact."

## Maintenance

When the skill catechisms change, the walkthroughs change with them —
they're tightly coupled. If a walkthrough's pinned output drifts from
what the CLI produces, the walkthrough is wrong (re-pin) or the CLI is
wrong (file an issue). Drift is meaningful, never noise.

When the ADCS arc itself evolves upstream (new requirements added,
artifacts revised), update [`examples/adcs-corpus/`](../../examples/adcs-corpus/)
first via `scripts/translate_adcs_corpus.py`, then update the
walkthroughs to match.
