"""Enrich hook-worthy patterns with hook metadata."""

import concurrent.futures
import json
import re
import sys

from .claude import call_claude, parse_json_object

HOOK_ENRICHMENT_FIELDS = (
    "hook_event", "hook_tool", "hook_glob", "hook_check", "hook_message", "hook_blocking",
    "hook_fp_risk",
)


def build_enrich_hooks_prompt(pattern: dict) -> str:
    """Build the Claude prompt to generate hook metadata for a pattern."""
    return (
        "You are generating automated hook configuration for a coding pattern mined from "
        "PR review history at Domino Data Lab. This pattern will become a shell script that "
        "runs automatically when files are edited in Claude Code.\n\n"
        f"Pattern ID: {pattern['id']}\n"
        f"Rule: {pattern['rule']}\n"
        f"Category: {pattern.get('scope', '')}\n"
        f"Source PRs: {', '.join(pattern.get('source_prs', []))}\n"
        f"Modules: {', '.join(pattern.get('modules', []))}\n"
        + (f"Good example:\n{pattern['good_example']}\n" if pattern.get('good_example') else "")
        + (f"Bad example:\n{pattern['bad_example']}\n" if pattern.get('bad_example') else "")
        + "\nGenerate a JSON object with these fields:\n"
        '1. "hook_event": either "PreToolUse" or "PostToolUse"\n'
        "   - PreToolUse = preventive hooks that warn/block BEFORE the action "
        "(security gates, auth checks, secret leakage, data safety)\n"
        "   - PostToolUse = detective hooks that inspect AFTER the action "
        "(consumer audits, quality warnings, PII checks)\n"
        '2. "hook_tool": which tool triggers it — usually "Edit" or "Write"\n'
        '3. "hook_glob": file glob pattern to match (e.g., "**/*Controller*.scala", '
        '"**/shared/**/*.tsx"). Use patterns appropriate for the modules listed above.\n'
        '4. "hook_check": a shell command (using grep, awk, or sed) that detects the '
        "anti-pattern in the file passed as $1. Exit code 0 = violation found, "
        "exit code 1 = no violation. Keep it simple and portable.\n"
        "   IMPORTANT: For PreToolUse hooks, ONLY check lines being ADDED in the current edit, "
        "not the entire file. Use: git diff -- \"$1\" | grep -E '^\\+[^+]' | grep -qE 'pattern'\n"
        "   This prevents blocking edits to files that have pre-existing violations the developer "
        "isn't touching. For PostToolUse hooks, grepping the whole file is fine.\n"
        '5. "hook_message": a concise warning message shown when the hook fires. '
        "Include what was detected and what the developer should do.\n"
        '6. "hook_blocking": true if the hook should block the action (security-critical), '
        "false if it should only warn (advisory).\n"
        '7. "hook_fp_risk": "LOW", "MEDIUM", or "HIGH" — your honest assessment of how often '
        "this hook will fire on CORRECT code (false positives).\n"
        "   - LOW: the grep targets a specific anti-pattern that rarely appears in correct code "
        "(e.g., `toJson(config.toMap)` in a controller, `Action.async` without authAction)\n"
        "   - MEDIUM: the grep may occasionally match legitimate code but the signal is still "
        "valuable (e.g., PII field names near analytics calls)\n"
        "   - HIGH: the grep matches very common patterns that appear in most correct code "
        "(e.g., any component name ending in Panel, any removed variable, any history.push). "
        "If you assess HIGH, this pattern should NOT be a hook — it should be a skill instead. "
        "Return hook_fp_risk: 'HIGH' and it will be demoted.\n\n"
        "Return ONLY the JSON object, no other text."
    )


HOOK_CHECK_LINT_RULES = [
    # (pattern, description) — if the regex matches hook_check, it's flagged
    (r'\|\s*head\b', "pipe to head always exits 0 — use grep -q instead"),
    (r'\|\s*tail\b', "pipe to tail always exits 0 — use grep -q instead"),
    (r'\|\s*wc\b', "pipe to wc always exits 0 — use grep -q or grep -c instead"),
    (r'\\s\*\\[)\]]', "\\s*\\) after method name misses the opening paren — use \\s*[({] or \\s*\\("),
    (r'\bexit\s+0\s*\|\|', "exit 0 || pattern may short-circuit subshell unexpectedly"),
]


def _lint_hook_check(hook_check: str, hook_event: str = "") -> list[str]:
    """Lint a hook_check shell command for common anti-patterns.

    Returns a list of warning strings (empty if clean).
    """
    warnings = []
    for pattern, desc in HOOK_CHECK_LINT_RULES:
        if re.search(pattern, hook_check):
            warnings.append(desc)

    # PreToolUse hooks must check git diff, not the whole file
    if hook_event == "PreToolUse" and "git diff" not in hook_check:
        warnings.append(
            "PreToolUse hook greps the whole file — must use "
            "'git diff -- \"$1\" | grep -E \"^\\+[^+]\"' to only check added lines, "
            "otherwise pre-existing violations block unrelated edits"
        )

    return warnings


MAX_LINT_RETRIES = 2


