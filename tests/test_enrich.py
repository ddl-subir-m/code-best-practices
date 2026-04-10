"""Tests for extract enrich and enrich-hooks subcommands."""

import json
from unittest.mock import patch

import pytest

from extract.enrich import cmd_enrich, enrich_single_pattern
from extract.enrich_hooks import cmd_enrich_hooks, enrich_single_hook, _lint_hook_check
from extract.validate import cmd_validate_hooks


def make_test_pattern(pid, **overrides):
    """Create a minimal pattern dict for testing."""
    p = {
        "id": pid,
        "rule": f"Rule for {pid}",
        "trigger": "",
        "rationale": "",
        "good_example": None,
        "bad_example": None,
        "source_prs": ["#1"],
        "scope": "testing",
        "modules": ["server"],
        "mode": "active",
        "confidence": 0.3,
        "review_count": 3,
        "status": "active",
    }
    p.update(overrides)
    return p


MOCK_ENRICHMENT = {
    "id": "test-pattern",
    "trigger": "You're writing a test and need guidance.",
    "steps": ["Step 1: Do this", "Step 2: Do that", "Step 3: Verify"],
    "good_example": "const x = doRight()",
    "bad_example": "const x = doWrong()",
    "rationale": "This prevents bugs.",
    "skill_title": "Apply the test pattern correctly",
}


class TestEnrichFiltering:
    def test_filters_skill_worthy_only(self, tmp_path):
        """Only skill_worthy=True patterns get enriched."""
        patterns = [
            make_test_pattern("worthy", skill_worthy=True),
            make_test_pattern("not-worthy", skill_worthy=False),
            make_test_pattern("no-field"),  # no skill_worthy key at all
        ]
        pf = tmp_path / "patterns.json"
        pf.write_text(json.dumps(patterns))

        enrich_calls = []

        def mock_claude(prompt, timeout=120):
            enrich_calls.append(prompt)
            return json.dumps({**MOCK_ENRICHMENT, "id": "worthy"})

        with patch("extract.enrich.call_claude", side_effect=mock_claude):
            args = type("Args", (), {"input": str(pf), "force": False, "workers": 1})()
            cmd_enrich(args)

        assert len(enrich_calls) == 1
        assert "worthy" in enrich_calls[0]

    def test_skips_already_enriched(self, tmp_path):
        """Patterns with non-empty steps are skipped."""
        patterns = [make_test_pattern("already-done", skill_worthy=True, steps=["existing step"])]
        pf = tmp_path / "patterns.json"
        pf.write_text(json.dumps(patterns))

        enrich_calls = []

        def mock_claude(prompt, timeout=120):
            enrich_calls.append(prompt)
            return json.dumps(MOCK_ENRICHMENT)

        with patch("extract.enrich.call_claude", side_effect=mock_claude):
            args = type("Args", (), {"input": str(pf), "force": False, "workers": 1})()
            cmd_enrich(args)

        assert len(enrich_calls) == 0  # no calls made


class TestEnrichWritesFields:
    def test_writes_all_fields(self, tmp_path):
        """Successful enrichment writes all 6 fields to the pattern."""
        patterns = [make_test_pattern("test-pattern", skill_worthy=True)]
        pf = tmp_path / "patterns.json"
        pf.write_text(json.dumps(patterns))

        def mock_claude(prompt, timeout=120):
            return json.dumps(MOCK_ENRICHMENT)

        with patch("extract.enrich.call_claude", side_effect=mock_claude):
            args = type("Args", (), {"input": str(pf), "force": False, "workers": 1})()
            cmd_enrich(args)

        result = json.loads(pf.read_text())
        p = result[0]
        assert p["trigger"] == "You're writing a test and need guidance."
        assert p["steps"] == ["Step 1: Do this", "Step 2: Do that", "Step 3: Verify"]
        assert p["good_example"] == "const x = doRight()"
        assert p["bad_example"] == "const x = doWrong()"
        assert p["rationale"] == "This prevents bugs."
        assert p["skill_title"] == "Apply the test pattern correctly"


