"""Fetch merged PR review threads from GitHub."""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from .constants import BOT_AUTHORS, GRAPHQL_SEARCH_QUERY, STATE_FILE


def run_gh_graphql(query: str, variables: dict) -> dict:
    """Execute a GraphQL query via `gh api graphql`."""
    cmd = [
        "gh", "api", "graphql",
        "-f", f"query={query}",
    ]
    for key, value in variables.items():
        if value is None:
            continue
        if isinstance(value, int):
            cmd += ["-F", f"{key}={value}"]
        else:
            cmd += ["-f", f"{key}={value}"]

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print(f"Error: gh api graphql failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
    return json.loads(result.stdout)


def filter_bot_comments(pr_data: dict) -> dict:
    """Remove bot-authored comments from review threads."""
    threads = pr_data.get("reviewThreads", {}).get("nodes", [])
    filtered_threads = []
    for thread in threads:
        comments = thread.get("comments", {}).get("nodes", [])
        human_comments = [
            c for c in comments
            if c.get("author", {}).get("login", "") not in BOT_AUTHORS
        ]
        if human_comments:
            filtered_thread = dict(thread)
            filtered_thread["comments"] = {"nodes": human_comments}
            filtered_threads.append(filtered_thread)
    result = dict(pr_data)
    result["reviewThreads"] = {"nodes": filtered_threads}
    return result


def load_state() -> dict:
    """Load extraction state from state.json."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {
        "last_extraction_date": None,
        "last_pr_number": None,
        "total_prs_processed": 0,
        "extraction_runs": [],
    }


def save_state(state: dict):
    """Persist extraction state to state.json."""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)
    print(f"State saved to {STATE_FILE}")


def cmd_fetch(args):
    """Fetch merged PR review threads from GitHub."""
    repo = args.repo
    since = args.since
    until = getattr(args, 'until', None)
    batch_size = min(args.batch_size, 100)  # GitHub max is 100
    output_dir = Path("raw-reviews")
    output_dir.mkdir(exist_ok=True)

    owner, name = repo.split("/")
    if until:
        date_filter = f"merged:{since}..{until}"
    else:
        date_filter = f"merged:>={since}"
    search_query = f"repo:{repo} is:pr is:merged {date_filter} sort:updated-desc"

    state = load_state()
    cursor = None
    total_fetched = 0
    highest_pr = state.get("last_pr_number") or 0

    print(f"Fetching merged PRs from {repo} since {since}...")

    while True:
        variables = {
            "searchQuery": search_query,
            "first": batch_size,
            "after": cursor,
        }
        response = run_gh_graphql(GRAPHQL_SEARCH_QUERY, variables)
        search_data = response.get("data", {}).get("search", {})
        nodes = search_data.get("nodes", [])

        if not nodes:
            break

        for pr in nodes:
            pr_number = pr.get("number")
            if not pr_number:
                continue

            # Filter bot comments
            filtered = filter_bot_comments(pr)

            # Check if any human threads remain
            threads = filtered.get("reviewThreads", {}).get("nodes", [])
            if not threads:
                print(f"  PR #{pr_number}: no human review threads, skipping")
                continue

            # Save raw review
            out_path = output_dir / f"pr-{pr_number}.json"
            with open(out_path, "w") as f:
                json.dump({"data": {"repository": {"pullRequest": filtered}}}, f)

            total_fetched += 1
            highest_pr = max(highest_pr, pr_number)
            print(f"  PR #{pr_number}: {len(threads)} threads saved")

        page_info = search_data.get("pageInfo", {})
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")

    # Update state
    state["last_extraction_date"] = datetime.now().strftime("%Y-%m-%d")
    state["last_pr_number"] = highest_pr
    state["total_prs_processed"] += total_fetched
    state["extraction_runs"].append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "prs": total_fetched,
        "patterns_found": None,  # filled in by analyze
    })
    save_state(state)

    print(f"\nDone. Fetched {total_fetched} PRs to {output_dir}/")
