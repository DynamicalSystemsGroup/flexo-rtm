# SPDX-License-Identifier: Apache-2.0
"""Live interop: GitHub identity adapter accepts real api.github.com payloads.

Sister test to ``tests/integration/flexo/test_live_smoke.py`` — the lesson
from flexo-rtm-research#20/#21/#22 is that adapter divergences only surface
against real upstream. This fetches a stable public GitHub user
(``octocat``, GitHub's canonical test/example account) and asserts that
:func:`oracle.identity.adapters.github.project_github_user` produces
well-formed projection RDF.

Auth-free (uses the public unauthenticated REST API; rate-limited at 60
req/hour per IP, which is fine for a single test).
"""

from __future__ import annotations

import json
import urllib.request

import pytest
from oracle.identity.adapters.github import project_github_user
from rdflib import FOAF, RDF, Namespace, URIRef

pytestmark = pytest.mark.network

RTM = Namespace("https://flexo-rtm.dev/ontology#")
STABLE_LOGIN = "octocat"


def _fetch_user(login: str) -> dict:
    req = urllib.request.Request(  # noqa: S310 — fixed api.github.com URL
        f"https://api.github.com/users/{login}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "flexo-rtm-live-test",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as r:  # noqa: S310
        payload = r.read()
    parsed = json.loads(payload)
    assert isinstance(parsed, dict)
    return parsed


def test_live_octocat_projects_to_well_formed_rdf() -> None:
    payload = _fetch_user(STABLE_LOGIN)
    assert payload.get("login") == STABLE_LOGIN, (
        f"unexpected api.github.com payload shape; got login={payload.get('login')!r}"
    )

    g = project_github_user(payload)

    person = URIRef(f"https://flexo-rtm.dev/identity/github/{STABLE_LOGIN}")
    assert (person, RDF.type, FOAF.Person) in g, (
        "projection missing FOAF.Person typing"
    )

    ext_ids = [str(o) for o in g.objects(person, RTM.hasExternalIdentity)]
    assert f"github:{STABLE_LOGIN}" in ext_ids, (
        f"projection missing github: external-identity literal; got {ext_ids!r}"
    )