class TestEnrichErrorHandling:
    def test_handles_malformed_json(self, tmp_path):
        """Malformed response causes pattern to fall back to ambient."""
        patterns = [make_test_pattern("broken", skill_worthy=True)]
        pf = tmp_path / "patterns.json"
        pf.write_text(json.dumps(patterns))

        def mock_claude(prompt, timeout=120):
            return "not valid json"

        with patch("extract.enrich.call_claude", side_effect=mock_claude):
            args = type("Args", (), {"input": str(pf), "force": False, "workers": 1})()
            cmd_enrich(args)

        result = json.loads(pf.read_text())
        p = result[0]
        # Failed enrichment falls back to ambient
        assert p["mode"] == "ambient"
        assert "failed" in p.get("mode_rationale", "").lower()


# ---------------------------------------------------------------------------
# Hook enrichment tests
# ---------------------------------------------------------------------------

MOCK_HOOK_ENRICHMENT = {
    "hook_event": "PostToolUse",
    "hook_tool": "Edit",
    "hook_glob": "**/shared/**",
    "hook_check": 'grep -rn "import.*$(basename $FILE)" --include="*.tsx" --include="*.ts" .',
    "hook_message": "Shared file modified. Check all consumers for compatibility.",
    "hook_blocking": False,
}


class TestEnrichHooksFiltering:
    def test_filters_hook_mode_only(self, tmp_path):
        """Only mode='hook' patterns get hook-enriched."""
        patterns = [
            make_test_pattern("hook-pattern", mode="hook"),
            make_test_pattern("active-pattern", mode="active"),
            make_test_pattern("ambient-pattern", mode="ambient"),
        ]
        pf = tmp_path / "patterns.json"
        pf.write_text(json.dumps(patterns))

        enrich_calls = []

        def mock_claude(prompt, timeout=120):
            enrich_calls.append(prompt)
            return json.dumps(MOCK_HOOK_ENRICHMENT)

        with patch("extract.enrich_hooks.call_claude", side_effect=mock_claude):
            args = type("Args", (), {"input": str(pf), "force": False, "workers": 1})()
            cmd_enrich_hooks(args)

        assert len(enrich_calls) == 1
        assert "hook-pattern" in enrich_calls[0]

    def test_skips_already_enriched(self, tmp_path):
        """Hook patterns with hook_event already set are skipped."""
        patterns = [make_test_pattern(
            "already-done", mode="hook", hook_event="PostToolUse",
        )]
        pf = tmp_path / "patterns.json"
        pf.write_text(json.dumps(patterns))

        enrich_calls = []

        def mock_claude(prompt, timeout=120):
            enrich_calls.append(prompt)
            return json.dumps(MOCK_HOOK_ENRICHMENT)

        with patch("extract.enrich_hooks.call_claude", side_effect=mock_claude):
            args = type("Args", (), {"input": str(pf), "force": False, "workers": 1})()
            cmd_enrich_hooks(args)

        assert len(enrich_calls) == 0


class TestEnrichHooksWritesFields:
    def test_writes_all_hook_fields(self, tmp_path):
        """Successful hook enrichment writes all 6 hook fields."""
        patterns = [make_test_pattern("consumer-audit", mode="hook")]
        pf = tmp_path / "patterns.json"
        pf.write_text(json.dumps(patterns))

        def mock_claude(prompt, timeout=120):
            return json.dumps(MOCK_HOOK_ENRICHMENT)

        with patch("extract.enrich_hooks.call_claude", side_effect=mock_claude):
            args = type("Args", (), {"input": str(pf), "force": False, "workers": 1})()
            cmd_enrich_hooks(args)

        result = json.loads(pf.read_text())
        p = result[0]
        assert p["hook_event"] == "PostToolUse"
        assert p["hook_tool"] == "Edit"
        assert p["hook_glob"] == "**/shared/**"
        assert "grep" in p["hook_check"]
        assert "Shared file" in p["hook_message"]
        assert p["hook_blocking"] is False

    def test_pretooluse_blocking_hook(self, tmp_path):
        """PreToolUse hooks with blocking=true are written correctly."""
        patterns = [make_test_pattern("auth-check", mode="hook")]
        pf = tmp_path / "patterns.json"
        pf.write_text(json.dumps(patterns))

        call_count = [0]

        def mock_claude(prompt, timeout=120):
            call_count[0] += 1
            if call_count[0] == 1:
                # Initial enrichment — returns PreToolUse but without git diff
                return json.dumps({
                    "hook_event": "PreToolUse",
                    "hook_tool": "Edit",
                    "hook_glob": "**/*Controller*.scala",
                    "hook_check": 'grep -L "authAction" "$1"',
                    "hook_message": "Endpoint missing auth wrapper.",
                    "hook_blocking": True,
                    "hook_fp_risk": "LOW",
                })
            else:
                # Lint fix — returns corrected command with git diff
                return json.dumps({
                    "hook_check": 'git diff -- "$1" | grep -E \'^\\+[^+]\' | grep -qE \'= *Action[.{ ]\'',
                })

        with patch("extract.enrich_hooks.call_claude", side_effect=mock_claude):
            args = type("Args", (), {"input": str(pf), "force": False, "workers": 1})()
            cmd_enrich_hooks(args)

        result = json.loads(pf.read_text())
        p = result[0]
        assert p["hook_event"] == "PreToolUse"
        assert p["hook_blocking"] is True
        assert "git diff" in p["hook_check"]


