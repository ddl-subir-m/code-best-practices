#!/usr/bin/env python3
"""
Extraction pipeline for mining best practices from GitHub PR review threads.

Usage:
  python extract.py fetch --repo cerebrotech/domino --since 2024-01-01
  python extract.py analyze --input raw-reviews/ --output patterns.json
  python extract.py report --input patterns.json --output validation-report.md
"""

import argparse
import concurrent.futures
import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import yaml


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BOT_AUTHORS = {"coderabbitai", "codecov", "github-actions", "dependabot"}

VALID_CATEGORIES = {
    "error-handling", "naming", "architecture", "testing", "performance",
    "logging", "security", "api-design", "code-organization", "documentation",
}

STATE_FILE = "state.json"

GRAPHQL_SEARCH_QUERY = """
query($searchQuery: String!, $first: Int!, $after: String) {
  search(query: $searchQuery, type: ISSUE, first: $first, after: $after) {
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      ... on PullRequest {
        number
        title
        author { login }
        mergedAt
        reviewThreads(first: 50) {
          nodes {
            comments(first: 20) {
              nodes {
                author { login }
                body
                createdAt
              }
            }
            isResolved
            path
            line
          }
        }
      }
    }
  }
}
"""

MODULE_THRESHOLD = 5


# ---------------------------------------------------------------------------
# Fetch subcommand
# ---------------------------------------------------------------------------

