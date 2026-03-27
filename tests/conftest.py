import json
import pytest


SAMPLE_PATTERNS = [
    {
        "id": "api-design-consistency",
        "rule": "API documentation and payloads should be semantically accurate and future-proof.",
        "trigger": "Modifying or adding public API endpoints or documentation",
        "rationale": "Inaccurate API docs erode consumer trust and create integration bugs.",
        "good_example": "PATCH semantics: 'Absent fields are left unchanged'",
        "bad_example": "Docs say 'by project id' when the upsert key may change",
        "source_prs": ["#47200", "#47212", "#47255"],
        "scope": "api-design",
        "modules": ["apps", "server"],
        "mode": "ambient",
        "confidence": 0.9,
        "review_count": 4,
        "status": "active",
    },
    {
        "id": "fail-explicitly",
        "rule": "When a method encounters an unsupported type or impossible state, throw an explicit error.",
        "trigger": "Adding a match/switch over a sealed type or handling optional lookups",
        "rationale": "Silent returns mask bugs and make debugging harder downstream.",
        "good_example": 'throw new IllegalStateException("Unsupported type: " + t)',
        "bad_example": "return Optional.empty() without logging",
        "source_prs": ["#47189", "#47216"],
        "scope": "error-handling",
        "modules": ["apps"],
        "mode": "ambient",
        "confidence": 0.85,
        "review_count": 3,
        "status": "active",
    },
    {
        "id": "db-layer-sorting",
        "rule": "Push sorting, filtering, and joins to the database layer instead of application memory.",
        "trigger": "Writing queries that fetch full collections then filter/sort in Scala/Python",
        "rationale": "In-memory sorting causes N+1 queries and OOM risks at scale.",
        "good_example": "Use aggregation pipeline with $lookup and $sort stages",
        "bad_example": "collection.find().toList.sortBy(_.createdAt).head",
        "source_prs": ["#47189"],
        "scope": "performance",
        "modules": ["apps", "server"],
        "mode": "active",
        "confidence": 0.8,
        "review_count": 3,
        "status": "active",
    },
]


@pytest.fixture
def sample_patterns():
    """Return a list of 3 sample pattern objects matching the canonical schema."""
    return [p.copy() for p in SAMPLE_PATTERNS]


@pytest.fixture
def sample_patterns_json(tmp_path):
    """Write sample patterns to a temp JSON file and return its path."""
    path = tmp_path / "patterns.json"
    path.write_text(json.dumps(SAMPLE_PATTERNS, indent=2))
    return path


@pytest.fixture
def empty_patterns_json(tmp_path):
    """Write an empty array to a temp JSON file and return its path."""
    path = tmp_path / "empty-patterns.json"
    path.write_text("[]")
    return path


@pytest.fixture
def invalid_json_file(tmp_path):
    """Write malformed JSON to a temp file and return its path."""
    path = tmp_path / "bad.json"
    path.write_text("{not valid json: [")
    return path


@pytest.fixture
def existing_cursorrules(tmp_path):
    """Write existing cursor rules content to a temp file and return its path."""
    content = """\
# Team Cursor Rules

## Code Style
- Use 4-space indentation
- Prefer explicit types over var/val inference

## Testing
- All public methods must have unit tests
"""
    path = tmp_path / ".cursorrules"
    path.write_text(content)
    return path
