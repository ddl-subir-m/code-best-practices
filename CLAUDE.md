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

- `extract.py` — fetch PR threads via `gh api graphql`, analyze with Claude agents, merge/dedup/triage/enrich/enrich-hooks patterns
- `compile.py` — read `patterns.json`, generate scoped rule files, skills, hooks for Claude Code and Cursor
- `classify_patterns.py` — LLM-based pattern classification (ambient rule vs active skill vs hook)
- `run-historical-extraction.sh` — batch extraction across month ranges with parallel Claude calls
- `patterns.json` — canonical source of truth for all mined patterns
- `modules.yaml` — auto-generated module mapping (path → module group)
- `prompts/extract-patterns-v1.md` — versioned extraction prompt

## Key Commands

```bash
# Fetch PR review threads
python extract.py fetch --repo cerebrotech/domino --since 2024-01-01

# Analyze threads for patterns
python extract.py analyze --input raw-reviews/ --output patterns.json

# Deduplicate patterns (exact ID + LLM semantic)
python extract.py dedup --input patterns.json

# Score active patterns on skill-worthiness and hook-worthiness
python extract.py triage --input patterns.json

# Enrich skill-worthy patterns with steps and examples
python extract.py enrich --input patterns.json

# Enrich hook-worthy patterns with hook metadata (event, glob, check script, message)
python extract.py enrich-hooks --input patterns.json

# Generate human-readable report
python extract.py report --input patterns.json --output validation-report.md

# Compile patterns into rules, skills, and hooks
python compile.py --input patterns.json --output output/
```

## Output Structure

```
output/
├── .claude/rules/mined-{module}-practices.md   — per-module ambient rules
├── .claude/skills/mined-{topic}/SKILL.md       — on-demand skills
├── .claude/hooks/mined-{pattern-id}.sh         — auto-triggered hook scripts
├── .claude/settings-hooks.json                 — hook wiring config (merge into settings.json)
└── .cursor/rules/mined-{module}-practices.mdc  — per-module Cursor rules
```