def run_gh_graphql(query: str, variables: dict) -> dict:
    """Execute a GraphQL query via `gh api graphql`."""
    cmd = [
        "gh", "api", "graphql",
        "-f", f"query={query}",
    ]
    for key, value in variables.items():
        if value is None:
            continue
        if isinstance(value, int):
            cmd += ["-F", f"{key}={value}"]
        else:
            cmd += ["-f", f"{key}={value}"]

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print(f"Error: gh api graphql failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
    return json.loads(result.stdout)


def filter_bot_comments(pr_data: dict) -> dict:
    """Remove bot-authored comments from review threads."""
    threads = pr_data.get("reviewThreads", {}).get("nodes", [])
    filtered_threads = []
    for thread in threads:
        comments = thread.get("comments", {}).get("nodes", [])
        human_comments = [
            c for c in comments
            if c.get("author", {}).get("login", "") not in BOT_AUTHORS
        ]
        if human_comments:
            filtered_thread = dict(thread)
            filtered_thread["comments"] = {"nodes": human_comments}
            filtered_threads.append(filtered_thread)
    result = dict(pr_data)
    result["reviewThreads"] = {"nodes": filtered_threads}
    return result


def load_state() -> dict:
    """Load extraction state from state.json."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {
        "last_extraction_date": None,
        "last_pr_number": None,
        "total_prs_processed": 0,
        "extraction_runs": [],
    }


def save_state(state: dict):
    """Persist extraction state to state.json."""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)
    print(f"State saved to {STATE_FILE}")


def cmd_fetch(args):
    """Fetch merged PR review threads from GitHub."""
    repo = args.repo
    since = args.since
    until = getattr(args, 'until', None)
    batch_size = min(args.batch_size, 100)  # GitHub max is 100
    output_dir = Path("raw-reviews")
    output_dir.mkdir(exist_ok=True)

    owner, name = repo.split("/")
    if until:
        date_filter = f"merged:{since}..{until}"
    else:
        date_filter = f"merged:>={since}"
    search_query = f"repo:{repo} is:pr is:merged {date_filter} sort:updated-desc"

    state = load_state()
    cursor = None
    total_fetched = 0
    highest_pr = state.get("last_pr_number") or 0

    print(f"Fetching merged PRs from {repo} since {since}...")

    while True:
        variables = {
            "searchQuery": search_query,
            "first": batch_size,
            "after": cursor,
        }
        response = run_gh_graphql(GRAPHQL_SEARCH_QUERY, variables)
        search_data = response.get("data", {}).get("search", {})
        nodes = search_data.get("nodes", [])

        if not nodes:
            break

        for pr in nodes:
            pr_number = pr.get("number")
            if not pr_number:
                continue

            # Filter bot comments
            filtered = filter_bot_comments(pr)

            # Check if any human threads remain
            threads = filtered.get("reviewThreads", {}).get("nodes", [])
            if not threads:
                print(f"  PR #{pr_number}: no human review threads, skipping")
                continue

            # Save raw review
            out_path = output_dir / f"pr-{pr_number}.json"
            with open(out_path, "w") as f:
                json.dump({"data": {"repository": {"pullRequest": filtered}}}, f)

            total_fetched += 1
            highest_pr = max(highest_pr, pr_number)
            print(f"  PR #{pr_number}: {len(threads)} threads saved")

        page_info = search_data.get("pageInfo", {})
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")

    # Update state
    state["last_extraction_date"] = datetime.now().strftime("%Y-%m-%d")
    state["last_pr_number"] = highest_pr
    state["total_prs_processed"] += total_fetched
    state["extraction_runs"].append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "prs": total_fetched,
        "patterns_found": None,  # filled in by analyze
    })
    save_state(state)

    print(f"\nDone. Fetched {total_fetched} PRs to {output_dir}/")


# ---------------------------------------------------------------------------
# Analyze subcommand
# ---------------------------------------------------------------------------

def load_raw_reviews(input_dir: str) -> list[dict]:
    """Load all raw review JSON files from a directory."""
    reviews = []
    input_path = Path(input_dir)
    for f in sorted(input_path.glob("pr-*.json")):
        with open(f) as fh:
            data = json.load(fh)
        pr = data.get("data", {}).get("repository", {}).get("pullRequest", {})
        if pr:
            reviews.append(pr)
    return reviews


def flatten_threads(reviews: list[dict]) -> list[dict]:
    """Flatten PR reviews into individual review threads with metadata."""
    threads = []
    for pr in reviews:
        pr_number = pr.get("number")
        pr_title = pr.get("title", "")
        pr_author = pr.get("author", {}).get("login", "")
        for thread in pr.get("reviewThreads", {}).get("nodes", []):
            comments = thread.get("comments", {}).get("nodes", [])
            # Filter out bot comments
            human_comments = [
                c for c in comments
                if c.get("author", {}).get("login", "") not in BOT_AUTHORS
            ]
            if not human_comments:
                continue
            threads.append({
                "pr_number": pr_number,
                "pr_title": pr_title,
                "pr_author": pr_author,
                "file_path": thread.get("path", ""),
                "line": thread.get("line"),
                "is_resolved": thread.get("isResolved", False),
                "comments": [
                    {"author": c["author"]["login"], "body": c["body"]}
                    for c in human_comments
                ],
            })
    return threads


def batch_threads(threads: list[dict], size: int = 20) -> list[list[dict]]:
    """Split threads into batches."""
    return [threads[i:i + size] for i in range(0, len(threads), size)]


def load_existing_pattern_ids(patterns_file: str = "patterns.json") -> dict[str, list[str]]:
    """Load existing pattern IDs grouped by category for dedup context in extraction prompts.

    Returns {category: [id, id, ...]} with only IDs (no rules) to keep prompt size small.
    """
    if not os.path.exists(patterns_file):
        return {}
    try:
        with open(patterns_file) as f:
            patterns = json.load(f)
        by_cat: dict[str, set[str]] = defaultdict(set)
        for p in patterns:
            pid = p.get("id", "")
            cat = p.get("scope", "general")
            if pid:
                by_cat[cat].add(pid)
        return {cat: sorted(ids) for cat, ids in sorted(by_cat.items())}
    except (json.JSONDecodeError, KeyError):
        return {}


def build_extraction_prompt(batch: list[dict], patterns_file: str = "patterns.json") -> str:
    """Build the Claude extraction prompt for a batch of threads."""
    prompt_path = Path("prompts/extract-patterns-v1.md")
    with open(prompt_path) as f:
        system_prompt = f.read()

    threads_text = json.dumps(batch, indent=2)

    # Include existing pattern IDs so the LLM reuses them instead of inventing new names
    existing = load_existing_pattern_ids(patterns_file)
    existing_section = ""
    if existing:
        lines = []
        for cat, ids in existing.items():
            lines.append(f"### {cat}")
            lines.append(", ".join(ids))
            lines.append("")
        id_text = "\n".join(lines)
        existing_section = f"""
---

## Existing Pattern Names (reuse these when the pattern matches)

If a review thread matches one of these existing patterns, reuse the EXACT name as
your `pattern_name` instead of creating a new one. Only invent a new name if the
pattern is genuinely novel.

{id_text}
"""

    return f"""{system_prompt}

---

## Review Threads to Analyze

{threads_text}
{existing_section}
---

Return a JSON array of patterns found. Each pattern should have:
- pattern_name (string — reuse an existing name from above if the pattern matches)
- rule (string)
- category (string, one of: {', '.join(sorted(VALID_CATEGORIES))})
- evidence (string — quote the reviewer's actual words)
- pr_number (integer)
- file_path (string)

If no patterns are found in this batch, return an empty array: []

Return ONLY the JSON array, no other text."""


def cmd_analyze(args):
    """Analyze review threads for generalizable patterns.

    This command prepares batched prompts for Claude analysis.
    In production, each batch prompt would be sent to the Claude API.
    For now, it outputs the batched threads as JSON for manual or
    scripted analysis.
    """
    input_dir = args.input
    output_file = args.output

    reviews = load_raw_reviews(input_dir)
    if not reviews:
        print(f"No review files found in {input_dir}/", file=sys.stderr)
        sys.exit(1)

    threads = flatten_threads(reviews)
    print(f"Loaded {len(reviews)} PRs with {len(threads)} review threads")

    batches = batch_threads(threads, size=20)
    print(f"Split into {len(batches)} batches of up to 20 threads")

    # Write batched threads for analysis
    tmp_dir = Path("tmp")
    tmp_dir.mkdir(exist_ok=True)
    all_batch_files = []
    for i, batch in enumerate(batches):
        batch_file = tmp_dir / f"review-batch-{i + 1}.json"
        with open(batch_file, "w") as f:
            json.dump(batch, f, indent=2)
        all_batch_files.append(str(batch_file))
        print(f"  Batch {i + 1}: {len(batch)} threads -> {batch_file}")

    # Build extraction prompts
    prompts_dir = tmp_dir / "prompts"
    prompts_dir.mkdir(exist_ok=True)
    for i, batch in enumerate(batches):
        prompt = build_extraction_prompt(batch)
        prompt_file = prompts_dir / f"batch-{i + 1}-prompt.md"
        with open(prompt_file, "w") as f:
            f.write(prompt)
        print(f"  Prompt {i + 1}: {prompt_file}")

    print(f"\nBatches written. Run each prompt through Claude, then use:")
    print(f"  python extract.py merge --input <results-dir> --output {output_file}")


# ---------------------------------------------------------------------------
# Merge subcommand
# ---------------------------------------------------------------------------

def normalize_rule(rule: str) -> str:
    """Normalize a rule string for comparison."""
    return rule.lower().strip().rstrip(".")


def patterns_match(existing: dict, new: dict) -> bool:
    """Check if two patterns are the same based on rule similarity."""
    e_rule = normalize_rule(existing.get("rule", ""))
    n_rule = normalize_rule(new.get("rule", ""))

    # Exact match
    if e_rule == n_rule:
        return True

    # Check if one contains the other (for minor wording variations)
    if len(e_rule) > 20 and len(n_rule) > 20:
        shorter, longer = sorted([e_rule, n_rule], key=len)
        if shorter in longer:
            return True

    # Same pattern_name (case-insensitive)
    e_name = existing.get("pattern_name", "").lower().strip()
    n_name = new.get("pattern_name", "").lower().strip()
    if e_name and n_name and e_name == n_name:
        return True

    # Match existing canonical id against new raw pattern_name slug
    e_id = existing.get("id", "")
    n_id = make_pattern_id(new.get("pattern_name", "")) if new.get("pattern_name") else ""
    if e_id and n_id and e_id == n_id:
        return True

    return False


def determine_mode(category: str, rule: str) -> str:
    """Determine if a pattern should be ambient (rule) or active (skill).

    Ambient — universal constraints always loaded in context (rules).
    Active  — multi-step processes or triggered guidance surfaced on demand (skills).
    Hook    — assigned only by LLM triage (cmd_triage), never by this heuristic.
    """
    rule_lower = rule.lower()

    # Contextual/triggered patterns -> active (skills)
    if rule_lower.startswith(("when ", "before ", "after ", "if ")):
        return "active"

    # Multi-step processes -> active (skills)
    if any(marker in rule_lower for marker in ("step 1", "1.", "2.", "first,", "then,")):
        return "active"

    # Everything else is a universal convention -> ambient (rules)
    return "ambient"


def make_pattern_id(pattern_name: str) -> str:
    """Generate a stable ID from a pattern name."""
    return pattern_name.lower().replace(" ", "-").replace("_", "-")


def merge_pattern(existing: dict, new_raw: dict) -> dict:
    """Merge a new raw pattern into an existing canonical pattern."""
    existing["review_count"] = existing.get("review_count", 1) + 1
    existing["confidence"] = min(1.0, existing["review_count"] / 10)

    # Append source PR
    pr_ref = f"#{new_raw['pr_number']}"
    if pr_ref not in existing.get("source_prs", []):
        existing.setdefault("source_prs", []).append(pr_ref)

    # Append module from file path
    module = extract_module_from_path(new_raw.get("file_path", ""))
    if module and module not in existing.get("modules", []):
        existing.setdefault("modules", []).append(module)

    return existing


def extract_module_from_path(file_path: str) -> str:
    """Extract the top-level directory from a file path."""
    if not file_path:
        return ""
    parts = file_path.strip("/").split("/")
    return parts[0] if parts else ""


def raw_to_canonical(raw: dict) -> dict:
    """Convert a raw extracted pattern to canonical schema."""
    pattern_name = raw.get("pattern_name", "unknown")
    category = raw.get("category", "code-organization")
    if category not in VALID_CATEGORIES:
        category = "code-organization"

    rule = raw.get("rule", "")
    module = extract_module_from_path(raw.get("file_path", ""))

    return {
        "id": make_pattern_id(pattern_name),
        "rule": rule,
        "trigger": "",
        "rationale": "",
        "good_example": None,
        "bad_example": None,
        "source_prs": [f"#{raw['pr_number']}"],
        "scope": category,
        "modules": [module] if module else [],
        "mode": "ambient",  # Default to ambient; triage is the only promotion path
        "confidence": 0.1,
        "review_count": 1,
        "status": "active",
    }


def cmd_merge(args):
    """Merge extracted patterns into patterns.json."""
    input_dir = Path(args.input)
    output_file = args.output

    # Load existing patterns
    existing_patterns = []
    if os.path.exists(output_file):
        with open(output_file) as f:
            existing_patterns = json.load(f)
        print(f"Loaded {len(existing_patterns)} existing patterns from {output_file}")

    # Load new raw patterns from input directory
    new_raw = []
    for f in sorted(input_dir.glob("*.json")):
        with open(f) as fh:
            data = json.load(fh)
        if isinstance(data, list):
            new_raw.extend(data)
        elif isinstance(data, dict) and "patterns" in data:
            new_raw.extend(data["patterns"])
    print(f"Loaded {len(new_raw)} new raw patterns from {input_dir}/")

    merged_count = 0
    added_count = 0

    for raw in new_raw:
        matched = False
        for existing in existing_patterns:
            if patterns_match(existing, raw):
                merge_pattern(existing, raw)
                merged_count += 1
                matched = True
                break

        if not matched:
            canonical = raw_to_canonical(raw)
            existing_patterns.append(canonical)
            added_count += 1

    # Save merged patterns
    with open(output_file, "w") as f:
        json.dump(existing_patterns, f, indent=2)

    print(f"\nMerge complete:")
    print(f"  Merged into existing: {merged_count}")
    print(f"  Added new: {added_count}")
    print(f"  Total patterns: {len(existing_patterns)}")
    print(f"  Written to: {output_file}")


# ---------------------------------------------------------------------------
# Dedup subcommand
# ---------------------------------------------------------------------------

def call_claude(prompt: str, timeout: int = 300) -> str:
    """Call Claude in headless mode via the claude CLI."""
    try:
        result = subprocess.run(
            ["claude", "-p", "--max-turns", "1", prompt],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            print(f"Warning: claude CLI failed: {result.stderr[:200]}", file=sys.stderr)
            return ""
        return result.stdout.strip()
    except FileNotFoundError:
        sys.exit("Error: 'claude' CLI not found. Install Claude Code first.")
    except subprocess.TimeoutExpired:
        print("Warning: claude CLI timed out", file=sys.stderr)
        return ""


def _strip_code_fences(text: str) -> str:
    """Strip markdown code fences from LLM output."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]  # remove opening ```json
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def parse_json_response(text: str) -> list:
    """Parse a JSON array from Claude's response, handling markdown code blocks."""
    text = _strip_code_fences(text)
    if not text:
        return []
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass
    return []


def merge_duplicate_group(patterns: list[dict]) -> dict:
    """Merge a group of duplicate patterns into one canonical pattern."""
    # Use the pattern with the longest rule as the base (most detailed wording)
    base = max(patterns, key=lambda p: len(p.get("rule", "")))
    merged = dict(base)

    for p in patterns:
        if p is base:
            continue
        merged["review_count"] = merged.get("review_count", 1) + p.get("review_count", 1)
        for pr in p.get("source_prs", []):
            if pr not in merged.get("source_prs", []):
                merged.setdefault("source_prs", []).append(pr)
        for mod in p.get("modules", []):
            if mod not in merged.get("modules", []):
                merged.setdefault("modules", []).append(mod)

    merged["confidence"] = min(1.0, merged["review_count"] / 10)
    return merged


def cmd_dedup(args):
    """Deduplicate patterns using exact ID matching + LLM semantic matching."""
    input_file = args.input

    with open(input_file) as f:
        patterns = json.load(f)

    original_count = len(patterns)
    print(f"Loaded {original_count} patterns from {input_file}", flush=True)

    # --- Pass 1: Merge exact ID duplicates (no LLM needed) ---
    by_id: dict[str, list[dict]] = defaultdict(list)
    for p in patterns:
        by_id[p["id"]].append(p)

    id_merged = []
    id_merge_count = 0
    for pid, group in by_id.items():
        if len(group) > 1:
            id_merge_count += len(group) - 1
            id_merged.append(merge_duplicate_group(group))
        else:
            id_merged.append(group[0])

    print(f"Pass 1 (exact ID): merged {id_merge_count} duplicates, {len(id_merged)} remaining", flush=True)

    # --- Pass 2: LLM semantic dedup across all patterns (scope-agnostic) ---
    BATCH_SIZE = 200

    # Sort by ID so similar names land in the same batch
    id_merged.sort(key=lambda p: p.get("id", ""))

    batches = [id_merged[i:i + BATCH_SIZE] for i in range(0, len(id_merged), BATCH_SIZE)]
    total_batches = len(batches)

    final_patterns = []
    llm_merge_count = 0
    max_workers = getattr(args, 'workers', 4)

    def _dedup_batch(batch_num_and_batch):
        batch_num, batch = batch_num_and_batch
        if len(batch) <= 1:
            return batch_num, batch, None

        pattern_list = json.dumps(
            [{"index": i, "id": p["id"], "rule": p["rule"]} for i, p in enumerate(batch)],
            indent=2,
        )

        prompt = (
            "You are deduplicating patterns extracted from code review history.\n\n"
            "Below is a list of patterns from various categories. Identify groups of "
            "patterns that describe the SAME underlying rule or convention, even if worded "
            "differently or filed under different categories.\n\n"
            "Return ONLY a JSON array of groups. Each group is an array of index numbers "
            "that should be merged. Only include groups with 2+ patterns. Patterns that "
            "are unique should NOT appear in any group. Be conservative — only group "
            "patterns that are clearly about the same thing.\n\n"
            f"Patterns:\n{pattern_list}\n\n"
            "Return ONLY the JSON array, e.g.: [[0, 3, 7], [2, 5]]"
        )

        print(f"  Batch {batch_num}/{total_batches}: "
              f"sending {len(batch)} patterns to Claude...", flush=True)
        response = call_claude(prompt)
        groups = parse_json_response(response)
        return batch_num, batch, groups

    # Run LLM calls in parallel
    batch_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_dedup_batch, (bn, b)): bn
            for bn, b in enumerate(batches, 1)
        }
        for future in concurrent.futures.as_completed(futures):
            try:
                batch_results.append(future.result())
            except Exception as e:
                bn = futures[future]
                print(f"  Error in dedup batch {bn}: {e}", file=sys.stderr)
                batch_results.append((bn, batches[bn - 1], None))

    # Post-process sequentially in batch order
    batch_results.sort(key=lambda r: r[0])

    for batch_num, batch, groups in batch_results:
        if not groups:
            final_patterns.extend(batch)
            continue

        merged_indices: set[int] = set()
        for group in groups:
            if not isinstance(group, list) or len(group) < 2:
                continue
            valid = [i for i in group if isinstance(i, int) and 0 <= i < len(batch)]
            if len(valid) < 2:
                continue
            group_patterns = [batch[i] for i in valid]
            final_patterns.append(merge_duplicate_group(group_patterns))
            merged_indices.update(valid)
            llm_merge_count += len(valid) - 1

        for i, p in enumerate(batch):
            if i not in merged_indices:
                final_patterns.append(p)

    print(f"\nPass 2 (LLM semantic): merged {llm_merge_count} duplicates", flush=True)
    print(f"\nDedup complete: {original_count} → {len(final_patterns)} patterns", flush=True)

    with open(input_file, "w") as f:
        json.dump(final_patterns, f, indent=2)
    print(f"Written to {input_file}", flush=True)


