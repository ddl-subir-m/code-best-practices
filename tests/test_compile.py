"""Tests for compile.py — pattern compilation into Claude rules, skills, and Cursor rules."""

import json
from pathlib import Path

import pytest

from compile import (
    generate_claude_rules,
    generate_claude_skills,
    generate_cursor_mdc,
    generate_hooks,
    load_patterns,
)


# ---------------------------------------------------------------------------
# 1. Claude rules: module grouping
# ---------------------------------------------------------------------------

class TestGenerateClaudeRules:
    def test_groups_by_module(self, sample_patterns, tmp_path):
        """Patterns are split into per-module rule files.

        Given 3 patterns (2 touching 'apps' + 'server', 1 touching only 'apps'),
        generates apps-practices.md and server-practices.md with correct contents.
        """
        generate_claude_rules(sample_patterns, str(tmp_path), {})

        rules_dir = tmp_path / ".claude" / "rules"
        apps_file = rules_dir / "mined-apps-practices.md"
        server_file = rules_dir / "mined-server-practices.md"

        assert apps_file.exists(), "Expected apps-practices.md to be generated"
        assert server_file.exists(), "Expected server-practices.md to be generated"

        apps_text = apps_file.read_text()
        server_text = server_file.read_text()

        # 2 ambient patterns reference "apps" (db-layer-sorting is active, so excluded from rules)
        assert "API documentation" in apps_text
        assert "explicit error" in apps_text or "unsupported type" in apps_text.lower()

        # Only api-design-consistency references "server" (fail-explicitly only has "apps")
        assert "API documentation" in server_text
        assert "explicit error" not in server_text

    def test_global_patterns(self, tmp_path):
        """Patterns appearing in 3+ modules go to global-practices.md."""
        pattern = {
            "id": "cross-cutting-pattern",
            "rule": "Always validate inputs at service boundaries.",
            "trigger": "Adding a new service method",
            "rationale": "Prevents invalid state from propagating.",
            "good_example": None,
            "bad_example": None,
            "source_prs": ["#47100"],
            "scope": "validation",
            "modules": ["apps", "server", "extensions"],
            "mode": "ambient",
            "confidence": 0.75,
            "review_count": 5,
            "status": "active",
        }

        generate_claude_rules([pattern], str(tmp_path), {})

        rules_dir = tmp_path / ".claude" / "rules"
        global_file = rules_dir / "mined-global-practices.md"
        assert global_file.exists(), "Expected mined-global-practices.md for 3+ module patterns"
        assert "validate inputs" in global_file.read_text().lower()

        # Should NOT appear in per-module files
        for name in ("mined-apps-practices.md", "mined-server-practices.md", "mined-extensions-practices.md"):
            module_file = rules_dir / name
            assert not module_file.exists(), f"{name} should not exist for global patterns"

    def test_special_characters(self, tmp_path):
        """Patterns with backticks, quotes, and angle brackets don't break markdown."""
        pattern = {
            "id": "special-chars",
            "rule": 'Use `Optional<T>` instead of returning "null" for <missing> values.',
            "trigger": "Returning null from a method",
            "rationale": "Null references cause `NullPointerException` at <runtime>.",
            "good_example": '```scala\ndef find(): Option[User] = ???\n```',
            "bad_example": None,
            "source_prs": ["#47300"],
            "scope": "error-handling",
            "modules": ["server"],
            "mode": "ambient",
            "confidence": 0.7,
            "review_count": 2,
            "status": "active",
        }

        generate_claude_rules([pattern], str(tmp_path), {})

        rules_dir = tmp_path / ".claude" / "rules"
        server_file = rules_dir / "mined-server-practices.md"
        assert server_file.exists()

        text = server_file.read_text()
        assert "`Optional<T>`" in text
        assert "<missing>" in text
        assert '"null"' in text


# ---------------------------------------------------------------------------
# 2. Claude skills: active-only generation
# ---------------------------------------------------------------------------

