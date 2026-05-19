# SPDX-License-Identifier: Apache-2.0
"""W3C Data Integrity verification — Signed Envelope Shapes §5 + S2.

Slice 9 ships eddsa-rdfc-2022 end-to-end; ecdsa-rdfc-2019 and the P-384 suite
follow the same pattern but are not exercised by tests yet. The signature is
computed over the RDFC-1.0 canonical bytes of the attestation graph (the
``sec:proof`` block itself is excluded from the canonicalization).
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import UTC, datetime

from rdflib import RDF, XSD, BNode, Graph, Literal, Namespace, URIRef

from oracle.canonicalize import canonicalize_graph
from oracle.signing.cryptosuites import is_known_cryptosuite
from oracle.signing.errors import OptionalDependencyMissing, VerificationError

SEC = Namespace("https://w3id.org/security#")
RTM = Namespace("https://flexo-rtm.dev/ontology#")

_EDDSA_SUITE = "eddsa-rdfc-2022"


@dataclass(frozen=True)
class DataIntegrityProof:
    cryptosuite: str
    verification_method: str
    proof_value_b64: str
    created: datetime


def _strip_proofs(graph: Graph) -> Graph:
    """Return a copy of ``graph`` with every sec:proof block removed.

    The proof is computed over the canonical bytes of the rest of the graph;
    leaving the proof block in would make the signature self-referential.
    """
    proof_iris = {o for _, _, o in graph.triples((None, SEC.proof, None))}
    out = Graph()
    for s, p, o in graph:
        if p == SEC.proof:
            continue
        if s in proof_iris:
            continue
        out.add((s, p, o))
    return out


def _serialize_payload(graph: Graph) -> bytes:
    return canonicalize_graph(_strip_proofs(graph)).canonical_bytes


def _load_cryptography() -> object:
    try:
        import cryptography  # noqa: F401  -- imported to trigger ImportError
        from cryptography.hazmat.primitives.asymmetric import ed25519

        return ed25519
    except ImportError as exc:
        raise OptionalDependencyMissing(
            "VC-DI verification needs the [signing] extra: pip install 'flexo-rtm[signing]'"
        ) from exc


def sign_and_attach(
    *,
    attestation_iri: URIRef,
    graph: Graph,
    private_key_bytes: bytes,
    verification_method: str,
    cryptosuite: str = _EDDSA_SUITE,
    created: datetime | None = None,
) -> Graph:
    """Sign the (proof-stripped) canonical form of ``graph`` and attach a
    sec:proof block to ``attestation_iri``. Returns the augmented graph.

    ``private_key_bytes`` is the 32-byte raw Ed25519 seed. Adopters generate keys
    through their PKI / KMS; this function only signs.
    """
    if cryptosuite != _EDDSA_SUITE:
        raise VerificationError(
            f"sign_and_attach v0.1 only supports {_EDDSA_SUITE!r}, got {cryptosuite!r}"
        )
    ed25519 = _load_cryptography()
    sk = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)  # type: ignore[attr-defined]
    payload = _serialize_payload(graph)
    signature = sk.sign(payload)

    proof_node = BNode()
    out = Graph()
    for triple in graph:
        out.add(triple)
    out.add((attestation_iri, SEC.proof, proof_node))
    out.add((proof_node, RDF.type, SEC.DataIntegrityProof))
    out.add((proof_node, SEC.cryptosuite, Literal(cryptosuite)))
    out.add(
        (
            proof_node,
            SEC.verificationMethod,
            URIRef(verification_method),
        )
    )
    out.add((proof_node, SEC.proofPurpose, SEC.assertionMethod))
    out.add(
        (
            proof_node,
            SEC.proofValue,
            Literal(base64.b64encode(signature).decode("ascii")),
        )
    )
    out.add(
        (
            proof_node,
            SEC.created,
            Literal((created or datetime.now(UTC)).isoformat(), datatype=XSD.dateTime),
        )
    )
    return out


def verify_data_integrity_proof(
    *,
    graph: Graph,
    public_key_bytes: bytes,
    verification_method: str,
) -> bool:
    """Verify that the sec:proof on the graph matches the signature produced
    by the public key with IRI ``verification_method``.

    Returns True iff the proof verifies. Raises :class:`VerificationError` on
    structural problems (missing proof, unknown cryptosuite, malformed value).
    """
    ed25519 = _load_cryptography()
    proof_iri: BNode | URIRef | None = None
    cryptosuite: str | None = None
    proof_value: str | None = None
    method_match = False

    for s, _, o in graph.triples((None, SEC.proof, None)):
        del s  # unused
        proof_iri = o  # type: ignore[assignment]
        break

    if proof_iri is None:
        raise VerificationError("graph has no sec:proof")

    for _, p, o in graph.triples((proof_iri, None, None)):
        if p == SEC.cryptosuite:
            cryptosuite = str(o)
        elif p == SEC.verificationMethod:
            method_match = str(o) == verification_method
        elif p == SEC.proofValue:
            proof_value = str(o)

    if cryptosuite is None or not is_known_cryptosuite(cryptosuite):
        raise VerificationError(f"unknown or missing cryptosuite: {cryptosuite!r}")
    if cryptosuite != _EDDSA_SUITE:
        raise VerificationError(f"verify v0.1 only supports {_EDDSA_SUITE!r}, got {cryptosuite!r}")
    if not method_match:
        raise VerificationError(f"verificationMethod mismatch: expected {verification_method!r}")
    if proof_value is None:
        raise VerificationError("proof has no sec:proofValue")

    pk = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)  # type: ignore[attr-defined]
    payload = _serialize_payload(graph)
    try:
        pk.verify(base64.b64decode(proof_value), payload)
    except Exception:
        return False
    return True


__all__ = ["DataIntegrityProof", "sign_and_attach", "verify_data_integrity_proof"]
