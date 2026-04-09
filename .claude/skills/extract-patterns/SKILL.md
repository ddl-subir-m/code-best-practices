---
name: extract-patterns
description: Mine best practices from PR review history. Fetches PR threads, extracts patterns using Claude, merges into patterns.json, and compiles into rules.
allowed-tools:
  - Bash
  - Read
  - Write
  - Agent
  - Glob
  - Grep
---

# Extract Patterns from PR Reviews

This skill orchestrates the full extraction pipeline: fetch PR review threads from
GitHub, analyze them for recurring patterns, merge results into patterns.json, and
compile into Claude rules and Cursor rules.

## Usage

The user invokes this with `/extract` and optionally provides arguments:

- `/extract` — **smart resume**: if a historical run is in progress, picks up the next month. If historical is complete, does an incremental run (new PRs since last run).
- `/extract --full --since 2024-01-01` — start a historical month-by-month extraction
- `/extract --full --since 2024-01-01 --batch all` — fetch the entire date range at once (no monthly chunking)
- `/extract --compile-only` — skip extraction, just recompile from existing patterns.json

## Step 0: Read State and Determine Mode

Read `state.json` to determine what to do:

```bash
cat state.json 2>/dev/null || echo "NO_STATE"
```

**Mode determination:**

1. If user passed `--compile-only` → skip to Step 5.

2. If user passed `--full --since DATE --batch all` → **single-batch historical run**:
   - Write to state.json:
     ```json
     {
       "historical_run": {
         "start_date": "2024-01-01",
         "end_date": "2026-03-26",
         "batch_mode": "all",
         "status": "in_progress"
       }
     }
     ```
   - Proceed to Step 1 with the full date range (WINDOW_START = start_date, WINDOW_END = today).
   - After Step 4 completes, mark `status: "complete"` and skip to Step 5.

3. If user passed `--full --since DATE` (without `--batch all`) → **initialize monthly historical run**:
   - Calculate all months from `--since` date to today
   - Write to state.json:
     ```json
     {
       "historical_run": {
         "start_date": "2024-01-01",
         "end_date": "2026-03-26",
         "batch_mode": "monthly",
         "months": ["2024-01", "2024-02", ..., "2026-03"],
         "current_month_index": 0,
         "status": "in_progress"
       }
     }
     ```
   - Proceed to Step 1 with the first month.

4. If `state.json` has `historical_run.status == "in_progress"` and `batch_mode == "monthly"` → **resume monthly historical run**:
   - Read `current_month_index` to find the next month to process
   - If `current_month_index >= len(months)` → mark `status: "complete"`, skip to Step 5
   - Otherwise proceed to Step 1 with that month

4. If `state.json` has `historical_run.status == "complete"` (or no historical_run) → **incremental run**:
   - Use `last_extraction_date` from state.json as the since date
   - Use today as the until date
   - Proceed to Step 1

**Display progress for historical runs:**
```
HISTORICAL EXTRACTION: Month {current+1}/{total} ({month_name})
Progress: [████████░░░░░░░░░░░░] 40%
Patterns so far: {N}
```

## Step 1: Fetch PR Review Threads for Current Window

**Clear raw-reviews/ before fetching** (for monthly runs, prevents accumulation across months):
```bash
rm -rf raw-reviews/
```

Determine the date window:
- **Historical run (batch_mode: "all")**: fetch the entire range (e.g., `--since 2024-03-26 --until 2026-03-26`)
- **Historical run (batch_mode: "monthly")**: fetch only the current month (e.g., `--since 2024-04-01 --until 2024-04-30`)
- **Incremental run**: fetch from `last_extraction_date` to today

Run:
```bash
source .venv/bin/activate && python extract.py fetch --repo {REPO} --since {WINDOW_START} --until {WINDOW_END} --batch-size 100
```

If the fetch subcommand doesn't support `--until`, filter the results after fetching:
only process PRs with `mergedAt` within the current window.

Report: "Fetched N PRs for {month} with M review threads."

If fetch fails with rate limiting, report: "GitHub API rate limit hit. Wait 1 hour and
run `/extract` again — it will resume from this month."

## Step 2: Prepare Analysis Batches

Run:
```bash
source .venv/bin/activate && python extract.py analyze --input raw-reviews/ --output patterns.json
```