class TestGenerateClaudeSkills:
    def test_active_only(self, sample_patterns, tmp_path):
        """Only active-mode patterns produce skill directories."""
        # sample_patterns has 2 ambient + 1 active ("db-layer-sorting")
        generate_claude_skills(sample_patterns, str(tmp_path))

        skills_dir = tmp_path / ".claude" / "skills"
        assert skills_dir.exists(), "Skills directory should be created"

        skill_dirs = [d for d in skills_dir.iterdir() if d.is_dir()]
        assert len(skill_dirs) == 1, f"Expected 1 skill directory, got {len(skill_dirs)}"

        skill_md = skill_dirs[0] / "SKILL.md"
        assert skill_md.exists(), "Skill directory must contain SKILL.md"

        content = skill_md.read_text()
        # Frontmatter validation
        assert content.startswith("---"), "SKILL.md must start with YAML frontmatter"
        assert "name:" in content, "Frontmatter must include name field"
        assert "description:" in content, "Frontmatter must include description field"

    def test_no_active_patterns(self, tmp_path):
        """When all patterns are ambient, no skills directory is created."""
        ambient_only = [
            {
                "id": "ambient-1",
                "rule": "Rule one",
                "trigger": "trigger",
                "rationale": "rationale",
                "good_example": None,
                "bad_example": None,
                "source_prs": ["#1"],
                "scope": "general",
                "modules": ["apps"],
                "mode": "ambient",
                "confidence": 0.7,
                "review_count": 2,
                "status": "active",
            },
            {
                "id": "ambient-2",
                "rule": "Rule two",
                "trigger": "trigger",
                "rationale": "rationale",
                "good_example": None,
                "bad_example": None,
                "source_prs": ["#2"],
                "scope": "general",
                "modules": ["server"],
                "mode": "ambient",
                "confidence": 0.6,
                "review_count": 1,
                "status": "active",
            },
        ]

        generate_claude_skills(ambient_only, str(tmp_path))

        skills_dir = tmp_path / ".claude" / "skills"
        assert not skills_dir.exists(), "No skills directory when all patterns are ambient"


# ---------------------------------------------------------------------------
# 3. Cursor rules
# ---------------------------------------------------------------------------

class TestGenerateCursorMdc:
    def test_creates_per_module_mdc_files(self, sample_patterns, tmp_path):
        """Generates per-module .mdc files under .cursor/rules/."""
        generate_cursor_mdc(sample_patterns, str(tmp_path), {})

        rules_dir = tmp_path / ".cursor" / "rules"
        assert rules_dir.exists(), ".cursor/rules/ directory should be created"

        mdc_files = list(rules_dir.glob("mined-*-practices.mdc"))
        assert len(mdc_files) > 0, "At least one .mdc file should be created"

        # Only ambient patterns should appear (db-layer-sorting is active, excluded)
        ambient = [p for p in sample_patterns if p["mode"] == "ambient"]
        all_text = "\n".join(f.read_text() for f in mdc_files)
        for p in ambient:
            assert p["rule"] in all_text, f"Ambient pattern '{p['id']}' rule text missing from .mdc files"

    def test_mdc_has_frontmatter(self, sample_patterns, tmp_path):
        """Each .mdc file starts with YAML frontmatter."""
        generate_cursor_mdc(sample_patterns, str(tmp_path), {})

        rules_dir = tmp_path / ".cursor" / "rules"
        for mdc_file in rules_dir.glob("mined-*-practices.mdc"):
            text = mdc_file.read_text()
            assert text.startswith("---"), f"{mdc_file.name} must start with frontmatter"
            assert "description:" in text, f"{mdc_file.name} must include description"


# ---------------------------------------------------------------------------
# 4. load_patterns validation
# ---------------------------------------------------------------------------

class TestLoadPatterns:
    def test_rejects_invalid_json(self, invalid_json_file):
        """Invalid JSON raises a clear error."""
        with pytest.raises(SystemExit) as exc_info:
            load_patterns(str(invalid_json_file))
        error_msg = str(exc_info.value).lower()
        assert "json" in error_msg or "parse" in error_msg or "decode" in error_msg or "invalid" in error_msg

    def test_rejects_missing_required_fields(self, tmp_path):
        """Valid JSON missing required 'rule' field raises an error."""
        bad_pattern = tmp_path / "bad-patterns.json"
        bad_pattern.write_text(json.dumps([{"id": "no-rule-field", "scope": "test"}]))

        with pytest.raises(SystemExit) as exc_info:
            load_patterns(str(bad_pattern))
        error_msg = str(exc_info.value).lower()
        assert "rule" in error_msg or "required" in error_msg or "missing" in error_msg

    def test_empty_array_returns_empty(self, empty_patterns_json):
        """Empty JSON array returns an empty list without error."""
        result = load_patterns(str(empty_patterns_json))
        assert result == []


# ---------------------------------------------------------------------------
# 5. Enriched skill generation
# ---------------------------------------------------------------------------

