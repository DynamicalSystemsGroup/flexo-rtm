<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Walkthrough 1 — Engineer: authoring the ADCS RTM

You are the satellite ADCS engineer. You've just completed a round of
analysis (symbolic + numerical) on a satellite Attitude Determination
and Control System. The artifacts of that analysis live as RDF in your
repo. You want to:

1. Register the four requirements you've been working against.
2. Register the proof and simulation artifacts you produced.
3. Link each artifact to the requirement(s) it addresses.
4. Walk adequacy / sufficiency / satisfaction attestations against each
   evidence/requirement pair — including the deliberately-failed case
   where your satisfaction attestation on REQ-001 has to be `fail`
   because the simulation evidence is insufficient.

You are using the `flexo-rtm-engineer` skill. The two-gate
verbatim-reflection contract applies to every CLI write.

## Preconditions

- `flexo-rtm` is installed (`uv run flexo-rtm --version` works).
- `git config user.email` is set — the engineer skill uses it to mint
  the approver IRI for attestations.
- A fresh session dir (no prior state). For these scripted walkthroughs
  use an explicit `--session-dir <path>` so the state is local to the
  walkthrough and doesn't pollute `~/.flexo-rtm/sessions/`.

Suggested session dir for the walkthrough:

```bash
export ADCS_SESSION=$(mktemp -d -t adcs-uat-XXXXXX)
echo "$ADCS_SESSION"   # e.g. /tmp/adcs-uat-abc/
```

## The ADCS requirements (from the original SysMLv2 model)

| IRI | Text |
|---|---|
| `https://rtm.example/adcs/REQ-001` | The ADCS shall maintain pointing accuracy within 0.1 degrees (3-sigma) under nominal disturbance conditions within 120 seconds of a slew maneuver. |
| `https://rtm.example/adcs/REQ-002` | Reaction wheel angular momentum shall not exceed the rated maximum momentum capacity (4.0 N.m.s) during nominal operations. |
| `https://rtm.example/adcs/REQ-003` | The closed-loop ADCS shall be asymptotically stable with all eigenvalues having real parts less than or equal to -0.010 rad/s. |
| `https://rtm.example/adcs/REQ-004` | The ADCS shall reject gravity gradient disturbance torques encountered in geostationary orbit without exceeding actuator torque capacity. |

## The artifacts you produced

| IRI | Kind | Addresses |
|---|---|---|
| `https://rtm.example/adcs/EV-PROOF-REQ-001` | symbolic proof (SymPy) | REQ-001 |
| `https://rtm.example/adcs/EV-PROOF-REQ-002` | symbolic proof (SymPy) | REQ-002 |
| `https://rtm.example/adcs/EV-PROOF-REQ-003` | symbolic proof (SymPy) | REQ-003 |
| `https://rtm.example/adcs/EV-PROOF-REQ-004` | symbolic proof (SymPy) | REQ-004 |
| `https://rtm.example/adcs/EV-SIM-REQ-001` | numerical simulation (scipy) | REQ-001 |
| `https://rtm.example/adcs/EV-SIM-REQ-002` | numerical simulation (scipy) | REQ-002 |
| `https://rtm.example/adcs/EV-SIM-REQ-004` | numerical simulation (scipy) | REQ-004 |

(REQ-003 has no simulation artifact — the closed-loop stability proof
is purely symbolic. This is faithful to the prototype.)

## Act 1 — Register the requirements

Tell Claude:

> Following `tests/acceptance/01-engineer-walkthrough.md`. I want to
> register the four ADCS requirements. Start with REQ-001 — pointing
> accuracy ≤ 0.1° (3-sigma) within 120s of a slew.

### Expected catechism (REQ-001)

Skill walks you through `new-requirement`:

1. "What's the IRI for this requirement?"
   → `https://rtm.example/adcs/REQ-001`
2. "Short label?"
   → `Pointing accuracy`
3. "Full statement?"
   → (the verbatim REQ-001 text from the table above)

### GATE 1 (proposed write)

The skill presents:

```
I'll run:
  uv run flexo-rtm constructor new-requirement \
      https://rtm.example/adcs/REQ-001 \
      --title "Pointing accuracy" \
      --statement "The ADCS shall maintain pointing accuracy within 0.1 degrees..." \
      --session-dir $ADCS_SESSION

Triples to be produced:
  <https://rtm.example/adcs/REQ-001>
      a rtm:Requirement ;
      rdfs:label "Pointing accuracy" ;
      rdfs:comment "The ADCS shall maintain pointing accuracy..." .

Confirm? (y / n / correct)
```

Answer `y`.

### GATE 2 (read-back)

The skill runs `flexo-rtm constructor show https://rtm.example/adcs/REQ-001 --session-dir $ADCS_SESSION`
and presents the Turtle. Confirm it matches what you intended.