# ---------------------------------------------------------------------------
# Modules subcommand
# ---------------------------------------------------------------------------

def cmd_modules(args):
    """Auto-detect modules from patterns.json and generate modules.yaml."""
    input_file = args.input

    with open(input_file) as f:
        patterns = json.load(f)

    # Count patterns per top-level directory
    dir_counts = defaultdict(int)
    dir_paths = defaultdict(set)

    for pattern in patterns:
        for pr_ref in pattern.get("source_prs", []):
            pass  # source_prs don't have paths

        for module in pattern.get("modules", []):
            if module:
                dir_counts[module] += 1
                dir_paths[module].add(f"/{module}/")

    # Also scan raw reviews for file paths
    raw_dir = Path("raw-reviews")
    if raw_dir.exists():
        for f in raw_dir.glob("pr-*.json"):
            with open(f) as fh:
                data = json.load(fh)
            pr = data.get("data", {}).get("repository", {}).get("pullRequest", {})
            for thread in pr.get("reviewThreads", {}).get("nodes", []):
                path = thread.get("path", "")
                if path:
                    top = path.strip("/").split("/")[0]
                    dir_counts[top] += 1
                    dir_paths[top].add(f"/{top}/")

    # Merge related directories by shared prefix
    merged = {}
    for dirname in sorted(dir_counts.keys()):
        base = dirname.split("-")[0]
        if base in merged:
            merged[base]["paths"].update(dir_paths[dirname])
            merged[base]["count"] += dir_counts[dirname]
        else:
            # Check if any existing merged key shares this prefix
            found = False
            for key in list(merged.keys()):
                if key == base or dirname.startswith(key + "-"):
                    merged[key]["paths"].update(dir_paths[dirname])
                    merged[key]["count"] += dir_counts[dirname]
                    found = True
                    break
            if not found:
                merged[dirname] = {
                    "paths": set(dir_paths[dirname]),
                    "count": dir_counts[dirname],
                }

    # Split into own-module vs other
    modules = {}
    other_paths = []
    for name, info in sorted(merged.items()):
        if info["count"] >= MODULE_THRESHOLD:
            modules[name] = sorted(info["paths"])
        else:
            other_paths.extend(sorted(info["paths"]))

    if other_paths:
        modules["other"] = ["*"]

    output = {
        "modules": modules,
        "threshold": MODULE_THRESHOLD,
        "auto_generated": True,
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
    }

    output_file = args.output
    with open(output_file, "w") as f:
        yaml.dump(output, f, default_flow_style=False, sort_keys=False)

    print(f"Module mapping written to {output_file}")
    for name, paths in modules.items():
        count = merged.get(name, {}).get("count", "?")
        print(f"  {name}: {paths} ({count} patterns)")


