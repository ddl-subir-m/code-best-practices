"""Tests for extract.py — schema validation of generated artifacts."""

import json
from pathlib import Path

import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_PATTERN_FIELDS = {
    "id",
    "rule",
    "trigger",
    "rationale",
    "source_prs",
    "scope",
    "modules",
    "mode",
    "confidence",
    "review_count",
    "status",
}


class TestPatternsJsonSchema:
    """Validate the actual patterns.json conforms to the canonical schema."""

    @pytest.fixture
    def patterns(self):
        path = PROJECT_ROOT / "patterns.json"
        if not path.exists():
            pytest.skip("patterns.json not yet generated")
        return json.loads(path.read_text())

    def test_all_required_fields_present(self, patterns):
        """Every pattern has all required fields."""
        for i, p in enumerate(patterns):
            missing = REQUIRED_PATTERN_FIELDS - set(p.keys())
            assert not missing, f"Pattern {i} ({p.get('id', '?')}) missing fields: {missing}"

    def test_confidence_range(self, patterns):
        """Confidence is between 0.0 and 1.0 inclusive."""
        for p in patterns:
            assert 0.0 <= p["confidence"] <= 1.0, (
                f"Pattern '{p['id']}' confidence {p['confidence']} out of range"
            )

    def test_mode_values(self, patterns):
        """Mode is either 'ambient' or 'active'."""
        for p in patterns:
            assert p["mode"] in ("ambient", "active"), (
                f"Pattern '{p['id']}' has invalid mode: {p['mode']}"
            )

    def test_status_values(self, patterns):
        """Status is 'active', 'deprecated', or 'rejected'."""
        valid_statuses = {"active", "deprecated", "rejected"}
        for p in patterns:
            assert p["status"] in valid_statuses, (
                f"Pattern '{p['id']}' has invalid status: {p['status']}"
            )

    def test_source_prs_format(self, patterns):
        """source_prs is a non-empty list of strings."""
        for p in patterns:
            assert isinstance(p["source_prs"], list), (
                f"Pattern '{p['id']}' source_prs should be a list"
            )
            assert len(p["source_prs"]) > 0, (
                f"Pattern '{p['id']}' source_prs should not be empty"
            )
            for pr in p["source_prs"]:
                assert isinstance(pr, str), (
                    f"Pattern '{p['id']}' source_prs entries should be strings"
                )

    def test_modules_is_list(self, patterns):
        """modules is a non-empty list of strings."""
        for p in patterns:
            assert isinstance(p["modules"], list) and len(p["modules"]) > 0, (
                f"Pattern '{p['id']}' modules should be a non-empty list"
            )


class TestStateJsonSchema:
    """Validate state.json has required tracking fields."""

    @pytest.fixture
    def state(self):
        path = PROJECT_ROOT / "state.json"
        if not path.exists():
            pytest.skip("state.json not yet generated")
        return json.loads(path.read_text())

    def test_required_fields(self, state):
        """state.json has last_extraction_date and total_prs_processed."""
        assert "last_extraction_date" in state, "Missing last_extraction_date"
        assert "total_prs_processed" in state, "Missing total_prs_processed"

    def test_extraction_runs_is_array(self, state):
        """extraction_runs is a list."""
        assert "extraction_runs" in state, "Missing extraction_runs"
        assert isinstance(state["extraction_runs"], list), "extraction_runs should be a list"


class TestModulesYamlSchema:
    """Validate modules.yaml maps module names to path prefixes."""

    @pytest.fixture
    def modules_data(self):
        path = PROJECT_ROOT / "modules.yaml"
        if not path.exists():
            pytest.skip("modules.yaml not yet generated")
        return yaml.safe_load(path.read_text())

    def test_has_modules_key(self, modules_data):
        """Top-level 'modules' key exists."""
        assert "modules" in modules_data, "modules.yaml must have a 'modules' key"

    def test_module_values_are_path_lists(self, modules_data):
        """Each module maps to a list of path prefixes."""
        for module_name, paths in modules_data["modules"].items():
            assert isinstance(paths, list), (
                f"Module '{module_name}' should map to a list, got {type(paths).__name__}"
            )
            for p in paths:
                assert isinstance(p, str), (
                    f"Module '{module_name}' path entries should be strings"
                )


class TestReclassGuard:
    """Verify reclass skips patterns that have been triaged."""

    def test_reclass_skips_triaged_patterns(self, tmp_path):
        """Patterns with skill_worthy set are not touched by reclass."""
        import json
        from extract import cmd_reclass

        patterns = [
            {
                "id": "triaged-active",
                "rule": "When writing tests, use specific assertions.",
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
                "skill_worthy": True,
                "skill_rationale": "multi-step workflow",
            },
            {
                "id": "untriaged",
                "rule": "Always use explicit imports.",
                "trigger": "",
                "rationale": "",
                "good_example": None,
                "bad_example": None,
                "source_prs": ["#2"],
                "scope": "naming",
                "modules": ["server"],
                "mode": "active",
                "confidence": 0.3,
                "review_count": 2,
                "status": "active",
            },
        ]
        pf = tmp_path / "patterns.json"
        pf.write_text(json.dumps(patterns))

        args = type("Args", (), {"input": str(pf)})()
        cmd_reclass(args)

        result = json.loads(pf.read_text())
        # Triaged pattern should keep its original mode (active)
        triaged = next(p for p in result if p["id"] == "triaged-active")
        assert triaged["mode"] == "active"

        # Untriaged pattern should be reclassified by the heuristic
        # "When writing tests..." starts with "When" -> active
        # "Always use explicit imports." doesn't start with when/before/after/if -> ambient
        untriaged = next(p for p in result if p["id"] == "untriaged")
        assert untriaged["mode"] == "ambient"
