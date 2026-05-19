# SPDX-License-Identifier: Apache-2.0
"""HTTPS client for Flexo MMS Layer 1 — Flexo REST Binding §3 + §9 + §10.

Used by ``@pytest.mark.live`` tests against a real Flexo deployment. Not used
in the default ``pytest -q`` (which routes through :class:`InMemoryFlexoBackend`).

Errors per §10 are surfaced verbatim — no retry loop in v0.1; adopters that
need retry/backoff wrap this client externally.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from urllib.error import HTTPError, URLError

from rdflib import Graph

from oracle.storage.backend import MergePolicyHints, MergeResult, TransactionError


@dataclass(frozen=True)
class FlexoConfig:
    base_url: str
    org: str
    repo: str
    token: str
    timeout_seconds: float = 30.0


class FlexoHttpClient:
    """Thin urllib-based client for the Flexo Layer 1 REST surface."""

    def __init__(self, config: FlexoConfig) -> None:
        self._config = config

    def _url(self, *parts: str) -> str:
        encoded = "/".join(urllib.parse.quote(p, safe="") for p in parts)
        return f"{self._config.base_url.rstrip('/')}/{encoded}"

    def _headers(self, *, content_type: str | None = None) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {self._config.token}"}
        if content_type is not None:
            headers["Content-Type"] = content_type
        return headers

    def _request(
        self,
        method: str,
        url: str,
        *,
        body: bytes | None = None,
        content_type: str | None = None,
    ) -> bytes:
        request = urllib.request.Request(  # noqa: S310 — adopter controls the URL
            url, method=method, headers=self._headers(content_type=content_type), data=body
        )
        try:
            with urllib.request.urlopen(request, timeout=self._config.timeout_seconds) as response:  # noqa: S310
                payload = response.read()
                assert isinstance(payload, bytes)
                return payload
        except HTTPError as exc:
            raise TransactionError(
                f"Flexo {method} {url} → HTTP {exc.code}: {exc.read().decode('utf-8', 'replace')}"
            ) from exc
        except URLError as exc:
            raise TransactionError(f"Flexo {method} {url} failed: {exc}") from exc

    def begin_transaction(self, branch: str) -> str:
        url = self._url(
            "orgs",
            self._config.org,
            "repos",
            self._config.repo,
            "branches",
            branch,
            "transactions",
        )
        payload = self._request("POST", url)
        return str(json.loads(payload)["tx-id"])

    def write_graph(self, tx_id: str, branch: str, graph_iri: str, graph: Graph) -> None:
        url = (
            self._url(
                "orgs",
                self._config.org,
                "repos",
                self._config.repo,
                "branches",
                branch,
                "graphs",
                graph_iri,
            )
            + f"?tx={urllib.parse.quote(tx_id, safe='')}"
        )
        body = graph.serialize(format="nt").encode("utf-8")
        self._request("PUT", url, body=body, content_type="application/n-triples")

    def commit_transaction(self, tx_id: str, branch: str) -> str:
        url = self._url(
            "orgs",
            self._config.org,
            "repos",
            self._config.repo,
            "branches",
            branch,
            "transactions",
            tx_id,
            "commit",
        )
        payload = self._request("POST", url)
        return str(json.loads(payload)["commit-iri"])

    def abort_transaction(self, tx_id: str, branch: str) -> None:
        url = self._url(
            "orgs",
            self._config.org,
            "repos",
            self._config.repo,
            "branches",
            branch,
            "transactions",
            tx_id,
            "abort",
        )
        self._request("POST", url)

    def read_graph(self, branch: str, graph_iri: str) -> Graph:
        url = self._url(
            "orgs",
            self._config.org,
            "repos",
            self._config.repo,
            "branches",
            branch,
            "graphs",
            graph_iri,
        )
        body = self._request("GET", url)
        g = Graph()
        g.parse(data=body.decode("utf-8"), format="nt")
        return g

    def list_graphs(self, branch: str) -> list[str]:
        url = self._url(
            "orgs",
            self._config.org,
            "repos",
            self._config.repo,
            "branches",
            branch,
            "graphs",
        )
        payload = self._request("GET", url)
        data = json.loads(payload)
        graphs = data.get("graphs", [])
        return sorted(str(g) for g in graphs)

    def create_branch(self, name: str, *, from_branch: str = "main") -> None:
        url = self._url(
            "orgs",
            self._config.org,
            "repos",
            self._config.repo,
            "branches",
        )
        body = json.dumps({"name": name, "from": from_branch}).encode("utf-8")
        self._request("POST", url, body=body, content_type="application/json")

    def list_branches(self) -> list[str]:
        url = self._url("orgs", self._config.org, "repos", self._config.repo, "branches")
        payload = self._request("GET", url)
        data = json.loads(payload)
        return sorted(str(b) for b in data.get("branches", []))

    def merge(self, *, source: str, target: str, policy: MergePolicyHints) -> MergeResult:
        url = self._url("orgs", self._config.org, "repos", self._config.repo, "merges")
        body = json.dumps(
            {
                "source": source,
                "target": target,
                "policy": {
                    "verification_scope": policy.verification_scope,
                    "validation_scope": policy.validation_scope,
                },
            }
        ).encode("utf-8")
        payload = self._request("POST", url, body=body, content_type="application/json")
        data = json.loads(payload)
        return MergeResult(
            ok=bool(data.get("ok", False)),
            detail=str(data.get("detail", "")),
            conflicts=tuple(str(c) for c in data.get("conflicts", [])),
        )


__all__ = ["FlexoConfig", "FlexoHttpClient"]
