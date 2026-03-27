"""Tests for compile.py — pattern compilation into Claude rules, skills, and Cursor rules."""

import json
import pytest

from compile import (
    generate_claude_rules,
    generate_claude_skills,
    generate_cursorrules,
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
        apps_file = rules_dir / "apps-practices.md"
        server_file = rules_dir / "server-practices.md"

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
        global_file = rules_dir / "global-practices.md"
        assert global_file.exists(), "Expected global-practices.md for 3+ module patterns"
        assert "validate inputs" in global_file.read_text().lower()

        # Should NOT appear in per-module files
        for name in ("apps-practices.md", "server-practices.md", "extensions-practices.md"):
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
        server_file = rules_dir / "server-practices.md"
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

class TestGenerateCursorRules:
    def test_creates_file(self, sample_patterns, tmp_path):
        """Generates a valid .cursorrules file with all patterns."""
        generate_cursorrules(sample_patterns, str(tmp_path), None, {})

        cursorrules = tmp_path / ".cursorrules"
        assert cursorrules.exists(), ".cursorrules file should be created"

        text = cursorrules.read_text()
        assert len(text) > 0, ".cursorrules should not be empty"
        # Only ambient patterns should appear (db-layer-sorting is active, excluded)
        ambient = [p for p in sample_patterns if p["mode"] in ("ambient", "both")]
        for p in ambient:
            assert p["rule"] in text, f"Ambient pattern '{p['id']}' rule text missing from .cursorrules"

    def test_merges_existing(self, sample_patterns, tmp_path, existing_cursorrules):
        """Merges auto-generated rules with existing .cursorrules content."""
        generate_cursorrules(
            sample_patterns, str(tmp_path), str(existing_cursorrules), {}
        )

        cursorrules = tmp_path / ".cursorrules"
        assert cursorrules.exists()

        text = cursorrules.read_text()

        # Existing content preserved
        assert "# Team Cursor Rules" in text
        assert "Use 4-space indentation" in text
        assert "All public methods must have unit tests" in text

        # Auto-generated section appended
        assert "## Auto-generated from PR review mining" in text

        # Ambient patterns present (active ones excluded from cursorrules)
        ambient = [p for p in sample_patterns if p["mode"] in ("ambient", "both")]
        for p in ambient:
            assert p["rule"] in text


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
