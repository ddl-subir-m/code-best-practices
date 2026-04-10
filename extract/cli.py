"""CLI entry point for the extraction pipeline."""

import argparse

from .fetch import cmd_fetch
from .analyze import cmd_analyze
from .merge import cmd_merge
from .modules import cmd_modules
from .report import cmd_report
from .reclass import cmd_reclass
from .dedup import cmd_dedup
from .triage import cmd_triage
from .enrich import cmd_enrich
from .enrich_hooks import cmd_enrich_hooks
from .validate import cmd_validate_hooks


def main():
    parser = argparse.ArgumentParser(
        description="Extract engineering best practices from PR review threads"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # fetch
    p_fetch = subparsers.add_parser("fetch", help="Fetch merged PR review threads")
    p_fetch.add_argument("--repo", required=True, help="GitHub repo (owner/name)")
    p_fetch.add_argument("--since", required=True, help="Fetch PRs merged since (YYYY-MM-DD)")
    p_fetch.add_argument("--until", default=None, help="Fetch PRs merged before (YYYY-MM-DD)")
    p_fetch.add_argument("--batch-size", type=int, default=100, help="PRs per page (max 100)")

    # analyze
    p_analyze = subparsers.add_parser("analyze", help="Prepare review threads for pattern extraction")
    p_analyze.add_argument("--input", required=True, help="Directory with raw review JSON files")
    p_analyze.add_argument("--output", default="patterns.json", help="Output patterns file")

    # merge
    p_merge = subparsers.add_parser("merge", help="Merge extracted patterns into patterns.json")
    p_merge.add_argument("--input", required=True, help="Directory with extracted pattern JSON files")
    p_merge.add_argument("--output", default="patterns.json", help="Output patterns file")

    # modules
    p_modules = subparsers.add_parser("modules", help="Auto-detect modules from patterns")
    p_modules.add_argument("--input", default="patterns.json", help="Patterns JSON file")
    p_modules.add_argument("--output", default="modules.yaml", help="Output modules YAML file")

    # report
    p_report = subparsers.add_parser("report", help="Generate validation report")
    p_report.add_argument("--input", required=True, help="Patterns JSON file")
    p_report.add_argument("--output", default="validation-report.md", help="Output report file")

    # reclass
    p_reclass = subparsers.add_parser("reclass", help="Reclassify pattern modes (ambient/active/hook)")
    p_reclass.add_argument("--input", default="patterns.json", help="Patterns JSON file to reclassify in-place")

    # dedup
    p_dedup = subparsers.add_parser("dedup", help="Deduplicate patterns (exact ID + LLM semantic)")
    p_dedup.add_argument("--input", default="patterns.json", help="Patterns JSON file to deduplicate in-place")
    p_dedup.add_argument("--workers", type=int, default=4, help="Number of parallel Claude calls")

    # triage
    p_triage = subparsers.add_parser("triage", help="Score active patterns on skill-worthiness")
    p_triage.add_argument("--input", default="patterns.json", help="Patterns JSON file to triage in-place")
    p_triage.add_argument("--dry-run", action="store_true", help="Print results without writing to disk")
    p_triage.add_argument("--force", action="store_true", help="Re-triage already-triaged patterns")
    p_triage.add_argument("--workers", type=int, default=4, help="Number of parallel Claude calls")

    # enrich
    p_enrich = subparsers.add_parser("enrich", help="Enrich skill-worthy patterns with steps and examples")
    p_enrich.add_argument("--input", default="patterns.json", help="Patterns JSON file to enrich in-place")
    p_enrich.add_argument("--force", action="store_true", help="Re-enrich already-enriched patterns")
    p_enrich.add_argument("--workers", type=int, default=4, help="Number of parallel Claude calls")

    # enrich-hooks
    p_enrich_hooks = subparsers.add_parser("enrich-hooks", help="Enrich hook-worthy patterns with hook metadata")
    p_enrich_hooks.add_argument("--input", default="patterns.json", help="Patterns JSON file to enrich in-place")
    p_enrich_hooks.add_argument("--force", action="store_true", help="Re-enrich already-enriched hook patterns")
    p_enrich_hooks.add_argument("--workers", type=int, default=4, help="Number of parallel Claude calls")

    # validate-hooks
    p_validate_hooks = subparsers.add_parser("validate-hooks", help="Validate hook_event/hook_blocking consistency")
    p_validate_hooks.add_argument("--input", default="patterns.json", help="Patterns JSON file to validate in-place")
    p_validate_hooks.add_argument("--dry-run", action="store_true", help="Print corrections without writing to disk")
    p_validate_hooks.add_argument("--workers", type=int, default=4, help="Number of parallel Claude calls")

    args = parser.parse_args()

    commands = {
        "fetch": cmd_fetch,
        "analyze": cmd_analyze,
        "merge": cmd_merge,
        "modules": cmd_modules,
        "report": cmd_report,
        "reclass": cmd_reclass,
        "dedup": cmd_dedup,
        "triage": cmd_triage,
        "enrich": cmd_enrich,
        "enrich-hooks": cmd_enrich_hooks,
        "validate-hooks": cmd_validate_hooks,
    }
    commands[args.command](args)
