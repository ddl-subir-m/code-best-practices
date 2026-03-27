#!/usr/bin/env python3
"""Compile patterns.json into Claude Code rules, Claude Code skills, and Cursor rules."""

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

REQUIRED_FIELDS = {"id", "rule", "scope", "modules", "mode", "status"}
GLOBAL_MODULE_THRESHOLD = 3


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


def load_modules_yaml(output_dir: str) -> dict[str, str]:
    """Load modules.yaml if it exists, returning module_key -> display_name mapping."""
    yaml_path = os.path.join(os.path.dirname(output_dir.rstrip("/")), "modules.yaml")
    if not os.path.exists(yaml_path):
        # Also check in the current working directory
        yaml_path = "modules.yaml"
    if not os.path.exists(yaml_path):
        return {}

    try:
        import yaml
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        if isinstance(data, dict):
            return {k: v if isinstance(v, str) else v.get("display_name", k) for k, v in data.items()}
    except Exception:
        pass
    return {}


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
        lines.append(f"  Sources: PR {', '.join(p['source_prs'])}")
    return "\n".join(lines)


def generate_claude_rules(patterns: list[dict], output_dir: str, modules_map: dict[str, str]) -> list[str]:
    """Generate .claude/rules/{module}-practices.md files. Returns list of created paths."""
    # Filter to ambient patterns only (ambient or both)
    ambient = [p for p in patterns if p["mode"] in ("ambient", "both")]
    groups = group_by_module(ambient)
    rules_dir = os.path.join(output_dir, ".claude", "rules")
    os.makedirs(rules_dir, exist_ok=True)

    created = []
    today = date.today().isoformat()

    for module, module_patterns in sorted(groups.items()):
        name = display_name(module, modules_map)
        filename = f"{module}-practices.md"
        filepath = os.path.join(rules_dir, filename)

        # Group by category within module
        by_category: dict[str, list[dict]] = defaultdict(list)
        for p in module_patterns:
            cat = p.get("category", p.get("scope", "general"))
            by_category[cat].append(p)

        lines = [
            f"# {name} Best Practices",
            f"Auto-generated from PR review history. Do not edit manually.",
            f"Source: patterns.json | Generated: {today}",
            "",
        ]

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
    active = [p for p in patterns if p["mode"] in ("active", "both")]
    skills_dir = os.path.join(output_dir, ".claude", "skills")
    created = []

    for p in active:
        topic = p["id"]
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
            p.get("rationale", ""),
            "",
            "## When to apply",
            p.get("trigger", ""),
            "",
            "## Steps",
            p["rule"],
            "",
            "## Examples",
        ]

        if p.get("good_example"):
            lines.append(f"Good: {p['good_example']}")
        if p.get("bad_example"):
            lines.append(f"Bad: {p['bad_example']}")

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

    modules_map = load_modules_yaml(args.output)

    # Generate all outputs
    rules = generate_claude_rules(patterns, args.output, modules_map)
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
