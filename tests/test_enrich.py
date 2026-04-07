"""Tests for extract.py enrich subcommand."""

import json
from unittest.mock import patch

import pytest

from extract import cmd_enrich, enrich_single_pattern


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

        with patch("extract.call_claude", side_effect=mock_claude):
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

        with patch("extract.call_claude", side_effect=mock_claude):
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

        with patch("extract.call_claude", side_effect=mock_claude):
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

        with patch("extract.call_claude", side_effect=mock_claude):
            args = type("Args", (), {"input": str(pf), "force": False, "workers": 1})()
            cmd_enrich(args)

        result = json.loads(pf.read_text())
        p = result[0]
        # Failed enrichment falls back to ambient
        assert p["mode"] == "ambient"
        assert "failed" in p.get("mode_rationale", "").lower()
