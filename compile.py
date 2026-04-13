#!/usr/bin/env python3
"""Compile patterns.json into Claude Code + Cursor rules, skills, and hooks."""

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


def _select_active_skill_patterns(patterns: list[dict]) -> list[dict]:
    """Return the enriched, deduped active-mode patterns eligible for skill generation."""
    active = [p for p in patterns if p["mode"] == "active"
              and p.get("review_count", 1) >= MIN_REVIEW_COUNT]
    active = dedup_skills(active)
    # Safety net: skip patterns with empty steps (they'd produce hollow skills)
    return [p for p in active if _has_steps(p)]


def _skill_dirname(p: dict) -> str:
    """Return the mined-* directory name for a skill pattern."""
    if p.get("skill_title"):
        return f"mined-{_slugify_title(p['skill_title'])}"
    return f"mined-{p['id']}"


def _render_skill_md(p: dict) -> str:
    """Render the SKILL.md body for a pattern. Shared by Claude and Cursor skill generators."""
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

    return "\n".join(lines)


def _write_skill_dirs(patterns: list[dict], skills_dir: str) -> list[str]:
    """Create mined-* skill dirs with SKILL.md under skills_dir. Cleans stale mined-* first."""
    if os.path.exists(skills_dir):
        for old in Path(skills_dir).iterdir():
            if old.is_dir() and old.name.startswith("mined-"):
                shutil.rmtree(old)

    created = []
    for p in patterns:
        skill_dir = os.path.join(skills_dir, _skill_dirname(p))
        os.makedirs(skill_dir, exist_ok=True)
        filepath = os.path.join(skill_dir, "SKILL.md")
        with open(filepath, "w") as f:
            f.write(_render_skill_md(p))
        created.append(filepath)
    return created


def generate_claude_skills(patterns: list[dict], output_dir: str) -> list[str]:
    """Generate .claude/skills/{topic}/SKILL.md files. Returns list of created paths."""
    active = _select_active_skill_patterns(patterns)
    skills_dir = os.path.join(output_dir, ".claude", "skills")
    return _write_skill_dirs(active, skills_dir)


def generate_cursor_skills(patterns: list[dict], output_dir: str) -> list[str]:
    """Generate .cursor/skills/{topic}/SKILL.md files. Returns list of created paths.

    Cursor and Claude Code share the same SKILL.md format, so the content is identical —
    Cursor just reads from its own directory. (Cursor also falls back to .claude/skills/
    for legacy compat, but emitting to .cursor/skills/ keeps the output self-describing.)
    """
    active = _select_active_skill_patterns(patterns)
    if not active:
        return []
    skills_dir = os.path.join(output_dir, ".cursor", "skills")
    return _write_skill_dirs(active, skills_dir)


