"""Auto-detect modules from patterns.json and generate modules.yaml."""

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import yaml

from .constants import MODULE_THRESHOLD


def cmd_modules(args):
    """Auto-detect modules from patterns.json and generate modules.yaml."""
    input_file = args.input

    with open(input_file) as f:
        patterns = json.load(f)

    # Count patterns per top-level directory
    dir_counts = defaultdict(int)
    dir_paths = defaultdict(set)

    for pattern in patterns:
        for pr_ref in pattern.get("source_prs", []):
            pass  # source_prs don't have paths

        for module in pattern.get("modules", []):
            if module:
                dir_counts[module] += 1
                dir_paths[module].add(f"/{module}/")

    # Also scan raw reviews for file paths
    raw_dir = Path("raw-reviews")
    if raw_dir.exists():
        for f in raw_dir.glob("pr-*.json"):
            with open(f) as fh:
                data = json.load(fh)
            pr = data.get("data", {}).get("repository", {}).get("pullRequest", {})
            for thread in pr.get("reviewThreads", {}).get("nodes", []):
                path = thread.get("path", "")
                if path:
                    top = path.strip("/").split("/")[0]
                    dir_counts[top] += 1
                    dir_paths[top].add(f"/{top}/")

    # Merge related directories by shared prefix
    merged = {}
    for dirname in sorted(dir_counts.keys()):
        base = dirname.split("-")[0]
        if base in merged:
            merged[base]["paths"].update(dir_paths[dirname])
            merged[base]["count"] += dir_counts[dirname]
        else:
            # Check if any existing merged key shares this prefix
            found = False
            for key in list(merged.keys()):
                if key == base or dirname.startswith(key + "-"):
                    merged[key]["paths"].update(dir_paths[dirname])
                    merged[key]["count"] += dir_counts[dirname]
                    found = True
                    break
            if not found:
                merged[dirname] = {
                    "paths": set(dir_paths[dirname]),
                    "count": dir_counts[dirname],
                }

    # Split into own-module vs other
    modules = {}
    other_paths = []
    for name, info in sorted(merged.items()):
        if info["count"] >= MODULE_THRESHOLD:
            modules[name] = sorted(info["paths"])
        else:
            other_paths.extend(sorted(info["paths"]))

    if other_paths:
        modules["other"] = ["*"]

    output = {
        "modules": modules,
        "threshold": MODULE_THRESHOLD,
        "auto_generated": True,
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
    }

    output_file = args.output
    with open(output_file, "w") as f:
        yaml.dump(output, f, default_flow_style=False, sort_keys=False)

    print(f"Module mapping written to {output_file}")
    for name, paths in modules.items():
        count = merged.get(name, {}).get("count", "?")
        print(f"  {name}: {paths} ({count} patterns)")
