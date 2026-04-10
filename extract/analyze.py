"""Analyze review threads for generalizable patterns."""

import json
import os
import sys
from collections import defaultdict
from pathlib import Path

from .constants import BOT_AUTHORS, VALID_CATEGORIES


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
    print(f"  python -m extract merge --input <results-dir> --output {output_file}")
