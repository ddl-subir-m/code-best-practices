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

- `/extract` — incremental run (uses last_extraction_date from state.json)
- `/extract --full --since 2024-01-01` — full historical extraction
- `/extract --compile-only` — skip extraction, just recompile from existing patterns.json

## Step 1: Parse Arguments

Read the user's message for arguments:
- `--repo REPO` — GitHub repo (default: read from state.json, fallback: cerebrotech/domino)
- `--since DATE` — start date for PR fetch (default: read last_extraction_date from state.json)
- `--full` — ignore state.json, fetch from --since date
- `--compile-only` — skip to Step 5
- `--batch-size N` — threads per analysis batch (default: 20)

If `--compile-only`, skip to Step 5.

## Step 2: Fetch PR Review Threads

Run:
```bash
source .venv/bin/activate && python extract.py fetch --repo {REPO} --since {SINCE_DATE} --batch-size 100
```

This fetches merged PRs with review comments via `gh api graphql` and saves
them to `raw-reviews/`. It updates `state.json` with progress.

Report: "Fetched N PRs with M review threads."

If fetch fails (auth error, rate limit), stop and report the error.

## Step 3: Analyze Batches

This is where YOU (Claude) are the LLM. Do NOT shell out to an API.

1. Run to prepare batches:
```bash
source .venv/bin/activate && python extract.py analyze --input raw-reviews/ --output patterns.json
```
This writes batch files (`review-batch-*.json`) and prompt files, but does NOT
call an LLM. That's your job.

2. Read `prompts/extract-patterns-v1.md` to get the extraction instructions.

3. For each batch file (`review-batch-*.json`):

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

4. After all batches are analyzed, ensure `tmp/` contains all result files.

## Step 4: Merge Results

Run:
```bash
source .venv/bin/activate && python extract.py merge --input tmp/ --output patterns.json
```

This merges new raw patterns into existing patterns.json:
- Matching patterns get review_count incremented and source_prs appended
- New patterns are added with review_count=1

Then auto-detect modules:
```bash
source .venv/bin/activate && python extract.py modules --input patterns.json --output modules.yaml
```

Then regenerate the human-readable report:
```bash
source .venv/bin/activate && python extract.py report --input patterns.json --output validation-report.md
```

Report: "Merged N new patterns, M matched existing. Total: X patterns across Y modules."

## Step 5: Compile Rules

Run:
```bash
source .venv/bin/activate && python compile.py --input patterns.json --output output/
```

Report what was generated:
- Number of Claude rule files and which modules
- Number of Claude skills (if any active-mode patterns)
- Cursor rules file

## Step 6: Summary

Display a summary:

```
EXTRACTION COMPLETE
═══════════════════
PRs fetched:      {N}
Review threads:   {M}
Batches analyzed: {B}
Patterns found:   {new} new, {merged} merged with existing
Total patterns:   {total}
Modules:          {list of modules}

Output files:
  output/.claude/rules/global-practices.md    ({N} rules)
  output/.claude/rules/apps-practices.md      ({N} rules)
  ...
  output/.cursorrules                         ({N} rules)

Next: copy output/ to your target repo, or review patterns.json
```

## Error Handling

- If `gh` is not authenticated: tell user to run `gh auth login`
- If fetch returns 0 PRs: "No new PRs since {date}. Nothing to extract."
- If a batch analysis produces no patterns: that's normal (not all batches have patterns)
- If merge finds 0 new patterns: "All patterns already captured. No changes to patterns.json."
- If compile finds 0 active patterns: "No active patterns found. Check patterns.json."

## Resumability

The pipeline is resumable at every step:
- Step 2: state.json tracks which PRs were fetched
- Step 3: batch files persist in tmp/ — if interrupted, re-run analyze and only
  process batches that don't have a corresponding results file in tmp/
- Step 4: merge is idempotent — running it twice with the same input produces the same output
- Step 5: compile always regenerates from patterns.json (stateless)