class TestEnrichHooksErrorHandling:
    def test_failed_enrichment_falls_back_to_active(self, tmp_path):
        """Failed hook enrichment falls back to mode='active'."""
        patterns = [make_test_pattern("broken-hook", mode="hook")]
        pf = tmp_path / "patterns.json"
        pf.write_text(json.dumps(patterns))

        def mock_claude(prompt, timeout=120):
            return "not valid json"

        with patch("extract.enrich_hooks.call_claude", side_effect=mock_claude):
            args = type("Args", (), {"input": str(pf), "force": False, "workers": 1})()
            cmd_enrich_hooks(args)

        result = json.loads(pf.read_text())
        p = result[0]
        assert p["mode"] == "active"
        assert "failed" in p.get("mode_rationale", "").lower()

    def test_lint_failure_rejects_hook(self, tmp_path):
        """Hook with unfixable lint issues (e.g., pipe to head) is rejected."""
        patterns = [make_test_pattern("lint-reject", mode="hook")]
        pf = tmp_path / "patterns.json"
        pf.write_text(json.dumps(patterns))

        call_count = [0]

        def mock_claude(prompt, timeout=120):
            call_count[0] += 1
            if call_count[0] == 1:
                # Initial enrichment returns a broken hook_check
                return json.dumps({
                    **MOCK_HOOK_ENRICHMENT,
                    "hook_check": 'grep -n "pattern" "$1" | head -1',
                })
            else:
                # Fix attempts also return broken commands
                return json.dumps({
                    "hook_check": 'grep -n "pattern" "$1" | head -5',
                })

        with patch("extract.enrich_hooks.call_claude", side_effect=mock_claude):
            args = type("Args", (), {"input": str(pf), "force": False, "workers": 1})()
            cmd_enrich_hooks(args)

        result = json.loads(pf.read_text())
        p = result[0]
        # Rejected → falls back to active
        assert p["mode"] == "active"

    def test_lint_fix_succeeds(self, tmp_path):
        """Hook with fixable lint issue gets corrected by re-prompt."""
        patterns = [make_test_pattern("lint-fix", mode="hook")]
        pf = tmp_path / "patterns.json"
        pf.write_text(json.dumps(patterns))

        call_count = [0]

        def mock_claude(prompt, timeout=120):
            call_count[0] += 1
            if call_count[0] == 1:
                # Initial enrichment returns broken hook_check
                return json.dumps({
                    **MOCK_HOOK_ENRICHMENT,
                    "hook_check": 'grep -n "pattern" "$1" | head -1',
                })
            else:
                # Fix attempt returns a clean command
                return json.dumps({
                    "hook_check": 'grep -q "pattern" "$1"',
                })

        with patch("extract.enrich_hooks.call_claude", side_effect=mock_claude):
            args = type("Args", (), {"input": str(pf), "force": False, "workers": 1})()
            cmd_enrich_hooks(args)

        result = json.loads(pf.read_text())
        p = result[0]
        assert p["mode"] == "hook"
        assert p["hook_check"] == 'grep -q "pattern" "$1"'


# ---------------------------------------------------------------------------
# Hook check linter tests
# ---------------------------------------------------------------------------