def _make_enriched_pattern(pid, steps=None, skill_title=None, trigger=None,
                           good_example=None, bad_example=None, rationale=None):
    """Create a pattern with enrichment fields for testing."""
    p = {
        "id": pid,
        "rule": f"Rule for {pid}",
        "trigger": trigger or "",
        "rationale": rationale or "",
        "good_example": good_example,
        "bad_example": bad_example,
        "source_prs": ["#100"],
        "scope": "testing",
        "modules": ["server"],
        "mode": "active",
        "confidence": 0.5,
        "review_count": 3,
        "status": "active",
    }
    if steps is not None:
        p["steps"] = steps
    if skill_title is not None:
        p["skill_title"] = skill_title
    return p


class TestEnrichedSkillGeneration:
    def test_skips_empty_steps(self, tmp_path):
        """Active pattern with no steps produces no SKILL.md."""
        patterns = [
            _make_enriched_pattern("no-steps"),
            _make_enriched_pattern("empty-steps", steps=[]),
            _make_enriched_pattern("null-steps", steps=None),
        ]
        # Ensure steps key doesn't exist for first pattern
        if "steps" in patterns[0]:
            del patterns[0]["steps"]

        generate_claude_skills(patterns, str(tmp_path))

        skills_dir = tmp_path / ".claude" / "skills"
        if skills_dir.exists():
            skill_dirs = [d for d in skills_dir.iterdir() if d.is_dir()]
            assert len(skill_dirs) == 0, f"No skills should be generated, got {len(skill_dirs)}"

    def test_uses_skill_title(self, tmp_path):
        """Pattern with skill_title uses it as the heading."""
        patterns = [_make_enriched_pattern(
            "test-count-query",
            steps=["Identify the query", "Replace with COUNT", "Verify"],
            skill_title="Replace full-object fetches with count queries",
        )]

        generate_claude_skills(patterns, str(tmp_path))

        skills_dir = tmp_path / ".claude" / "skills"
        skill_dirs = [d for d in skills_dir.iterdir() if d.is_dir()]
        assert len(skill_dirs) == 1

        content = (skill_dirs[0] / "SKILL.md").read_text()
        assert "# Replace full-object fetches with count queries" in content
        # Directory should use slugified title
        assert "replace-full-object-fetches" in skill_dirs[0].name

    def test_renders_trigger_section(self, tmp_path):
        """Pattern with trigger field renders ## When to apply section."""
        patterns = [_make_enriched_pattern(
            "trigger-test",
            steps=["Step 1", "Step 2", "Step 3"],
            trigger="You're writing a query that fetches full objects just to count them.",
        )]

        generate_claude_skills(patterns, str(tmp_path))

        skills_dir = tmp_path / ".claude" / "skills"
        skill_dirs = [d for d in skills_dir.iterdir() if d.is_dir()]
        content = (skill_dirs[0] / "SKILL.md").read_text()
        assert "## When to apply" in content
        assert "fetches full objects" in content

    def test_renders_numbered_steps(self, tmp_path):
        """Steps array renders as numbered list, not single-line rule."""
        patterns = [_make_enriched_pattern(
            "steps-test",
            steps=["Identify the problem", "Apply the fix", "Verify the result"],
        )]

        generate_claude_skills(patterns, str(tmp_path))

        skills_dir = tmp_path / ".claude" / "skills"
        skill_dirs = [d for d in skills_dir.iterdir() if d.is_dir()]
        content = (skill_dirs[0] / "SKILL.md").read_text()
        assert "1. Identify the problem" in content
        assert "2. Apply the fix" in content
        assert "3. Verify the result" in content

    def test_skips_prefix_dedup_for_enriched(self, tmp_path):
        """Two enriched patterns sharing a prefix both produce skills."""
        patterns = [
            _make_enriched_pattern(
                "add-tests-for-new-methods",
                steps=["Write test", "Run test", "Check coverage"],
            ),
            _make_enriched_pattern(
                "add-tests-for-edge-cases",
                steps=["Identify edges", "Write edge tests", "Verify boundaries"],
            ),
        ]

        generate_claude_skills(patterns, str(tmp_path))

        skills_dir = tmp_path / ".claude" / "skills"
        skill_dirs = [d for d in skills_dir.iterdir() if d.is_dir()]
        # Both should survive despite sharing "add-tests-for" prefix
        assert len(skill_dirs) == 2


# ---------------------------------------------------------------------------
# 6. Hook generation
# ---------------------------------------------------------------------------

