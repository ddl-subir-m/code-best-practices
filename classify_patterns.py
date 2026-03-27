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


def cmd_prepare_enrich(args):
    """Extract active (skill) patterns into batches for LLM enrichment."""
    with open(args.input) as f:
        patterns = json.load(f)

    active = [p for p in patterns if p.get("mode") == "active"]
    if not active:
        print("No active patterns to enrich.")
        return

    slim = []
    for p in active:
        slim.append({
            "id": p["id"],
            "rule": p.get("rule", ""),
            "category": p.get("scope", ""),
            "source_prs": p.get("source_prs", [])[:5],
        })

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    batch_size = 20  # smaller batches — enrichment produces more output per pattern
    batches = [slim[i:i + batch_size] for i in range(0, len(slim), batch_size)]

    for i, batch in enumerate(batches):
        batch_file = output_dir / f"batch-{i + 1}.json"
        with open(batch_file, "w") as f:
            json.dump(batch, f, indent=2)

    print(f"Prepared {len(batches)} enrichment batches ({len(slim)} skills)")


def cmd_apply_enrich(args):
    """Apply LLM enrichments back to active patterns in patterns.json."""
    with open(args.input) as f:
        patterns = json.load(f)

    by_id = {p["id"]: p for p in patterns}

    enrich_dir = Path(args.enrichments)
    enriched = 0
    for result_file in sorted(enrich_dir.glob("batch-*-results.json")):
        with open(result_file) as f:
            enrichments = json.load(f)
        for e in enrichments:
            pid = e.get("id")
            if pid not in by_id:
                continue
            p = by_id[pid]
            if e.get("trigger"):
                p["trigger"] = e["trigger"]
            if e.get("rationale"):
                p["rationale"] = e["rationale"]
            if e.get("steps"):
                p["steps"] = e["steps"]
            if e.get("good_example"):
                p["good_example"] = e["good_example"]
            if e.get("bad_example"):
                p["bad_example"] = e["bad_example"]
            enriched += 1

    with open(args.input, "w") as f:
        json.dump(patterns, f, indent=2)

    print(f"Enriched {enriched} skills with trigger, rationale, and examples")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p_prep = sub.add_parser("prepare")
    p_prep.add_argument("--input", required=True)
    p_prep.add_argument("--output-dir", required=True)

    p_apply = sub.add_parser("apply")
    p_apply.add_argument("--input", required=True)
    p_apply.add_argument("--classifications", required=True)

    p_prep_enrich = sub.add_parser("prepare-enrich")
    p_prep_enrich.add_argument("--input", required=True)
    p_prep_enrich.add_argument("--output-dir", required=True)

    p_apply_enrich = sub.add_parser("apply-enrich")
    p_apply_enrich.add_argument("--input", required=True)
    p_apply_enrich.add_argument("--enrichments", required=True)

    args = parser.parse_args()
    {
        "prepare": cmd_prepare,
        "apply": cmd_apply,
        "prepare-enrich": cmd_prepare_enrich,
        "apply-enrich": cmd_apply_enrich,
    }[args.command](args)


if __name__ == "__main__":
    main()