class TestHookCheckLinter:
    def test_catches_pipe_to_head(self):
        """Pipe to head always exits 0 — should be flagged."""
        warnings = _lint_hook_check('grep -n "pattern" "$1" | head -1')
        assert any("head" in w for w in warnings)

    def test_catches_pipe_to_wc(self):
        """Pipe to wc always exits 0 — should be flagged."""
        warnings = _lint_hook_check('grep -c "pattern" "$1" | wc -l')
        assert any("wc" in w for w in warnings)

    def test_clean_command_passes(self):
        """A well-formed grep -q command has no warnings."""
        warnings = _lint_hook_check('grep -qE "pattern" "$1"')
        assert warnings == []

    def test_clean_pipeline_passes(self):
        """A pipeline ending in grep -q passes."""
        warnings = _lint_hook_check('grep -n "foo" "$1" | grep -q "bar"')
        assert warnings == []

    def test_pretooluse_requires_git_diff(self):
        """PreToolUse hooks that grep the whole file are flagged."""
        warnings = _lint_hook_check('grep -qE "Action" "$1"', hook_event="PreToolUse")
        assert any("git diff" in w for w in warnings)

    def test_pretooluse_with_git_diff_passes(self):
        """PreToolUse hooks using git diff pass the check."""
        warnings = _lint_hook_check(
            'git diff -- "$1" | grep -E \'^\\+[^+]\' | grep -qE "Action"',
            hook_event="PreToolUse",
        )
        assert warnings == []

    def test_posttooluse_whole_file_is_fine(self):
        """PostToolUse hooks can grep the whole file."""
        warnings = _lint_hook_check('grep -qE "pattern" "$1"', hook_event="PostToolUse")
        assert warnings == []


# ---------------------------------------------------------------------------
# Validate-hooks tests
# ---------------------------------------------------------------------------

class TestValidateHooksCorrections:
    def test_corrects_blocking_posttooluse(self, tmp_path):
        """Blocking PostToolUse hooks get corrected to PreToolUse."""
        patterns = [make_test_pattern(
            "bad-combo", mode="hook",
            hook_event="PostToolUse", hook_blocking=True,
            hook_check='grep -q "secret" "$FILE"',
            hook_glob="**/*.scala",
            hook_message="Found secret",
        )]
        pf = tmp_path / "patterns.json"
        pf.write_text(json.dumps(patterns))

        def mock_claude(prompt, timeout=300):
            return json.dumps([{
                "id": "bad-combo",
                "hook_event": "PreToolUse",
                "hook_blocking": True,
                "rationale": "Security check should block before edit, not after",
            }])

        with patch("extract.validate.call_claude", side_effect=mock_claude):
            args = type("Args", (), {"input": str(pf), "dry_run": False})()
            cmd_validate_hooks(args)

        result = json.loads(pf.read_text())
        p = result[0]
        assert p["hook_event"] == "PreToolUse"
        assert p["hook_blocking"] is True
        assert "before edit" in p.get("hook_validation_rationale", "").lower()

    def test_no_corrections_needed(self, tmp_path):
        """When all hooks are correct, no changes are made."""
        patterns = [make_test_pattern(
            "good-hook", mode="hook",
            hook_event="PostToolUse", hook_blocking=False,
            hook_check='grep -q "test" "$FILE"',
            hook_glob="**/*.tsx",
            hook_message="Found test",
        )]
        pf = tmp_path / "patterns.json"
        original = json.dumps(patterns)
        pf.write_text(original)

        def mock_claude(prompt, timeout=300):
            return "[]"

        with patch("extract.validate.call_claude", side_effect=mock_claude):
            args = type("Args", (), {"input": str(pf), "dry_run": False})()
            cmd_validate_hooks(args)

        assert pf.read_text() == original

    def test_dry_run_no_write(self, tmp_path):
        """--dry-run prints corrections without modifying patterns.json."""
        patterns = [make_test_pattern(
            "dry-test", mode="hook",
            hook_event="PostToolUse", hook_blocking=True,
            hook_check='grep -q "x" "$FILE"',
            hook_glob="**/*.scala",
            hook_message="Found x",
        )]
        pf = tmp_path / "patterns.json"
        original = json.dumps(patterns)
        pf.write_text(original)

        def mock_claude(prompt, timeout=300):
            return json.dumps([{
                "id": "dry-test",
                "hook_event": "PreToolUse",
                "hook_blocking": True,
                "rationale": "should be pre",
            }])

        with patch("extract.validate.call_claude", side_effect=mock_claude):
            args = type("Args", (), {"input": str(pf), "dry_run": True})()
            cmd_validate_hooks(args)

        assert pf.read_text() == original