This writes batch files and prompt files but does NOT call an LLM.

**Check for already-processed batches** (resumability):
```bash
ls tmp/batch-*-results.json 2>/dev/null | wc -l
```
Skip any batch that already has a results file in tmp/.

## Step 3: Analyze Batches (YOU are the LLM)

Read `prompts/extract-patterns-v1.md` for the extraction instructions.

For each batch file (`tmp/review-batch-*.json`) that does NOT have a corresponding
`tmp/batch-N-results.json`:

**For small runs (≤4 batches):** Process sequentially.
Read each batch file, analyze the review threads following the extraction prompt
instructions, and write results to `tmp/batch-N-results.json` as a JSON array of:
```json
[
  {
    "pattern_name": "descriptive name",
    "rule": "one sentence rule",
    "category": "error-handling",
    "evidence": "reviewer's exact words",
    "pr_number": 47189,
    "file_path": "apps/impl/src/.../Service.scala"
  }
]
```

**For large runs (>4 batches):** Use the Agent tool to process 4 batches in
parallel. Launch 4 agents at a time, each with:
- The extraction prompt from prompts/extract-patterns-v1.md
- The batch file path to read
- Instructions to write results to tmp/batch-N-results.json

Wait for each wave of 4 to complete before launching the next wave.

**Important analysis rules:**
- Skip threads that are just acknowledgments ("LGTM", "Fixed", "Done")
- Skip threads where only the PR author is talking (no reviewer feedback)
- Only extract genuinely generalizable patterns, not PR-specific comments
- Quote the reviewer's actual words in the evidence field
- Use the exact categories: error-handling, naming, architecture, testing,
  performance, logging, security, api-design, code-organization, documentation

**Note on mode assignment:** All new patterns default to `mode: "ambient"`.
Promotion to `mode: "active"` (skill) happens only via the triage step (4d).
Do NOT set mode in your extraction output — merge handles this.

## Step 4: Merge, Dedup, Classify, Triage, Enrich

### 4a: Merge results

```bash
source .venv/bin/activate && python extract.py merge --input tmp/ --output patterns.json
```

### 4b: Deduplicate patterns

Two-pass dedup: exact ID merge, then LLM semantic grouping (batches of 200).
Runs 4 parallel Claude calls by default.

```bash
source .venv/bin/activate && python extract.py dedup --input patterns.json
```

Use `--workers N` to change parallelism.

### 4c: Reclassify modes

Reclassifies all untriaged patterns as ambient or active based on rule wording
(conditional/multi-step → active, everything else → ambient). Patterns already
triaged by Step 4d are left untouched.

```bash
source .venv/bin/activate && python extract.py reclass --input patterns.json
```

### 4d: Triage skill-worthiness

Sends active patterns (review_count >= 2) to Claude in batches of 50 to decide
if each is genuinely skill-worthy (multi-step, contextual) or should be demoted
back to ambient. Adds `skill_worthy` and `skill_rationale` fields.
Runs 4 parallel Claude calls by default.

```bash
source .venv/bin/activate && python extract.py triage --input patterns.json
```

Use `--dry-run` to preview results without writing. Use `--force` to re-triage
patterns that were already triaged. Use `--workers N` to change parallelism.

### 4e: Enrich skill-worthy patterns

Enriches patterns where `skill_worthy=True` with trigger, steps, good/bad
examples, rationale, and skill_title. Runs 4 parallel Claude calls by default.
Patterns that fail enrichment are demoted to ambient.

```bash
source .venv/bin/activate && python extract.py enrich --input patterns.json
```

Use `--force` to re-enrich already-enriched patterns. Use `--workers N` to
change parallelism.

### 4f: Auto-detect modules

```bash
source .venv/bin/activate && python extract.py modules --input patterns.json --output modules.yaml
```

### 4g: Regenerate report

```bash
source .venv/bin/activate && python extract.py report --input patterns.json --output validation-report.md
```

**Update state.json:**

For historical runs with `batch_mode: "all"`, mark complete immediately:
- Set `historical_run.status` to `"complete"`
- Update `last_extraction_date` to today
- Skip the monthly advancement logic below

