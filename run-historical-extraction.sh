#!/bin/bash
#
# Monthly historical extraction — calls Claude Code headless for the LLM analysis step.
#
# Usage:
#   ./run-historical-extraction.sh                        # default: 2024-03 to now, 4 parallel
#   ./run-historical-extraction.sh 2024-04 2026-03        # custom range
#   ./run-historical-extraction.sh 2024-04 2026-03 8      # custom range, 8 parallel Claude calls
#
set -eo pipefail

REPO="cerebrotech/domino"
START_MONTH="${1:-2024-03}"
END_MONTH="${2:-$(date +%Y-%m)}"
MAX_PARALLEL="${3:-4}"  # concurrent Claude calls (3rd arg, default 4)
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$PROJECT_DIR/.venv/bin/activate"
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR" "$PROJECT_DIR/tmp"

# ── Generate month list ──────────────────────────────────────────────────────
months=()
current="$START_MONTH"
while [[ "$current" < "$END_MONTH" || "$current" == "$END_MONTH" ]]; do
  months+=("$current")
  year="${current:0:4}"
  month="${current:5:2}"
  if [[ "$month" == "12" ]]; then
    current="$((year + 1))-01"
  else
    current="$year-$(printf '%02d' $((10#$month + 1)))"
  fi
done

total=${#months[@]}
echo "=== Historical extraction: $total months ($START_MONTH → $END_MONTH) ==="
echo ""

# ── Process each month ───────────────────────────────────────────────────────
for i in "${!months[@]}"; do
  m="${months[$i]}"
  idx=$((i + 1))
  year="${m:0:4}"
  month="${m:5:2}"

  # Calculate last day of month using python (reliable cross-platform)
  last_day=$(python3 -c "
import calendar
print(calendar.monthrange($year, $((10#$month)))[1])
")

  since="$year-$month-01"
  until="$year-$month-$last_day"

  echo "[$idx/$total] Processing $m ($since → $until)"
  echo "──────────────────────────────────────────"

  # Step 1: Fetch PRs (deterministic — no LLM needed)
  echo "  Fetching PRs..."
  rm -rf "$PROJECT_DIR/raw-reviews/"
  source "$VENV" && python "$PROJECT_DIR/extract.py" fetch \
    --repo "$REPO" --since "$since" --until "$until" --batch-size 100 \
    2>&1 | tee "$LOG_DIR/fetch-$m.log"

  # Check if any PRs were fetched
  pr_count=$(ls "$PROJECT_DIR/raw-reviews/"pr-*.json 2>/dev/null | wc -l | tr -d ' ')
  if [[ "$pr_count" == "0" ]]; then
    echo "  No PRs found for $m, skipping."
    echo ""
    continue
  fi
  echo "  Fetched $pr_count PRs."

  # Step 2: Prepare batches (deterministic — no LLM needed)
  echo "  Preparing analysis batches..."
  source "$VENV" && python "$PROJECT_DIR/extract.py" analyze \
    --input raw-reviews/ --output patterns.json \
    2>&1 | tee "$LOG_DIR/analyze-$m.log"

  # Step 3: LLM analysis — call Claude Code headless, up to MAX_PARALLEL at a time
  batch_count=$(ls "$PROJECT_DIR"/tmp/review-batch-*.json 2>/dev/null | wc -l | tr -d ' ')
  echo "  Analyzing $batch_count batches with Claude Code ($MAX_PARALLEL parallel)..."

  # Function to process a single batch (runs in background)
  analyze_batch() {
    local batch_file="$1"
    local batch_num="$2"
    local result_file="$PROJECT_DIR/tmp/batch-${batch_num}-results.json"
    local prompt_file="$PROJECT_DIR/tmp/prompts/batch-${batch_num}-prompt.md"
    local prompt_content

    if [[ -f "$prompt_file" ]]; then
      prompt_content=$(cat "$prompt_file")
    else
      local extraction_prompt=$(cat "$PROJECT_DIR/prompts/extract-patterns-v1.md")
      local batch_data=$(cat "$batch_file")
      prompt_content="$extraction_prompt

---

## Review Threads to Analyze

$batch_data

---

Return a JSON array of patterns found. Each pattern should have:
- pattern_name (string)
- rule (string)
- category (string, one of: api-design, architecture, code-organization, documentation, error-handling, logging, naming, performance, security, testing)
- evidence (string — quote the reviewer's actual words)
- pr_number (integer)
- file_path (string)

If no patterns are found in this batch, return an empty array: []

Return ONLY the JSON array, no other text."
    fi

    claude -p "$prompt_content" \
      --output-format text \
      --max-turns 1 \
      > "$result_file" \
      2>> "$LOG_DIR/claude-$m-batch-$batch_num.log" || {
        echo "    ⚠ Claude failed on batch $batch_num"
        rm -f "$result_file"
        return 1
      }

    # Validate JSON output — strip markdown fences if present
    python3 -c "
import json, sys, re
with open('$result_file') as f:
    text = f.read().strip()
text = re.sub(r'^\`\`\`json?\s*', '', text)
text = re.sub(r'\s*\`\`\`$', '', text)
data = json.loads(text)
if not isinstance(data, list):
    print('Not a JSON array', file=sys.stderr)
    sys.exit(1)
with open('$result_file', 'w') as f:
    json.dump(data, f, indent=2)
print(f'    Batch $batch_num: {len(data)} patterns')
" 2>&1 || {
      echo "    ⚠ Invalid JSON from batch $batch_num, removing."
      rm -f "$result_file"
      return 1
    }
  }

  # Launch batches in parallel waves
  running=0
  pids=()
  batch_nums=()

  for batch_file in "$PROJECT_DIR"/tmp/review-batch-*.json; do
    batch_name=$(basename "$batch_file" .json)
    batch_num="${batch_name#review-batch-}"
    result_file="$PROJECT_DIR/tmp/batch-${batch_num}-results.json"

    # Skip if already analyzed
    if [[ -f "$result_file" ]]; then
      echo "    Batch $batch_num: already done, skipping."
      continue
    fi

    # Launch in background
    analyze_batch "$batch_file" "$batch_num" &
    pids+=($!)
    batch_nums+=("$batch_num")
    running=$((running + 1))

    # Wait for wave to finish when we hit the concurrency limit
    if [[ $running -ge $MAX_PARALLEL ]]; then
      for pid in "${pids[@]}"; do
        wait "$pid" 2>/dev/null || true
      done
      pids=()
      batch_nums=()
      running=0
    fi
  done

  # Wait for any remaining background jobs
  for pid in "${pids[@]}"; do
    wait "$pid" 2>/dev/null || true
  done

  # Step 4: Merge results (deterministic)
  result_count=$(ls "$PROJECT_DIR/tmp/"batch-*-results.json 2>/dev/null | wc -l | tr -d ' ')
  if [[ "$result_count" -gt 0 ]]; then
    echo "  Merging $result_count batch results..."
    source "$VENV" && python "$PROJECT_DIR/extract.py" merge \
      --input tmp/ --output patterns.json \
      2>&1 | tee "$LOG_DIR/merge-$m.log"

    # Update modules and report
    source "$VENV" && python "$PROJECT_DIR/extract.py" modules \
      --input patterns.json --output modules.yaml 2>&1
    source "$VENV" && python "$PROJECT_DIR/extract.py" report \
      --input patterns.json --output validation-report.md 2>&1
  else
    echo "  No batch results to merge."
  fi

  # Step 5: Clean up intermediate files for this month
  rm -f "$PROJECT_DIR"/tmp/review-batch-*.json
  rm -f "$PROJECT_DIR"/tmp/prompts/batch-*-prompt.md
  rm -f "$PROJECT_DIR"/tmp/batch-*-results.json

  # Count current patterns
  pattern_count=$(python3 -c "import json; print(len(json.load(open('patterns.json'))))" 2>/dev/null || echo "?")
  echo "  ✓ Month $m complete. Total patterns: $pattern_count"
  echo ""
done

# ── Classify patterns (LLM decides rule vs skill) ───────────────────────────
echo "=== Classifying patterns with Claude (rule vs skill)... ==="

# Split patterns into classification batches of 50
python3 "$PROJECT_DIR/classify_patterns.py" prepare --input patterns.json --output-dir "$PROJECT_DIR/tmp/classify"

classify_batch_count=$(ls "$PROJECT_DIR/tmp/classify/"batch-*.json 2>/dev/null | wc -l | tr -d ' ')
echo "  $classify_batch_count classification batches to process..."

# Process classification batches in parallel
classify_batch() {
  local batch_file="$1"
  local batch_num="$2"
  local result_file="$PROJECT_DIR/tmp/classify/batch-${batch_num}-results.json"

  local prompt="You are classifying engineering patterns mined from PR reviews into two modes:

- **ambient**: A passive coding convention, style rule, or best practice that should always be followed.
  These are simple, single-sentence guidelines. Examples: \"Always validate error responses before unwrapping\",
  \"Use descriptive variable names for database query results\", \"Log the original error when wrapping exceptions\".

- **active**: A multi-step procedure, workflow, or checklist that an engineer would invoke on-demand.
  These involve sequential steps or decision trees. Examples: \"When adding a new API endpoint, follow these steps...\",
  \"Migration checklist for renaming a database column\", \"How to set up integration tests for a new service\".

Most patterns (roughly 80-90%) should be **ambient**. Only classify as **active** if the pattern genuinely
describes a procedure with multiple steps that would be lost if reduced to a single sentence.

For each pattern, return the same id with your classification and a one-line rationale.

Input patterns:
$(cat "$batch_file")

Return a JSON array:
\`\`\`json
[
  {\"id\": \"pattern-id\", \"mode\": \"ambient\", \"rationale\": \"Simple convention about X\"},
  {\"id\": \"other-id\", \"mode\": \"active\", \"rationale\": \"Multi-step workflow for Y\"}
]
\`\`\`

Return ONLY the JSON array, no other text."

  claude -p "$prompt" \
    --output-format text \
    --max-turns 1 \
    > "$result_file" \
    2>> "$LOG_DIR/classify.log" || {
      echo "    ⚠ Classification failed for batch $batch_num"
      rm -f "$result_file"
      return 1
    }

  # Validate JSON
  python3 -c "
import json, sys, re
with open('$result_file') as f:
    text = f.read().strip()
text = re.sub(r'^\`\`\`json?\s*', '', text)
text = re.sub(r'\s*\`\`\`$', '', text)
data = json.loads(text)
if not isinstance(data, list):
    sys.exit(1)
with open('$result_file', 'w') as f:
    json.dump(data, f, indent=2)
print(f'    Classify batch $batch_num: {len(data)} patterns classified')
" 2>&1 || {
    echo "    ⚠ Invalid JSON from classify batch $batch_num, removing."
    rm -f "$result_file"
    return 1
  }
}

running=0
pids=()

for batch_file in "$PROJECT_DIR/tmp/classify/"batch-*.json; do
  [[ "$batch_file" == *"-results.json" ]] && continue
  batch_name=$(basename "$batch_file" .json)
  batch_num="${batch_name#batch-}"
  result_file="$PROJECT_DIR/tmp/classify/batch-${batch_num}-results.json"

  [[ -f "$result_file" ]] && continue

  classify_batch "$batch_file" "$batch_num" &
  pids+=($!)
  running=$((running + 1))

  if [[ $running -ge $MAX_PARALLEL ]]; then
    for pid in "${pids[@]}"; do wait "$pid" 2>/dev/null || true; done
    pids=()
    running=0
  fi
done
for pid in "${pids[@]}"; do wait "$pid" 2>/dev/null || true; done

# Apply classifications back to patterns.json
python3 "$PROJECT_DIR/classify_patterns.py" apply \
  --input patterns.json \
  --classifications "$PROJECT_DIR/tmp/classify" \
  2>&1 | tee "$LOG_DIR/classify-apply.log"

rm -rf "$PROJECT_DIR/tmp/classify"

# ── Final compile ────────────────────────────────────────────────────────────
echo "=== Compiling rules... ==="
source "$VENV" && python "$PROJECT_DIR/compile.py" --input patterns.json --output output/

echo ""
echo "=== DONE ==="
echo "Months processed: $total"
pattern_count=$(python3 -c "import json; print(len(json.load(open('patterns.json'))))" 2>/dev/null || echo "?")
ambient_count=$(python3 -c "import json; ps=json.load(open('patterns.json')); print(sum(1 for p in ps if p.get('mode')=='ambient'))" 2>/dev/null || echo "?")
active_count=$(python3 -c "import json; ps=json.load(open('patterns.json')); print(sum(1 for p in ps if p.get('mode')=='active'))" 2>/dev/null || echo "?")
echo "Total patterns:   $pattern_count ($ambient_count rules, $active_count skills)"
echo "Output:           output/"

# Final cleanup
rm -rf "$PROJECT_DIR/tmp"
