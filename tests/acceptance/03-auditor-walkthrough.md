<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Walkthrough 3 — Auditor: independent audit of the ADCS scope

You are an auditor — internal or external — independent of the engineer
who authored the ADCS RTM. You did not run any of the symbolic or
numerical analysis; you don't make the adequacy / sufficiency
judgements. Your job is to **read the engineer's RDF + the
attestations attached to it, evaluate coverage and certification
level, surface gaps, and produce a structured audit summary**.

You are using the `flexo-rtm-auditor` skill. The skill is read-only by
construction — `allowed-paths: []`. Whenever a resolution is needed,
the auditor classifies the finding but never picks; resolution routes
to `flexo-rtm-engineer` (write) or `flexo-rtm-reconcile` (drift).

## Preconditions

- Engineer + reviewer walkthroughs completed; ADCS state pushed to a
  Flexo branch (or available in the archived session at
  `$ADCS_SESSION/archive/`).
- You have read access to the pushed RDF — either via a pulled
  snapshot, the local archive, or the regression fixture at
  [`examples/adcs-corpus/rtm.ttl`](../../examples/adcs-corpus/rtm.ttl)
  (the structural ground truth, without the attestation layer).

For this walkthrough, point the auditor at the archived session — that
is the auditable snapshot of "what was pushed."

```bash
export ADCS_AUDIT_INPUT="$ADCS_SESSION/archive/state-*.trig"
ls -1 $ADCS_AUDIT_INPUT     # confirm a single matching file
```

## Act 1 — Scope + input

Tell Claude:

> Following `tests/acceptance/03-auditor-walkthrough.md`. Audit the
> ADCS scope. The input is the archived session at $ADCS_AUDIT_INPUT
> and the scope IRI is https://rtm.example/adcs/scope/full.

### Expected skill behavior

The auditor skill asks for scope + input (as above), then runs:

```bash
uv run flexo-rtm certify \
    --input $ADCS_AUDIT_INPUT \
    --scope https://rtm.example/adcs/scope/full
```

## Act 2 — Read the structured audit

The skill presents the audit summary in the canonical reading format:

```
Audit summary for https://rtm.example/adcs/scope/full
  Input: $ADCS_AUDIT_INPUT
  Transcript: <run-id>
  Reproducibility manifest: <run-id>

  Coverage:
    forward:   100% — requirements with ≥ 1 addressing artifact
    backward:  100% — artifacts addressing ≥ 1 requirement

  Attestations:
    live:        18
    deprecated:  0
    by class:
      Satisfaction:    3 pass / 1 fail
      Adequacy:        7 pass / 0 fail
      Sufficiency:     6 pass / 1 fail

  Certification level: SELF_CERT_ONLY
    (no external ScopeCertificationAttestation present — this is an
     internal-only attestation chain so far)

  Gap findings:
    T3.unattested-satisfaction:  0   ← every addresses-edge has a satisfaction attempt
    T1.orphan-requirement:       0
    T2.dangling-evidence:        0

  Verdict: certified=false
```

`certified=false` is correct. REQ-001's satisfaction attestation is
`rtm:fail`. The audit's job is to register that faithfully.

## Act 3 — Walk each meaningful finding

The auditor skill goes through each material item and asks you to
classify:

### Finding 1 — failed satisfaction attestation on REQ-001

Skill presents (in addition to the count above):

```
SatisfactionAttestation on https://rtm.example/adcs/REQ-001
  status: rtm:fail
  approver: <engineer-iri>
  reason (rdfs:comment): "Cannot judge REQ-001 satisfied. The
    sufficiency attestation on EV-SIM-REQ-001 [<iri>] failed — the
    simulation envelope is too narrow to support the 3-sigma pointing
    claim. A wider-envelope simulation is required before this
    attestation can be revisited."
```

Skill asks:

> What do you want to do with this finding?
> - `note` — add to audit summary as something to track
> - `ask engineer to resolve` — route to flexo-rtm-engineer (the
>   engineer would either run a wider-envelope simulation OR amend
>   the simulation scope and re-attest)
> - `looks like upstream drift` — not applicable here; the failure
>   is internal-judgement, not source-drift
> - `skip` — not interesting

Auditor's call. The right answer in this scenario is `ask engineer to
resolve` if the auditor wants the failure remediated, or `note` if the
auditor accepts the failure as the current state (e.g., "REQ-001 is
not yet satisfied, here's what needs to happen, the engineer is on
it").

### Finding 2 — failed sufficiency attestation on EV-SIM-REQ-001

Skill presents:

```
SufficiencyAttestation on https://rtm.example/adcs/EV-SIM-REQ-001
  status: rtm:fail
  approver: <engineer-iri>
  reason: "The simulation sweeps disturbance magnitudes only up to
    1× the nominal gravity gradient envelope; the 3-sigma claim in
    REQ-001 needs at least 2× envelope coverage..."
```

Same four-option classification. The right answer is consistent with
Finding 1 — these two failures are coupled (the failed sufficiency is
WHY the failed satisfaction).

### No other gaps

For this clean ADCS arc, there are no orphans, no danglers, no
unattested edges. The audit summary records 0 for all gap codes.

## Act 4 — GATE — the audit summary

After all findings are walked and classified, the skill presents the
complete audit summary:

```
GATE — complete audit for https://rtm.example/adcs/scope/full

  Scope coverage: forward 100% / backward 100%
  Verdict: certified=false (1 satisfaction fail, 1 sufficiency fail
    — coupled findings on REQ-001)
  Certification level: SELF_CERT_ONLY

  Findings classified:
    1. REQ-001 satisfaction fail   → routed to flexo-rtm-engineer (resolve)
    2. EV-SIM-REQ-001 sufficiency  → routed to flexo-rtm-engineer (resolve)
       (coupled; root cause is the simulation scope)

  Findings noted-for-tracking: 0
  Findings as upstream drift: 0

Confirm? (y / amend / cancel)
```

Confirm `y` to finalize the audit.

The skill emits a structured summary you can copy to your audit log.
The skill itself doesn't write the summary to disk — `allowed-paths:
[]` — so you take the output and save it yourself if you want a
persistent record.

## Act 5 — Compare to ground truth (optional)

For UAT, compare the audit against the regression fixture
[`examples/adcs-corpus/rtm.ttl`](../../examples/adcs-corpus/rtm.ttl) +
the existing regression test:

```bash
uv run pytest tests/regression/ -v -k adcs
```

The regression fixture is the structural ground truth (without the
attestation layer). The auditor's walk-through should produce the same
forward + backward coverage % (both 100%) and the same set of
addresses-edges that the regression test pins.

## Pass criteria

✅ Auditor skill asked for scope + input explicitly; did not invent
   them.

✅ Audit summary presented per-class attestation counts (live vs
   deprecated breakdown).

✅ Failed satisfaction on REQ-001 was surfaced as a finding (with the
   engineer's verbatim reason quoted).

✅ Failed sufficiency on EV-SIM-REQ-001 was surfaced as a finding;
   the auditor recognized it as the root cause of the satisfaction
   failure (coupled findings).

✅ Auditor classified each finding (note / route / skip); did not pick
   the resolution.

✅ Skill wrote nothing to disk — only presented output to the auditor.

✅ Final GATE confirmation explicit (`y` to finalize).

Once these hold:

- If any finding was routed to "ask engineer to resolve" → route to
  [`01-engineer-walkthrough.md`](01-engineer-walkthrough.md) (the
  engineer either runs the wider-envelope simulation and re-attests,
  or deprecates the failing simulation artifact and registers a new
  one).
- If a finding looked like upstream drift (not this scenario, but
  possible in others) → route to
  [`04-reconcile-walkthrough.md`](04-reconcile-walkthrough.md).
- If no further action: the audit ends here. The state remains
  `certified=false` on REQ-001 until the underlying judgement
  changes — that's the design.
