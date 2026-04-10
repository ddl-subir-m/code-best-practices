"""Validate hook_event/hook_blocking consistency via a second Claude pass."""

import concurrent.futures
import json
import sys

from .claude import call_claude, parse_json_response


def build_validate_hooks_prompt(batch: list[dict]) -> str:
    """Build the Claude prompt to validate hook_event/hook_blocking consistency."""
    hook_summaries = json.dumps(
        [{
            "id": p["id"],
            "rule": p["rule"],
            "scope": p.get("scope", ""),
            "hook_event": p.get("hook_event", ""),
            "hook_tool": p.get("hook_tool", ""),
            "hook_blocking": p.get("hook_blocking", False),
            "hook_glob": p.get("hook_glob", ""),
            "hook_check": p.get("hook_check", ""),
            "hook_message": p.get("hook_message", ""),
            "hook_fp_risk": p.get("hook_fp_risk", ""),
        } for p in batch],
        indent=2,
    )
    return (
        "You are reviewing automated hook configurations for correctness. "
        "Each hook has hook_event (PreToolUse or PostToolUse), hook_tool (Edit or Write), "
        "hook_blocking (true/false), and hook_fp_risk (LOW/MEDIUM/HIGH).\n\n"
        "Rules:\n"
        "- PreToolUse runs BEFORE the file edit is written. Use for checks that should "
        "PREVENT bad code from being written: auth gates, secret leakage, credential safety, "
        "data loss prevention. Blocking makes sense here — it stops the edit.\n"
        "- PostToolUse runs AFTER the file edit is written. Use for checks that INSPECT "
        "the result: consumer audits, quality warnings, compatibility checks. "
        "Blocking does NOT make sense here — the edit is already written, blocking just "
        "forces the developer to address it before continuing.\n"
        "- hook_tool determines WHICH tool triggers the hook:\n"
        '  - "Edit" = fires when modifying an existing file (most common — the vast majority of code changes)\n'
        '  - "Write" = fires only when creating a brand new file\n'
        '  - Most hooks should use "Edit" because that is where the majority of code changes happen. '
        '"Write" alone misses edits to existing files, which is almost always wrong. '
        'Use "Write" ONLY if the check genuinely applies only to newly created files.\n'
        "- hook_fp_risk: Look at the hook_check command and the hook_glob together. "
        "Will this grep fire on almost every file matching the glob? If so, it's HIGH risk "
        "and should be demoted (set demote: true). A good hook targets a SPECIFIC anti-pattern "
        "that is rare in correct code.\n"
        "- Actionability: A hook must change behavior compared to an ambient rule. Ask: "
        "does this hook BLOCK a bad edit (PreToolUse+blocking) or provide SPECIFIC actionable "
        "output (e.g., a list of affected consumers, the exact offending line)? "
        "A PostToolUse non-blocking hook that just says 'check X before merging' or "
        "'verify consumers' adds no value over the ambient rule that already says the same thing. "
        "Demote these — they are reminders, not enforcement.\n\n"
        "For each hook, decide:\n"
        "1. Is hook_event correct? Should a preventive check be PreToolUse instead of PostToolUse?\n"
        "2. Is hook_blocking appropriate? Blocking PostToolUse is a contradiction.\n"
        '3. Is hook_tool correct? Should "Write" be "Edit"?\n'
        "4. Is the signal-to-noise ratio acceptable? Look at hook_check + hook_glob: will this "
        "fire on nearly every edit to matching files? If yes, set demote: true.\n"
        "5. Is this hook actionable? A PostToolUse non-blocking hook that only says "
        "'verify X' or 'check Y before merging' without blocking or providing specific "
        "data (consumer lists, exact violations) is just a reminder — demote it.\n\n"
        f"Hooks to review:\n{hook_summaries}\n\n"
        "Return ONLY a JSON array of corrections. Each correction:\n"
        '{"id": "pattern-id", "hook_event": "corrected or omit", '
        '"hook_tool": "corrected or omit", '
        '"hook_blocking": "corrected or omit", '
        '"demote": true (if hook should be demoted to skill due to high FP risk — omit if not), '
        '"rationale": "one sentence explaining the change"}\n\n'
        "Only include hooks that NEED changes. If a hook is already correct, omit it.\n"
        "Return an empty array [] if all hooks are correct.\n\n"
        "Return ONLY the JSON array, no other text."
    )


