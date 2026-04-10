"""Score active patterns on skill-worthiness and hook-worthiness."""

import concurrent.futures
import json
import sys

from .claude import call_claude, parse_json_response

MIN_REVIEW_COUNT_TRIAGE = 2


def build_triage_prompt(batch: list[dict]) -> str:
    """Build the Claude triage prompt for a batch of patterns."""
    pattern_list = json.dumps(
        [{"id": p["id"], "rule": p["rule"], "scope": p.get("scope", ""), "modules": p.get("modules", [])}
         for p in batch],
        indent=2,
    )
    return (
        "For each pattern below, determine TWO things:\n\n"
        "1. **skill_worthy**: Does this pattern require multi-step guidance "
        "(a workflow, decision tree, or code example) to be useful as a coding assistant skill? "
        "A pattern is skill-worthy if an engineer would benefit from step-by-step instructions, "
        "concrete code examples, or a decision tree to apply it correctly. "
        "A pattern is NOT skill-worthy if it can be fully communicated in a single sentence.\n\n"
        "2. **hook_worthy**: Should this pattern be enforced as an automated hook "
        "(a shell script that runs automatically when files are edited)? "
        "A pattern is hook-worthy if ALL of the following are true:\n"
        "   - The check is mechanically automatable (grep, regex, or AST scan — not judgment calls)\n"
        "   - It's high-severity (security, breaking changes, data loss, or compliance)\n"
        "   - It's tied to a specific file-edit event (e.g., editing shared files, adding endpoints, modifying migrations)\n"
        "   - It's too important to rely on someone remembering to apply it\n"
        "   - **The check can be precise enough to have a low false positive rate.** A grep that "
        "fires on nearly every edit to common files (e.g., matching any component name, any "
        "variable removal, any history.push) is NOT hook-worthy — it becomes noise that gets "
        "ignored. The grep must target a SPECIFIC anti-pattern that is rare in correct code.\n\n"
        "Examples of NOT hook-worthy (too noisy):\n"
        "   - 'Guard new features behind feature flags' — would fire on any component, not just flag-gated ones\n"
        "   - 'Verify backward compat when removing fields' — would fire on any removed variable, not just API fields\n"
        "   - 'Use history.replace for URL state' — would fire on every navigation, not just state updates\n\n"
        "A pattern can be BOTH skill_worthy and hook_worthy (e.g., a security check that also "
        "benefits from step-by-step guidance). If hook_worthy is true, it takes precedence — "
        "the pattern becomes a hook rather than a skill.\n\n"
        f"Patterns:\n{pattern_list}\n\n"
        'Return ONLY a JSON array: [{"id": "pattern-id", "skill_worthy": true/false, '
        '"skill_rationale": "one sentence", "hook_worthy": true/false, '
        '"hook_rationale": "one sentence explaining why or why not"}]\n\n'
        "Return ONLY the JSON array, no other text."
    )


def cmd_triage(args):
    """Score active patterns on skill-worthiness and demote simple conventions."""
    input_file = args.input
    dry_run = args.dry_run
    force = args.force
    batch_size = 50

    with open(input_file) as f:
        patterns = json.load(f)

    # Filter to triage population: active + review_count >= threshold
    candidates = []
    for p in patterns:
        if p.get("mode") != "active":
            continue
        if p.get("review_count", 1) < MIN_REVIEW_COUNT_TRIAGE:
            continue
        if not force and p.get("skill_worthy") is not None:
            continue
        candidates.append(p)

    print(f"Loaded {len(patterns)} patterns, {len(candidates)} eligible for triage", flush=True)

    if not candidates:
        print("No patterns to triage.")
        return

    # Batch and send to Claude in parallel
    batches = [candidates[i:i + batch_size] for i in range(0, len(candidates), batch_size)]
    results: dict[str, dict] = {}  # id -> {skill_worthy, skill_rationale}
    max_workers = getattr(args, 'workers', 4)

    def _triage_batch(batch_num_and_batch):
        batch_num, batch = batch_num_and_batch
        prompt = build_triage_prompt(batch)
        print(f"  Batch {batch_num}/{len(batches)}: sending {len(batch)} patterns to Claude...", flush=True)
        response = call_claude(prompt)
        parsed = parse_json_response(response)

        if not parsed:
            print(f"  Warning: batch {batch_num} returned no valid results, skipping", file=sys.stderr)
            return {}

        batch_results = {}
        for item in parsed:
            if not isinstance(item, dict):
                continue
            pid = item.get("id", "")
            if pid and "skill_worthy" in item:
                batch_results[pid] = {
                    "skill_worthy": bool(item["skill_worthy"]),
                    "skill_rationale": item.get("skill_rationale", ""),
                    "hook_worthy": bool(item.get("hook_worthy", False)),
                    "hook_rationale": item.get("hook_rationale", ""),
                }
        return batch_results

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_triage_batch, (bn, b)): bn
            for bn, b in enumerate(batches, 1)
        }
        for future in concurrent.futures.as_completed(futures):
            try:
                batch_results = future.result()
                results.update(batch_results)
            except Exception as e:
                print(f"  Error in triage batch: {e}", file=sys.stderr)

    # Report results
    hooks = sum(1 for r in results.values() if r["hook_worthy"])
    worthy = sum(1 for r in results.values() if r["skill_worthy"] and not r["hook_worthy"])
    not_worthy = sum(1 for r in results.values() if not r["skill_worthy"] and not r["hook_worthy"])
    print(f"\nTriage results: {hooks} hook-worthy, {worthy} skill-worthy, {not_worthy} demoted to ambient", flush=True)

    if dry_run:
        print("\n[DRY RUN] No changes written to disk.")
        if hooks:
            print(f"\nHook-worthy patterns ({hooks}):")
            for pid, r in sorted(results.items()):
                if r["hook_worthy"]:
                    print(f"  {pid}: {r['hook_rationale']}")
        print(f"\nSkill-worthy patterns ({worthy}):")
        for pid, r in sorted(results.items()):
            if r["skill_worthy"] and not r["hook_worthy"]:
                print(f"  {pid}: {r['skill_rationale']}")
        return

    # Apply results to patterns
    for p in patterns:
        pid = p.get("id", "")
        if pid in results:
            r = results[pid]
            p["skill_worthy"] = r["skill_worthy"]
            p["skill_rationale"] = r["skill_rationale"]
            p["hook_worthy"] = r["hook_worthy"]
            p["hook_rationale"] = r["hook_rationale"]
            # Hook-worthy takes precedence over skill-worthy
            if r["hook_worthy"]:
                p["mode"] = "hook"
                p["mode_rationale"] = r["hook_rationale"]
            elif not r["skill_worthy"]:
                p["mode"] = "ambient"
                p["mode_rationale"] = r["skill_rationale"]

    with open(input_file, "w") as f:
        json.dump(patterns, f, indent=2)

    print(f"Written to {input_file}", flush=True)