def generate_hooks(patterns: list[dict], output_dir: str) -> tuple[list[str], str | None]:
    """Generate .claude/hooks/*.sh scripts and settings-hooks.json.

    Returns (list of created script paths, path to settings-hooks.json or None).
    """
    hook_patterns = [p for p in patterns if p.get("mode") == "hook"
                     and p.get("hook_check")
                     and p.get("hook_event")]

    if not hook_patterns:
        return [], None

    hooks_dir = os.path.join(output_dir, ".claude", "hooks")
    os.makedirs(hooks_dir, exist_ok=True)

    # Clean up stale mined-* hook scripts from previous runs
    for old in Path(hooks_dir).glob("mined-*.sh"):
        old.unlink()

    created_scripts = []
    settings_hooks: dict[str, list[dict]] = {}

    for p in hook_patterns:
        # Generate script filename from pattern id
        script_name = f"mined-{p['id']}.sh"
        script_path = os.path.join(hooks_dir, script_name)

        hook_event = p.get("hook_event", "PostToolUse")
        hook_tool = p.get("hook_tool", "Edit")
        hook_glob = p.get("hook_glob", "**/*")
        hook_check = p["hook_check"]
        hook_message = p.get("hook_message", f"Hook triggered: {p['rule']}")
        hook_blocking = p.get("hook_blocking", False)

        # Escape single quotes in message for shell safety
        safe_message = hook_message.replace("'", "'\\''")
        suppress_comment = f"hook-ok: {p['id']}"

        # Write the shell script
        # Claude Code hook exit codes: 0 = pass (allow), non-zero = fail (block/warn)
        script_content = (
            "#!/usr/bin/env bash\n"
            "# Auto-generated hook script. Do not edit manually.\n"
            f"# Pattern: {p['id']}\n"
            f"# Rule: {p['rule']}\n"
            f"# Sources: {', '.join(p.get('source_prs', []))}\n"
            "#\n"
            "# Exit 0 = no violation (pass), Exit 1 = violation found (block/warn)\n"
            f"# Suppress with: // {suppress_comment}\n"
            "\n"
            'FILE="${1:?Usage: $0 <file>}"\n'
            "\n"
            "# Skip if file contains a suppression comment for this hook\n"
            f'grep -q "{suppress_comment}" "$FILE" && exit 0\n'
            "\n"
            "# Run the check in a subshell so embedded exits don't leak\n"
            f"if ( {hook_check} ); then\n"
            f"  echo '{safe_message}'\n"
            f"  echo 'Ask the developer: should I (1) fix the issue, or (2) suppress this check by adding // {suppress_comment} to the file?'\n"
            "  exit 1\n"
            "fi\n"
            "exit 0\n"
        )

        with open(script_path, "w") as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)
        created_scripts.append(script_path)

        # Build settings entry
        entry = {
            "matcher": hook_tool,
            "command": f".claude/hooks/{script_name} $FILE",
        }
        if hook_glob != "**/*":
            entry["fileGlob"] = hook_glob
        if hook_blocking:
            entry["blocking"] = True

        settings_hooks.setdefault(hook_event, []).append(entry)

    # Write settings-hooks.json
    settings_path = os.path.join(output_dir, ".claude", "settings-hooks.json")
    with open(settings_path, "w") as f:
        json.dump({"hooks": settings_hooks}, f, indent=2)

    return created_scripts, settings_path


def _glob_to_regex(glob: str) -> str:
    """Convert an extended glob (supports **, *, ?, {a,b,c}) to a POSIX ERE pattern.

    Returns a single regex that matches any of the brace-expanded alternatives,
    anchored at both ends. Used to embed path filtering directly inside Cursor
    hook scripts, since Cursor's afterFileEdit event has no config-level globbing.
    """
    def expand_braces(s: str) -> list[str]:
        m = re.search(r"\{([^{}]+)\}", s)
        if not m:
            return [s]
        before, after = s[: m.start()], s[m.end():]
        out = []
        for alt in m.group(1).split(","):
            for rest in expand_braces(after):
                out.append(before + alt + rest)
        return out

    def to_regex(p: str) -> str:
        out = []
        i = 0
        while i < len(p):
            c = p[i]
            if c == "*":
                if i + 1 < len(p) and p[i + 1] == "*":
                    out.append(".*")
                    i += 2
                    # Consume a trailing slash so **/foo matches foo at root too
                    if i < len(p) and p[i] == "/":
                        i += 1
                else:
                    out.append("[^/]*")
                    i += 1
            elif c == "?":
                out.append("[^/]")
                i += 1
            elif c in r".+^$()[]|\\":
                out.append("\\" + c)
                i += 1
            else:
                out.append(c)
                i += 1
        return "^" + "".join(out) + "$"

    return "|".join(to_regex(p) for p in expand_braces(glob))


# Cursor hook events: map Claude Code hook_event → (cursor_event, tool_matcher).
# matcher=None means the event is fired unconditionally; path filtering happens in-script.
_CURSOR_HOOK_EVENT_MAP = {
    "PostToolUse": ("afterFileEdit", None),
    "PreToolUse": ("preToolUse", "Write"),
}


def _shell_squote(s: str) -> str:
    """Wrap s in single quotes for bash, escaping any embedded single quotes safely."""
    return "'" + s.replace("'", "'\\''") + "'"