# ---------------------------------------------------------------------------
# Report subcommand
# ---------------------------------------------------------------------------

def cmd_report(args):
    """Generate a human-readable validation report from patterns.json."""
    input_file = args.input
    output_file = args.output

    with open(input_file) as f:
        patterns = json.load(f)

    # Group by category
    by_category = defaultdict(list)
    for p in patterns:
        by_category[p.get("scope", "uncategorized")].append(p)

    # Sort patterns by review_count descending
    all_sorted = sorted(patterns, key=lambda p: p.get("review_count", 0), reverse=True)
    recurring = [p for p in all_sorted if p.get("review_count", 0) >= 2]
    single = [p for p in all_sorted if p.get("review_count", 0) < 2]

    lines = []
    lines.append("# Pattern Validation Report — cerebrotech/domino\n")
    lines.append(f"**Generated:** {datetime.now().strftime('%B %d, %Y')}")
    lines.append(f"**Total patterns:** {len(patterns)}")
    lines.append(f"**Recurring patterns (2+ PRs):** {len(recurring)}")
    lines.append(f"**Single-occurrence patterns:** {len(single)}")
    lines.append("")
    lines.append("---\n")

    # Recurring patterns
    if recurring:
        lines.append("## Recurring Patterns (ranked by frequency)\n")
        for i, p in enumerate(recurring, 1):
            lines.append(f"### {i}. {p.get('id', 'unknown').replace('-', ' ').title()}")
            lines.append(f"**Rule:** {p.get('rule', 'N/A')}\n")
            lines.append(f"**Category:** {p.get('scope', 'N/A')}")
            lines.append(f"**Mode:** {p.get('mode', 'ambient')}")
            lines.append(f"**Confidence:** {p.get('confidence', 0):.1f}")
            lines.append(f"**Review count:** {p.get('review_count', 0)}")
            lines.append(f"**Source PRs:** {', '.join(p.get('source_prs', []))}")
            lines.append(f"**Modules:** {', '.join(p.get('modules', []))}")
            if p.get("trigger"):
                lines.append(f"**Trigger:** {p['trigger']}")
            if p.get("rationale"):
                lines.append(f"**Rationale:** {p['rationale']}")
            lines.append("")
            lines.append("---\n")

    # Single-occurrence patterns
    if single:
        lines.append(f"## Single-Occurrence Patterns ({len(single)} patterns)\n")
        lines.append("| # | Pattern | Category | Source PRs |")
        lines.append("|---|---------|----------|------------|")
        for i, p in enumerate(single, len(recurring) + 1):
            name = p.get("id", "unknown").replace("-", " ").title()
            lines.append(
                f"| {i} | {name} | {p.get('scope', '')} "
                f"| {', '.join(p.get('source_prs', []))} |"
            )
        lines.append("")
        lines.append("---\n")

    # Summary statistics
    lines.append("## Summary Statistics\n")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total patterns | {len(patterns)} |")
    lines.append(f"| Recurring (2+ PRs) | {len(recurring)} |")
    lines.append(f"| Single-occurrence | {len(single)} |")
    lines.append("")

    lines.append("### Category Distribution\n")
    lines.append("| Category | Count |")
    lines.append("|----------|-------|")
    for cat in sorted(by_category.keys()):
        lines.append(f"| {cat} | {len(by_category[cat])} |")
    lines.append("")

    report = "\n".join(lines)
    with open(output_file, "w") as f:
        f.write(report)

    print(f"Report written to {output_file}")
    print(f"  {len(recurring)} recurring patterns, {len(single)} single-occurrence")


# ---------------------------------------------------------------------------
# Triage subcommand
# ---------------------------------------------------------------------------

MIN_REVIEW_COUNT_TRIAGE = 2


def build_triage_prompt(batch: list[dict]) -> str:
    """Build the Claude triage prompt for a batch of patterns."""
    pattern_list = json.dumps(
        [{"id": p["id"], "rule": p["rule"], "scope": p.get("scope", ""), "modules": p.get("modules", [])}
         for p in batch],
        indent=2,
    )
    return (
        "For each pattern below, determine TWO things:\n\n"
        "1. **skill_worthy**: Does this pattern require multi-step guidance "
        "(a workflow, decision tree, or code example) to be useful as a coding assistant skill? "
        "A pattern is skill-worthy if an engineer would benefit from step-by-step instructions, "
        "concrete code examples, or a decision tree to apply it correctly. "
        "A pattern is NOT skill-worthy if it can be fully communicated in a single sentence.\n\n"
        "2. **hook_worthy**: Should this pattern be enforced as an automated hook "
        "(a shell script that runs automatically when files are edited)? "
        "A pattern is hook-worthy if ALL of the following are true:\n"
        "   - The check is mechanically automatable (grep, regex, or AST scan — not judgment calls)\n"
        "   - It's high-severity (security, breaking changes, data loss, or compliance)\n"
        "   - It's tied to a specific file-edit event (e.g., editing shared files, adding endpoints, modifying migrations)\n"
        "   - It's too important to rely on someone remembering to apply it\n"
        "   - **The check can be precise enough to have a low false positive rate.** A grep that "
        "fires on nearly every edit to common files (e.g., matching any component name, any "
        "variable removal, any history.push) is NOT hook-worthy — it becomes noise that gets "
        "ignored. The grep must target a SPECIFIC anti-pattern that is rare in correct code.\n\n"
        "Examples of NOT hook-worthy (too noisy):\n"
        "   - 'Guard new features behind feature flags' — would fire on any component, not just flag-gated ones\n"
        "   - 'Verify backward compat when removing fields' — would fire on any removed variable, not just API fields\n"
        "   - 'Use history.replace for URL state' — would fire on every navigation, not just state updates\n\n"
        "A pattern can be BOTH skill_worthy and hook_worthy (e.g., a security check that also "
        "benefits from step-by-step guidance). If hook_worthy is true, it takes precedence — "
        "the pattern becomes a hook rather than a skill.\n\n"
        f"Patterns:\n{pattern_list}\n\n"
        'Return ONLY a JSON array: [{"id": "pattern-id", "skill_worthy": true/false, '
        '"skill_rationale": "one sentence", "hook_worthy": true/false, '
        '"hook_rationale": "one sentence explaining why or why not"}]\n\n'
        "Return ONLY the JSON array, no other text."
    )


