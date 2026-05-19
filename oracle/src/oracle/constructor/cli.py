# SPDX-License-Identifier: Apache-2.0
"""Constructor Typer sub-app.

Each command:

1. Resolves the engineer IRI (override or git-config-derived).
2. Loads (or creates) the local session at ``--session-dir/state.trig``.
3. Builds RDF via :mod:`oracle.constructor.builders`.
4. Commits atomically through the existing ``commit_atomic_batch`` write
   path against the session's ``InMemoryFlexoBackend``.
5. Auto-persists session state to disk.

Every interactive prompt has a matching ``--flag`` override; when all
required flags are present the command runs non-interactively, which is
how the engineer's LLM (Claude Code etc.) invokes the constructor as a
tool.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated
from uuid import uuid4

import typer
from rdflib import URIRef

from oracle.constructor.builders import (
    build_addresses_edge,
    build_artifact,
    build_attestation,
    build_deprecation,
    build_requirement,
)
from oracle.constructor.identity import IdentityError, resolve_engineer_iri
from oracle.constructor.push import push_session
from oracle.constructor.session import SessionContext, default_state_path
from oracle.storage.adapter import commit_atomic_batch
from oracle.storage.flexo_client import FlexoConfig, FlexoHttpClient
from oracle.storage.iri_scheme import PARTITION_GRAPHS

constructor_app = typer.Typer(
    name="constructor",
    help=(
        "Engineer-facing tooling: produce flexo-rtm RDF interactively, "
        "commit locally, push to Flexo."
    ),
    no_args_is_help=True,
)


def _session(session_dir: Path | None) -> SessionContext:
    if session_dir is None:
        # Fall back to ~/.flexo-rtm/sessions/<id>/state.trig based on the
        # current engineer's email + cwd. Engineers who haven't set
        # git config user.email get a clear error from resolve_engineer_iri.
        try:
            iri = resolve_engineer_iri()
        except IdentityError:
            iri = URIRef("urn:rtm:engineer/anonymous")
        path = default_state_path(email=str(iri), cwd=Path.cwd())
        return SessionContext(state_path=path)
    return SessionContext(state_path=session_dir / "state.trig")


def _commit_local(session: SessionContext, partition: str, new_triples) -> str:  # type: ignore[no-untyped-def]
    """Merge ``new_triples`` into the existing partition and commit atomically.

    The hot-path ``commit_atomic_batch`` replaces a partition's graph wholesale
    (its design: build the full graph once, commit once). The constructor needs
    incremental accumulation, so we read-merge-write at the partition level
    here — the underlying transaction is still atomic and the activity graph
    still threads PROV correctly.
    """
    partition_iri = PARTITION_GRAPHS[partition]
    existing = session.backend.read_graph(session.branch, partition_iri)
    merged = Graph()
    for triple in existing:
        merged.add(triple)
    for triple in new_triples:
        merged.add(triple)
    result = commit_atomic_batch(
        session.backend,
        branch=session.branch,
        writes={partition_iri: merged},
    )
    session.persist()
    return result.commit_iri


# --------------------------------------------------------------------- new-requirement


@constructor_app.command("new-requirement")
def new_requirement(
    iri: Annotated[
        str, typer.Argument(help="IRI of the new requirement, e.g. https://rtm.example/req/REQ-001")
    ],
    title: Annotated[str, typer.Option("--title", "-t", help="Short human-readable label.")],
    statement: Annotated[
        str | None,
        typer.Option("--statement", "-s", help="Full requirement statement (optional)."),
    ] = None,
    session_dir: Annotated[
        Path | None,
        typer.Option(
            "--session-dir",
            help="Override the session directory (default: ~/.flexo-rtm/sessions/<id>/).",
        ),
    ] = None,
) -> None:
    """Create an rtm:Requirement and stage it into the local session."""
    session = _session(session_dir)
    graph = build_requirement(iri=URIRef(iri), title=title, statement=statement)
    commit_iri = _commit_local(session, "model", graph)
    typer.echo(f"created Requirement {iri} (local commit {commit_iri})")


# --------------------------------------------------------------------- new-artifact


@constructor_app.command("new-artifact")
def new_artifact(
    iri: Annotated[
        str, typer.Argument(help="IRI of the new artifact, e.g. https://rtm.example/art/proof-1")
    ],
    title: Annotated[str, typer.Option("--title", "-t", help="Short human-readable label.")],
    content_hash: Annotated[
        str | None,
        typer.Option("--content-hash", help='Artifact content hash, e.g. "sha256:abc…".'),
    ] = None,
    git_commit: Annotated[
        str | None,
        typer.Option("--git-commit", help="Git commit SHA carrying the artifact."),
    ] = None,
    session_dir: Annotated[
        Path | None, typer.Option("--session-dir", help="Override the session directory.")
    ] = None,
    on_conflict: Annotated[
        str,
        typer.Option(
            "--on-conflict",
            help="If this artifact IRI already has a different content hash: "
            "'prompt' (default), 'deprecate', 'keep', or 'abort'.",
        ),
    ] = "prompt",
) -> None:
    """Create an rtm:Artifact and stage it into the local session.

    When the artifact IRI already exists in the session with a different
    content hash, surface all attestations that reference it and ask the
    engineer whether each should be deprecated. The judgement-bearing
    question is "does the change invalidate the prior judgement?" The
    engineer answers per-attestation.
    """
    session = _session(session_dir)
    target = URIRef(iri)
    conflicts = _detect_hash_conflict(session, target, new_content_hash=content_hash)
    if conflicts:
        _handle_conflicts(session, conflicts, on_conflict)

    graph = build_artifact(
        iri=target,
        title=title,
        content_hash=content_hash,
        git_commit=git_commit,
    )
    commit_iri = _commit_local(session, "model", graph)
    typer.echo(f"created Artifact {iri} (local commit {commit_iri})")


def _detect_hash_conflict(
    session: SessionContext,
    artifact: URIRef,
    *,
    new_content_hash: str | None,
) -> list[URIRef]:
    """Return attestations whose rtm:appliesTo references ``artifact`` when
    the artifact already exists with a different content hash."""
    if new_content_hash is None:
        return []
    from rdflib import Literal

    model = session.backend.read_graph(session.branch, PARTITION_GRAPHS["model"])
    from rdflib import Namespace

    rtm = Namespace("https://flexo-rtm.dev/ontology#")
    existing_hashes = list(model.objects(artifact, rtm.hasContentHash))
    if not existing_hashes:
        return []
    if any(str(h) == new_content_hash for h in existing_hashes):
        return []  # same hash, no conflict
    # The hash changed; collect attestations that reference this artifact.
    attestations = session.backend.read_graph(session.branch, PARTITION_GRAPHS["attestations"])
    affected: list[URIRef] = []
    for att in attestations.subjects(rtm.appliesTo, artifact):
        # type guard: subjects can be BNode | URIRef; we only care about IRIs
        if isinstance(att, URIRef):
            affected.append(att)
    del Literal  # silence
    return affected


def _handle_conflicts(
    session: SessionContext,
    affected: list[URIRef],
    on_conflict: str,
) -> None:
    if on_conflict not in {"prompt", "deprecate", "keep", "abort"}:
        raise typer.BadParameter(
            f"--on-conflict must be one of prompt/deprecate/keep/abort; got {on_conflict!r}"
        )
    if on_conflict == "abort":
        typer.echo(
            f"abort: {len(affected)} prior attestations would be affected "
            "by this content-hash change."
        )
        raise typer.Exit(code=1)
    if on_conflict == "keep":
        typer.echo(
            f"keep: {len(affected)} prior attestations remain valid by your stated judgement."
        )
        return
    deprecations = Graph()
    if on_conflict == "deprecate":
        activity = URIRef(f"urn:rtm:commit/{uuid4()}")
        for att in affected:
            deprecations += build_deprecation(
                target_attestation=att, invalidating_activity=activity
            )
    else:  # prompt
        typer.echo(
            f"{len(affected)} prior attestation(s) reference this artifact "
            "with the previous content hash."
        )
        for att in affected:
            choice = (
                typer.prompt(
                    f"  {att}: [d]eprecate / [k]eep / [a]bort",
                    default="d",
                )
                .strip()
                .lower()
            )
            if choice.startswith("a"):
                typer.echo("aborting; no triples committed.")
                raise typer.Exit(code=1)
            if choice.startswith("k"):
                reason = typer.prompt("    reason for keeping (required)")
                if not reason.strip():
                    typer.echo("keep requires a reason; aborting.")
                    raise typer.Exit(code=1)
                continue
            reason = typer.prompt(
                "    reason for deprecating (optional, press enter to skip)", default=""
            )
            activity = URIRef(f"urn:rtm:commit/{uuid4()}")
            deprecations += build_deprecation(
                target_attestation=att,
                invalidating_activity=activity,
                reason=reason or None,
            )
    if len(deprecations) > 0:
        _commit_local(session, "attestations", deprecations)


# Need Graph in scope for _handle_conflicts; deferred import to keep the
# module top-level clean of rdflib boilerplate.
from rdflib import Graph  # noqa: E402

# --------------------------------------------------------------------- link


@constructor_app.command("link")
def link(
    artifact: Annotated[str, typer.Option("--artifact", "-a", help="Artifact IRI.")],
    requirement: Annotated[str, typer.Option("--requirement", "-r", help="Requirement IRI.")],
    session_dir: Annotated[
        Path | None, typer.Option("--session-dir", help="Override the session directory.")
    ] = None,
) -> None:
    """Stage an rtm:addresses edge (artifact → requirement)."""
    session = _session(session_dir)
    graph = build_addresses_edge(artifact=URIRef(artifact), requirement=URIRef(requirement))
    commit_iri = _commit_local(session, "model", graph)
    typer.echo(f"linked {artifact} -> {requirement} (local commit {commit_iri})")


# --------------------------------------------------------------------- attest


_ATTEST_PROMPT_FOR_CLASS = {
    "SatisfactionAttestation": "Do you, the engineer, judge the requirement satisfied? (y/N)",
    "AdequacyAttestation": "Is the model representation adequate for this claim? (y/N)",
    "SufficiencyAttestation": "Is the evidence sufficient to support this claim? (y/N)",
}


@constructor_app.command("attest")
def attest(
    applies_to: Annotated[
        str,
        typer.Option(
            "--applies-to",
            help=(
                "Subject IRI: usually a Requirement (Satisfaction) or an "
                "Artifact (Adequacy/Sufficiency)."
            ),
        ),
    ],
    attestation_class: Annotated[
        str,
        typer.Option(
            "--class",
            "-c",
            help="One of SatisfactionAttestation, AdequacyAttestation, SufficiencyAttestation.",
        ),
    ],
    outcome: Annotated[
        str | None,
        typer.Option(
            "--outcome",
            help="pass / fail / deferred — skip the prompt when set.",
        ),
    ] = None,
    reason: Annotated[
        str | None,
        typer.Option(
            "--reason",
            help=(
                "Free-text reasoning (attached as rdfs:comment). "
                "If omitted, prompted interactively."
            ),
        ),
    ] = None,
    engineer_iri: Annotated[
        str | None,
        typer.Option(
            "--engineer-iri",
            help="Override the approver IRI; default derives from git config user.email.",
        ),
    ] = None,
    session_dir: Annotated[
        Path | None, typer.Option("--session-dir", help="Override the session directory.")
    ] = None,
) -> None:
    """Drive an interactive signoff and emit one attestation.

    The engineer is asked the class-specific question (adequacy /
    sufficiency / satisfaction) and a free-text reason. The constructor
    binds the approver IRI from ``--engineer-iri`` or git config, mints
    a fresh attestation IRI, and commits to the local session.
    """
    if attestation_class not in _ATTEST_PROMPT_FOR_CLASS:
        raise typer.BadParameter(
            f"--class must be one of {sorted(_ATTEST_PROMPT_FOR_CLASS)}; got {attestation_class!r}"
        )

    session = _session(session_dir)
    approver = resolve_engineer_iri(override=engineer_iri)

    if outcome is None:
        agreed = typer.confirm(_ATTEST_PROMPT_FOR_CLASS[attestation_class], default=False)
        outcome = "pass" if agreed else "fail"
    if outcome not in {"pass", "fail", "deferred", "deprecated"}:
        raise typer.BadParameter(f"--outcome must be pass/fail/deferred; got {outcome!r}")

    if reason is None:
        reason = typer.prompt("reason (optional, press enter to skip)", default="")
    reason = reason.strip() or None

    iri = URIRef(f"urn:rtm:attest/{uuid4()}")
    graph = build_attestation(
        iri=iri,
        attestation_class=attestation_class,  # type: ignore[arg-type]
        approved_by=approver,
        applies_to=URIRef(applies_to),
        status=outcome,  # type: ignore[arg-type]
        timestamp=datetime.now(UTC),
        reason=reason,
    )
    commit_iri = _commit_local(session, "attestations", graph)
    typer.echo(f"created {attestation_class} {iri} (local commit {commit_iri})")


# --------------------------------------------------------------------- deprecate


@constructor_app.command("deprecate")
def deprecate(
    attestation_iri: Annotated[
        str,
        typer.Argument(help="IRI of the attestation being invalidated."),
    ],
    reason: Annotated[
        str | None,
        typer.Option(
            "--reason",
            help="Why the prior judgement no longer holds (required).",
        ),
    ] = None,
    session_dir: Annotated[
        Path | None, typer.Option("--session-dir", help="Override the session directory.")
    ] = None,
) -> None:
    """Mark an existing attestation as invalidated.

    The judgement-bearing claim is "the prior approval no longer holds because
    of [reason]." Emits one ``prov:wasInvalidatedBy`` triple linking the
    attestation to a fresh activity; the reason attaches to that activity so
    later readers can distinguish the original attestation's commentary
    from the deprecation explanation. Reason is mandatory.
    """
    if not reason or not reason.strip():
        typer.echo(
            "error: --reason is required (state why the prior judgement is invalidated).", err=True
        )
        raise typer.Exit(code=2)
    session = _session(session_dir)
    activity = URIRef(f"urn:rtm:commit/{uuid4()}")
    graph = build_deprecation(
        target_attestation=URIRef(attestation_iri),
        invalidating_activity=activity,
        reason=reason.strip(),
    )
    commit_iri = _commit_local(session, "attestations", graph)
    typer.echo(f"deprecated {attestation_iri} via activity {activity} (local commit {commit_iri})")


# --------------------------------------------------------------------- push


@constructor_app.command("push")
def push(
    url: Annotated[
        str,
        typer.Option(
            "--url",
            envvar="FLEXO_URL",
            help="Flexo MMS base URL (e.g., https://try-layer1.starforge.app/).",
        ),
    ],
    org: Annotated[str, typer.Option("--org", help="Flexo org slug.")],
    repo: Annotated[str, typer.Option("--repo", help="Flexo repo slug.")],
    branch: Annotated[
        str,
        typer.Option("--branch", help="Target Flexo branch (e.g., engineering/zargham)."),
    ] = "master",
    token: Annotated[
        str,
        typer.Option(
            "--token",
            envvar="FLEXO_TOKEN",
            help="Bearer token (typically passed via FLEXO_TOKEN env var, not as a flag).",
        ),
    ] = "",
    scope_iri: Annotated[
        str | None,
        typer.Option(
            "--scope",
            help="Active rtm:Scope IRI recorded on the push activity (F4 of Design Spec).",
        ),
    ] = None,
    session_dir: Annotated[
        Path | None,
        typer.Option("--session-dir", help="Override the session directory."),
    ] = None,
    archive_on_success: Annotated[
        bool,
        typer.Option(
            "--archive/--keep",
            help="Archive the local session after a successful push (default) or keep it.",
        ),
    ] = True,
) -> None:
    """Push the local session to a remote Flexo backend (one atomic commit).

    Reads every non-empty data partition from the local session and emits
    a single ``commit_atomic_batch`` against the remote. The local activity
    log is not pushed; the remote builds its own activity for the push.
    """
    if not token:
        typer.echo("error: bearer token required; pass --token or set FLEXO_TOKEN.", err=True)
        raise typer.Exit(code=2)

    session = _session(session_dir)
    config = FlexoConfig(base_url=url, org=org, repo=repo, token=token)
    remote = FlexoHttpClient(config)
    try:
        approver = resolve_engineer_iri()
    except IdentityError:
        approver = URIRef("urn:rtm:engineer/anonymous")
    result = push_session(
        session,
        remote=remote,
        branch=branch,
        scope_iri=scope_iri,
        associated_with=str(approver),
    )
    typer.echo(f"pushed to {url} (branch {branch}; commit {result.commit_iri})")
    if archive_on_success:
        archived = session.archive()
        typer.echo(f"archived session to {archived}")


# --------------------------------------------------------------------- status / show


@constructor_app.command("status")
def status(
    session_dir: Annotated[
        Path | None, typer.Option("--session-dir", help="Override the session directory.")
    ] = None,
) -> None:
    """List IRIs in the local session, marking any with prov:wasInvalidatedBy as deprecated."""
    from rdflib import PROV, RDF, RDFS

    session = _session(session_dir)
    rtm = "https://flexo-rtm.dev/ontology#"
    model = session.backend.read_graph(session.branch, PARTITION_GRAPHS["model"])
    attestations = session.backend.read_graph(session.branch, PARTITION_GRAPHS["attestations"])

    typer.echo(f"session: {session.state_path}")
    for subj in sorted({str(s) for s in model.subjects(RDF.type, URIRef(rtm + "Requirement"))}):
        label = next(model.objects(URIRef(subj), RDFS.label), "")
        typer.echo(f"  Requirement   {subj}  {label}")
    for subj in sorted({str(s) for s in model.subjects(RDF.type, URIRef(rtm + "Artifact"))}):
        label = next(model.objects(URIRef(subj), RDFS.label), "")
        typer.echo(f"  Artifact      {subj}  {label}")
    for s, _, o in sorted(model.triples((None, URIRef(rtm + "addresses"), None))):
        typer.echo(f"  addresses     {s} -> {o}")
    for subj in sorted(
        {
            str(s)
            for s in attestations.subjects(RDF.type, None)
            if str(s).startswith("urn:rtm:attest/")
        }
    ):
        deprecated = any(attestations.triples((URIRef(subj), PROV.wasInvalidatedBy, None)))
        marker = " [DEPRECATED]" if deprecated else ""
        typer.echo(f"  attest        {subj}{marker}")


@constructor_app.command("show")
def show(
    iri: Annotated[str, typer.Argument(help="IRI to dump as Turtle.")],
    session_dir: Annotated[
        Path | None, typer.Option("--session-dir", help="Override the session directory.")
    ] = None,
) -> None:
    """Print all triples for IRI from the local session, in human Turtle."""
    session = _session(session_dir)
    target = URIRef(iri)
    sub = Graph()
    for partition in PARTITION_GRAPHS.values():
        g = session.backend.read_graph(session.branch, partition)
        for s, p, o in g:
            if s == target or o == target:
                sub.add((s, p, o))
    typer.echo(sub.serialize(format="turtle"))


__all__ = ["constructor_app"]
