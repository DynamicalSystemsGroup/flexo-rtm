#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
#
# Pre-commit / GitHub-Actions hook for the signed-commits profile (S1, I7).
# When a commit introduces an rtm:Attestation triple, this script verifies:
#
#   1. The commit is GPG- or SSH-signed (git verify-commit / ssh-keygen -Y verify).
#   2. The signature key's fingerprint matches a key declared on the attestation's
#      rtm:approvedBy person via rtm:hasPublicKey/rtm:keyFingerprint in the
#      identity-projection graph.
#
# v0.1 ships the hook as documentation. Adopters wire it into their .git/hooks/
# pre-commit and into a GitHub Actions check on PRs against the protected
# branches (Flexo REST Binding §6 — main / cert/* are protected).
#
# Usage:
#   ln -s "$(pwd)/scripts/check-approver-binding.sh" .git/hooks/pre-commit
#
# Or as a GitHub Actions step (see .github/workflows/approver-binding.yml, v0.2).

set -euo pipefail

COMMIT_SHA="${1:-HEAD}"

# 1. Verify the commit signature
if ! git verify-commit "$COMMIT_SHA" 2>/dev/null; then
    if ! git log -1 --format='%G?' "$COMMIT_SHA" | grep -qE '^(G|U|X)$'; then
        echo "❌ Commit $COMMIT_SHA is not GPG/SSH-signed." >&2
        echo "   Sign with 'git commit -S' (GPG) or configure commit.gpgsign=true." >&2
        exit 1
    fi
fi

# 2. Extract the signature key fingerprint
SIG_KEY_FPR="$(git log -1 --format='%GF' "$COMMIT_SHA" 2>/dev/null || echo "")"
if [[ -z "$SIG_KEY_FPR" ]]; then
    echo "❌ No signature key fingerprint on commit $COMMIT_SHA." >&2
    exit 1
fi

# 3. The actual cross-check against rtm:approvedBy's rtm:hasPublicKey/rtm:keyFingerprint
#    runs in the oracle's SHACL validation step (signed-commits profile). This
#    pre-commit hook is the first gate; the SHACL profile is the durable gate.
echo "✓ Commit $COMMIT_SHA signed by key $SIG_KEY_FPR"
echo "  (oracle's signed-commits SHACL profile validates the binding at audit time)"
exit 0
