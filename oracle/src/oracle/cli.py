# SPDX-License-Identifier: Apache-2.0
"""flexo-rtm CLI. Slice 1 ships --help and --version only; certify/audit land in slice 11."""

from __future__ import annotations

import typer

from oracle import __version__

app = typer.Typer(
    name="flexo-rtm",
    help="Verifiable self-certification oracle for bidirectional requirements traceability.",
    no_args_is_help=True,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """flexo-rtm root command."""


if __name__ == "__main__":
    app()