def _make_hook_pattern(pid, **overrides):
    """Create a pattern with hook enrichment fields for testing."""
    p = {
        "id": pid,
        "rule": f"Rule for {pid}",
        "trigger": "",
        "rationale": "",
        "good_example": None,
        "bad_example": None,
        "source_prs": ["#100"],
        "scope": "security",
        "modules": ["server"],
        "mode": "hook",
        "confidence": 0.5,
        "review_count": 3,
        "status": "active",
        "hook_event": "PostToolUse",
        "hook_tool": "Edit",
        "hook_glob": "**/shared/**",
        "hook_check": 'grep -rn "import" "$FILE"',
        "hook_message": "Check consumers of this shared file.",
        "hook_blocking": False,
    }
    p.update(overrides)
    return p


class TestGenerateHooks:
    def test_generates_hook_scripts(self, tmp_path):
        """Hook patterns produce executable .sh scripts."""
        patterns = [_make_hook_pattern("consumer-audit")]

        scripts, settings_path = generate_hooks(patterns, str(tmp_path))

        assert len(scripts) == 1
        assert scripts[0].endswith(".sh")

        script = Path(scripts[0])
        assert script.exists()
        content = script.read_text()
        assert content.startswith("#!/usr/bin/env bash")
        assert "consumer-audit" in content
        assert 'grep -rn "import" "$FILE"' in content

    def test_generates_settings_hooks_json(self, tmp_path):
        """Hook compilation produces a settings-hooks.json with correct structure."""
        patterns = [
            _make_hook_pattern("post-hook", hook_event="PostToolUse"),
            _make_hook_pattern("pre-hook", hook_event="PreToolUse", hook_blocking=True),
        ]

        scripts, settings_path = generate_hooks(patterns, str(tmp_path))

        assert settings_path is not None
        settings = json.loads(Path(settings_path).read_text())
        assert "hooks" in settings
        assert "PostToolUse" in settings["hooks"]
        assert "PreToolUse" in settings["hooks"]
        assert len(settings["hooks"]["PostToolUse"]) == 1
        assert len(settings["hooks"]["PreToolUse"]) == 1

        pre_hook = settings["hooks"]["PreToolUse"][0]
        assert pre_hook.get("blocking") is True

    def test_no_hooks_returns_empty(self, tmp_path):
        """When no hook patterns exist, returns empty lists."""
        patterns = [
            {
                "id": "ambient-pattern",
                "rule": "An ambient rule",
                "trigger": "",
                "rationale": "",
                "good_example": None,
                "bad_example": None,
                "source_prs": ["#1"],
                "scope": "naming",
                "modules": ["server"],
                "mode": "ambient",
                "confidence": 0.5,
                "review_count": 2,
                "status": "active",
            }
        ]

        scripts, settings_path = generate_hooks(patterns, str(tmp_path))
        assert scripts == []
        assert settings_path is None

    def test_hook_scripts_are_executable(self, tmp_path):
        """Generated hook scripts have executable permissions."""
        import os
        import stat

        patterns = [_make_hook_pattern("exec-test")]
        scripts, _ = generate_hooks(patterns, str(tmp_path))

        mode = os.stat(scripts[0]).st_mode
        assert mode & stat.S_IXUSR, "Script should be user-executable"

    def test_cleans_stale_hook_scripts(self, tmp_path):
        """Previous mined-*.sh scripts are removed before generating new ones."""
        hooks_dir = tmp_path / ".claude" / "hooks"
        hooks_dir.mkdir(parents=True)
        stale = hooks_dir / "mined-old-hook.sh"
        stale.write_text("#!/bin/bash\n# stale")

        patterns = [_make_hook_pattern("new-hook")]
        generate_hooks(patterns, str(tmp_path))

        assert not stale.exists(), "Stale hook script should be cleaned up"
        new_scripts = list(hooks_dir.glob("mined-*.sh"))
        assert len(new_scripts) == 1
        assert "new-hook" in new_scripts[0].name

    def test_hook_glob_in_settings(self, tmp_path):
        """Hook glob pattern appears in settings-hooks.json entry."""
        patterns = [_make_hook_pattern(
            "controller-auth",
            hook_glob="**/*Controller*.scala",
        )]

        _, settings_path = generate_hooks(patterns, str(tmp_path))
        settings = json.loads(Path(settings_path).read_text())
        entry = settings["hooks"]["PostToolUse"][0]
        assert entry["fileGlob"] == "**/*Controller*.scala"