def cmd_triage(args):
    """Score active patterns on skill-worthiness and demote simple conventions."""
    input_file = args.input
    dry_run = args.dry_run
    force = args.force
    batch_size = 50

    with open(input_file) as f:
        patterns = json.load(f)

    # Filter to triage population: active + review_count >= threshold
    candidates = []
    for p in patterns:
        if p.get("mode") != "active":
            continue
        if p.get("review_count", 1) < MIN_REVIEW_COUNT_TRIAGE:
            continue
        if not force and p.get("skill_worthy") is not None:
            continue
        candidates.append(p)

    print(f"Loaded {len(patterns)} patterns, {len(candidates)} eligible for triage", flush=True)

    if not candidates:
        print("No patterns to triage.")
        return

    # Batch and send to Claude in parallel
    batches = [candidates[i:i + batch_size] for i in range(0, len(candidates), batch_size)]
    results: dict[str, dict] = {}  # id -> {skill_worthy, skill_rationale}
    max_workers = getattr(args, 'workers', 4)

    def _triage_batch(batch_num_and_batch):
        batch_num, batch = batch_num_and_batch
        prompt = build_triage_prompt(batch)
        print(f"  Batch {batch_num}/{len(batches)}: sending {len(batch)} patterns to Claude...", flush=True)
        response = call_claude(prompt)
        parsed = parse_json_response(response)

        if not parsed:
            print(f"  Warning: batch {batch_num} returned no valid results, skipping", file=sys.stderr)
            return {}

        batch_results = {}
        for item in parsed:
            if not isinstance(item, dict):
                continue
            pid = item.get("id", "")
            if pid and "skill_worthy" in item:
                batch_results[pid] = {
                    "skill_worthy": bool(item["skill_worthy"]),
                    "skill_rationale": item.get("skill_rationale", ""),
                    "hook_worthy": bool(item.get("hook_worthy", False)),
                    "hook_rationale": item.get("hook_rationale", ""),
                }
        return batch_results

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_triage_batch, (bn, b)): bn
            for bn, b in enumerate(batches, 1)
        }
        for future in concurrent.futures.as_completed(futures):
            try:
                batch_results = future.result()
                results.update(batch_results)
            except Exception as e:
                print(f"  Error in triage batch: {e}", file=sys.stderr)

    # Report results
    hooks = sum(1 for r in results.values() if r["hook_worthy"])
    worthy = sum(1 for r in results.values() if r["skill_worthy"] and not r["hook_worthy"])
    not_worthy = sum(1 for r in results.values() if not r["skill_worthy"] and not r["hook_worthy"])
    print(f"\nTriage results: {hooks} hook-worthy, {worthy} skill-worthy, {not_worthy} demoted to ambient", flush=True)

    if dry_run:
        print("\n[DRY RUN] No changes written to disk.")
        if hooks:
            print(f"\nHook-worthy patterns ({hooks}):")
            for pid, r in sorted(results.items()):
                if r["hook_worthy"]:
                    print(f"  {pid}: {r['hook_rationale']}")
        print(f"\nSkill-worthy patterns ({worthy}):")
        for pid, r in sorted(results.items()):
            if r["skill_worthy"] and not r["hook_worthy"]:
                print(f"  {pid}: {r['skill_rationale']}")
        return

    # Apply results to patterns
    for p in patterns:
        pid = p.get("id", "")
        if pid in results:
            r = results[pid]
            p["skill_worthy"] = r["skill_worthy"]
            p["skill_rationale"] = r["skill_rationale"]
            p["hook_worthy"] = r["hook_worthy"]
            p["hook_rationale"] = r["hook_rationale"]
            # Hook-worthy takes precedence over skill-worthy
            if r["hook_worthy"]:
                p["mode"] = "hook"
                p["mode_rationale"] = r["hook_rationale"]
            elif not r["skill_worthy"]:
                p["mode"] = "ambient"
                p["mode_rationale"] = r["skill_rationale"]

    with open(input_file, "w") as f:
        json.dump(patterns, f, indent=2)

    print(f"Written to {input_file}", flush=True)


# ---------------------------------------------------------------------------
# Enrich subcommand
# ---------------------------------------------------------------------------

def build_enrich_prompt(pattern: dict) -> str:
    """Build the Claude enrichment prompt for a single pattern."""
    return (
        "You are enriching an engineering pattern mined from PR review history "
        "at Domino Data Lab. Given this pattern, generate structured skill content.\n\n"
        f"Pattern ID: {pattern['id']}\n"
        f"Rule: {pattern['rule']}\n"
        f"Category: {pattern.get('scope', '')}\n"
        f"Source PRs: {', '.join(pattern.get('source_prs', []))}\n"
        f"Modules: {', '.join(pattern.get('modules', []))}\n\n"
        "Generate a JSON object with these fields:\n"
        '1. "id": the pattern ID (echo it back for validation)\n'
        '2. "trigger": 1-2 sentences describing when this applies (second person: "You\'re writing...")\n'
        '3. "steps": array of 3-6 concrete action steps as strings\n'
        '4. "good_example": a concrete code example showing the correct approach '
        "(use Scala for server/apps patterns, TypeScript/React for frontend patterns)\n"
        '5. "bad_example": a concrete code example showing the anti-pattern\n'
        '6. "rationale": 1-2 sentences explaining WHY this matters\n'
        '7. "skill_title": an imperative-voice title (e.g., "Replace full-object fetches with count queries")\n\n'
        "Return ONLY the JSON object, no other text."
    )


def parse_json_object(text: str) -> dict:
    """Parse a JSON object from Claude's response, handling markdown code blocks."""
    text = _strip_code_fences(text)
    if not text:
        return {}
    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass
    return {}


def enrich_single_pattern(pattern: dict) -> dict | None:
    """Enrich a single pattern via Claude. Returns enrichment fields or None on failure."""
    prompt = build_enrich_prompt(pattern)
    response = call_claude(prompt, timeout=120)
    result = parse_json_object(response)
    if not result:
        return None

    # Validate the response has steps
    steps = result.get("steps", [])
    if not isinstance(steps, list) or len(steps) < 1:
        return None

    return result


def cmd_enrich(args):
    """Enrich skill-worthy patterns with steps, examples, and triggers."""
    input_file = args.input
    force = args.force
    max_workers = args.workers

    with open(input_file) as f:
        patterns = json.load(f)

    # Filter to enrichment population: skill_worthy=True + not already enriched
    candidates = []
    candidate_indices = []
    for i, p in enumerate(patterns):
        if not p.get("skill_worthy"):
            continue
        if not force and isinstance(p.get("steps"), list) and len(p.get("steps", [])) > 0:
            continue
        candidates.append(p)
        candidate_indices.append(i)

    print(f"Loaded {len(patterns)} patterns, {len(candidates)} eligible for enrichment", flush=True)

    if not candidates:
        print("No patterns to enrich.")
        return

    # Enrich in parallel
    enriched_count = 0
    failed_count = 0

    def process(idx_pattern):
        idx, pattern = idx_pattern
        result = enrich_single_pattern(pattern)
        return idx, pattern["id"], result

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process, (candidate_indices[i], c)): i
            for i, c in enumerate(candidates)
        }
        for future in concurrent.futures.as_completed(futures):
            try:
                idx, pid, result = future.result()
                if result:
                    # Validate id matches
                    if result.get("id") and result["id"] != pid:
                        print(f"  Warning: id mismatch for {pid}, skipping", file=sys.stderr)
                        failed_count += 1
                        continue
                    # Apply enrichment fields
                    p = patterns[idx]
                    for field in ("trigger", "steps", "good_example", "bad_example", "rationale", "skill_title"):
                        if field in result and result[field]:
                            p[field] = result[field]
                    enriched_count += 1
                    print(f"  [{enriched_count}/{len(candidates)}] Enriched: {pid}", flush=True)
                else:
                    failed_count += 1
                    print(f"  Warning: enrichment failed for {pid}", file=sys.stderr)
                    # Fall back to ambient mode to avoid the black hole
                    patterns[idx]["mode"] = "ambient"
                    patterns[idx]["mode_rationale"] = "Enrichment failed, fell back to ambient"
            except Exception as e:
                failed_count += 1
                print(f"  Error enriching pattern: {e}", file=sys.stderr)

    print(f"\nEnrichment complete: {enriched_count} enriched, {failed_count} failed", flush=True)

    with open(input_file, "w") as f:
        json.dump(patterns, f, indent=2)

    print(f"Written to {input_file}", flush=True)


