"""
Extraction pipeline for mining best practices from GitHub PR review threads.

Usage:
  python -m extract fetch --repo cerebrotech/domino --since 2024-01-01
  python -m extract analyze --input raw-reviews/ --output patterns.json
  python -m extract report --input patterns.json --output validation-report.md
"""

# Re-export public API for backward compatibility (from extract import X)
from .constants import BOT_AUTHORS, VALID_CATEGORIES, STATE_FILE, MODULE_THRESHOLD
from .claude import call_claude, parse_json_response, parse_json_object
from .fetch import run_gh_graphql, filter_bot_comments, load_state, save_state, cmd_fetch
from .analyze import (
    load_raw_reviews, flatten_threads, batch_threads,
    load_existing_pattern_ids, build_extraction_prompt, cmd_analyze,
)
from .merge import (
    normalize_rule, patterns_match, determine_mode, make_pattern_id,
    merge_pattern, extract_module_from_path, raw_to_canonical,
    merge_duplicate_group, cmd_merge,
)
from .dedup import cmd_dedup
from .modules import cmd_modules
from .report import cmd_report
from .reclass import cmd_reclass
from .triage import MIN_REVIEW_COUNT_TRIAGE, build_triage_prompt, cmd_triage
from .enrich import build_enrich_prompt, enrich_single_pattern, cmd_enrich
from .enrich_hooks import (
    HOOK_ENRICHMENT_FIELDS, build_enrich_hooks_prompt,
    HOOK_CHECK_LINT_RULES, _lint_hook_check, MAX_LINT_RETRIES,
    enrich_single_hook, cmd_enrich_hooks,
)
from .validate import build_validate_hooks_prompt, cmd_validate_hooks
from .cli import main
