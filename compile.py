#!/usr/bin/env python3
"""Compile patterns.json into Claude Code rules, Claude Code skills, and Cursor rules."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

REQUIRED_FIELDS = {"id", "rule", "scope", "modules", "mode", "status"}
GLOBAL_MODULE_THRESHOLD = 3
MIN_REVIEW_COUNT = 2
MAX_RULES_PER_FILE = 15


def load_patterns(path: str) -> list[dict]:
    """Load and validate patterns.json."""
    try:
        with open(path) as f:
            data = json.load(f)
    except FileNotFoundError:
        sys.exit(f"Error: {path} not found")
    except json.JSONDecodeError as e:
        sys.exit(f"Error: invalid JSON in {path}: {e}")

    if not isinstance(data, list):
        sys.exit(f"Error: {path} must contain a JSON array")

    active = []
    for i, pattern in enumerate(data):
        missing = REQUIRED_FIELDS - set(pattern.keys())
        if missing:
            sys.exit(f"Error: pattern at index {i} missing required fields: {', '.join(sorted(missing))}")
        if pattern["status"] != "active":
            continue
        active.append(pattern)

    return active


def load_modules_yaml(output_dir: str) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Load modules.yaml if it exists.

    Returns (module_key -> display_name, module_key -> glob_paths).
    """
    yaml_path = os.path.join(os.path.dirname(output_dir.rstrip("/")), "modules.yaml")
    if not os.path.exists(yaml_path):
        yaml_path = "modules.yaml"
    if not os.path.exists(yaml_path):
        return {}, {}

    try:
        import yaml
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        if isinstance(data, dict):
            modules = data.get("modules", data)
            names = {}
            globs = {}
            for k, v in modules.items():
                if isinstance(v, str):
                    names[k] = v
                elif isinstance(v, dict):
                    names[k] = v.get("display_name", k)
                elif isinstance(v, list):
                    # v is a list of path prefixes like ["/frontend/"]
                    # Convert to globs: /frontend/ -> frontend/**
                    globs[k] = [p.strip("/") + "/**" for p in v if p != "*"]
            return names, globs
    except Exception:
        pass
    return {}, {}


def display_name(module: str, modules_map: dict[str, str]) -> str:
    """Get the display name for a module."""
    return modules_map.get(module, module.replace("-", " ").replace("_", " ").title())