For historical runs with `batch_mode: "monthly"`, advance to the next month:
- Read state.json
- Increment `historical_run.current_month_index` by 1
- Update `last_extraction_date` to the end of the current month
- Add an entry to `extraction_runs`
- Write state.json back

```bash
# Use python to update state.json atomically
source .venv/bin/activate && python3 -c "
import json
from datetime import datetime

with open('state.json') as f:
    state = json.load(f)

hr = state.get('historical_run', {})
if hr.get('status') == 'in_progress':
    idx = hr['current_month_index']
    month = hr['months'][idx]
    hr['current_month_index'] = idx + 1
    if hr['current_month_index'] >= len(hr['months']):
        hr['status'] = 'complete'
    state['last_extraction_date'] = datetime.now().strftime('%Y-%m-%d')

with open('state.json', 'w') as f:
    json.dump(state, f, indent=2)

print(json.dumps(state, indent=2))
"
```

**Clean up tmp/ for next month:**
```bash
rm -f tmp/batch-*-results.json tmp/review-batch-*.json tmp/prompts/batch-*-prompt.md
```

Report: "Month {N}/{total} complete. Merged X new patterns, Y matched existing. Dedup removed D. Triage: S skill-worthy, A ambient. Total: Z patterns."

## Step 5: Compile Rules

Run:
```bash
source .venv/bin/activate && python compile.py --input patterns.json --output output/
```

## Step 6: Summary and Next Action

**If historical run still in progress:**
```
MONTH {N}/{TOTAL} COMPLETE ({month_name})
══════════════════════════════════════════
PRs this month:   {N}
Batches analyzed: {B}
New patterns:     {new} new, {merged} merged
Dedup removed:    {D}
Triage:           {skill} skill-worthy, {ambient} ambient
Enriched:         {enriched}
Total patterns:   {total} across {modules} modules
Progress:         [████████████░░░░░░░░] {pct}%

Rules updated in output/

Next month: {next_month}
Run /extract to continue, or wait and resume later.
```

**If historical run just completed:**
```
HISTORICAL EXTRACTION COMPLETE
═══════════════════════════════
Months processed: {total_months}
Total PRs:        {total_prs}
Total patterns:   {total_patterns}
  Ambient (rules): {ambient_count}
  Active (skills): {skill_count}
Modules:          {module_list}

Output files:
  output/.claude/rules/mined-global-practices.md
  output/.claude/rules/mined-apps-practices.md
  ...
  output/.claude/skills/{topic}/SKILL.md
  output/.cursorrules

All future /extract runs will be incremental (new PRs only).
Copy output/ to your target repo to deploy.
```

**If incremental run:**
```
INCREMENTAL EXTRACTION COMPLETE
════════════════════════════════
PRs since last run: {N}
New patterns:       {new}
Updated patterns:   {merged}
Dedup removed:      {D}
Triage:             {skill} skill-worthy, {ambient} ambient
Enriched:           {enriched}
Total patterns:     {total}

Next: copy output/ to your target repo
```

## Error Handling

- If `gh` is not authenticated: tell user to run `gh auth login`
- If GitHub rate limit hit during fetch: stop gracefully, state is saved, tell user to run `/extract` again after the rate limit resets (~1 hour)
- If fetch returns 0 PRs for a month: skip to next month, log "No PRs in {month}"
- If context is getting large (you notice slowness): stop after the current batch, save state, tell user to run `/extract` in a new session
- If a batch analysis produces no patterns: normal, continue
- If merge finds 0 new patterns: "All patterns already captured for this month."

## Resumability

Every step is resumable:
- **Fetch**: state.json tracks which month we're on
- **Analyze**: tmp/ batch results persist — skip batches that already have results
- **Merge**: idempotent — same input produces same output
- **Dedup**: idempotent — re-running just finds fewer duplicates
- **Reclass**: idempotent — skips already-triaged patterns
- **Triage**: skips patterns that already have `skill_worthy` set (use `--force` to re-triage)
- **Enrich**: skips patterns that already have `steps` (use `--force` to re-enrich)
- **Compile**: stateless — always regenerates from patterns.json
- **Monthly progress**: state.json.historical_run.current_month_index tracks exactly where we are

If Claude Code crashes, context resets, or you close the terminal — just type `/extract`
and it picks up exactly where it left off.
