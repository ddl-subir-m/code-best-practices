"""Shared test helpers."""


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
