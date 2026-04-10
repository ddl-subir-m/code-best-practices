# code-best-practices

Turn your team's PR review history into AI-native developer tooling. Mines recurring patterns from GitHub PR review threads and compiles them into Claude Code rules, Claude Code skills, Claude Code hooks, and Cursor rules — so engineers get best practices embedded in their workflow automatically.

## How It Works

```
GitHub PR reviews ──→ Extract patterns ──→ patterns.json ──→ Compile ──→ Rules
                        (Claude Code)       (source of truth)              │
                                                                           ├─ .claude/rules/  (ambient)
                                                                           ├─ .claude/skills/ (on-demand)
                                                                           ├─ .claude/hooks/  (automated)
                                                                           └─ .cursor/rules/  (Cursor)
```

1. **Fetch** PR review threads from GitHub via `gh api graphql`
2. **Extract** generalizable patterns using Claude Code as the analysis engine
3. **Merge** new patterns with existing ones (dedup, increment confidence)
4. **Triage** patterns into ambient rules, active skills, or automated hooks
5. **Enrich** skill-worthy patterns with steps/examples, hook-worthy patterns with shell checks
6. **Compile** patterns into scoped rule files for Claude Code and Cursor
7. **Deploy** by copying output files to your target repo

## Quick Start

### Prerequisites

