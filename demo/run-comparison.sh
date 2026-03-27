#!/bin/bash
# Compare Claude Code reviews with and without mined Domino rules.
# Run from the repo root: bash demo/run-comparison.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEMO_FILE="$REPO_ROOT/demo/bad-code.tsx"
RULES_DIR="$REPO_ROOT/output/.claude"
PROMPT="Review bad-code.tsx for issues a PR reviewer would flag. Be specific about what to fix and why."

CLEAN_DIR=$(mktemp -d)
RULES_DEMO_DIR=$(mktemp -d)

cleanup() { rm -rf "$CLEAN_DIR" "$RULES_DEMO_DIR"; }
trap cleanup EXIT

cp "$DEMO_FILE" "$CLEAN_DIR/"
cp "$DEMO_FILE" "$RULES_DEMO_DIR/"
cp -r "$RULES_DIR" "$RULES_DEMO_DIR/.claude"

echo "============================================"
echo "  WITHOUT rules (baseline Claude)"
echo "============================================"
echo ""
cd "$CLEAN_DIR"
claude --print "$PROMPT" 2>/dev/null | tee "$REPO_ROOT/demo/review-without-rules.md"

echo ""
echo ""
echo "============================================"
echo "  WITH rules (mined Domino patterns)"
echo "============================================"
echo ""
cd "$RULES_DEMO_DIR"
claude --print "$PROMPT" 2>/dev/null | tee "$REPO_ROOT/demo/review-with-rules.md"

echo ""
echo ""
echo "============================================"
echo "  Done. Results saved to:"
echo "    demo/review-without-rules.md"
echo "    demo/review-with-rules.md"
echo "============================================"