def _build_lint_fix_prompt(pattern: dict, hook_check: str, warnings: list[str]) -> str:
    """Build a prompt asking Claude to fix a broken hook_check command."""
    warning_text = "\n".join(f"- {w}" for w in warnings)
    return (
        "You previously generated this shell command for a hook check, but it has issues:\n\n"
        f"Pattern: {pattern['id']}\n"
        f"Rule: {pattern['rule']}\n"
        f"Current hook_check: {hook_check}\n\n"
        f"Issues found:\n{warning_text}\n\n"
        "Fix the command. Requirements:\n"
        "- The exit code of the LAST command in the pipeline determines the result\n"
        "- Do NOT pipe to head, tail, or wc — they always exit 0 regardless of input\n"
        "- Use grep -q for existence checks (exits 0 if found, 1 if not)\n"
        "- If you need to filter then check, pipe through grep then end with grep -q\n"
        "- The file path is passed as $1\n"
        "- Exit 0 = violation found, Exit 1 = no violation\n\n"
        'Return ONLY the fixed shell command as a JSON object: {"hook_check": "fixed command"}\n'
        "Return ONLY the JSON object, no other text."
    )


def enrich_single_hook(pattern: dict) -> dict | None:
    """Enrich a single hook pattern via Claude. Returns hook fields or None on failure."""
    prompt = build_enrich_hooks_prompt(pattern)
    response = call_claude(prompt, timeout=120)
    result = parse_json_object(response)
    if not result:
        return None

    # Validate required hook fields
    if not result.get("hook_event") or not result.get("hook_check"):
        return None

    # Lint the generated shell command and re-prompt Claude to fix issues
    pid = pattern.get("id", "?")
    hook_event = result.get("hook_event", "")
    for attempt in range(MAX_LINT_RETRIES):
        warnings = _lint_hook_check(result["hook_check"], hook_event)
        if not warnings:
            break
        for w in warnings:
            print(f"  Lint ({pid}, attempt {attempt + 1}): {w}", file=sys.stderr)
        fix_prompt = _build_lint_fix_prompt(pattern, result["hook_check"], warnings)
        fix_response = call_claude(fix_prompt, timeout=60)
        fix_result = parse_json_object(fix_response)
        if fix_result and fix_result.get("hook_check"):
            result["hook_check"] = fix_result["hook_check"]
        else:
            print(f"  Lint fix failed for {pid}, keeping original", file=sys.stderr)
            break

    # Final lint check — reject if still broken
    final_warnings = _lint_hook_check(result["hook_check"], hook_event)
    if final_warnings:
        print(f"  Rejecting {pid}: hook_check still has issues after {MAX_LINT_RETRIES} fix attempts",
              file=sys.stderr)
        return None

    # Reject hooks that Claude itself assessed as high false positive risk
    fp_risk = result.get("hook_fp_risk", "").upper()
    if fp_risk == "HIGH":
        print(f"  Rejecting {pid}: Claude assessed hook_fp_risk as HIGH (too noisy)",
              file=sys.stderr)
        return None

    return result


def cmd_enrich_hooks(args):
    """Enrich hook-worthy patterns with hook_event, hook_glob, hook_check, etc."""
    input_file = args.input
    force = args.force
    max_workers = args.workers

    with open(input_file) as f:
        patterns = json.load(f)

    # Filter to hook enrichment population: mode=hook + not already enriched
    candidates = []
    candidate_indices = []
    for i, p in enumerate(patterns):
        if p.get("mode") != "hook":
            continue
        if not force and p.get("hook_event"):
            continue
        candidates.append(p)
        candidate_indices.append(i)

    print(f"Loaded {len(patterns)} patterns, {len(candidates)} eligible for hook enrichment", flush=True)

    if not candidates:
        print("No hook patterns to enrich.")
        return

    enriched_count = 0
    failed_count = 0

    def process(idx_pattern):
        idx, pattern = idx_pattern
        result = enrich_single_hook(pattern)
        return idx, pattern["id"], result

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process, (candidate_indices[i], c)): i
            for i, c in enumerate(candidates)
        }
        for future in concurrent.futures.as_completed(futures):
            try:
                idx, pid, result = future.result()
                if result:
                    p = patterns[idx]
                    for field in HOOK_ENRICHMENT_FIELDS:
                        if field in result and result[field] is not None:
                            p[field] = result[field]
                    enriched_count += 1
                    print(f"  [{enriched_count}/{len(candidates)}] Enriched hook: {pid}", flush=True)
                else:
                    failed_count += 1
                    print(f"  Warning: hook enrichment failed for {pid}", file=sys.stderr)
                    # Fall back to active mode (will become a skill instead)
                    patterns[idx]["mode"] = "active"
                    patterns[idx]["mode_rationale"] = "Hook enrichment failed, fell back to active"
            except Exception as e:
                failed_count += 1
                print(f"  Error enriching hook pattern: {e}", file=sys.stderr)

    print(f"\nHook enrichment complete: {enriched_count} enriched, {failed_count} failed", flush=True)

    with open(input_file, "w") as f:
        json.dump(patterns, f, indent=2)

    print(f"Written to {input_file}", flush=True)
