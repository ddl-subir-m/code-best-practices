# code-best-practices

Mines PR review history from cerebrotech/domino and generates AI-native developer tooling (Claude Code rules/skills + Cursor rules).

## Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Testing

```bash
pytest tests/ -v
```

## Architecture

- `extract.py` — fetch PR threads via `gh api graphql`, analyze with Claude agents, merge patterns
- `compile.py` — read `patterns.json`, generate scoped rule files for Claude Code and Cursor
- `patterns.json` — canonical source of truth for all mined patterns
- `modules.yaml` — auto-generated module mapping (path → module group)
- `prompts/extract-patterns-v1.md` — versioned extraction prompt

## Key Commands

```bash
# Fetch PR review threads
python extract.py fetch --repo cerebrotech/domino --since 2024-01-01

# Analyze threads for patterns
python extract.py analyze --input raw-reviews/ --output patterns.json

# Generate human-readable report
python extract.py report --input patterns.json --output validation-report.md

# Compile patterns into rules
python compile.py --input patterns.json --output output/
```

## Output Structure

```
output/
├── .claude/rules/{module}-practices.md   — per-module ambient rules
├── .claude/skills/{topic}/SKILL.md       — on-demand skills (pass 2)
└── .cursor/rules/{module}-practices.mdc  — per-module Cursor rules
```
