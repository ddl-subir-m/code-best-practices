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

- `extract/` — package split by pipeline stage:
  - `constants.py` — shared constants (categories, GraphQL query, bot authors)
  - `claude.py` — `call_claude()` CLI wrapper + JSON response parsers
  - `fetch.py` — fetch PR threads via `gh api graphql`
  - `analyze.py` — batch threads + build extraction prompts
  - `merge.py` — merge extracted patterns + pattern utilities (ID generation, dedup grouping)
  - `dedup.py` — exact ID + LLM semantic deduplication
  - `modules.py` — auto-detect module mapping from file paths
  - `report.py` — generate human-readable validation report
  - `reclass.py` — reclassify pattern modes (ambient/active)
  - `triage.py` — score patterns on skill-worthiness and hook-worthiness
  - `enrich.py` — enrich skill-worthy patterns with steps and examples
  - `enrich_hooks.py` — enrich hook-worthy patterns with hook metadata + lint/fix
  - `validate.py` — validate hook_event/hook_blocking consistency
  - `cli.py` — argparse CLI entry point
- `compile.py` — read `patterns.json`, generate scoped rule files, skills, hooks for Claude Code and Cursor
- `classify_patterns.py` — LLM-based pattern classification (ambient rule vs active skill vs hook)
- `run-historical-extraction.sh` — batch extraction across month ranges with parallel Claude calls
- `patterns.json` — canonical source of truth for all mined patterns
- `modules.yaml` — auto-generated module mapping (path → module group)
- `prompts/extract-patterns-v1.md` — versioned extraction prompt

## Key Commands

```bash
# Fetch PR review threads
python -m extract fetch --repo cerebrotech/domino --since 2024-01-01

# Analyze threads for patterns
python -m extract analyze --input raw-reviews/ --output patterns.json

# Deduplicate patterns (exact ID + LLM semantic)
python -m extract dedup --input patterns.json

# Score active patterns on skill-worthiness and hook-worthiness
python -m extract triage --input patterns.json

# Enrich skill-worthy patterns with steps and examples
python -m extract enrich --input patterns.json

# Enrich hook-worthy patterns with hook metadata (event, glob, check script, message)
python -m extract enrich-hooks --input patterns.json

# Generate human-readable report
python -m extract report --input patterns.json --output validation-report.md

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
