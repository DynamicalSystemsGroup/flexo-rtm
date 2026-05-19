<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Walkthrough 2 — Reviewer: pre-push gate

You are the engineer (or a designated reviewer — it doesn't matter
which; the role is whoever decides "we're ready to push this to the
shared Flexo branch"). The engineer has finished authoring the ADCS
session per
[`01-engineer-walkthrough.md`](01-engineer-walkthrough.md). Now the
session needs to:

1. Be walked through one more time so the reviewer sees what's about
   to push.
2. Get a pre-push audit (`flexo-rtm certify` against the session
   state).
3. Pass GATE 1 (proposed push) with explicit user confirmation.
4. Push atomically to the remote Flexo branch.
5. Pass GATE 2 (remote read-back) confirming what landed matches.

You are using the `flexo-rtm-reviewer` skill.

## Preconditions

- Engineer walkthrough completed and pass criteria satisfied.
- `$ADCS_SESSION` env var still points at the session dir.
- For the live-push test segment: `FLEXO_TOKEN` and `FLEXO_URL`
  available (typically loaded from `.env`); a sandbox org you can
  create on the target Flexo instance.

If you don't have Flexo credentials, you can run this walkthrough
through GATE 1 and stop there — the push step auto-skips when no token
is available.

## Act 1 — Enumerate the local session

Tell Claude:

> Following `tests/acceptance/02-reviewer-walkthrough.md`. Review my
> session before push: $ADCS_SESSION

### Expected skill behavior

The reviewer skill runs `flexo-rtm constructor status --session-dir
$ADCS_SESSION` and presents the output grouped by kind. You should see:

```
session: <session-dir>/state.trig
  Requirement   https://rtm.example/adcs/REQ-001  Pointing accuracy
  Requirement   https://rtm.example/adcs/REQ-002  Momentum capacity
  Requirement   https://rtm.example/adcs/REQ-003  Closed-loop stability
  Requirement   https://rtm.example/adcs/REQ-004  Disturbance rejection
  Artifact      https://rtm.example/adcs/EV-PROOF-REQ-001  Symbolic proof — pointing accuracy
  Artifact      https://rtm.example/adcs/EV-PROOF-REQ-002  Symbolic proof — momentum capacity
  ...
  addresses     https://rtm.example/adcs/EV-PROOF-REQ-001 -> https://rtm.example/adcs/REQ-001
  addresses     https://rtm.example/adcs/EV-PROOF-REQ-002 -> https://rtm.example/adcs/REQ-002
  ...
  attest        urn:rtm:attest/<uuid>
  attest        urn:rtm:attest/<uuid>
  ...
```

The skill then asks: "Drill into any specific IRI? (`show <iri>` /
`audit` / `cancel`)".

## Act 2 — Drill into the failing attestations

This is the load-bearing review step. The reviewer wants to see what
the engineer's failure judgements looked like.

Tell Claude:

> Show me the satisfaction attestation on REQ-001 — that's the one
> that should be the failed case.

The skill runs `constructor show` on each attestation referencing
REQ-001 and presents the Turtle verbatim. Look for:

- `a rtm:SatisfactionAttestation`
- `rtm:status rtm:fail`
- `rtm:appliesTo <https://rtm.example/adcs/REQ-001>`
- `rdfs:comment "Cannot judge REQ-001 satisfied. The sufficiency
  attestation on EV-SIM-REQ-001 ... failed ..."`

Then drill into the failing sufficiency attestation:

> Now show me the failing sufficiency attestation on EV-SIM-REQ-001.

Same pattern. Confirm:

- `a rtm:SufficiencyAttestation`
- `rtm:status rtm:fail`
- `rtm:appliesTo <https://rtm.example/adcs/EV-SIM-REQ-001>`
- `rdfs:comment "The simulation sweeps disturbance magnitudes only up
  to 1× ... needs at least 2× envelope coverage ..."`

This is what auditable engineering judgement looks like. Both
attestations carry a named human approver and verbatim reason.

## Act 3 — Pre-push audit

Tell Claude:

> Now run the pre-push audit.

### Expected skill behavior

```
uv run flexo-rtm certify \
    --input $ADCS_SESSION/state.trig \
    --scope https://rtm.example/adcs/scope/full
```

