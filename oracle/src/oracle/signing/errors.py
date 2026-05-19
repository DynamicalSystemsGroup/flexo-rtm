# SPDX-License-Identifier: Apache-2.0
"""Signing-layer error types."""

from __future__ import annotations


class VerificationError(RuntimeError):
    """A signature did not verify, or a recorded envelope failed structural checks."""


class OptionalDependencyMissing(ImportError):
    """The optional extra needed for this profile is not installed.

    The message names the ``pip install`` extra to add (e.g. ``flexo-rtm[cosign]``).
    """


__all__ = ["OptionalDependencyMissing", "VerificationError"]
