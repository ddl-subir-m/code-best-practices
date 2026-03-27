# code-best-practices

Turn your team's PR review history into AI-native developer tooling. Mines recurring patterns from GitHub PR review threads and compiles them into Claude Code rules, Claude Code skills, and Cursor rules — so engineers get best practices embedded in their workflow automatically.

## How It Works

```
GitHub PR reviews ──→ Extract patterns ──→ patterns.json ──→ Compile ──→ Rules
                        (Claude Code)       (source of truth)              │
                                                                           ├─ .claude/rules/  (ambient)
                                                                           ├─ .claude/skills/ (on-demand)
                                                                           └─ .cursorrules    (Cursor)
```

1. **Fetch** PR review threads from GitHub via `gh api graphql`
2. **Extract** generalizable patterns using Claude Code as the analysis engine
3. **Merge** new patterns with existing ones (dedup, increment confidence)
4. **Compile** patterns into scoped rule files for Claude Code and Cursor
5. **Deploy** by copying output files to your target repo

## Quick Start

### Prerequisites

- Python 3.10+
- [GitHub CLI](https://cli.github.com/) (`gh`) authenticated with repo access
- [Claude Code](https://claude.ai/code) (for the `/extract` skill)

### Setup

```bash
git clone https://github.com/cerebrotech/code-best-practices.git
cd code-best-practices
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run Your First Extraction (via Claude Code)

The easiest way to run the full pipeline is the `/extract` skill inside Claude Code:

```
/extract --full --since 2024-01-01
```

This fetches PR threads, analyzes them for patterns, merges results, and compiles rules — all in one command. Claude Code IS the LLM engine; no API key needed.

### Run Incrementally

After the first run, just type:

```
/extract
```

This picks up where you left off — fetches only new PRs since the last run, extracts patterns, merges, and recompiles.

### Compile Only (no extraction)

If you've edited `patterns.json` manually and want to regenerate rules:

```
/extract --compile-only
```

Or directly:

```bash
python compile.py --input patterns.json --output output/
```

## CLI Reference

### extract.py

```bash
# Fetch PR review threads from GitHub
python extract.py fetch --repo cerebrotech/domino --since 2024-01-01 --batch-size 100

# Prepare analysis batches (prompts written to prompts/)
python extract.py analyze --input raw-reviews/ --output patterns.json

# Merge extracted patterns into patterns.json
python extract.py merge --input tmp/ --output patterns.json

# Auto-detect modules from file paths in patterns
python extract.py modules --input patterns.json --output modules.yaml

# Generate human-readable validation report
python extract.py report --input patterns.json --output validation-report.md
```

### compile.py

```bash
# Generate rules from patterns
python compile.py --input patterns.json --output output/

# Merge with existing Cursor rules (preserves hand-written rules)
python compile.py --input patterns.json --output output/ --cursorrules-merge /path/to/.cursorrules
```

## Output Structure

```
output/
├── .claude/
│   ├── rules/
│   │   ├── global-practices.md          # Cross-cutting rules (3+ modules)
│   │   ├── apps-practices.md            # Rules specific to /apps/
│   │   ├── server-practices.md          # Rules specific to /server/
│   │   ├── extensions-practices.md      # Rules specific to /extensions/
│   │   └── ...                          # One per module with 5+ patterns
│   └── skills/
│       └── {topic}/SKILL.md             # On-demand skills (procedural patterns)
└── .cursorrules                         # Global rules for Cursor (merged)
```

### How Rules Are Scoped

Rules are grouped by **module** (derived from file paths in PR threads), not just by category. An engineer working on `/apps/` gets apps-specific patterns; someone working on `/compute-grid/` gets compute patterns. Patterns appearing in 3+ modules are promoted to `global-practices.md`.

### Ambient vs Active

- **Ambient rules** (`.claude/rules/`) are loaded automatically by Claude Code on every interaction. Engineers don't need to do anything.
- **Active skills** (`.claude/skills/`) are invoked explicitly via `/skill-name`. Only created for procedural patterns (setup guides, workflows, checklists).

## Deploying Rules to Your Repo

After running the pipeline:

```bash
# Copy generated rules to your target repo
cp -r output/.claude/ /path/to/your-repo/.claude/
cp output/.cursorrules /path/to/your-repo/.cursorrules

# Commit and push
cd /path/to/your-repo
git add .claude/ .cursorrules
git commit -m "Update AI coding rules from PR review mining"
git push
```

Engineers get the rules automatically when they pull.

## Pattern Schema

Each pattern in `patterns.json` follows this schema:

```json
{
  "id": "fail-explicitly-not-silently",
  "rule": "When a method encounters an unsupported type or impossible state, throw an explicit error rather than silently returning.",
  "trigger": "Adding a match/switch over types or handling optional lookups",
  "rationale": "Silent returns mask bugs and make debugging harder downstream.",
  "good_example": "throw new IllegalStateException(\"Unsupported: \" + t)",
  "bad_example": "return Optional.empty()",
  "source_prs": ["#47189", "#47216"],
  "scope": "error-handling",
  "modules": ["apps", "server"],
  "mode": "ambient",
  "confidence": 0.3,
  "review_count": 3,
  "status": "active"
}
```

| Field | Description |
|-------|-------------|
| `id` | Kebab-case identifier |
| `rule` | One-sentence best practice |
| `trigger` | When this rule applies |
| `rationale` | Why it matters |
| `good_example` | Correct code example (nullable) |
| `bad_example` | Incorrect code example (nullable) |
| `source_prs` | PR numbers where this pattern was observed |
| `scope` | Category (error-handling, performance, api-design, etc.) |
| `modules` | Repo modules where this applies (apps, server, etc.) |
| `mode` | `ambient` (always-on rule) or `active` (on-demand skill) |
| `confidence` | 0.0-1.0, computed as `min(1.0, review_count / 10)` |
| `review_count` | Number of distinct PRs where this was flagged |
| `status` | `active`, `deprecated`, or `rejected` |

## Project Structure

```
code-best-practices/
├── extract.py                    # Extraction pipeline (fetch, analyze, merge)
├── compile.py                    # Output compiler (JSON -> rules/skills)
├── patterns.json                 # Source of truth — all mined patterns
├── state.json                    # Extraction state (last run date, progress)
├── modules.yaml                  # Auto-generated module mapping
├── validation-report.md          # Human-readable pattern report
├── prompts/
│   └── extract-patterns-v1.md    # Versioned extraction prompt
├── raw-reviews/                  # Fetched PR review threads (one JSON per PR)
├── tmp/                          # Intermediate batch results
├── output/                       # Generated rules (copy to target repo)
├── tests/
│   ├── conftest.py               # Shared test fixtures
│   ├── test_compile.py           # Compiler tests (10 tests)
│   └── test_extract.py           # Schema validation tests (8 tests)
├── .claude/
│   └── skills/
│       └── extract-patterns/
│           └── SKILL.md          # /extract skill for Claude Code
├── conductor.json                # Conductor workspace config
├── conductor-prompts.md          # Parallel build prompts for Conductor
├── CLAUDE.md                     # Claude Code project context
└── README.md                     # This file
```

## Testing

```bash
source .venv/bin/activate
pytest tests/ -v
```

18 tests covering:
- Compiler: module grouping, global patterns, special characters, skills generation, cursor rules merge, schema validation
- Extract: patterns.json schema, state.json schema, modules.yaml schema

## How It Was Built

This project was designed and built in a single Claude Code session:

1. **`/office-hours`** — structured the problem, challenged premises, produced the design doc
2. **`/plan-eng-review`** — reviewed architecture, reduced scope (dropped external dependencies), added module scoping and incremental extraction
3. **Conductor** — 4 parallel workspaces built extract.py, compile.py, tests, and seed data simultaneously
4. **Phase 0 validation** — extracted 9 recurring patterns from 20 PRs (2 weeks) to prove the approach before scaling

## Adapting for Your Repo

To use this for a different GitHub repo:

1. Clone this project
2. Run `/extract --full --repo your-org/your-repo --since 2024-01-01`
3. The pipeline auto-detects modules from your repo's directory structure
4. Copy `output/` to your target repo

The only thing specific to cerebrotech/domino is `patterns.json` and `state.json` — everything else is repo-agnostic.
