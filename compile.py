#!/usr/bin/env python3
"""Compile patterns.json into Claude Code rules, Claude Code skills, and Cursor rules."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

REQUIRED_FIELDS = {"id", "rule", "scope", "modules", "mode", "status"}
GLOBAL_MODULE_THRESHOLD = 3
MIN_REVIEW_COUNT = 2
MAX_RULES_PER_FILE = 30


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
               and p["mode"] in ("ambient", "both")
               and p.get("rule", "").strip()]  # skip empty rules
    groups = group_by_module(ambient)
    rules_dir = os.path.join(output_dir, ".claude", "rules")
    os.makedirs(rules_dir, exist_ok=True)

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


def generate_claude_skills(patterns: list[dict], output_dir: str) -> list[str]:
    """Generate .claude/skills/{topic}/SKILL.md files. Returns list of created paths."""
    active = [p for p in patterns if p["mode"] in ("active", "both")
              and p.get("review_count", 1) >= MIN_REVIEW_COUNT]
    skills_dir = os.path.join(output_dir, ".claude", "skills")
    created = []

    for p in active:
        topic = f"mined-{p['id']}"
        skill_dir = os.path.join(skills_dir, topic)
        os.makedirs(skill_dir, exist_ok=True)
        filepath = os.path.join(skill_dir, "SKILL.md")

        name = p["id"].replace("-", " ").replace("_", " ").title()
        sources = ", ".join(p.get("source_prs", []))

        lines = [
            "---",
            f"name: {p['id']}",
            f"description: {p['rule']}",
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
        if p.get("steps"):
            for step in p["steps"]:
                lines.append(f"- {step}")
        else:
            lines.append(p["rule"])
        lines.append("")

        if p.get("good_example") or p.get("bad_example"):
            lines.append("## Examples")

        if p.get("bad_example"):
            lines.append(f"**Bad:** {p['bad_example']}")
            lines.append("")
        if p.get("good_example"):
            lines.append(f"**Good:** {p['good_example']}")

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
    ambient = [p for p in patterns if p["mode"] in ("ambient", "both")]

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