def group_by_module(patterns: list[dict]) -> dict[str, list[dict]]:
    """Group patterns by module. Patterns in 3+ modules go to 'global'."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for p in patterns:
        modules = p.get("modules", [])
        if len(modules) >= GLOBAL_MODULE_THRESHOLD:
            groups["global"].append(p)
        else:
            for mod in modules:
                groups[mod].append(p)
    return dict(groups)


def format_rule_entry(p: dict) -> str:
    """Format a single pattern as a markdown rule entry."""
    lines = [f"- {p['rule']}"]
    if p.get("rationale"):
        lines.append(f"  Rationale: {p['rationale']}")
    bad = p.get("bad_example")
    good = p.get("good_example")
    if bad and good:
        lines.append(f"  Bad: `{bad}` | Good: `{good}`")
    elif good:
        lines.append(f"  Good: `{good}`")
    elif bad:
        lines.append(f"  Bad: `{bad}`")
    if p.get("source_prs"):
        prs = p["source_prs"]
        if len(prs) > 5:
            lines.append(f"  Sources: {len(prs)} PRs")
        else:
            lines.append(f"  Sources: PR {', '.join(prs)}")
    return "\n".join(lines)


def generate_claude_rules(
    patterns: list[dict], output_dir: str, modules_map: dict[str, str],
    globs_map: dict[str, list[str]] | None = None,
) -> list[str]:
    """Generate .claude/rules/{module}-practices.md files. Returns list of created paths."""
    globs_map = globs_map or {}
    # Only include patterns validated by repetition (review_count >= MIN_REVIEW_COUNT).
    # Active-mode patterns that meet the threshold become skills instead (handled separately).
    ambient = [p for p in patterns if p.get("review_count", 1) >= MIN_REVIEW_COUNT
               and p["mode"] == "ambient"
               and p.get("rule", "").strip()]  # skip empty rules
    groups = group_by_module(ambient)
    rules_dir = os.path.join(output_dir, ".claude", "rules")
    os.makedirs(rules_dir, exist_ok=True)

    # Clean up stale mined-* rule files from previous runs
    for old in Path(rules_dir).glob("mined-*-practices.md"):
        old.unlink()

    created = []
    today = date.today().isoformat()

    for module, module_patterns in sorted(groups.items()):
        name = display_name(module, modules_map)
        filename = f"mined-{module}-practices.md"
        filepath = os.path.join(rules_dir, filename)

        # Cap rules per file: keep highest review_count patterns
        ranked = sorted(module_patterns, key=lambda p: p.get("review_count", 1), reverse=True)
        capped = ranked[:MAX_RULES_PER_FILE]
        if len(ranked) > MAX_RULES_PER_FILE:
            print(f"  {module}: capped {len(ranked)} → {MAX_RULES_PER_FILE} rules (by review_count)")

        # Group by category within module
        by_category: dict[str, list[dict]] = defaultdict(list)
        for p in capped:
            cat = p.get("category", p.get("scope", "general"))
            by_category[cat].append(p)

        # Build frontmatter with globs so rules only load for relevant files
        lines = ["---"]
        if module != "global" and module in globs_map:
            glob_list = ", ".join(globs_map[module])
            lines.append(f"globs: [{glob_list}]")
        lines.append(f"description: {name} best practices from PR review history")
        lines.append("---")
        lines.append("")
        lines.append(f"# {name} Best Practices")
        lines.append(f"Auto-generated from PR review history. Do not edit manually.")
        lines.append(f"Source: patterns.json | Generated: {today}")
        lines.append("")

        for cat in sorted(by_category.keys()):
            cat_display = cat.replace("-", " ").replace("_", " ").title()
            lines.append(f"## {cat_display}")
            for p in by_category[cat]:
                lines.append(format_rule_entry(p))
                lines.append("")

        with open(filepath, "w") as f:
            f.write("\n".join(lines))
        created.append(filepath)

    return created


def _has_steps(p: dict) -> bool:
    """Check if a pattern has non-empty enriched steps."""
    steps = p.get("steps")
    return isinstance(steps, list) and len(steps) > 0


def dedup_skills(patterns: list[dict]) -> list[dict]:
    """Deduplicate skills by grouping on shared ID prefixes.

    Skills like reuse-existing-ui-components, reuse-existing-shared-components,
    reuse-existing-hooks-and-utilities all share the prefix "reuse-existing" and
    describe the same convention. Keep only the one with the highest review_count.

    Enriched skills (non-empty steps) bypass prefix dedup — they were individually
    triaged and enriched, so they earned their spot.
    """
    enriched = []
    unenriched = []
    for p in patterns:
        if _has_steps(p):
            enriched.append(p)
        else:
            unenriched.append(p)

    # Only prefix-dedup unenriched skills
    groups: dict[str, list[dict]] = defaultdict(list)
    for p in unenriched:
        parts = p["id"].split("-")
        prefix = "-".join(parts[:3]) if len(parts) >= 3 else p["id"]
        groups[prefix].append(p)

    deduped = list(enriched)  # enriched pass through directly
    for prefix, group in groups.items():
        if len(group) == 1:
            deduped.append(group[0])
        else:
            best = max(group, key=lambda p: p.get("review_count", 1))
            deduped.append(best)
    return deduped


def _skill_description(p: dict) -> str:
    """Build a 'what + when' description for skill frontmatter."""
    rule = p.get("rule", "")
    trigger = p.get("trigger", "")
    if trigger:
        return f"{rule} Use when: {trigger}"
    return rule


def _slugify_title(title: str) -> str:
    """Convert a skill title to a URL-safe slug."""
    slug = title.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def generate_claude_skills(patterns: list[dict], output_dir: str) -> list[str]:
    """Generate .claude/skills/{topic}/SKILL.md files. Returns list of created paths."""
    active = [p for p in patterns if p["mode"] == "active"
              and p.get("review_count", 1) >= MIN_REVIEW_COUNT]
    active = dedup_skills(active)

    # Safety net: skip patterns with empty steps (they'd produce hollow skills)
    active = [p for p in active if _has_steps(p)]

    skills_dir = os.path.join(output_dir, ".claude", "skills")

    # Clean up stale mined-* skill dirs from previous runs
    if os.path.exists(skills_dir):
        for old in Path(skills_dir).iterdir():
            if old.is_dir() and old.name.startswith("mined-"):
                shutil.rmtree(old)

    created = []

    for p in active:
        # Use skill_title for directory name if available
        if p.get("skill_title"):
            topic = f"mined-{_slugify_title(p['skill_title'])}"
        else:
            topic = f"mined-{p['id']}"
        skill_dir = os.path.join(skills_dir, topic)
        os.makedirs(skill_dir, exist_ok=True)
        filepath = os.path.join(skill_dir, "SKILL.md")

        # Use skill_title for display name, fall back to title-cased id
        name = p.get("skill_title") or p["id"].replace("-", " ").replace("_", " ").title()
        sources = ", ".join(p.get("source_prs", []))
        description = _skill_description(p)

        lines = [
            "---",
            f"name: {p['id']}",
            f"description: {description}",
            "---",
            f"# {name}",
            "",
        ]

        if p.get("rationale"):
            lines.append(p["rationale"])
            lines.append("")

        if p.get("trigger"):
            lines.append("## When to apply")
            lines.append(p["trigger"])
            lines.append("")

        lines.append("## Steps")
        for i, step in enumerate(p["steps"], 1):
            lines.append(f"{i}. {step}")
        lines.append("")

        if p.get("good_example") or p.get("bad_example"):
            lines.append("## Examples")
            lines.append("")

        if p.get("bad_example"):
            lines.append(f"**Bad:**\n```\n{p['bad_example']}\n```")
            lines.append("")
        if p.get("good_example"):
            lines.append(f"**Good:**\n```\n{p['good_example']}\n```")

        lines.append("")
        if sources:
            lines.append(f"Sources: PR {sources}")

        with open(filepath, "w") as f:
            f.write("\n".join(lines))
        created.append(filepath)

    return created


def generate_cursorrules(patterns: list[dict], output_dir: str, merge_path: str | None, modules_map: dict[str, str]) -> str:
    """Generate .cursorrules file, merging with existing if provided. Returns path."""
    # Use only global-scope patterns (in 3+ modules) plus ambient patterns
    ambient = [p for p in patterns if p["mode"] == "ambient"]

    today = date.today().isoformat()
    marker = "## Auto-generated from PR review mining"

    # Group by category for the generated section
    by_category: dict[str, list[dict]] = defaultdict(list)
    for p in ambient:
        cat = p.get("category", p.get("scope", "general"))
        by_category[cat].append(p)

    gen_lines = [
        marker,
        f"Source: patterns.json | Generated: {today}",
        "",
    ]
    for cat in sorted(by_category.keys()):
        cat_display = cat.replace("-", " ").replace("_", " ").title()
        gen_lines.append(f"### {cat_display}")
        for p in by_category[cat]:
            gen_lines.append(format_rule_entry(p))
            gen_lines.append("")

    generated_section = "\n".join(gen_lines)

    # Merge with existing cursorrules if provided
    existing_content = ""
    if merge_path and os.path.exists(merge_path):
        with open(merge_path) as f:
            existing_content = f.read()

    if existing_content and marker in existing_content:
        # Replace the existing auto-generated section
        before = existing_content.split(marker)[0].rstrip()
        output_content = before + "\n\n" + generated_section
    elif existing_content:
        # Append
        output_content = existing_content.rstrip() + "\n\n" + generated_section
    else:
        output_content = generated_section

    filepath = os.path.join(output_dir, ".cursorrules")
    with open(filepath, "w") as f:
        f.write(output_content + "\n")

    return filepath


def main():
    parser = argparse.ArgumentParser(description="Compile patterns.json into AI coding assistant rules")
    parser.add_argument("--input", required=True, help="Path to patterns.json")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--cursorrules-merge", default=None, help="Path to existing .cursorrules to merge with")
    args = parser.parse_args()

    patterns = load_patterns(args.input)
    if not patterns:
        print("No active patterns found. Nothing to generate.")
        return

    modules_map, globs_map = load_modules_yaml(args.output)

    # Generate all outputs
    rules = generate_claude_rules(patterns, args.output, modules_map, globs_map)
    skills = generate_claude_skills(patterns, args.output)
    cursorrules = generate_cursorrules(patterns, args.output, args.cursorrules_merge, modules_map)

    print(f"Generated {len(rules)} Claude rule file(s):")
    for r in rules:
        print(f"  {r}")
    print(f"Generated {len(skills)} Claude skill(s):")
    for s in skills:
        print(f"  {s}")
    print(f"Generated Cursor rules: {cursorrules}")


if __name__ == "__main__":
    main()
