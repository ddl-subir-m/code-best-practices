"""Merge extracted patterns into patterns.json and pattern utilities."""

import json
import os
import sys
from pathlib import Path

from .constants import DEFAULT_CATEGORY, VALID_CATEGORIES


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
    category = raw.get("category", DEFAULT_CATEGORY)
    if category not in VALID_CATEGORIES:
        category = DEFAULT_CATEGORY

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


def merge_duplicate_group(patterns: list[dict]) -> dict:
    """Merge a group of duplicate patterns into one canonical pattern."""
    base = max(patterns, key=lambda p: len(p.get("rule", "")))
    merged = dict(base)
    # Copy mutable nested lists so appends don't mutate the original pattern
    merged["source_prs"] = list(base.get("source_prs", []))
    merged["modules"] = list(base.get("modules", []))

    for p in patterns:
        if p is base:
            continue
        merged["review_count"] = merged.get("review_count", 1) + p.get("review_count", 1)
        for pr in p.get("source_prs", []):
            if pr not in merged["source_prs"]:
                merged["source_prs"].append(pr)
        for mod in p.get("modules", []):
            if mod not in merged["modules"]:
                merged["modules"].append(mod)

    merged["confidence"] = min(1.0, merged["review_count"] / 10)
    return merged


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
