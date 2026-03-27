# Conductor Parallel Build Prompts

Project: code-best-practices — Review Memory Compiler
Run these 4 workspaces in parallel in Conductor. Each touches different files.

## Setup (conductor.json)

```json
{
  "scripts": {
    "setup": "python3.11 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt",
    "run": "source .venv/bin/activate && pytest tests/ -v"
  }
}
```

---

## Workspace 1: Extraction Pipeline

**Files created:** `extract.py`, `prompts/extract-patterns-v1.md`, `modules.yaml` (auto-generated)

**Prompt:**

```
Build an extraction pipeline for mining best practices from GitHub PR review threads.

PROJECT CONTEXT:
- This project mines PR review comments from cerebrotech/domino (43K PRs, Scala monorepo, 115 modules, 14 teams)
- We use `gh api graphql` to fetch PR review threads, then Claude agents analyze them for recurring patterns
- Phase 0 already validated this approach on 20 PRs and found 9 recurring patterns

BUILD extract.py with these capabilities:

1. FETCH: Use `gh api graphql` to fetch merged PR review threads from cerebrotech/domino
   - Accept --repo, --since-date, --batch-size arguments
   - Paginate through results (GitHub returns max 100 per request)
   - Filter out bot comments (coderabbitai, codecov, github-actions, dependabot)
   - Save raw threads to raw-reviews/ directory, one JSON per PR
   - Track progress in state.json:
     ```json
     {
       "last_extraction_date": "2026-03-26",
       "last_pr_number": 47285,
       "total_prs_processed": 20,
       "extraction_runs": [{"date": "...", "prs": 20, "patterns_found": 33}]
     }
     ```

2. EXTRACT: Analyze review threads for generalizable patterns
   - Split threads into batches of 20
   - For each batch, use the versioned prompt from prompts/extract-patterns-v1.md
   - Output raw patterns as JSON with fields:
     {id, pattern_name, rule, category, evidence, pr_number, file_path}
   - Categories: error-handling, naming, architecture, testing, performance, logging, security, api-design, code-organization, documentation

3. MERGE: Combine new patterns with existing patterns.json
   - If patterns.json exists, load it
   - For each new pattern, check if it matches an existing pattern (same rule, similar wording)
   - If match: increment review_count, append to source_prs, recalculate confidence
   - If new: add to patterns.json with review_count=1
   - Confidence formula: min(1.0, review_count / 10)

4. AUTO-DETECT MODULES: Generate modules.yaml from file paths
   - Extract top-level directory from each pattern's file_path
   - Count patterns per top-level directory
   - Directories with 5+ patterns → own module
   - Directories with <5 patterns → grouped into "other"
   - Merge related directories by shared prefix (compute-cluster + compute-grid → compute)
   - Output modules.yaml:
     ```yaml
     modules:
       apps: ["/apps/"]
       server: ["/server/"]
       extensions: ["/extensions/"]
       compute: ["/compute-cluster/", "/compute-grid/"]
       other: ["*"]
     threshold: 5
     auto_generated: true
     last_updated: "2026-03-26"
     ```

5. GENERATE REPORT: Create validation-report.md from patterns.json
   - Human-readable markdown with pattern name, rule, evidence table, source PRs
   - Grouped by category
   - Summary statistics at the bottom

Also create prompts/extract-patterns-v1.md with this versioned extraction prompt:

```markdown
# Pattern Extraction Prompt v1

For each review thread, identify if the reviewer is enforcing a generalizable engineering pattern, convention, or best practice.

Skip threads that are:
- Simple acknowledgments ("LGTM", "Fixed", "Good catch")
- PR-specific discussion with no generalizable takeaway
- The PR author explaining their own code (not reviewer feedback)

For each pattern found, output JSON:
1. pattern_name: short, descriptive name
2. rule: one sentence describing what engineers should do
3. category: one of [error-handling, naming, architecture, testing, performance, logging, security, api-design, code-organization, documentation]
4. evidence: quote the reviewer's actual words
5. pr_number: the PR number
6. file_path: the file being reviewed

Only include genuinely generalizable patterns, not one-off code-specific comments.
```

CANONICAL SCHEMA for patterns.json:
```json
[
  {
    "id": "string",
    "rule": "string",
    "trigger": "string — when this rule applies",
    "rationale": "string — why this matters",
    "good_example": "string or null",
    "bad_example": "string or null",
    "source_prs": ["#1234", "#5678"],
    "scope": "string — category",
    "modules": ["apps", "server"],
    "mode": "ambient or active",
    "confidence": 0.7,
    "review_count": 7,
    "status": "active"
  }
]
```

Mode heuristic: coding conventions/style/naming → "ambient". Multi-step procedures/workflows/setup guides → "active". Default to "ambient".

CLI interface:
  python extract.py fetch --repo cerebrotech/domino --since 2024-01-01 --batch-size 100
  python extract.py analyze --input raw-reviews/ --output patterns.json
  python extract.py report --input patterns.json --output validation-report.md

Use argparse with subcommands. Python 3.11+. Dependencies: pyyaml only.
The project has a venv at .venv/ — run `source .venv/bin/activate` before executing.
Do NOT touch: compile.py, tests/, output/
```

