"""Deduplicate patterns using exact ID matching + LLM semantic matching."""

import concurrent.futures
import json
import sys
from collections import defaultdict

from .claude import call_claude, parse_json_response
from .merge import merge_duplicate_group


def cmd_dedup(args):
    """Deduplicate patterns using exact ID matching + LLM semantic matching."""
    input_file = args.input

    with open(input_file) as f:
        patterns = json.load(f)

    original_count = len(patterns)
    print(f"Loaded {original_count} patterns from {input_file}", flush=True)

    # --- Pass 1: Merge exact ID duplicates (no LLM needed) ---
    by_id: dict[str, list[dict]] = defaultdict(list)
    for p in patterns:
        by_id[p["id"]].append(p)

    id_merged = []
    id_merge_count = 0
    for pid, group in by_id.items():
        if len(group) > 1:
            id_merge_count += len(group) - 1
            id_merged.append(merge_duplicate_group(group))
        else:
            id_merged.append(group[0])

    print(f"Pass 1 (exact ID): merged {id_merge_count} duplicates, {len(id_merged)} remaining", flush=True)

    # --- Pass 2: LLM semantic dedup across all patterns (scope-agnostic) ---
    BATCH_SIZE = 200

    # Sort by ID so similar names land in the same batch
    id_merged.sort(key=lambda p: p.get("id", ""))

    batches = [id_merged[i:i + BATCH_SIZE] for i in range(0, len(id_merged), BATCH_SIZE)]
    total_batches = len(batches)

    final_patterns = []
    llm_merge_count = 0
    max_workers = getattr(args, 'workers', 4)

    def _dedup_batch(batch_num_and_batch):
        batch_num, batch = batch_num_and_batch
        if len(batch) <= 1:
            return batch_num, batch, None

        pattern_list = json.dumps(
            [{"index": i, "id": p["id"], "rule": p["rule"]} for i, p in enumerate(batch)],
            indent=2,
        )

        prompt = (
            "You are deduplicating patterns extracted from code review history.\n\n"
            "Below is a list of patterns from various categories. Identify groups of "
            "patterns that describe the SAME underlying rule or convention, even if worded "
            "differently or filed under different categories.\n\n"
            "Return ONLY a JSON array of groups. Each group is an array of index numbers "
            "that should be merged. Only include groups with 2+ patterns. Patterns that "
            "are unique should NOT appear in any group. Be conservative — only group "
            "patterns that are clearly about the same thing.\n\n"
            f"Patterns:\n{pattern_list}\n\n"
            "Return ONLY the JSON array, e.g.: [[0, 3, 7], [2, 5]]"
        )

        print(f"  Batch {batch_num}/{total_batches}: "
              f"sending {len(batch)} patterns to Claude...", flush=True)
        response = call_claude(prompt)
        groups = parse_json_response(response)
        return batch_num, batch, groups

    # Run LLM calls in parallel
    batch_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_dedup_batch, (bn, b)): bn
            for bn, b in enumerate(batches, 1)
        }
        for future in concurrent.futures.as_completed(futures):
            try:
                batch_results.append(future.result())
            except Exception as e:
                bn = futures[future]
                print(f"  Error in dedup batch {bn}: {e}", file=sys.stderr)
                batch_results.append((bn, batches[bn - 1], None))

    # Post-process sequentially in batch order
    batch_results.sort(key=lambda r: r[0])

    for batch_num, batch, groups in batch_results:
        if not groups:
            final_patterns.extend(batch)
            continue

        merged_indices: set[int] = set()
        for group in groups:
            if not isinstance(group, list) or len(group) < 2:
                continue
            valid = [i for i in group if isinstance(i, int) and 0 <= i < len(batch)]
            if len(valid) < 2:
                continue
            group_patterns = [batch[i] for i in valid]
            final_patterns.append(merge_duplicate_group(group_patterns))
            merged_indices.update(valid)
            llm_merge_count += len(valid) - 1

        for i, p in enumerate(batch):
            if i not in merged_indices:
                final_patterns.append(p)

    print(f"\nPass 2 (LLM semantic): merged {llm_merge_count} duplicates", flush=True)
    print(f"\nDedup complete: {original_count} → {len(final_patterns)} patterns", flush=True)

    with open(input_file, "w") as f:
        json.dump(final_patterns, f, indent=2)
    print(f"Written to {input_file}", flush=True)
