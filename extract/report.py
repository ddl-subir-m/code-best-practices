"""Generate a human-readable validation report from patterns.json."""

import json
from collections import defaultdict
from datetime import datetime


def cmd_report(args):
    """Generate a human-readable validation report from patterns.json."""
    input_file = args.input
    output_file = args.output

    with open(input_file) as f:
        patterns = json.load(f)

    # Group by category
    by_category = defaultdict(list)
    for p in patterns:
        by_category[p.get("scope", "uncategorized")].append(p)

    # Sort patterns by review_count descending
    all_sorted = sorted(patterns, key=lambda p: p.get("review_count", 0), reverse=True)
    recurring = [p for p in all_sorted if p.get("review_count", 0) >= 2]
    single = [p for p in all_sorted if p.get("review_count", 0) < 2]

    lines = []
    lines.append("# Pattern Validation Report — cerebrotech/domino\n")
    lines.append(f"**Generated:** {datetime.now().strftime('%B %d, %Y')}")
    lines.append(f"**Total patterns:** {len(patterns)}")
    lines.append(f"**Recurring patterns (2+ PRs):** {len(recurring)}")
    lines.append(f"**Single-occurrence patterns:** {len(single)}")
    lines.append("")
    lines.append("---\n")

    # Recurring patterns
    if recurring:
        lines.append("## Recurring Patterns (ranked by frequency)\n")
        for i, p in enumerate(recurring, 1):
            lines.append(f"### {i}. {p.get('id', 'unknown').replace('-', ' ').title()}")
            lines.append(f"**Rule:** {p.get('rule', 'N/A')}\n")
            lines.append(f"**Category:** {p.get('scope', 'N/A')}")
            lines.append(f"**Mode:** {p.get('mode', 'ambient')}")
            lines.append(f"**Confidence:** {p.get('confidence', 0):.1f}")
            lines.append(f"**Review count:** {p.get('review_count', 0)}")
            lines.append(f"**Source PRs:** {', '.join(p.get('source_prs', []))}")
            lines.append(f"**Modules:** {', '.join(p.get('modules', []))}")
            if p.get("trigger"):
                lines.append(f"**Trigger:** {p['trigger']}")
            if p.get("rationale"):
                lines.append(f"**Rationale:** {p['rationale']}")
            lines.append("")
            lines.append("---\n")

    # Single-occurrence patterns
    if single:
        lines.append(f"## Single-Occurrence Patterns ({len(single)} patterns)\n")
        lines.append("| # | Pattern | Category | Source PRs |")
        lines.append("|---|---------|----------|------------|")
        for i, p in enumerate(single, len(recurring) + 1):
            name = p.get("id", "unknown").replace("-", " ").title()
            lines.append(
                f"| {i} | {name} | {p.get('scope', '')} "
                f"| {', '.join(p.get('source_prs', []))} |"
            )
        lines.append("")
        lines.append("---\n")

    # Summary statistics
    lines.append("## Summary Statistics\n")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total patterns | {len(patterns)} |")
    lines.append(f"| Recurring (2+ PRs) | {len(recurring)} |")
    lines.append(f"| Single-occurrence | {len(single)} |")
    lines.append("")

    lines.append("### Category Distribution\n")
    lines.append("| Category | Count |")
    lines.append("|----------|-------|")
    for cat in sorted(by_category.keys()):
        lines.append(f"| {cat} | {len(by_category[cat])} |")
    lines.append("")

    report = "\n".join(lines)
    with open(output_file, "w") as f:
        f.write(report)

    print(f"Report written to {output_file}")
    print(f"  {len(recurring)} recurring patterns, {len(single)} single-occurrence")