- Python 3.10+
- [GitHub CLI](https://cli.github.com/) (`gh`) authenticated with repo access
- [Claude Code](https://claude.ai/code) (for the `/extract` skill)

### Setup

```bash
git clone https://github.com/ddl-subir-m/code-best-practices.git
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

### extract package

```bash
# Fetch PR review threads from GitHub
python -m extract fetch --repo cerebrotech/domino --since 2024-01-01 --batch-size 100

# Prepare analysis batches (prompts written to tmp/prompts/)
python -m extract analyze --input raw-reviews/ --output patterns.json

# Merge extracted patterns into patterns.json
python -m extract merge --input tmp/ --output patterns.json

# Auto-detect modules from file paths in patterns
python -m extract modules --input patterns.json --output modules.yaml

# Reclassify pattern modes (ambient/active)
python -m extract reclass --input patterns.json

# Deduplicate patterns (exact ID + LLM semantic)
python -m extract dedup --input patterns.json

# Score active patterns on skill-worthiness and hook-worthiness
python -m extract triage --input patterns.json

# Enrich skill-worthy patterns with steps and examples
python -m extract enrich --input patterns.json

# Enrich hook-worthy patterns with hook metadata (event, glob, check script, message)
python -m extract enrich-hooks --input patterns.json

# Validate hook_event/hook_blocking consistency
python -m extract validate-hooks --input patterns.json

# Generate human-readable validation report
python -m extract report --input patterns.json --output validation-report.md
```

### compile.py

```bash
# Generate rules from patterns
python compile.py --input patterns.json --output output/
```

### Batch extraction

```bash
# Run historical extraction across month ranges with parallel Claude calls
./run-historical-extraction.sh 2024-04 2026-03 4
```

## Output Structure

```
output/
├── .claude/
│   ├── rules/
│   │   ├── mined-global-practices.md    # Cross-cutting rules (3+ modules)
│   │   ├── mined-apps-practices.md      # Rules specific to /apps/
│   │   ├── mined-server-practices.md    # Rules specific to /server/
│   │   └── ...                          # One per module with patterns
│   ├── skills/
│   │   └── mined-{topic}/SKILL.md       # On-demand skills (procedural patterns)
│   ├── hooks/
│   │   └── mined-{pattern-id}.sh        # Auto-triggered hook scripts
│   └── settings-hooks.json              # Hook wiring config (merge into settings.json)
└── .cursor/
    └── rules/
        ├── mined-global-practices.mdc   # Cross-cutting Cursor rules
        ├── mined-apps-practices.mdc     # Per-module Cursor rules
        └── ...                          # One .mdc per module
```

### How Rules Are Scoped

Rules are grouped by **module** (derived from file paths in PR threads), not just by category. An engineer working on `/apps/` gets apps-specific patterns; someone working on `/compute-grid/` gets compute patterns. Patterns appearing in 3+ modules are promoted to `global-practices.md`.

### Ambient vs Active vs Hook

- **Ambient rules** (`.claude/rules/`) are loaded automatically by Claude Code on every interaction. Engineers don't need to do anything.
- **Active skills** (`.claude/skills/`) are invoked explicitly via `/skill-name`. Only created for procedural patterns (setup guides, workflows, checklists).
- **Hooks** (`.claude/hooks/`) run automatically when files are edited. Used for high-severity, mechanically automatable checks (security gates, auth wrappers, secret leakage). Hooks can block edits (PreToolUse) or warn after (PostToolUse).

## Deploying Rules to Your Repo

After running the pipeline:

```bash
# Copy generated rules to your target repo
cp -r output/.claude/ /path/to/your-repo/.claude/
cp -r output/.cursor/ /path/to/your-repo/.cursor/

# Commit and push
cd /path/to/your-repo
git add .claude/ .cursor/
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
| `mode` | `ambient` (always-on rule), `active` (on-demand skill), or `hook` (automated check) |
| `confidence` | 0.0-1.0, computed as `min(1.0, review_count / 10)` |
| `review_count` | Number of distinct PRs where this was flagged |
| `status` | `active`, `deprecated`, or `rejected` |

Hook-mode patterns also include:

| Field | Description |
|-------|-------------|
| `hook_event` | `PreToolUse` (block before edit) or `PostToolUse` (warn after edit) |
| `hook_tool` | Which tool triggers it — `Edit` or `Write` |
| `hook_glob` | File glob pattern to match (e.g., `**/*Controller*.scala`) |
| `hook_check` | Shell command that detects the anti-pattern (exit 0 = violation) |
| `hook_message` | Warning message shown when the hook fires |
| `hook_blocking` | Whether the hook blocks the action or just warns |
| `hook_fp_risk` | `LOW`, `MEDIUM`, or `HIGH` — false positive risk assessment |

## Project Structure

```
code-best-practices/
├── extract/                          # Extraction pipeline package
│   ├── __init__.py                   # Re-exports for backward compat
│   ├── __main__.py                   # python -m extract entry point
│   ├── constants.py                  # Shared constants (categories, GraphQL query)
│   ├── claude.py                     # Claude CLI wrapper + JSON response parsers
│   ├── fetch.py                      # Fetch PR threads via gh api graphql
│   ├── analyze.py                    # Batch threads + build extraction prompts
│   ├── merge.py                      # Merge patterns + utilities (ID generation, dedup)
│   ├── dedup.py                      # Exact ID + LLM semantic deduplication
│   ├── modules.py                    # Auto-detect module mapping from file paths
│   ├── report.py                     # Human-readable validation report
│   ├── reclass.py                    # Reclassify pattern modes (ambient/active)
│   ├── triage.py                     # Score skill-worthiness and hook-worthiness
│   ├── enrich.py                     # Enrich skills with steps and examples
│   ├── enrich_hooks.py               # Enrich hooks with metadata + lint/fix
│   ├── validate.py                   # Validate hook consistency
│   └── cli.py                        # Argparse CLI entry point
├── compile.py                        # Output compiler (JSON -> rules/skills/hooks/mdc)
├── classify_patterns.py              # LLM-based pattern classification (rule vs skill)
├── run-historical-extraction.sh      # Batch extraction across month ranges
├── patterns.json                     # Source of truth — all mined patterns
├── state.json                        # Extraction state (last run date, progress)
├── modules.yaml                      # Auto-generated module mapping
├── validation-report.md              # Human-readable pattern report
├── prompts/
│   └── extract-patterns-v1.md        # Versioned extraction prompt
├── raw-reviews/                      # Fetched PR review threads (one JSON per PR)
├── tmp/                              # Intermediate batch results
├── output/                           # Generated rules (copy to target repo)
├── tests/
│   ├── conftest.py                   # Shared test fixtures
│   ├── test_compile.py               # Compiler tests
│   ├── test_extract.py               # Schema validation tests
│   ├── test_triage.py                # Triage pipeline tests
│   └── test_enrich.py                # Enrichment pipeline tests
├── .claude/
│   └── skills/
│       └── extract-patterns/
│           └── SKILL.md              # /extract skill for Claude Code
├── CLAUDE.md                         # Claude Code project context
└── README.md                         # This file
```

## Testing

```bash
source .venv/bin/activate
pytest tests/ -v
```

Tests covering:
- Compiler: module grouping, global patterns, special characters, skills generation, hooks generation, Cursor .mdc generation, schema validation
- Extract: patterns.json schema, state.json schema, modules.yaml schema, reclass guard
- Triage: filtering, demotion, dry-run, hook classification, error handling
- Enrich: filtering, field writing, hook enrichment, lint/fix pipeline, hook validation, error handling


## Adapting for Your Repo

To use this for a different GitHub repo:

1. Clone this project
2. Run `/extract --full --repo your-org/your-repo --since 2024-01-01`
3. The pipeline auto-detects modules from your repo's directory structure
4. Copy `output/` to your target repo