def _render_cursor_hook_script(p: dict) -> str:
    """Render a Cursor hook bash script. Reads JSON from stdin, emits JSON decision on stdout."""
    hook_check = p["hook_check"]
    hook_glob = p.get("hook_glob", "**/*")
    glob_regex = _glob_to_regex(hook_glob)
    hook_message = p.get("hook_message", f"Hook triggered: {p['rule']}")
    hook_blocking = p.get("hook_blocking", False)
    suppress_comment = f"hook-ok: {p['id']}"

    # Compact JSON (no spaces) keeps the generated scripts readable and tests stable.
    allow_json = json.dumps({"permission": "allow"}, separators=(",", ":"))
    if hook_blocking:
        deny_json = json.dumps({
            "permission": "deny",
            "user_message": f"{hook_message} (suppress with // {suppress_comment})",
            "agent_message": hook_message,
        }, separators=(",", ":"))
        violation_exit = "2"
    else:
        # Non-blocking: surface the message to the user but allow the action.
        deny_json = json.dumps({
            "permission": "allow",
            "user_message": hook_message,
        }, separators=(",", ":"))
        violation_exit = "0"

    # Single-quote everything we hand to the shell so $, `, \, etc. stay literal.
    glob_regex_q = _shell_squote(glob_regex)
    suppress_q = _shell_squote(suppress_comment)
    allow_q = _shell_squote(allow_json)
    deny_q = _shell_squote(deny_json)

    return (
        "#!/usr/bin/env bash\n"
        "# Auto-generated Cursor hook script. Do not edit manually.\n"
        f"# Pattern: {p['id']}\n"
        f"# Rule: {p['rule']}\n"
        f"# Sources: {', '.join(p.get('source_prs', []))}\n"
        "#\n"
        f"# Suppress with: // {suppress_comment}\n"
        "\n"
        "INPUT=$(cat)\n"
        "FILE=$(printf '%s' \"$INPUT\" | python3 -c '\n"
        "import json, sys\n"
        "try:\n"
        "    d = json.loads(sys.stdin.read())\n"
        "except Exception:\n"
        "    sys.exit(0)\n"
        "p = d.get(\"file_path\") or (d.get(\"tool_input\") or {}).get(\"file_path\") or \"\"\n"
        "print(p)\n"
        "')\n"
        "\n"
        "if [ -z \"$FILE\" ] || [ ! -f \"$FILE\" ]; then\n"
        f"  printf '%s\\n' {allow_q}\n"
        "  exit 0\n"
        "fi\n"
        "\n"
        f"# Filter by glob: {hook_glob}\n"
        f"if ! printf '%s' \"$FILE\" | grep -qE {glob_regex_q}; then\n"
        f"  printf '%s\\n' {allow_q}\n"
        "  exit 0\n"
        "fi\n"
        "\n"
        "# Skip if file contains a suppression comment for this hook\n"
        f"if grep -q {suppress_q} \"$FILE\"; then\n"
        f"  printf '%s\\n' {allow_q}\n"
        "  exit 0\n"
        "fi\n"
        "\n"
        "# Hook checks (from enrichment) reference \"$1\" — position FILE there for compatibility\n"
        "set -- \"$FILE\"\n"
        "\n"
        "# Run the check in a subshell so embedded exits don't leak\n"
        f"if ( {hook_check} ); then\n"
        f"  printf '%s\\n' {deny_q}\n"
        f"  exit {violation_exit}\n"
        "fi\n"
        f"printf '%s\\n' {allow_q}\n"
        "exit 0\n"
    )


def generate_cursor_hooks(patterns: list[dict], output_dir: str) -> tuple[list[str], str | None]:
    """Generate .cursor/hooks/*.sh scripts and .cursor/hooks.json.

    Returns (list of created script paths, path to hooks.json or None).
    """
    hook_patterns = [p for p in patterns if p.get("mode") == "hook"
                     and p.get("hook_check")
                     and p.get("hook_event")]

    if not hook_patterns:
        return [], None

    hooks_dir = os.path.join(output_dir, ".cursor", "hooks")
    os.makedirs(hooks_dir, exist_ok=True)

    # Clean up stale mined-* hook scripts from previous runs
    for old in Path(hooks_dir).glob("mined-*.sh"):
        old.unlink()

    created_scripts: list[str] = []
    cursor_hooks: dict[str, list[dict]] = {}

    for p in hook_patterns:
        script_name = f"mined-{p['id']}.sh"
        script_path = os.path.join(hooks_dir, script_name)

        with open(script_path, "w") as f:
            f.write(_render_cursor_hook_script(p))
        os.chmod(script_path, 0o755)
        created_scripts.append(script_path)

        claude_event = p.get("hook_event", "PostToolUse")
        cursor_event, matcher = _CURSOR_HOOK_EVENT_MAP.get(claude_event, ("afterFileEdit", None))

        entry: dict = {
            "command": f".cursor/hooks/{script_name}",
            "type": "command",
        }
        if matcher is not None:
            entry["matcher"] = matcher
        if p.get("hook_blocking"):
            # If the script itself crashes, prefer blocking over silently allowing.
            entry["failClosed"] = True

        cursor_hooks.setdefault(cursor_event, []).append(entry)

    settings_path = os.path.join(output_dir, ".cursor", "hooks.json")
    with open(settings_path, "w") as f:
        json.dump({"version": 1, "hooks": cursor_hooks}, f, indent=2)

    return created_scripts, settings_path


