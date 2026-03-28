#!/usr/bin/env python3
"""
Extraction pipeline for mining best practices from GitHub PR review threads.

Usage:
  python extract.py fetch --repo cerebrotech/domino --since 2024-01-01
  python extract.py analyze --input raw-reviews/ --output patterns.json
  python extract.py report --input patterns.json --output validation-report.md
"""

import argparse
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
    Both    — universal constraint that also has detailed step-by-step guidance.
    """
    rule_lower = rule.lower()

    # Contextual/triggered patterns -> active (skills)
    if rule_lower.startswith(("when ", "before ", "after ", "if ")):
        return "active"

    # Multi-step processes -> active (skills)
    if any(marker in rule_lower for marker in ("step 1", "1.", "2.", "first,", "then,")):
        return "active"

    # Very long rules (300+ chars) are detailed guides, better as skills
    if len(rule) > 300:
        return "both"

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
        "mode": determine_mode(category, rule),
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

def call_claude(prompt: str, timeout: int = 120) -> str:
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


def parse_json_response(text: str) -> list:
    """Parse a JSON array from Claude's response, handling markdown code blocks."""
    text = text.strip()
    if not text:
        return []
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]  # remove opening ```json
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
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
    print(f"Loaded {original_count} patterns from {input_file}")

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

    print(f"Pass 1 (exact ID): merged {id_merge_count} duplicates, {len(id_merged)} remaining")

    # --- Pass 2: LLM semantic dedup within each scope ---
    by_scope: dict[str, list[dict]] = defaultdict(list)
    for p in id_merged:
        by_scope[p.get("scope", "general")].append(p)

    final_patterns = []
    llm_merge_count = 0

    for scope, scope_patterns in sorted(by_scope.items()):
        if len(scope_patterns) <= 1:
            final_patterns.extend(scope_patterns)
            continue

        # Batch into groups of 50 for LLM processing
        batches = [scope_patterns[i:i + 50] for i in range(0, len(scope_patterns), 50)]

        for batch_num, batch in enumerate(batches, 1):
            if len(batch) <= 1:
                final_patterns.extend(batch)
                continue

            pattern_list = json.dumps(
                [{"index": i, "id": p["id"], "rule": p["rule"]} for i, p in enumerate(batch)],
                indent=2,
            )

            prompt = (
                "You are deduplicating patterns extracted from code review history.\n\n"
                f"Below is a list of patterns in the \"{scope}\" category. Identify groups of "
                "patterns that describe the SAME underlying rule or convention, even if worded "
                "differently.\n\n"
                "Return ONLY a JSON array of groups. Each group is an array of index numbers "
                "that should be merged. Only include groups with 2+ patterns. Patterns that "
                "are unique should NOT appear in any group. Be conservative — only group "
                "patterns that are clearly about the same thing.\n\n"
                f"Patterns:\n{pattern_list}\n\n"
                "Return ONLY the JSON array, e.g.: [[0, 3, 7], [2, 5]]"
            )

            print(f"  Scope '{scope}' batch {batch_num}/{len(batches)}: "
                  f"sending {len(batch)} patterns to Claude...")
            response = call_claude(prompt)
            groups = parse_json_response(response)

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

        print(f"  Scope '{scope}': {len(scope_patterns)} → "
              f"{len(scope_patterns) - llm_merge_count} patterns")

    print(f"\nPass 2 (LLM semantic): merged {llm_merge_count} duplicates")
    print(f"\nDedup complete: {original_count} → {len(final_patterns)} patterns")

    with open(input_file, "w") as f:
        json.dump(final_patterns, f, indent=2)
    print(f"Written to {input_file}")


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
    p_reclass = subparsers.add_parser("reclass", help="Reclassify pattern modes (ambient/active)")
    p_reclass.add_argument("--input", default="patterns.json", help="Patterns JSON file to reclassify in-place")

    # dedup
    p_dedup = subparsers.add_parser("dedup", help="Deduplicate patterns (exact ID + LLM semantic)")
    p_dedup.add_argument("--input", default="patterns.json", help="Patterns JSON file to deduplicate in-place")

    args = parser.parse_args()

    commands = {
        "fetch": cmd_fetch,
        "analyze": cmd_analyze,
        "merge": cmd_merge,
        "modules": cmd_modules,
        "report": cmd_report,
        "reclass": cmd_reclass,
        "dedup": cmd_dedup,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