---

## Workspace 2: Output Compiler

**Files created:** `compile.py`

**Prompt:**

```
Build an output compiler that reads patterns.json and generates Claude Code rules, Claude Code skills, and Cursor rules.

PROJECT CONTEXT:
- This project mines best practices from PR reviews and outputs them as AI coding assistant rules
- patterns.json contains an array of pattern objects (canonical schema below)
- Engineers use both Claude Code and Cursor — we need to generate rules for both
- Rules should be scoped by module (apps, server, extensions, etc.) not just category
- The compiler outputs to a local output/ directory

BUILD compile.py with these capabilities:

1. LOAD: Read patterns.json and validate against canonical schema
   - Exit with clear error if JSON is invalid or required fields missing
   - Required fields: id, rule, scope, modules, mode, status
   - Skip patterns where status != "active"

2. GENERATE CLAUDE RULES (.claude/rules/{module}-practices.md):
   - Group patterns by module (from the "modules" field)
   - Patterns in 3+ modules → output to global-practices.md
   - Per-module file format:
     ```markdown
     # {Module} Best Practices
     Auto-generated from PR review history. Do not edit manually.
     Source: patterns.json | Generated: {date}

     ## {Category}
     - {rule}
       Rationale: {rationale}
       Bad: `{bad_example}` | Good: `{good_example}`
       Sources: PR {source_prs}
     ```
   - Only include patterns where mode == "ambient" (or both)

3. GENERATE CLAUDE SKILLS (.claude/skills/{topic}/SKILL.md):
   - Only for patterns where mode == "active"
   - Each active pattern gets its own skill directory
   - SKILL.md format:
     ```markdown
     ---
     name: {id}
     description: {rule}
     ---
     # {pattern_name}

     {rationale}

     ## When to apply
     {trigger}

     ## Steps
     {rule — expanded into actionable steps}

     ## Examples
     Good: {good_example}
     Bad: {bad_example}

     Sources: PR {source_prs}
     ```

4. GENERATE CURSOR RULES (.cursorrules):
   - MERGE with existing .cursorrules, do NOT overwrite
   - Read existing file if present
   - Find section marked "## Auto-generated from PR review mining"
   - Replace that section (or append if not found)
   - Preserve everything above the auto-generated section
   - Format: same as Claude rules but in a single file, global patterns only

5. READ modules.yaml if it exists to map module names to display names.
   If modules.yaml doesn't exist, derive modules from the patterns' "modules" field directly.

CANONICAL SCHEMA for patterns.json input:
```json
[
  {
    "id": "string",
    "rule": "string",
    "trigger": "string",
    "rationale": "string",
    "good_example": "string or null",
    "bad_example": "string or null",
    "source_prs": ["#1234"],
    "scope": "string",
    "modules": ["apps", "server"],
    "mode": "ambient or active",
    "confidence": 0.7,
    "review_count": 7,
    "status": "active"
  }
]
```

CLI interface:
  python compile.py --input patterns.json --output output/
  python compile.py --input patterns.json --output output/ --cursorrules-merge path/to/existing/.cursorrules

Use argparse. Python 3.11+. No external dependencies (stdlib only).
The project has a venv at .venv/ — run `source .venv/bin/activate` before executing.
Do NOT touch: extract.py, tests/, prompts/
```

---

## Workspace 3: Tests

**Files created:** `tests/__init__.py`, `tests/test_compile.py`, `tests/test_extract.py`, `tests/conftest.py`

**Prompt:**

