#!/bin/bash
# Compare Claude Code generation with and without mined Domino rules.
# Run from the repo root: bash demo/run-codegen-comparison.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RULES_DIR="$REPO_ROOT/output/.claude"
PROMPT="Write the code for a React component called ProjectHealthDashboard (frontend/ProjectHealthDashboard.tsx) that:
- Fetches a list of projects from the API endpoint /v4/projects
- Shows each project in a card with its name, status (active/archived/failed), and last updated date
- Status should be color-coded (green for active, red for failed, gray for archived)
- Cards should be clickable, navigating to /projects/{id}/overview
- Include a search input to filter projects by name
- Show a loading spinner while fetching
- Show an error message if the fetch fails
- Sort projects by last updated date using lodash

Write production-ready TypeScript. Use whatever libraries and patterns you think are appropriate for a Domino Data Lab frontend codebase.

Output ONLY the code as a single fenced code block. No explanations before or after."

CLEAN_DIR=$(mktemp -d)
RULES_DEMO_DIR=$(mktemp -d)

cleanup() { rm -rf "$CLEAN_DIR" "$RULES_DEMO_DIR"; }
trap cleanup EXIT

# Create frontend/ dirs so glob-scoped rules load correctly
mkdir -p "$CLEAN_DIR/frontend" "$RULES_DEMO_DIR/frontend"
cp -r "$RULES_DIR" "$RULES_DEMO_DIR/.claude"

echo "============================================"
echo "  WITHOUT rules (baseline Claude)"
echo "============================================"
echo ""
cd "$CLEAN_DIR"
claude --print "$PROMPT" 2>/dev/null | tee "$REPO_ROOT/demo/codegen-without-rules.md"

echo ""
echo ""
echo "============================================"
echo "  WITH rules (mined Domino patterns)"
echo "============================================"
echo ""
cd "$RULES_DEMO_DIR"
claude --print "$PROMPT" 2>/dev/null | tee "$REPO_ROOT/demo/codegen-with-rules.md"

echo ""
echo ""
echo "============================================"
echo "  Done. Results saved to:"
echo "    demo/codegen-without-rules.md"
echo "    demo/codegen-with-rules.md"
echo "============================================"
