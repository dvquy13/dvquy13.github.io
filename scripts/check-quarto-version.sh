#!/usr/bin/env bash
# Check that the local Quarto version matches the version pinned in CI.
# Reads the pinned version from .github/workflows/publish.yml.

set -euo pipefail

WORKFLOW="$(dirname "$0")/../.github/workflows/publish.yml"

PINNED=$(grep 'version:' "$WORKFLOW" | grep -v '#' | head -1 | sed 's/.*version: *//' | tr -d ' "')
LOCAL=$(quarto --version 2>/dev/null || echo "not found")

if [[ "$LOCAL" == "not found" ]]; then
  echo "✗ Quarto is not installed"
  exit 1
fi

if [[ "$LOCAL" != "$PINNED" ]]; then
  echo "✗ Quarto version mismatch: local=$LOCAL, CI pinned=$PINNED"
  echo "  Update local Quarto or change the version in .github/workflows/publish.yml"
  exit 1
fi

echo "✓ Quarto version OK ($LOCAL)"