```
Write pytest tests for the code-best-practices project. This project has two main scripts:
1. compile.py — reads patterns.json, generates Claude rules + Cursor rules
2. extract.py — fetches PR threads, extracts patterns, manages state

BUILD tests/conftest.py with shared fixtures:
- sample_patterns: a list of 3 sample pattern objects matching the canonical schema
- sample_patterns_json: a temp file containing the sample patterns as JSON
- empty_patterns_json: a temp file with an empty array
- invalid_json_file: a temp file with malformed JSON
- existing_cursorrules: a temp file with existing cursor rules content

CANONICAL SCHEMA for patterns:
```json
{
  "id": "string",
  "rule": "string",
  "trigger": "string",
  "rationale": "string",
  "good_example": "string or null",
  "bad_example": "string or null",
  "source_prs": ["#1234"],
  "scope": "string — category like error-handling, performance",
  "modules": ["apps", "server"],
  "mode": "ambient or active",
  "confidence": 0.7,
  "review_count": 7,
  "status": "active"
}
```

BUILD tests/test_compile.py with 8 tests:

1. test_generate_claude_rules_groups_by_module
   - Given 3 patterns (2 in "apps", 1 in "server"), generates two files:
     output/.claude/rules/apps-practices.md and output/.claude/rules/server-practices.md
   - Each file contains only the patterns for that module

2. test_generate_claude_rules_global_patterns
   - Patterns appearing in 3+ modules go to global-practices.md
   - A pattern with modules: ["apps", "server", "extensions"] → global-practices.md

3. test_generate_claude_rules_special_characters
   - Pattern with backticks, quotes, and angle brackets in rule text
   - Output markdown is valid and doesn't break formatting

4. test_generate_claude_skills_active_only
   - Given 3 patterns (2 ambient, 1 active), only 1 skill directory is created
   - Skill has valid SKILL.md with frontmatter (name, description fields)

5. test_generate_claude_skills_no_active_patterns
   - Given only ambient patterns, no skills directory is created at all

6. test_generate_cursor_rules_creates_file
   - Generates valid .cursorrules file with all global patterns

7. test_generate_cursor_rules_merges_existing
   - Given an existing .cursorrules with custom content
   - Output preserves existing content and appends auto-generated section
   - Auto-generated section is marked with "## Auto-generated from PR review mining"

8. test_load_patterns_rejects_invalid
   - Invalid JSON → clear error message
   - Valid JSON missing required fields (no "rule" field) → clear error message
   - Empty array → no error, returns empty list

BUILD tests/test_extract.py with 3 tests:

1. test_patterns_json_matches_schema
   - Read the actual patterns.json file (if it exists)
   - Validate every pattern has all required fields
   - Validate confidence is 0.0-1.0
   - Validate mode is "ambient" or "active"
   - Validate status is "active", "deprecated", or "rejected"

2. test_state_json_schema
   - Validate state.json has required fields: last_extraction_date, total_prs_processed
   - Validate extraction_runs is an array

3. test_modules_yaml_schema
   - If modules.yaml exists, validate it has a "modules" key
   - Each module maps to a list of path prefixes

Use pytest (already installed in .venv/). Create tests/__init__.py as empty file.
Use tmp_path fixture for all file I/O (don't write to the real project directory).
Do NOT touch: extract.py, compile.py, prompts/
```

---

## Workspace 4: Seed Data — Convert Phase 0 Patterns to JSON

**Files created:** `patterns.json`, `state.json`

**Prompt:**

```
Convert the validated patterns from validation-report.md into the canonical patterns.json format.

Read the file validation-report.md in this project. It contains 9 recurring patterns extracted from cerebrotech/domino PR reviews.

For EACH of the 9 recurring patterns in the report, create a JSON object matching this schema:

```json
{
  "id": "kebab-case-id",
  "rule": "one sentence rule from the report",
  "trigger": "when this rule applies — derive from the pattern context",
  "rationale": "why this matters — derive from the evidence",
  "good_example": "good code example if inferable from evidence, else null",
  "bad_example": "bad code example if inferable from evidence, else null",
  "source_prs": ["#47189", "#47216"],
  "scope": "the category from the report (error-handling, performance, etc.)",
  "modules": ["module names derived from file paths in evidence"],
  "mode": "ambient or active — use heuristic: conventions → ambient, procedures → active",
  "confidence": "min(1.0, review_count / 10) where review_count = number of evidence rows",
  "review_count": "count of evidence rows in the report",
  "status": "active"
}
```

RULES:
- Derive the "modules" field from the file paths in the evidence table. Map:
  /apps/** → "apps"
  /server/** → "server"
  /extensions/** → "extensions"
  /nucleus/** → "nucleus"
  Patterns found in 3+ modules → also include "global"
- For "trigger", write a natural language description of WHEN an engineer would encounter this situation
- For good_example and bad_example, only include if they can be reasonably inferred from the evidence quotes. Don't fabricate code examples.
- The id should be a kebab-case slug derived from the pattern name
- Mode: all 9 patterns from the report are conventions, so all should be "ambient"

Write the output to patterns.json as a JSON array.

Also create state.json to record the Phase 0 extraction:
```json
{
  "last_extraction_date": "2026-03-26",
  "last_pr_number": 47285,
  "total_prs_processed": 20,
  "extraction_runs": [
    {
      "date": "2026-03-26",
      "prs_analyzed": 20,
      "raw_patterns_found": 33,
      "clusters_after_dedup": 15,
      "recurring_patterns": 9
    }
  ]
}
```

Do NOT touch: extract.py, compile.py, tests/, prompts/
```

---

## Execution Order

All 4 workspaces run in parallel — they touch completely different files:

| Workspace | Creates | Depends on |
|-----------|---------|------------|
| 1: Extract | extract.py, prompts/, modules.yaml | nothing |
| 2: Compile | compile.py | nothing (reads patterns.json schema, not file) |
| 3: Tests | tests/ | nothing (tests against schema, not implementation) |
| 4: Seed Data | patterns.json, state.json | validation-report.md (already exists) |

After all 4 complete:
1. Run `pytest tests/ -v` to verify
2. Run `python compile.py --input patterns.json --output output/` to generate rules
3. Review output/ directory
4. Copy to cerebrotech/domino repo

## conductor.json

```json
{
  "scripts": {
    "setup": "python3.11 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt",
    "run": "source .venv/bin/activate && pytest tests/ -v"
  }
}
```