def generate_cursor_mdc(
    patterns: list[dict], output_dir: str, modules_map: dict[str, str],
    globs_map: dict[str, list[str]] | None = None,
) -> list[str]:
    """Generate .cursor/rules/{module}-practices.mdc files. Returns list of created paths."""
    globs_map = globs_map or {}
    ambient = [p for p in patterns if p.get("review_count", 1) >= MIN_REVIEW_COUNT
               and p["mode"] == "ambient"
               and p.get("rule", "").strip()]
    groups = group_by_module(ambient)
    rules_dir = os.path.join(output_dir, ".cursor", "rules")
    os.makedirs(rules_dir, exist_ok=True)

    # Clean up stale mined-* mdc files from previous runs
    for old in Path(rules_dir).glob("mined-*-practices.mdc"):
        old.unlink()

    created = []
    today = date.today().isoformat()

    for module, module_patterns in sorted(groups.items()):
        name = display_name(module, modules_map)
        filename = f"mined-{module}-practices.mdc"
        filepath = os.path.join(rules_dir, filename)

        ranked = sorted(module_patterns, key=lambda p: p.get("review_count", 1), reverse=True)
        capped = ranked[:MAX_RULES_PER_FILE]

        by_category: dict[str, list[dict]] = defaultdict(list)
        for p in capped:
            cat = p.get("category", p.get("scope", "general"))
            by_category[cat].append(p)

        # Build .mdc frontmatter
        lines = ["---"]
        lines.append(f"description: {name} best practices from PR review history")
        if module != "global" and module in globs_map:
            glob_list = ", ".join(globs_map[module])
            lines.append(f"globs: [{glob_list}]")
            lines.append("alwaysApply: false")
        else:
            lines.append("alwaysApply: true" if module == "global" else "alwaysApply: false")
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


def main():
    parser = argparse.ArgumentParser(description="Compile patterns.json into AI coding assistant rules")
    parser.add_argument("--input", required=True, help="Path to patterns.json")
    parser.add_argument("--output", required=True, help="Output directory")
    args = parser.parse_args()

    patterns = load_patterns(args.input)
    if not patterns:
        print("No active patterns found. Nothing to generate.")
        return

    modules_map, globs_map = load_modules_yaml(args.output)

    # Generate all outputs
    rules = generate_claude_rules(patterns, args.output, modules_map, globs_map)
    skills = generate_claude_skills(patterns, args.output)
    hooks, hooks_settings = generate_hooks(patterns, args.output)
    mdc_rules = generate_cursor_mdc(patterns, args.output, modules_map, globs_map)
    cursor_skills = generate_cursor_skills(patterns, args.output)
    cursor_hooks, cursor_hooks_settings = generate_cursor_hooks(patterns, args.output)

    print(f"Generated {len(rules)} Claude rule file(s):")
    for r in rules:
        print(f"  {r}")
    print(f"Generated {len(skills)} Claude skill(s):")
    for s in skills:
        print(f"  {s}")
    if hooks:
        print(f"Generated {len(hooks)} Claude hook script(s):")
        for h in hooks:
            print(f"  {h}")
        if hooks_settings:
            print(f"Generated hook settings: {hooks_settings}")
    print(f"Generated {len(mdc_rules)} Cursor .mdc rule file(s):")
    for m in mdc_rules:
        print(f"  {m}")
    print(f"Generated {len(cursor_skills)} Cursor skill(s):")
    for s in cursor_skills:
        print(f"  {s}")
    if cursor_hooks:
        print(f"Generated {len(cursor_hooks)} Cursor hook script(s):")
        for h in cursor_hooks:
            print(f"  {h}")
        if cursor_hooks_settings:
            print(f"Generated Cursor hook settings: {cursor_hooks_settings}")


if __name__ == "__main__":
    main()
