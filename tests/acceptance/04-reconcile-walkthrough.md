<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Walkthrough 4 — Reconcile: the simulation re-run conflict

You (in some role — could be the engineer, the reviewer, the auditor,
or a dedicated reconciler depending on your org) have discovered a
conflict. In the ADCS arc, the canonical conflict scenario is:

> The engineer re-runs the REQ-001 simulation with a wider disturbance
> envelope (2× nominal — addressing the sufficiency failure from
> Walkthrough 1). The new simulation has a different content hash than
> the original. Multiple attestations reference the original
> `EV-SIM-REQ-001` IRI. What should happen?

This is exactly the kind of judgement-bearing decision the reconcile
skill exists for. You are using the `flexo-rtm-reconcile` skill.

## Preconditions

- Walkthroughs 1–3 completed; the ADCS RTM exists in either the local
  session or the pushed Flexo branch.
- The original simulation artifact `EV-SIM-REQ-001` has content hash
  `sha256:sim001-narrow-envelope-...` (or whatever you used in
  Walkthrough 1).
- The engineer has run a new simulation. Its content hash is different —
  for the walkthrough use `sha256:sim001-wide-envelope-...`.

## Act 1 — Name the conflict

Tell Claude:

> Following `tests/acceptance/04-reconcile-walkthrough.md`. I have a
> conflict on https://rtm.example/adcs/EV-SIM-REQ-001 — Source A is
> the original narrow-envelope simulation (in my session, content hash
> sha256:sim001-narrow-...), Source B is the re-run wide-envelope
> simulation (proposed, content hash sha256:sim001-wide-...). Source A
> has two attestations on it (adequacy pass, sufficiency fail) plus
> a satisfaction attestation on REQ-001 that fails because of the
> sufficiency. Source B doesn't exist in the session yet.

### Expected skill behavior

The reconcile skill confirms the two sources, asks for handles to each
(session path for Source A; the new content hash + label for the
proposed Source B), and runs comparisons:

```bash
uv run flexo-rtm constructor show \
    https://rtm.example/adcs/EV-SIM-REQ-001 \
    --session-dir $ADCS_SESSION
```

Plus enumerate the attestations referencing it:

```bash
uv run flexo-rtm constructor status --session-dir $ADCS_SESSION
# pick out the AdequacyAttestation, SufficiencyAttestation, and the
# SatisfactionAttestation that depends on the failing sufficiency
```

## Act 2 — Surface the divergence

The skill presents BOTH sides verbatim:

```
DIVERGENCE
  IRI: https://rtm.example/adcs/EV-SIM-REQ-001

  Source A (in-session, original narrow-envelope simulation):
    <https://rtm.example/adcs/EV-SIM-REQ-001>
        a rtm:Artifact ;
        rdfs:label "Numerical simulation — pointing accuracy" ;
        rtm:hasContentHash "sha256:sim001-narrow-envelope-..." ;
        rtm:addresses <https://rtm.example/adcs/REQ-001> .

    Affected attestations:
      urn:rtm:attest/<uuid-A1>  AdequacyAttestation   pass  "rigid-body model adequate..."
      urn:rtm:attest/<uuid-A2>  SufficiencyAttestation fail  "narrow envelope; need 2×..."
      urn:rtm:attest/<uuid-S1>  SatisfactionAttestation (on REQ-001) fail "cannot judge satisfied; cites A2"

  Source B (proposed, re-run wide-envelope simulation):
    <https://rtm.example/adcs/EV-SIM-REQ-001>      ← same IRI, different content
        a rtm:Artifact ;
        rdfs:label "Numerical simulation — pointing accuracy (re-run, wide envelope)" ;
        rtm:hasContentHash "sha256:sim001-wide-envelope-..." ;
        rtm:addresses <https://rtm.example/adcs/REQ-001> .

    Affected attestations: none yet (B is proposed; if registered, new
    adequacy/sufficiency/satisfaction attestations will be authored
    against it via the engineer skill).

  Disagreement on: rtm:hasContentHash
```

## Act 3 — Present the four options (GATE 1)

The skill presents the canonical four-options menu:

```
GATE 1 — proposed resolution. Pick one:

  AcceptA   — The original narrow-envelope simulation is the
              authoritative artifact for this IRI. Source B is wrong
              (or the engineer made an error proposing it). Don't
              register B. Route to engineer skill — no follow-up
              writes; the conflict ends here.

  AcceptB   — The wide-envelope simulation supersedes the narrow one.
              The original simulation's sufficiency failure no longer
              applies. The three attestations on Source A
              (adequacy/sufficiency/satisfaction) need to be
              deprecated because their judgements were against the
              old evidence. The engineer then registers Source B and
              re-attests. Route to engineer skill with a checklist.

  AcceptBoth — Both simulations are valid in different scopes (e.g.,
              "narrow envelope simulation for the design-basis case"
              and "wide envelope simulation for the safety-margin
              case"). Each gets its own IRI; the conflict was an
              IRI-collision, not a content conflict. No deprecation;
              both attestation chains stay live. The engineer
              registers Source B under a DIFFERENT IRI (e.g.
              EV-SIM-REQ-001-WIDE).

  Deferred  — Can't decide right now. Record a rtm:DeferredJudgment
              with verbatim reason; surface this on the next audit.
```

