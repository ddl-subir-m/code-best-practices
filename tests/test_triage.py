"""Tests for extract.py triage subcommand."""

import json
from unittest.mock import patch

import pytest

from extract import cmd_triage, parse_json_response


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


class TestTriageFiltering:
    def test_filters_active_rc2_only(self, tmp_path):
        """Only active patterns with review_count >= 2 are sent to Claude."""
        patterns = [
            make_test_pattern("active-rc3", mode="active", review_count=3),
            make_test_pattern("active-rc1", mode="active", review_count=1),
            make_test_pattern("ambient-rc5", mode="ambient", review_count=5),
        ]
        pf = tmp_path / "patterns.json"
        pf.write_text(json.dumps(patterns))

        triage_calls = []

        def mock_claude(prompt, timeout=300):
            triage_calls.append(prompt)
            return json.dumps([{"id": "active-rc3", "skill_worthy": True, "skill_rationale": "multi-step"}])

        with patch("extract.call_claude", side_effect=mock_claude):
            args = type("Args", (), {"input": str(pf), "dry_run": False, "force": False})()
            cmd_triage(args)

        assert len(triage_calls) == 1
        assert "active-rc3" in triage_calls[0]
        assert "active-rc1" not in triage_calls[0]
        assert "ambient-rc5" not in triage_calls[0]

    def test_skips_already_triaged(self, tmp_path):
        """Patterns with skill_worthy set are skipped unless --force."""
        patterns = [
            make_test_pattern("already-triaged", skill_worthy=True, skill_rationale="already triaged"),
            make_test_pattern("not-triaged"),
        ]
        pf = tmp_path / "patterns.json"
        pf.write_text(json.dumps(patterns))

        triage_calls = []

        def mock_claude(prompt, timeout=300):
            triage_calls.append(prompt)
            return json.dumps([{"id": "not-triaged", "skill_worthy": False, "skill_rationale": "simple"}])

        with patch("extract.call_claude", side_effect=mock_claude):
            args = type("Args", (), {"input": str(pf), "dry_run": False, "force": False})()
            cmd_triage(args)

        assert len(triage_calls) == 1
        assert "already-triaged" not in triage_calls[0]
        assert "not-triaged" in triage_calls[0]


class TestTriageDemotion:
    def test_demotes_non_worthy(self, tmp_path):
        """Non-skill-worthy patterns get mode=ambient and mode_rationale updated."""
        patterns = [make_test_pattern("simple-convention")]
        pf = tmp_path / "patterns.json"
        pf.write_text(json.dumps(patterns))

        def mock_claude(prompt, timeout=300):
            return json.dumps([{"id": "simple-convention", "skill_worthy": False,
                                "skill_rationale": "single sentence convention"}])

        with patch("extract.call_claude", side_effect=mock_claude):
            args = type("Args", (), {"input": str(pf), "dry_run": False, "force": False})()
            cmd_triage(args)

        result = json.loads(pf.read_text())
        p = result[0]
        assert p["skill_worthy"] is False
        assert p["mode"] == "ambient"
        assert p["mode_rationale"] == "single sentence convention"

    def test_preserves_worthy_as_active(self, tmp_path):
        """Skill-worthy patterns keep mode=active."""
        patterns = [make_test_pattern("complex-workflow")]
        pf = tmp_path / "patterns.json"
        pf.write_text(json.dumps(patterns))

        def mock_claude(prompt, timeout=300):
            return json.dumps([{"id": "complex-workflow", "skill_worthy": True,
                                "skill_rationale": "requires step-by-step guidance"}])

        with patch("extract.call_claude", side_effect=mock_claude):
            args = type("Args", (), {"input": str(pf), "dry_run": False, "force": False})()
            cmd_triage(args)

        result = json.loads(pf.read_text())
        p = result[0]
        assert p["skill_worthy"] is True
        assert p["mode"] == "active"


class TestTriageDryRun:
    def test_dry_run_no_write(self, tmp_path):
        """--dry-run outputs results without modifying patterns.json."""
        patterns = [make_test_pattern("test-pattern")]
        pf = tmp_path / "patterns.json"
        original = json.dumps(patterns)
        pf.write_text(original)

        def mock_claude(prompt, timeout=300):
            return json.dumps([{"id": "test-pattern", "skill_worthy": True,
                                "skill_rationale": "multi-step"}])

        with patch("extract.call_claude", side_effect=mock_claude):
            args = type("Args", (), {"input": str(pf), "dry_run": True, "force": False})()
            cmd_triage(args)

        # File should be unchanged
        assert pf.read_text() == original


