"""Reclassify mode (ambient/active) for all patterns in patterns.json."""

import json
from collections import defaultdict

from .merge import determine_mode


def cmd_reclass(args):
    """Reclassify mode (ambient/active) for all patterns in patterns.json."""
    input_file = args.input

    with open(input_file) as f:
        patterns = json.load(f)

    before = defaultdict(int)
    after = defaultdict(int)

    for p in patterns:
        old_mode = p.get("mode", "ambient")
        before[old_mode] += 1
        # Skip patterns that have been triaged — triage decisions take precedence
        if p.get("skill_worthy") is not None:
            after[old_mode] += 1
            continue
        new_mode = determine_mode(p.get("scope", ""), p.get("rule", ""))
        after[new_mode] += 1
        p["mode"] = new_mode

    with open(input_file, "w") as f:
        json.dump(patterns, f, indent=2)

    print(f"Reclassified {len(patterns)} patterns in {input_file}")
    print(f"  Before: { {k: v for k, v in sorted(before.items())} }")
    print(f"  After:  { {k: v for k, v in sorted(after.items())} }")
