#!/usr/bin/env python3
"""Prepare and apply LLM-based pattern classification (rule vs skill)."""

import argparse
import json
import os
import sys
from pathlib import Path


def cmd_prepare(args):
    """Split patterns.json into classification batches."""
    with open(args.input) as f:
        patterns = json.load(f)

    # Extract just the fields the LLM needs to classify
    slim = []
    for p in patterns:
        slim.append({
            "id": p["id"],
            "rule": p.get("rule", ""),
            "category": p.get("scope", ""),
            "review_count": p.get("review_count", 1),
            "source_prs": p.get("source_prs", [])[:3],  # limit context
        })

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    batch_size = 50
    batches = [slim[i:i + batch_size] for i in range(0, len(slim), batch_size)]

    for i, batch in enumerate(batches):
        batch_file = output_dir / f"batch-{i + 1}.json"
        with open(batch_file, "w") as f:
            json.dump(batch, f, indent=2)

    print(f"Prepared {len(batches)} classification batches ({len(slim)} patterns)")


def cmd_apply(args):
    """Apply LLM classifications back to patterns.json."""
    with open(args.input) as f:
        patterns = json.load(f)

    # Build lookup from id -> pattern
    by_id = {}
    for p in patterns:
        by_id[p["id"]] = p

    # Read all classification results
    classify_dir = Path(args.classifications)
    applied = 0
    for result_file in sorted(classify_dir.glob("batch-*-results.json")):
        with open(result_file) as f:
            classifications = json.load(f)
        for c in classifications:
            pid = c.get("id")
            mode = c.get("mode")
            if pid in by_id and mode in ("ambient", "active"):
                old_mode = by_id[pid].get("mode", "ambient")
                by_id[pid]["mode"] = mode
                if c.get("rationale"):
                    by_id[pid]["mode_rationale"] = c["rationale"]
                if old_mode != mode:
                    applied += 1

    with open(args.input, "w") as f:
        json.dump(patterns, f, indent=2)

    ambient = sum(1 for p in patterns if p.get("mode") == "ambient")
    active = sum(1 for p in patterns if p.get("mode") == "active")
    print(f"Applied classifications: {applied} changed")
    print(f"  ambient (rules): {ambient}")
    print(f"  active (skills): {active}")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p_prep = sub.add_parser("prepare")
    p_prep.add_argument("--input", required=True)
    p_prep.add_argument("--output-dir", required=True)

    p_apply = sub.add_parser("apply")
    p_apply.add_argument("--input", required=True)
    p_apply.add_argument("--classifications", required=True)

    args = parser.parse_args()
    {"prepare": cmd_prepare, "apply": cmd_apply}[args.command](args)


if __name__ == "__main__":
    main()