def cmd_validate_hooks(args):
    """Validate hook_event/hook_blocking consistency via a second Claude pass."""
    input_file = args.input
    dry_run = args.dry_run
    batch_size = 50

    with open(input_file) as f:
        patterns = json.load(f)

    # Filter to enriched hooks
    hooks = [p for p in patterns if p.get("mode") == "hook" and p.get("hook_event")]

    print(f"Loaded {len(patterns)} patterns, {len(hooks)} enriched hooks to validate", flush=True)

    if not hooks:
        print("No hooks to validate.")
        return

    batches = [hooks[i:i + batch_size] for i in range(0, len(hooks), batch_size)]
    corrections: dict[str, dict] = {}
    max_workers = getattr(args, 'workers', 4)

    def _validate_batch(batch_num_and_batch):
        batch_num, batch = batch_num_and_batch
        prompt = build_validate_hooks_prompt(batch)
        print(f"  Batch {batch_num}/{len(batches)}: sending {len(batch)} hooks to Claude...", flush=True)
        response = call_claude(prompt)
        parsed = parse_json_response(response)

        if not parsed:
            return {}

        batch_corrections = {}
        for item in parsed:
            if not isinstance(item, dict):
                continue
            pid = item.get("id", "")
            if pid and ("hook_event" in item or "hook_blocking" in item
                        or "hook_tool" in item or item.get("demote")):
                batch_corrections[pid] = item
        return batch_corrections

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_validate_batch, (bn, b)): bn
            for bn, b in enumerate(batches, 1)
        }
        for future in concurrent.futures.as_completed(futures):
            try:
                batch_corrections = future.result()
                corrections.update(batch_corrections)
            except Exception as e:
                print(f"  Error in validation batch: {e}", file=sys.stderr)

    if not corrections:
        print("\nAll hooks validated — no corrections needed.", flush=True)
        return

    print(f"\nValidation found {len(corrections)} hook(s) to correct:", flush=True)
    for pid, c in sorted(corrections.items()):
        print(f"  {pid}: {c.get('rationale', 'no rationale')}", flush=True)

    demotions = {pid for pid, c in corrections.items() if c.get("demote")}
    fixes = {pid for pid in corrections if pid not in demotions}

    if dry_run:
        print("\n[DRY RUN] No changes written to disk.")
        if demotions:
            print(f"\nDemotions to skill ({len(demotions)}):")
            for pid in sorted(demotions):
                print(f"  {pid}: {corrections[pid].get('rationale', '')}")
        if fixes:
            print(f"\nFixes ({len(fixes)}):")
            for pid in sorted(fixes):
                c = corrections[pid]
                old_p = next((p for p in hooks if p["id"] == pid), None)
                if old_p:
                    print(f"  {pid}: {old_p.get('hook_event')}/{old_p.get('hook_blocking')} → "
                          f"{c.get('hook_event', old_p.get('hook_event'))}/{c.get('hook_blocking', old_p.get('hook_blocking'))}")
        return

    # Apply corrections
    for p in patterns:
        pid = p.get("id", "")
        if pid in corrections:
            c = corrections[pid]
            if c.get("demote"):
                p["mode"] = "active"
                p["mode_rationale"] = f"Demoted from hook: {c.get('rationale', 'high false positive risk')}"
                print(f"  Demoted to skill: {pid}", flush=True)
            else:
                if "hook_event" in c:
                    p["hook_event"] = c["hook_event"]
                if "hook_tool" in c:
                    p["hook_tool"] = c["hook_tool"]
                if "hook_blocking" in c:
                    p["hook_blocking"] = c["hook_blocking"]
            p["hook_validation_rationale"] = c.get("rationale", "")

    with open(input_file, "w") as f:
        json.dump(patterns, f, indent=2)

    print(f"Applied {len(fixes)} fix(es), {len(demotions)} demotion(s) to {input_file}", flush=True)