The skill presents the AuditReport as a readable summary. Expected
shape (counts approximate; exact UUIDs vary):

```
Audit summary for https://rtm.example/adcs/scope/full

  Coverage:
    forward:   100% — every requirement has ≥ 1 addressing artifact
    backward:  100% — every artifact addresses ≥ 1 requirement

  Attestations:
    live:        18    (all 18 are still live — no deprecations yet)
    deprecated:  0
    by class:
      Satisfaction:  3 pass, 1 fail
      Adequacy:      7 pass, 0 fail
      Sufficiency:   6 pass, 1 fail

  Verdict: certified=false   ← because of the REQ-001 satisfaction fail
```

Note: `certified=false` is the **expected** outcome. The audit
correctly registers that one requirement is not satisfied. This is the
prototype's canonical scenario.

The skill asks:

> The pre-push audit flags 1 failed satisfaction + 1 failed
> sufficiency. Want to amend before pushing (route to engineer),
> accept-and-push anyway (the gaps will surface to the auditor
> downstream), or cancel?

The right answer for this scenario is **accept-and-push**: the failure
itself is the meaningful audit artifact. We're not hiding it; we're
recording that REQ-001 is not yet satisfied because the simulation
scope is too narrow.

## Act 4 — GATE 1 (proposed push)

The skill composes and presents:

```
GATE 1 — proposed push

  Remote:    <FLEXO_URL>                  (e.g. https://try-layer1.starforge.app)
  Org:       <your-sandbox-org>
  Repo:      adcs-cert
  Branch:    engineering/<your-name>
  Scope:     https://rtm.example/adcs/scope/full

  Partitions being pushed:
    urn:rtm:model:           <N> triples
    urn:rtm:attestations:    <N> triples
    urn:rtm:audit:           (excluded — remote builds its own)

  Authorization: FLEXO_TOKEN env var (will be sourced; never echoed).

Confirm push? (y / n / cancel)
```

Answer `y` if you have Flexo credentials; `cancel` if you don't (the
walkthrough ends here in that case, and you can resume by pushing
later from a terminal that has the env vars set).

## Act 5 — Execute the push

The skill runs:

```bash
( set -a; . ./.env; set +a; \
  uv run flexo-rtm constructor push \
      --url $FLEXO_URL \
      --org <sandbox-org> \
      --repo adcs-cert \
      --branch engineering/<your-name> \
      --scope https://rtm.example/adcs/scope/full \
      --session-dir $ADCS_SESSION \
      --archive )
```

Expected output:

```
pushed to <FLEXO_URL> (branch engineering/<your-name>; commit urn:rtm:commit/<uuid>)
archived session to <session-dir>/archive/state-<timestamp>.trig
```

## Act 6 — GATE 2 (remote read-back)

The skill re-fetches and re-audits the remote state:

```bash
# Re-pull each partition from the remote into a temp graph;
# re-run certify against the pulled snapshot
```

(For v0.1 you can simulate the pull by re-running certify against the
ARCHIVED local session — that's the snapshot you just pushed.)

Expected: the audit summary matches what was presented in GATE 1
(same counts, same verdict).

The skill asks:

> GATE 2 — this is what the remote now contains for the scope. Confirm
> it matches what you authorized in GATE 1? (y / n)

Answer `y` if everything matches. If `n`, route to
[`04-reconcile-walkthrough.md`](04-reconcile-walkthrough.md) — the
remote diverged from what we authorized.

## Pass criteria

✅ Reviewer skill enumerated all 4 reqs + 7 artifacts + 7 edges + 18
   attestations.

✅ The two failed attestations (sufficiency on `EV-SIM-REQ-001`,
   satisfaction on `REQ-001`) were drilled into and reviewed verbatim.

✅ Pre-push audit returned `certified=false` for the right reason.

✅ GATE 1 confirmation was explicit; no silent push.

✅ Push succeeded; remote commit IRI captured.

✅ GATE 2 read-back matched the local session; no divergence.

✅ Local session archived to `<session-dir>/archive/`.

Once these hold, route to
[`03-auditor-walkthrough.md`](03-auditor-walkthrough.md) to walk an
independent audit of the now-pushed state.