# ---------------------------------------------------------------------------
# Enrich-hooks subcommand
# ---------------------------------------------------------------------------

HOOK_ENRICHMENT_FIELDS = (
    "hook_event", "hook_tool", "hook_glob", "hook_check", "hook_message", "hook_blocking",
    "hook_fp_risk",
)


def build_enrich_hooks_prompt(pattern: dict) -> str:
    """Build the Claude prompt to generate hook metadata for a pattern."""
    return (
        "You are generating automated hook configuration for a coding pattern mined from "
        "PR review history at Domino Data Lab. This pattern will become a shell script that "
        "runs automatically when files are edited in Claude Code.\n\n"
        f"Pattern ID: {pattern['id']}\n"
        f"Rule: {pattern['rule']}\n"
        f"Category: {pattern.get('scope', '')}\n"
        f"Source PRs: {', '.join(pattern.get('source_prs', []))}\n"
        f"Modules: {', '.join(pattern.get('modules', []))}\n"
        + (f"Good example:\n{pattern['good_example']}\n" if pattern.get('good_example') else "")
        + (f"Bad example:\n{pattern['bad_example']}\n" if pattern.get('bad_example') else "")
        + "\nGenerate a JSON object with these fields:\n"
        '1. "hook_event": either "PreToolUse" or "PostToolUse"\n'
        "   - PreToolUse = preventive hooks that warn/block BEFORE the action "
        "(security gates, auth checks, secret leakage, data safety)\n"
        "   - PostToolUse = detective hooks that inspect AFTER the action "
        "(consumer audits, quality warnings, PII checks)\n"
        '2. "hook_tool": which tool triggers it — usually "Edit" or "Write"\n'
        '3. "hook_glob": file glob pattern to match (e.g., "**/*Controller*.scala", '
        '"**/shared/**/*.tsx"). Use patterns appropriate for the modules listed above.\n'
        '4. "hook_check": a shell command (using grep, awk, or sed) that detects the '
        "anti-pattern in the file passed as $1. Exit code 0 = violation found, "
        "exit code 1 = no violation. Keep it simple and portable.\n"
        '5. "hook_message": a concise warning message shown when the hook fires. '
        "Include what was detected and what the developer should do.\n"
        '6. "hook_blocking": true if the hook should block the action (security-critical), '
        "false if it should only warn (advisory).\n"
        '7. "hook_fp_risk": "LOW", "MEDIUM", or "HIGH" — your honest assessment of how often '
        "this hook will fire on CORRECT code (false positives).\n"
        "   - LOW: the grep targets a specific anti-pattern that rarely appears in correct code "
        "(e.g., `toJson(config.toMap)` in a controller, `Action.async` without authAction)\n"
        "   - MEDIUM: the grep may occasionally match legitimate code but the signal is still "
        "valuable (e.g., PII field names near analytics calls)\n"
        "   - HIGH: the grep matches very common patterns that appear in most correct code "
        "(e.g., any component name ending in Panel, any removed variable, any history.push). "
        "If you assess HIGH, this pattern should NOT be a hook — it should be a skill instead. "
        "Return hook_fp_risk: 'HIGH' and it will be demoted.\n\n"
        "Return ONLY the JSON object, no other text."
    )


HOOK_CHECK_LINT_RULES = [
    # (pattern, description) — if the regex matches hook_check, it's flagged
    (r'\|\s*head\b', "pipe to head always exits 0 — use grep -q instead"),
    (r'\|\s*tail\b', "pipe to tail always exits 0 — use grep -q instead"),
    (r'\|\s*wc\b', "pipe to wc always exits 0 — use grep -q or grep -c instead"),
    (r'\\s\*\\[)\]]', "\\s*\\) after method name misses the opening paren — use \\s*[({] or \\s*\\("),
    (r'\bexit\s+0\s*\|\|', "exit 0 || pattern may short-circuit subshell unexpectedly"),
]


def _lint_hook_check(hook_check: str) -> list[str]:
    """Lint a hook_check shell command for common anti-patterns.

    Returns a list of warning strings (empty if clean).
    """
    import re
    warnings = []
    for pattern, desc in HOOK_CHECK_LINT_RULES:
        if re.search(pattern, hook_check):
            warnings.append(desc)
    return warnings


MAX_LINT_RETRIES = 2


def _build_lint_fix_prompt(pattern: dict, hook_check: str, warnings: list[str]) -> str:
    """Build a prompt asking Claude to fix a broken hook_check command."""
    warning_text = "\n".join(f"- {w}" for w in warnings)
    return (
        "You previously generated this shell command for a hook check, but it has issues:\n\n"
        f"Pattern: {pattern['id']}\n"
        f"Rule: {pattern['rule']}\n"
        f"Current hook_check: {hook_check}\n\n"
        f"Issues found:\n{warning_text}\n\n"
        "Fix the command. Requirements:\n"
        "- The exit code of the LAST command in the pipeline determines the result\n"
        "- Do NOT pipe to head, tail, or wc — they always exit 0 regardless of input\n"
        "- Use grep -q for existence checks (exits 0 if found, 1 if not)\n"
        "- If you need to filter then check, pipe through grep then end with grep -q\n"
        "- The file path is passed as $1\n"
        "- Exit 0 = violation found, Exit 1 = no violation\n\n"
        'Return ONLY the fixed shell command as a JSON object: {"hook_check": "fixed command"}\n'
        "Return ONLY the JSON object, no other text."
    )


def enrich_single_hook(pattern: dict) -> dict | None:
    """Enrich a single hook pattern via Claude. Returns hook fields or None on failure."""
    prompt = build_enrich_hooks_prompt(pattern)
    response = call_claude(prompt, timeout=120)
    result = parse_json_object(response)
    if not result:
        return None

    # Validate required hook fields
    if not result.get("hook_event") or not result.get("hook_check"):
        return None

    # Lint the generated shell command and re-prompt Claude to fix issues
    pid = pattern.get("id", "?")
    for attempt in range(MAX_LINT_RETRIES):
        warnings = _lint_hook_check(result["hook_check"])
        if not warnings:
            break
        for w in warnings:
            print(f"  Lint ({pid}, attempt {attempt + 1}): {w}", file=sys.stderr)
        fix_prompt = _build_lint_fix_prompt(pattern, result["hook_check"], warnings)
        fix_response = call_claude(fix_prompt, timeout=60)
        fix_result = parse_json_object(fix_response)
        if fix_result and fix_result.get("hook_check"):
            result["hook_check"] = fix_result["hook_check"]
        else:
            print(f"  Lint fix failed for {pid}, keeping original", file=sys.stderr)
            break

    # Final lint check — reject if still broken
    final_warnings = _lint_hook_check(result["hook_check"])
    if final_warnings:
        print(f"  Rejecting {pid}: hook_check still has issues after {MAX_LINT_RETRIES} fix attempts",
              file=sys.stderr)
        return None

    # Reject hooks that Claude itself assessed as high false positive risk
    fp_risk = result.get("hook_fp_risk", "").upper()
    if fp_risk == "HIGH":
        print(f"  Rejecting {pid}: Claude assessed hook_fp_risk as HIGH (too noisy)",
              file=sys.stderr)
        return None

    return result