### Repeat for REQ-002, REQ-003, REQ-004

Use the IRIs and text from the requirements table above. Suggested
short labels:

- REQ-002 → `Momentum capacity`
- REQ-003 → `Closed-loop stability`
- REQ-004 → `Disturbance rejection`

Each pass is one full GATE 1 + GATE 2 cycle.

## Act 2 — Register the proof artifacts

Tell Claude:

> Now the four proof artifacts. Start with EV-PROOF-REQ-001 — a
> symbolic stability proof generated from SymPy.

### Expected catechism (EV-PROOF-REQ-001)

Skill walks `new-artifact`:

1. "IRI for the artifact?"
   → `https://rtm.example/adcs/EV-PROOF-REQ-001`
2. "Short label?"
   → `Symbolic proof — pointing accuracy`
3. "Content hash?"
   → choose something representative, e.g.
     `sha256:proof001a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1`
     (in real workflows this comes from your build pipeline)
4. "Git commit?"
   → optional; use the SHA of the commit the proof was generated under,
     or skip.

### GATE 1

Skill presents the proposed CLI + intended Turtle. Confirm.

### GATE 2

`constructor show <iri>` read-back. Confirm.

### Repeat for EV-PROOF-REQ-002, -003, -004

Use distinct content hashes per artifact. Labels:

- `EV-PROOF-REQ-002` → `Symbolic proof — momentum capacity`
- `EV-PROOF-REQ-003` → `Symbolic proof — closed-loop stability`
- `EV-PROOF-REQ-004` → `Symbolic proof — disturbance rejection`

## Act 3 — Register the simulation artifacts

Same shape as Act 2, three artifacts:

- `EV-SIM-REQ-001` → `Numerical simulation — pointing accuracy`
- `EV-SIM-REQ-002` → `Numerical simulation — momentum capacity`
- `EV-SIM-REQ-004` → `Numerical simulation — disturbance rejection`

Each gets a distinct content hash. No simulation for REQ-003.

## Act 4 — Link artifacts to requirements (addresses-edges)

Tell Claude:

> Now link every artifact to the requirement it addresses. Seven edges
> total.

### Expected catechism (per edge)

Short flow — no judgement, just confirming the pairing:

1. "Artifact IRI?"
2. "Requirement IRI?"

### GATE 1 + GATE 2

For each of the seven edges. The expected pairs:

| Artifact | Requirement |
|---|---|
| `EV-PROOF-REQ-001` | `REQ-001` |
| `EV-PROOF-REQ-002` | `REQ-002` |
| `EV-PROOF-REQ-003` | `REQ-003` |
| `EV-PROOF-REQ-004` | `REQ-004` |
| `EV-SIM-REQ-001` | `REQ-001` |
| `EV-SIM-REQ-002` | `REQ-002` |
| `EV-SIM-REQ-004` | `REQ-004` |

After Act 4, your session should structurally match
[`examples/adcs-corpus/rtm.ttl`](../../examples/adcs-corpus/rtm.ttl) —
the regression fixture. Run a sanity check:

```bash
uv run flexo-rtm constructor status --session-dir $ADCS_SESSION
```

Expected: 4 Requirements, 7 Artifacts, 7 addresses-edges. No
attestations yet.

## Act 5 — Adequacy and sufficiency attestations

For each `(artifact, requirement)` pair, you make TWO attestations:

- **Adequacy** — is the model representation adequate for this claim?
- **Sufficiency** — is the evidence sufficient to support this claim?

In the ADCS arc, every adequacy attestation passes (the rigid-body
dynamics + linear control model is adequate for all four
requirements). Sufficiency mostly passes, with **one critical
exception**: the simulation for REQ-001 covers a too-narrow disturbance
envelope to support the 3-sigma pointing claim — sufficiency
**fails** on that one.

### Worked example — Adequacy attestation on EV-PROOF-REQ-001

Tell Claude:

> Attest adequacy on the EV-PROOF-REQ-001 — for the pointing accuracy
> requirement. The rigid-body model with reaction-wheel dynamics is
> adequate for this claim.

#### Catechism

1. "Subject IRI?" → `https://rtm.example/adcs/EV-PROOF-REQ-001`
2. "Class?" → `AdequacyAttestation`
3. "Is the model representation adequate?" → `yes`
4. "Reason?" → e.g. *"The rigid-body 6-DOF model with linearized
   reaction-wheel actuator dynamics captures the dominant attitude
   physics under the 3-sigma disturbance envelope. Higher-order
   flex modes were assessed and shown to be outside the controller
   bandwidth."*

#### GATE 1 + GATE 2 as usual.

### Repeat for every artifact

That's seven adequacy attestations + seven sufficiency attestations.
For brevity here is the suggested outcome table:

| Artifact | Adequacy | Sufficiency |
|---|---|---|
| `EV-PROOF-REQ-001` | pass | pass |
| `EV-PROOF-REQ-002` | pass | pass |
| `EV-PROOF-REQ-003` | pass | pass |
| `EV-PROOF-REQ-004` | pass | pass |
| `EV-SIM-REQ-001` | pass | **fail** ← the prototype's deliberately-insufficient case |
| `EV-SIM-REQ-002` | pass | pass |
| `EV-SIM-REQ-004` | pass | pass |

For the **failing** sufficiency attestation on `EV-SIM-REQ-001`,
your reason should explain why:

> *"The simulation sweeps disturbance magnitudes only up to 1× the
> nominal gravity gradient envelope; the 3-sigma claim in REQ-001
> needs at least 2× envelope coverage to be statistically defensible.
> The simulation is well-formed but its scope is too narrow to
> support the claim."*

This is the moment where you, the engineer, exercise the
Hawkins-Habli judgement that the system relies on: the evidence is
real, but it's not enough for the conclusion the requirement demands.

## Act 6 — Satisfaction attestations

For each requirement, you (the engineer) judge whether — given the
adequacy + sufficiency evidence — the requirement is satisfied. This
is the synthesizing claim.

### Worked example — Satisfaction on REQ-002

Tell Claude:

> Attest satisfaction on REQ-002 — momentum capacity. With the
> symbolic bound from the proof and the sweep in the simulation, I
> judge it satisfied.

#### Catechism

1. "Subject IRI?" → `https://rtm.example/adcs/REQ-002`
2. "Class?" → `SatisfactionAttestation`
3. "Do you judge the requirement satisfied?" → `yes`
4. "Reason?" → e.g. *"Symbolic proof bounds wheel momentum at 3.6
   N.m.s under the simulated nominal-operations profile (rated 4.0
   N.m.s); the simulation confirms the bound is met across the swept
   disturbance envelope."*

### The four satisfaction outcomes

| Requirement | Outcome | Notes |
|---|---|---|
| `REQ-001` | **fail** | The sufficiency attestation on `EV-SIM-REQ-001` failed (the simulation scope is too narrow). You cannot judge REQ-001 satisfied without sufficient evidence. The reason on this satisfaction attestation should cite the failing sufficiency attestation. |
| `REQ-002` | pass | (as worked above) |
| `REQ-003` | pass | Symbolic proof of asymptotic stability with the required eigenvalue bound is itself the satisfying evidence; no simulation needed. |
| `REQ-004` | pass | Symbolic + simulation agree the gravity-gradient torque rejection envelope is within actuator capacity. |

For the **failing** REQ-001 satisfaction attestation, your reason:

> *"Cannot judge REQ-001 satisfied. The sufficiency attestation on
> EV-SIM-REQ-001 [<iri>] failed — the simulation envelope is too
> narrow to support the 3-sigma pointing claim. A wider-envelope
> simulation is required before this attestation can be revisited."*

This deliberately-failed case is the prototype's canonical scenario;
it demonstrates that the audit-side downstream correctly registers a
non-certified requirement when judgement says so.

## Final sanity check

Run:

```bash
uv run flexo-rtm constructor status --session-dir $ADCS_SESSION
```

Expected: 4 Requirements + 7 Artifacts + 7 addresses-edges +
~18 attestations (4 + 7 adequacy + 7 sufficiency + 4 satisfaction).

Run a coverage check:

```bash
uv run flexo-rtm certify \
    --input $ADCS_SESSION/state.trig \
    --scope https://rtm.example/adcs/scope/full
```

(The scope IRI is your choice; pass any IRI here for the walkthrough.)

## Pass criteria

✅ All 4 requirements present with `rtm:Requirement` typing + `rdfs:label`
+ `rdfs:comment`.

✅ All 7 artifacts present with `rtm:Artifact` typing + content hashes.

✅ All 7 addresses-edges present.

✅ 18 attestations across 3 classes — including:
   - 7 `rtm:AdequacyAttestation` instances (all `rtm:pass`)
   - 7 `rtm:SufficiencyAttestation` instances (6 `rtm:pass`, 1 `rtm:fail`
     on `EV-SIM-REQ-001`)
   - 4 `rtm:SatisfactionAttestation` instances (3 `rtm:pass` on REQ-002,
     003, 004; 1 `rtm:fail` on REQ-001)

✅ Every attestation has `rtm:approvedBy <your-engineer-iri>` derived
   from `git config user.email`.

✅ Every attestation has a non-empty `rdfs:comment` (the reason you
   provided verbatim).

✅ Every CLI write went through GATE 1 (you confirmed pre-execution)
   AND GATE 2 (you confirmed the Turtle landed correctly).

✅ The session state file at `$ADCS_SESSION/state.trig` parses as
   well-formed TriG.

Once these all hold, route to
[`02-reviewer-walkthrough.md`](02-reviewer-walkthrough.md) to gate the
push.
