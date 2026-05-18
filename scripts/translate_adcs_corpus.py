# SPDX-License-Identifier: Apache-2.0
"""One-shot translator: ADCS-prototype RDF → flexo-rtm RDF.

The prototype's vocabulary at ``<http://example.org/ontology/rtm#>`` predates the
flexo-rtm framework split. The structural mapping is one-to-one:

| Prototype term                       | flexo-rtm term                            |
|--------------------------------------|-------------------------------------------|
| ``proto:addresses`` (predicate)      | ``rtm:addresses``                         |
| ``proto:ProofArtifact``              | ``rtm:Artifact`` (lose proof/sim subtype) |
| ``proto:SimulationResult``           | ``rtm:Artifact``                          |
| ``sysml:RequirementDefinition``      | ``rtm:Requirement`` (ADCS-team scope)     |

Only ADCS-team-owned requirements (IRIs containing ``REQ-0NN``) are typed as
``rtm:Requirement``. Satellite-level ``SAT-REQ-*`` requirements remain as
``sysml:RequirementDefinition`` (a different scope per ADR-030 polycentric ASOT).

Attestations, SymbolicAnalysis / NumericalSimulation activities, gsn:* nodes,
and structural sysml:* triples are not translated by this slice 3 pass; they
land when slices 4 (identity) and 9 (signed envelopes) bring the attestation
profiles online. The corpus carries only what §4.1 (traditional bidirectional
traceability) needs — that is the slice 3 regression target.

Idempotent: re-running over the source produces byte-identical output (after
the deterministic Turtle serialisation in this script).
"""

from __future__ import annotations

import re
from pathlib import Path

from rdflib import OWL, RDF, RDFS, Graph, Literal, Namespace, URIRef

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = REPO_ROOT / "examples" / "adcs-corpus" / "source"
OUTPUT_TTL = REPO_ROOT / "examples" / "adcs-corpus" / "rtm.ttl"

PROTO = Namespace("http://example.org/ontology/rtm#")
RTM = Namespace("https://flexo-rtm.dev/ontology#")
SYSML = Namespace("https://www.omg.org/spec/SysML/2.0/")
ADCS = Namespace("http://example.org/adcs-demo/")

ADCS_REQ_PATTERN = re.compile(r"REQ-0\d+$")


def _is_adcs_team_requirement(iri: URIRef) -> bool:
    """ADCS-team-owned requirements use the IRI suffix REQ-0NN."""
    return bool(ADCS_REQ_PATTERN.search(str(iri)))


def translate() -> Graph:
    source = Graph()
    for ttl in sorted(SOURCE_DIR.glob("*.ttl")):
        source.parse(ttl, format="turtle")

    out = Graph()
    out.bind("rtm", RTM)
    out.bind("adcs", ADCS)
    out.bind("sysml", SYSML)

    # 1. Translate the addresses-edges (Evidence → Requirement)
    for ev, _, req in source.triples((None, PROTO.addresses, None)):
        out.add((ev, RTM.addresses, req))

    # 2. Type each evidence artifact as rtm:Artifact (and preserve the prototype
    #    subtype as rdfs:comment for provenance)
    for proto_class, role in (
        (PROTO.ProofArtifact, "ProofArtifact"),
        (PROTO.SimulationResult, "SimulationResult"),
        (PROTO.Evidence, "Evidence"),
    ):
        for art in source.subjects(RDF.type, proto_class):
            out.add((art, RDF.type, RTM.Artifact))
            out.add(
                (
                    art,
                    RDFS.comment,
                    Literal(f"Translated from prototype role: {role}"),
                )
            )

    # 3. Type ADCS-team requirements as rtm:Requirement (SAT-REQ-* are
    #    system-of-interest scope and stay sysml:RequirementDefinition only)
    for req in source.subjects(RDF.type, SYSML.RequirementDefinition):
        if _is_adcs_team_requirement(req):
            out.add((req, RDF.type, RTM.Requirement))

    # 4. Provenance: record where this graph came from
    out.add(
        (
            URIRef("https://flexo-rtm.dev/examples/adcs-corpus"),
            RDF.type,
            OWL.Ontology,
        )
    )
    out.add(
        (
            URIRef("https://flexo-rtm.dev/examples/adcs-corpus"),
            RDFS.comment,
            Literal(
                "Translated from DynamicalSystemsGroup/ADCS-lifecycle-demo "
                "via scripts/translate_adcs_corpus.py. See source/PROVENANCE.md."
            ),
        )
    )
    return out


def main() -> int:
    g = translate()
    g.serialize(destination=OUTPUT_TTL, format="turtle")
    n_req = len(list(g.subjects(RDF.type, RTM.Requirement)))
    n_art = len(list(g.subjects(RDF.type, RTM.Artifact)))
    n_addr = len(list(g.triples((None, RTM.addresses, None))))
    print(f"  rtm:Requirement   {n_req:>3}")
    print(f"  rtm:Artifact      {n_art:>3}")
    print(f"  rtm:addresses     {n_addr:>3}")
    print(f"\nWrote {OUTPUT_TTL.relative_to(REPO_ROOT)} ({len(g)} triples)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