def cmd_enrich_hooks(args):
    """Enrich hook-worthy patterns with hook_event, hook_glob, hook_check, etc."""
    input_file = args.input
    force = args.force
    max_workers = args.workers

    with open(input_file) as f:
        patterns = json.load(f)

    # Filter to hook enrichment population: mode=hook + not already enriched
    candidates = []
    candidate_indices = []
    for i, p in enumerate(patterns):
        if p.get("mode") != "hook":
            continue
        if not force and p.get("hook_event"):
            continue
        candidates.append(p)
        candidate_indices.append(i)

    print(f"Loaded {len(patterns)} patterns, {len(candidates)} eligible for hook enrichment", flush=True)

    if not candidates:
        print("No hook patterns to enrich.")
        return

    enriched_count = 0
    failed_count = 0

    def process(idx_pattern):
        idx, pattern = idx_pattern
        result = enrich_single_hook(pattern)
        return idx, pattern["id"], result

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process, (candidate_indices[i], c)): i
            for i, c in enumerate(candidates)
        }
        for future in concurrent.futures.as_completed(futures):
            try:
                idx, pid, result = future.result()
                if result:
                    p = patterns[idx]
                    for field in HOOK_ENRICHMENT_FIELDS:
                        if field in result and result[field] is not None:
                            p[field] = result[field]
                    enriched_count += 1
                    print(f"  [{enriched_count}/{len(candidates)}] Enriched hook: {pid}", flush=True)
                else:
                    failed_count += 1
                    print(f"  Warning: hook enrichment failed for {pid}", file=sys.stderr)
                    # Fall back to active mode (will become a skill instead)
                    patterns[idx]["mode"] = "active"
                    patterns[idx]["mode_rationale"] = "Hook enrichment failed, fell back to active"
            except Exception as e:
                failed_count += 1
                print(f"  Error enriching hook pattern: {e}", file=sys.stderr)

    print(f"\nHook enrichment complete: {enriched_count} enriched, {failed_count} failed", flush=True)

    with open(input_file, "w") as f:
        json.dump(patterns, f, indent=2)

    print(f"Written to {input_file}", flush=True)


# ---------------------------------------------------------------------------
# Validate-hooks subcommand
# ---------------------------------------------------------------------------

def build_validate_hooks_prompt(batch: list[dict]) -> str:
    """Build the Claude prompt to validate hook_event/hook_blocking consistency."""
    hook_summaries = json.dumps(
        [{
            "id": p["id"],
            "rule": p["rule"],
            "scope": p.get("scope", ""),
            "hook_event": p.get("hook_event", ""),
            "hook_tool": p.get("hook_tool", ""),
            "hook_blocking": p.get("hook_blocking", False),
            "hook_glob": p.get("hook_glob", ""),
            "hook_check": p.get("hook_check", ""),
            "hook_message": p.get("hook_message", ""),
            "hook_fp_risk": p.get("hook_fp_risk", ""),
        } for p in batch],
        indent=2,
    )
    return (
        "You are reviewing automated hook configurations for correctness. "
        "Each hook has hook_event (PreToolUse or PostToolUse), hook_tool (Edit or Write), "
        "hook_blocking (true/false), and hook_fp_risk (LOW/MEDIUM/HIGH).\n\n"
        "Rules:\n"
        "- PreToolUse runs BEFORE the file edit is written. Use for checks that should "
        "PREVENT bad code from being written: auth gates, secret leakage, credential safety, "
        "data loss prevention. Blocking makes sense here — it stops the edit.\n"
        "- PostToolUse runs AFTER the file edit is written. Use for checks that INSPECT "
        "the result: consumer audits, quality warnings, compatibility checks. "
        "Blocking does NOT make sense here — the edit is already written, blocking just "
        "forces the developer to address it before continuing.\n"
        "- hook_tool determines WHICH tool triggers the hook:\n"
        '  - "Edit" = fires when modifying an existing file (most common — the vast majority of code changes)\n'
        '  - "Write" = fires only when creating a brand new file\n'
        '  - Most hooks should use "Edit" because that is where the majority of code changes happen. '
        '"Write" alone misses edits to existing files, which is almost always wrong. '
        'Use "Write" ONLY if the check genuinely applies only to newly created files.\n'
        "- hook_fp_risk: Look at the hook_check command and the hook_glob together. "
        "Will this grep fire on almost every file matching the glob? If so, it's HIGH risk "
        "and should be demoted (set demote: true). A good hook targets a SPECIFIC anti-pattern "
        "that is rare in correct code.\n"
        "- Actionability: A hook must change behavior compared to an ambient rule. Ask: "
        "does this hook BLOCK a bad edit (PreToolUse+blocking) or provide SPECIFIC actionable "
        "output (e.g., a list of affected consumers, the exact offending line)? "
        "A PostToolUse non-blocking hook that just says 'check X before merging' or "
        "'verify consumers' adds no value over the ambient rule that already says the same thing. "
        "Demote these — they are reminders, not enforcement.\n\n"
        "For each hook, decide:\n"
        "1. Is hook_event correct? Should a preventive check be PreToolUse instead of PostToolUse?\n"
        "2. Is hook_blocking appropriate? Blocking PostToolUse is a contradiction.\n"
        '3. Is hook_tool correct? Should "Write" be "Edit"?\n'
        "4. Is the signal-to-noise ratio acceptable? Look at hook_check + hook_glob: will this "
        "fire on nearly every edit to matching files? If yes, set demote: true.\n"
        "5. Is this hook actionable? A PostToolUse non-blocking hook that only says "
        "'verify X' or 'check Y before merging' without blocking or providing specific "
        "data (consumer lists, exact violations) is just a reminder — demote it.\n\n"
        f"Hooks to review:\n{hook_summaries}\n\n"
        "Return ONLY a JSON array of corrections. Each correction:\n"
        '{"id": "pattern-id", "hook_event": "corrected or omit", '
        '"hook_tool": "corrected or omit", '
        '"hook_blocking": "corrected or omit", '
        '"demote": true (if hook should be demoted to skill due to high FP risk — omit if not), '
        '"rationale": "one sentence explaining the change"}\n\n'
        "Only include hooks that NEED changes. If a hook is already correct, omit it.\n"
        "Return an empty array [] if all hooks are correct.\n\n"
        "Return ONLY the JSON array, no other text."
    )