class TestTriageHookClassification:
    def test_hook_worthy_sets_mode_hook(self, tmp_path):
        """Patterns flagged as hook_worthy get mode='hook'."""
        patterns = [make_test_pattern("security-auth-check")]
        pf = tmp_path / "patterns.json"
        pf.write_text(json.dumps(patterns))

        def mock_claude(prompt, timeout=300):
            return json.dumps([{
                "id": "security-auth-check",
                "skill_worthy": True,
                "skill_rationale": "multi-step auth workflow",
                "hook_worthy": True,
                "hook_rationale": "mechanical grep for auth wrapper, security-critical",
            }])

        with patch("extract.call_claude", side_effect=mock_claude):
            args = type("Args", (), {"input": str(pf), "dry_run": False, "force": False})()
            cmd_triage(args)

        result = json.loads(pf.read_text())
        p = result[0]
        assert p["mode"] == "hook"
        assert p["hook_worthy"] is True
        assert p["hook_rationale"] == "mechanical grep for auth wrapper, security-critical"

    def test_hook_worthy_overrides_skill_worthy(self, tmp_path):
        """When both hook_worthy and skill_worthy are true, mode is 'hook' not 'active'."""
        patterns = [make_test_pattern("dual-worthy")]
        pf = tmp_path / "patterns.json"
        pf.write_text(json.dumps(patterns))

        def mock_claude(prompt, timeout=300):
            return json.dumps([{
                "id": "dual-worthy",
                "skill_worthy": True,
                "skill_rationale": "needs steps",
                "hook_worthy": True,
                "hook_rationale": "automatable security check",
            }])

        with patch("extract.call_claude", side_effect=mock_claude):
            args = type("Args", (), {"input": str(pf), "dry_run": False, "force": False})()
            cmd_triage(args)

        result = json.loads(pf.read_text())
        assert result[0]["mode"] == "hook"

    def test_not_hook_worthy_stays_active(self, tmp_path):
        """Patterns with hook_worthy=false and skill_worthy=true stay active."""
        patterns = [make_test_pattern("skill-only")]
        pf = tmp_path / "patterns.json"
        pf.write_text(json.dumps(patterns))

        def mock_claude(prompt, timeout=300):
            return json.dumps([{
                "id": "skill-only",
                "skill_worthy": True,
                "skill_rationale": "needs guidance",
                "hook_worthy": False,
                "hook_rationale": "requires judgment",
            }])

        with patch("extract.call_claude", side_effect=mock_claude):
            args = type("Args", (), {"input": str(pf), "dry_run": False, "force": False})()
            cmd_triage(args)

        result = json.loads(pf.read_text())
        assert result[0]["mode"] == "active"

    def test_hook_worthy_missing_defaults_false(self, tmp_path):
        """When Claude response omits hook_worthy, it defaults to false."""
        patterns = [make_test_pattern("old-format")]
        pf = tmp_path / "patterns.json"
        pf.write_text(json.dumps(patterns))

        def mock_claude(prompt, timeout=300):
            # Simulate old-format response without hook_worthy
            return json.dumps([{
                "id": "old-format",
                "skill_worthy": True,
                "skill_rationale": "needs steps",
            }])

        with patch("extract.call_claude", side_effect=mock_claude):
            args = type("Args", (), {"input": str(pf), "dry_run": False, "force": False})()
            cmd_triage(args)

        result = json.loads(pf.read_text())
        assert result[0]["mode"] == "active"
        assert result[0]["hook_worthy"] is False


class TestTriageErrorHandling:
    def test_handles_malformed_json(self, tmp_path):
        """Malformed Claude response doesn't crash; batch is skipped."""
        patterns = [make_test_pattern("p1"), make_test_pattern("p2")]
        pf = tmp_path / "patterns.json"
        pf.write_text(json.dumps(patterns))

        def mock_claude(prompt, timeout=300):
            return "this is not json at all"

        with patch("extract.call_claude", side_effect=mock_claude):
            args = type("Args", (), {"input": str(pf), "dry_run": False, "force": False})()
            cmd_triage(args)  # should not raise

        result = json.loads(pf.read_text())
        # Patterns should be unchanged (no skill_worthy field added)
        for p in result:
            assert "skill_worthy" not in p

    def test_handles_timeout(self, tmp_path):
        """Claude timeout (empty response) doesn't crash."""
        patterns = [make_test_pattern("timeout-test")]
        pf = tmp_path / "patterns.json"
        pf.write_text(json.dumps(patterns))

        def mock_claude(prompt, timeout=300):
            return ""  # timeout returns empty string

        with patch("extract.call_claude", side_effect=mock_claude):
            args = type("Args", (), {"input": str(pf), "dry_run": False, "force": False})()
            cmd_triage(args)  # should not raise

        result = json.loads(pf.read_text())
        assert "skill_worthy" not in result[0]