The most likely answer in the canonical ADCS arc is **AcceptB**: the
wide-envelope simulation addresses the sufficiency failure exactly,
and the original simulation's narrow scope is now superseded. But the
skill must not assume this — it presents the menu and waits.

## Act 4 — Capture the reconciler's reason

After you pick (let's say `AcceptB` for the worked example), the
skill asks:

> Your reason — your own words. (This becomes the verbatim rdfs:comment
> on the reconciliation record. The record is append-only; if you
> later think this decision was wrong, you'll add a NEW record
> overriding it, not edit this one.)

Suggested reason for the worked AcceptB:

> *"The wide-envelope simulation directly addresses the sufficiency
> failure on REQ-001 — the original narrow-envelope simulation's
> scope was the documented insufficiency. Superseding is the correct
> action; the deprecated attestations on the narrow simulation
> remain visible to audit as a record of the original judgement."*

Capture VERBATIM. Don't paraphrase.

## Act 5 — GATE 1 confirm + write

The skill presents the proposed reconciliation record:

```
GATE 1 — proposed reconciliation record

  Path: ~/.flexo-rtm/reconciliation/<YYYY-MM-DD>-<short-id>.trig

  Content:
    @prefix rtm: <https://flexo-rtm.dev/ontology#> .
    @prefix prov: <http://www.w3.org/ns/prov#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

    <urn:rtm:reconciliation/<short-id>>
        a rtm:ReconciliationRecord ;
        rtm:reconciledBy <reconciler-iri> ;
        rtm:decision rtm:AcceptB ;
        rtm:appliesTo <https://rtm.example/adcs/EV-SIM-REQ-001> ;
        rtm:sourceA <session-local-narrow-envelope-handle> ;
        rtm:sourceB <proposed-wide-envelope-handle> ;
        prov:atTime "<now>"^^xsd:dateTime ;
        rdfs:comment "<verbatim reconciler reason>" .

Note: rtm:ReconciliationRecord is not in v0.1's ontology yet. For v0.1
the record is captured as plain RDF in your allowed-paths directory;
future ontology work can promote it to a first-class class.

Confirm? (y / n / correct)
```

Answer `y`. The skill writes the file.

## Act 6 — GATE 2 (read-back)

The skill reads the file it just wrote and presents the contents
verbatim:

```
GATE 2 — this is what landed in <path>:

  <full file contents>

Confirm? (y / n)
```

Answer `y` if it matches. If `n` — **do not delete or overwrite**.
Records are append-only. The skill explains: "I'll record a NEW
reconciliation noting the prior record was misfiled. What's the
correction?" Then loop back through GATE 1.

## Act 7 — Route the follow-up writes

For `AcceptB`, the skill produces a routed checklist for the engineer
skill:

> Reconciliation recorded. The follow-up writes need to happen via
> `flexo-rtm-engineer`:
>
> 1. Deprecate the three attestations referencing the original
>    EV-SIM-REQ-001 (adequacy, sufficiency, and the dependent
>    satisfaction on REQ-001).
> 2. Register the new EV-SIM-REQ-001 (same IRI, new content hash) —
>    the constructor's content-hash conflict detection will
>    auto-surface the deprecation prompt; choose `deprecate` for each
>    affected attestation if you haven't done step 1 manually.
> 3. Re-attest adequacy / sufficiency / satisfaction against the
>    re-run simulation. Expected outcome: all three pass (the
>    wide-envelope addresses what the narrow envelope couldn't).
>
> Switch to flexo-rtm-engineer and follow
> tests/acceptance/01-engineer-walkthrough.md's Act-5 + Act-6 patterns
> for the new attestations.

## Pass criteria

✅ Reconcile skill required explicit naming of both sources A and B;
   did not invent them.

✅ Divergence presented both sources verbatim, side-by-side.

✅ All four options (AcceptA / AcceptB / AcceptBoth / Deferred) were
   presented. The skill did NOT pick.

✅ Reconciler's reason captured VERBATIM (no paraphrasing).

✅ GATE 1 confirmed before writing the reconciliation record.

✅ Record written to `~/.flexo-rtm/reconciliation/` only; no other
   path touched.

✅ GATE 2 read-back matched what was written.

✅ For `AcceptB` (or `AcceptA`): follow-up CLI writes routed to
   `flexo-rtm-engineer` with a concrete checklist. Reconcile did not
   call any constructor write commands itself.

✅ If the same conflict is re-walked later, a new record is created;
   the old record is NEVER edited or deleted.

If `AcceptB` was the decision and the engineer follow-up completed:
the next audit run (Walkthrough 3 against the updated state) should
show:

- 3 deprecated attestations on the original `EV-SIM-REQ-001`
- 3 new live attestations on the re-registered `EV-SIM-REQ-001` (with
  the wide-envelope content hash) — all `rtm:pass` this time
- The satisfaction attestation on REQ-001 now `rtm:pass`
- Verdict: `certified=true`

That's the canonical close-out of the ADCS arc as far as a flexo-rtm
acceptance walkthrough goes.