def cmd_validate_hooks(args):
    """Validate hook_event/hook_blocking consistency via a second Claude pass."""
    input_file = args.input
    dry_run = args.dry_run
    batch_size = 50

    with open(input_file) as f:
        patterns = json.load(f)

    # Filter to enriched hooks
    hooks = [p for p in patterns if p.get("mode") == "hook" and p.get("hook_event")]

    print(f"Loaded {len(patterns)} patterns, {len(hooks)} enriched hooks to validate", flush=True)

    if not hooks:
        print("No hooks to validate.")
        return

    batches = [hooks[i:i + batch_size] for i in range(0, len(hooks), batch_size)]
    corrections: dict[str, dict] = {}
    max_workers = getattr(args, 'workers', 4)

    def _validate_batch(batch_num_and_batch):
        batch_num, batch = batch_num_and_batch
        prompt = build_validate_hooks_prompt(batch)
        print(f"  Batch {batch_num}/{len(batches)}: sending {len(batch)} hooks to Claude...", flush=True)
        response = call_claude(prompt)
        parsed = parse_json_response(response)

        if not parsed:
            return {}

        batch_corrections = {}
        for item in parsed:
            if not isinstance(item, dict):
                continue
            pid = item.get("id", "")
            if pid and ("hook_event" in item or "hook_blocking" in item
                        or "hook_tool" in item or item.get("demote")):
                batch_corrections[pid] = item
        return batch_corrections

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_validate_batch, (bn, b)): bn
            for bn, b in enumerate(batches, 1)
        }
        for future in concurrent.futures.as_completed(futures):
            try:
                batch_corrections = future.result()
                corrections.update(batch_corrections)
            except Exception as e:
                print(f"  Error in validation batch: {e}", file=sys.stderr)

    if not corrections:
        print("\nAll hooks validated — no corrections needed.", flush=True)
        return

    print(f"\nValidation found {len(corrections)} hook(s) to correct:", flush=True)
    for pid, c in sorted(corrections.items()):
        print(f"  {pid}: {c.get('rationale', 'no rationale')}", flush=True)

    demotions = {pid for pid, c in corrections.items() if c.get("demote")}
    fixes = {pid for pid in corrections if pid not in demotions}

    if dry_run:
        print("\n[DRY RUN] No changes written to disk.")
        if demotions:
            print(f"\nDemotions to skill ({len(demotions)}):")
            for pid in sorted(demotions):
                print(f"  {pid}: {corrections[pid].get('rationale', '')}")
        if fixes:
            print(f"\nFixes ({len(fixes)}):")
            for pid in sorted(fixes):
                c = corrections[pid]
                old_p = next((p for p in hooks if p["id"] == pid), None)
                if old_p:
                    print(f"  {pid}: {old_p.get('hook_event')}/{old_p.get('hook_blocking')} → "
                          f"{c.get('hook_event', old_p.get('hook_event'))}/{c.get('hook_blocking', old_p.get('hook_blocking'))}")
        return

    # Apply corrections
    for p in patterns:
        pid = p.get("id", "")
        if pid in corrections:
            c = corrections[pid]
            if c.get("demote"):
                p["mode"] = "active"
                p["mode_rationale"] = f"Demoted from hook: {c.get('rationale', 'high false positive risk')}"
                print(f"  Demoted to skill: {pid}", flush=True)
            else:
                if "hook_event" in c:
                    p["hook_event"] = c["hook_event"]
                if "hook_tool" in c:
                    p["hook_tool"] = c["hook_tool"]
                if "hook_blocking" in c:
                    p["hook_blocking"] = c["hook_blocking"]
            p["hook_validation_rationale"] = c.get("rationale", "")

    with open(input_file, "w") as f:
        json.dump(patterns, f, indent=2)

    print(f"Applied {len(fixes)} fix(es), {len(demotions)} demotion(s) to {input_file}", flush=True)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def cmd_reclass(args):
    """Reclassify mode (ambient/active) for all patterns in patterns.json."""
    input_file = args.input

    with open(input_file) as f:
        patterns = json.load(f)

    before = defaultdict(int)
    after = defaultdict(int)

    for p in patterns:
        old_mode = p.get("mode", "ambient")
        before[old_mode] += 1
        # Skip patterns that have been triaged — triage decisions take precedence
        if p.get("skill_worthy") is not None:
            after[old_mode] += 1
            continue
        new_mode = determine_mode(p.get("scope", ""), p.get("rule", ""))
        after[new_mode] += 1
        p["mode"] = new_mode

    with open(input_file, "w") as f:
        json.dump(patterns, f, indent=2)

    print(f"Reclassified {len(patterns)} patterns in {input_file}")
    print(f"  Before: { {k: v for k, v in sorted(before.items())} }")
    print(f"  After:  { {k: v for k, v in sorted(after.items())} }")


def main():
    parser = argparse.ArgumentParser(
        description="Extract engineering best practices from PR review threads"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # fetch
    p_fetch = subparsers.add_parser("fetch", help="Fetch merged PR review threads")
    p_fetch.add_argument("--repo", required=True, help="GitHub repo (owner/name)")
    p_fetch.add_argument("--since", required=True, help="Fetch PRs merged since (YYYY-MM-DD)")
    p_fetch.add_argument("--until", default=None, help="Fetch PRs merged before (YYYY-MM-DD)")
    p_fetch.add_argument("--batch-size", type=int, default=100, help="PRs per page (max 100)")

    # analyze
    p_analyze = subparsers.add_parser("analyze", help="Prepare review threads for pattern extraction")
    p_analyze.add_argument("--input", required=True, help="Directory with raw review JSON files")
    p_analyze.add_argument("--output", default="patterns.json", help="Output patterns file")

    # merge
    p_merge = subparsers.add_parser("merge", help="Merge extracted patterns into patterns.json")
    p_merge.add_argument("--input", required=True, help="Directory with extracted pattern JSON files")
    p_merge.add_argument("--output", default="patterns.json", help="Output patterns file")

    # modules
    p_modules = subparsers.add_parser("modules", help="Auto-detect modules from patterns")
    p_modules.add_argument("--input", default="patterns.json", help="Patterns JSON file")
    p_modules.add_argument("--output", default="modules.yaml", help="Output modules YAML file")

    # report
    p_report = subparsers.add_parser("report", help="Generate validation report")
    p_report.add_argument("--input", required=True, help="Patterns JSON file")
    p_report.add_argument("--output", default="validation-report.md", help="Output report file")

    # reclass
    p_reclass = subparsers.add_parser("reclass", help="Reclassify pattern modes (ambient/active/hook)")
    p_reclass.add_argument("--input", default="patterns.json", help="Patterns JSON file to reclassify in-place")

    # dedup
    p_dedup = subparsers.add_parser("dedup", help="Deduplicate patterns (exact ID + LLM semantic)")
    p_dedup.add_argument("--input", default="patterns.json", help="Patterns JSON file to deduplicate in-place")
    p_dedup.add_argument("--workers", type=int, default=4, help="Number of parallel Claude calls")

    # triage
    p_triage = subparsers.add_parser("triage", help="Score active patterns on skill-worthiness")
    p_triage.add_argument("--input", default="patterns.json", help="Patterns JSON file to triage in-place")
    p_triage.add_argument("--dry-run", action="store_true", help="Print results without writing to disk")
    p_triage.add_argument("--force", action="store_true", help="Re-triage already-triaged patterns")
    p_triage.add_argument("--workers", type=int, default=4, help="Number of parallel Claude calls")

    # enrich
    p_enrich = subparsers.add_parser("enrich", help="Enrich skill-worthy patterns with steps and examples")
    p_enrich.add_argument("--input", default="patterns.json", help="Patterns JSON file to enrich in-place")
    p_enrich.add_argument("--force", action="store_true", help="Re-enrich already-enriched patterns")
    p_enrich.add_argument("--workers", type=int, default=4, help="Number of parallel Claude calls")

    # enrich-hooks
    p_enrich_hooks = subparsers.add_parser("enrich-hooks", help="Enrich hook-worthy patterns with hook metadata")
    p_enrich_hooks.add_argument("--input", default="patterns.json", help="Patterns JSON file to enrich in-place")
    p_enrich_hooks.add_argument("--force", action="store_true", help="Re-enrich already-enriched hook patterns")
    p_enrich_hooks.add_argument("--workers", type=int, default=4, help="Number of parallel Claude calls")

    # validate-hooks
    p_validate_hooks = subparsers.add_parser("validate-hooks", help="Validate hook_event/hook_blocking consistency")
    p_validate_hooks.add_argument("--input", default="patterns.json", help="Patterns JSON file to validate in-place")
    p_validate_hooks.add_argument("--dry-run", action="store_true", help="Print corrections without writing to disk")
    p_validate_hooks.add_argument("--workers", type=int, default=4, help="Number of parallel Claude calls")

    args = parser.parse_args()

    commands = {
        "fetch": cmd_fetch,
        "analyze": cmd_analyze,
        "merge": cmd_merge,
        "modules": cmd_modules,
        "report": cmd_report,
        "reclass": cmd_reclass,
        "dedup": cmd_dedup,
        "triage": cmd_triage,
        "enrich": cmd_enrich,
        "enrich-hooks": cmd_enrich_hooks,
        "validate-hooks": cmd_validate_hooks,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
