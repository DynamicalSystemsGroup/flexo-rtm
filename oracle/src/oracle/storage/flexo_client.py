# SPDX-License-Identifier: Apache-2.0
"""HTTPS client for Flexo MMS Layer-1 — reconciled with the real OpenMBEE
Flexo MMS Layer-1 API. The :class:`FlexoBackend` Protocol shape is unchanged;
internally this client buffers staged writes between ``begin_transaction`` and
``commit_transaction`` and issues a single ``POST /update`` with combined
SPARQL ``INSERT DATA`` at commit. That single request is the atomic batch.

Spec divergences tracked upstream as flexo-rtm-research#20 (transaction
endpoints don't exist) and #21 (master vs main).
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from urllib.error import HTTPError, URLError
from uuid import uuid4

from rdflib import Graph, Literal, URIRef
from rdflib.term import Identifier

from oracle.storage.backend import MergePolicyHints, MergeResult, TransactionError

_USER_AGENT = "flexo-rtm/0.0.1 (oracle storage client)"
_RESOURCE_BODY_PREFIX = "<> <http://purl.org/dc/terms/title> "
_MMS_REF = "https://mms.openmbee.org/rdf/ontology/ref"


@dataclass(frozen=True)
class FlexoConfig:
    base_url: str
    org: str
    repo: str
    token: str
    timeout_seconds: float = 60.0


@dataclass
class _StagedWrite:
    graph_iri: str
    graph: Graph


@dataclass
class _PendingTx:
    branch: str
    staged: list[_StagedWrite] = field(default_factory=list)


def _serialize_term(term: Identifier) -> str:
    if isinstance(term, URIRef):
        return f"<{term}>"
    if isinstance(term, Literal):
        return term.n3()
    return term.n3()


def _graph_to_insert_clause(graph_iri: str, graph: Graph) -> str:
    """Flatten an rdflib Graph to bare N-Triples for SPARQL ``INSERT DATA``.

    Flexo MMS Layer-1 doesn't accept GRAPH clauses inside ``INSERT DATA``
    (it raises ``QuadsNotAllowedException``) — a Flexo branch IS the named
    graph. Adopters who need per-partition graphs map each partition IRI to
    its own Flexo branch (the ADCS-lifecycle-demo pattern). The branch-as-
    graph semantics are a Flexo Layer-1 design constraint; tracked upstream
    as flexo-rtm-research#22.
    """
    del graph_iri
    triples = [
        f"  {_serialize_term(s)} {_serialize_term(p)} {_serialize_term(o)} ."  # type: ignore[arg-type]
        for s, p, o in graph
    ]
    if not triples:
        return ""
    return "\n".join(triples)


class FlexoHttpClient:
    """OpenMBEE Flexo MMS Layer-1 client (PUT-then-SPARQL-INSERT-DATA pattern)."""

    def __init__(self, config: FlexoConfig) -> None:
        self._config = config
        self._pending: dict[str, _PendingTx] = {}

    def _url(self, *parts: str) -> str:
        encoded = "/".join(urllib.parse.quote(p, safe="") for p in parts)
        return f"{self._config.base_url.rstrip('/')}/{encoded}"

    def _request(
        self,
        method: str,
        url: str,
        *,
        body: bytes | None = None,
        content_type: str | None = None,
        accept: str | None = None,
        accept_codes: tuple[int, ...] = (200, 201, 204),
    ) -> tuple[int, bytes]:
        request = urllib.request.Request(  # noqa: S310 — adopter-controlled URL
            url, method=method, data=body
        )
        request.add_header("Authorization", f"Bearer {self._config.token}")
        request.add_header("User-Agent", _USER_AGENT)
        if content_type is not None:
            request.add_header("Content-Type", content_type)
        if accept is not None:
            request.add_header("Accept", accept)
        try:
            with urllib.request.urlopen(  # noqa: S310
                request, timeout=self._config.timeout_seconds
            ) as response:
                payload = response.read()
                assert isinstance(payload, bytes)
                return response.status, payload
        except HTTPError as exc:
            payload = exc.read()
            if exc.code in accept_codes:
                return exc.code, payload
            raise TransactionError(
                f"Flexo {method} {url} → HTTP {exc.code}: "
                f"{payload.decode('utf-8', 'replace')[:500]}"
            ) from exc
        except URLError as exc:
            raise TransactionError(f"Flexo {method} {url} failed: {exc}") from exc

    def _put_resource(self, url: str, *, title: str, extra_body: str = "") -> None:
        body = (_RESOURCE_BODY_PREFIX + f'"{title}"@en .' + extra_body).encode("utf-8")
        self._request(
            "PUT",
            url,
            body=body,
            content_type="text/turtle",
            accept_codes=(200, 201, 409),
        )

    def _ensure_resource(self, url: str, *, title: str, extra_body: str = "") -> None:
        try:
            self._request("HEAD", url, accept_codes=(200, 204))
            return
        except TransactionError:
            pass
        self._put_resource(url, title=title, extra_body=extra_body)

    # ------------------------------------------------------------ Backend API

    def begin_transaction(self, branch: str) -> str:
        self._ensure_resource(self._url("orgs", self._config.org), title=self._config.org)
        self._ensure_resource(
            self._url("orgs", self._config.org, "repos", self._config.repo),
            title=self._config.repo,
        )
        if branch != "master":
            extra = f" .\n<> <{_MMS_REF}> <./master>"
            self._ensure_resource(
                self._url("orgs", self._config.org, "repos", self._config.repo, "branches", branch),
                title=branch,
                extra_body=extra,
            )
        tx_id = f"tx-{uuid4()}"
        self._pending[tx_id] = _PendingTx(branch=branch)
        return tx_id

    def write_graph(self, tx_id: str, branch: str, graph_iri: str, graph: Graph) -> None:
        if tx_id not in self._pending:
            raise TransactionError(f"unknown transaction {tx_id!r}")
        pending = self._pending[tx_id]
        if pending.branch != branch:
            raise TransactionError(f"transaction {tx_id} is for {pending.branch!r}, not {branch!r}")
        copy = Graph()
        for triple in graph:
            copy.add(triple)
        pending.staged.append(_StagedWrite(graph_iri=graph_iri, graph=copy))

    def commit_transaction(self, tx_id: str, branch: str) -> str:
        if tx_id not in self._pending:
            raise TransactionError(f"unknown transaction {tx_id!r}")
        pending = self._pending.pop(tx_id)
        if pending.branch != branch:
            raise TransactionError(f"transaction {tx_id} is for {pending.branch!r}, not {branch!r}")

        clauses = [
            clause
            for write in pending.staged
            if (clause := _graph_to_insert_clause(write.graph_iri, write.graph))
        ]
        if not clauses:
            return f"urn:rtm:commit/empty-{tx_id}"

        update_body = ("INSERT DATA {\n" + "\n".join(clauses) + "\n}").encode("utf-8")
        url = self._url(
            "orgs", self._config.org, "repos", self._config.repo, "branches", branch, "update"
        )
        self._request("POST", url, body=update_body, content_type="application/sparql-update")
        return f"urn:rtm:commit/{tx_id}"

    def abort_transaction(self, tx_id: str, branch: str) -> None:
        del branch
        self._pending.pop(tx_id, None)

    def read_graph(self, branch: str, graph_iri: str) -> Graph:
        # Branch-is-graph: ``graph_iri`` is informational only. Adopters who
        # partition by Flexo branch (ADCS pattern) map the partition IRI to
        # the branch name before calling. See flexo-rtm-research#22.
        del graph_iri
        query = "CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }"
        url = self._url(
            "orgs", self._config.org, "repos", self._config.repo, "branches", branch, "query"
        )
        _, payload = self._request(
            "POST",
            url,
            body=query.encode("utf-8"),
            content_type="application/sparql-query",
            accept="text/turtle",
        )
        g = Graph()
        if payload.strip():
            g.parse(data=payload.decode("utf-8"), format="turtle")
        return g

    def list_graphs(self, branch: str) -> list[str]:
        query = "SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } }"
        url = self._url(
            "orgs", self._config.org, "repos", self._config.repo, "branches", branch, "query"
        )
        _, payload = self._request(
            "POST",
            url,
            body=query.encode("utf-8"),
            content_type="application/sparql-query",
            accept="application/sparql-results+json",
        )
        try:
            data = json.loads(payload)
        except ValueError:
            return []
        graphs = data.get("results", {}).get("bindings", [])
        return sorted(b["g"]["value"] for b in graphs if "g" in b)

    def create_branch(self, name: str, *, from_branch: str = "master") -> None:
        extra = f" .\n<> <{_MMS_REF}> <./{from_branch}>"
        self._put_resource(
            self._url("orgs", self._config.org, "repos", self._config.repo, "branches", name),
            title=name,
            extra_body=extra,
        )

    def list_branches(self) -> list[str]:
        url = self._url("orgs", self._config.org, "repos", self._config.repo, "branches")
        _, payload = self._request("GET", url, accept="text/turtle")
        g = Graph()
        if payload.strip():
            g.parse(data=payload.decode("utf-8"), format="turtle")
        names: set[str] = set()
        for subject in g.subjects():
            iri = str(subject)
            if "/branches/" in iri:
                names.add(iri.rsplit("/", 1)[-1])
        return sorted(names)

    def merge(self, *, source: str, target: str, policy: MergePolicyHints) -> MergeResult:
        del source, target, policy
        return MergeResult(
            ok=False,
            detail="live merge is deferred — slice 10 composes via attestations, not Flexo merges",
        )


__all__ = ["FlexoConfig", "FlexoHttpClient"]
