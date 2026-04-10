"""Enrich skill-worthy patterns with steps, examples, and triggers."""

import concurrent.futures
import json
import sys

from .claude import call_claude, parse_json_object


def build_enrich_prompt(pattern: dict) -> str:
    """Build the Claude enrichment prompt for a single pattern."""
    return (
        "You are enriching an engineering pattern mined from PR review history "
        "at Domino Data Lab. Given this pattern, generate structured skill content.\n\n"
        f"Pattern ID: {pattern['id']}\n"
        f"Rule: {pattern['rule']}\n"
        f"Category: {pattern.get('scope', '')}\n"
        f"Source PRs: {', '.join(pattern.get('source_prs', []))}\n"
        f"Modules: {', '.join(pattern.get('modules', []))}\n\n"
        "Generate a JSON object with these fields:\n"
        '1. "id": the pattern ID (echo it back for validation)\n'
        '2. "trigger": 1-2 sentences describing when this applies (second person: "You\'re writing...")\n'
        '3. "steps": array of 3-6 concrete action steps as strings\n'
        '4. "good_example": a concrete code example showing the correct approach '
        "(use Scala for server/apps patterns, TypeScript/React for frontend patterns)\n"
        '5. "bad_example": a concrete code example showing the anti-pattern\n'
        '6. "rationale": 1-2 sentences explaining WHY this matters\n'
        '7. "skill_title": an imperative-voice title (e.g., "Replace full-object fetches with count queries")\n\n'
        "Return ONLY the JSON object, no other text."
    )


def enrich_single_pattern(pattern: dict) -> dict | None:
    """Enrich a single pattern via Claude. Returns enrichment fields or None on failure."""
    prompt = build_enrich_prompt(pattern)
    response = call_claude(prompt, timeout=120)
    result = parse_json_object(response)
    if not result:
        return None

    # Validate the response has steps
    steps = result.get("steps", [])
    if not isinstance(steps, list) or len(steps) < 1:
        return None

    return result


def cmd_enrich(args):
    """Enrich skill-worthy patterns with steps, examples, and triggers."""
    input_file = args.input
    force = args.force
    max_workers = args.workers

    with open(input_file) as f:
        patterns = json.load(f)

    # Filter to enrichment population: skill_worthy=True + not already enriched
    candidates = []
    candidate_indices = []
    for i, p in enumerate(patterns):
        if not p.get("skill_worthy"):
            continue
        if not force and isinstance(p.get("steps"), list) and len(p.get("steps", [])) > 0:
            continue
        candidates.append(p)
        candidate_indices.append(i)

    print(f"Loaded {len(patterns)} patterns, {len(candidates)} eligible for enrichment", flush=True)

    if not candidates:
        print("No patterns to enrich.")
        return

    # Enrich in parallel
    enriched_count = 0
    failed_count = 0

    def process(idx_pattern):
        idx, pattern = idx_pattern
        result = enrich_single_pattern(pattern)
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
                    # Validate id matches
                    if result.get("id") and result["id"] != pid:
                        print(f"  Warning: id mismatch for {pid}, skipping", file=sys.stderr)
                        failed_count += 1
                        continue
                    # Apply enrichment fields
                    p = patterns[idx]
                    for field in ("trigger", "steps", "good_example", "bad_example", "rationale", "skill_title"):
                        if field in result and result[field]:
                            p[field] = result[field]
                    enriched_count += 1
                    print(f"  [{enriched_count}/{len(candidates)}] Enriched: {pid}", flush=True)
                else:
                    failed_count += 1
                    print(f"  Warning: enrichment failed for {pid}", file=sys.stderr)
                    # Fall back to ambient mode to avoid the black hole
                    patterns[idx]["mode"] = "ambient"
                    patterns[idx]["mode_rationale"] = "Enrichment failed, fell back to ambient"
            except Exception as e:
                failed_count += 1
                print(f"  Error enriching pattern: {e}", file=sys.stderr)

    print(f"\nEnrichment complete: {enriched_count} enriched, {failed_count} failed", flush=True)

    with open(input_file, "w") as f:
        json.dump(patterns, f, indent=2)

    print(f"Written to {input_file}", flush=True)
