"""Claude CLI integration and response parsing."""

import json
import subprocess
import sys


def call_claude(prompt: str, timeout: int = 300) -> str:
    """Call Claude in headless mode via the claude CLI."""
    try:
        result = subprocess.run(
            ["claude", "-p", "--max-turns", "1", prompt],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            print(f"Warning: claude CLI failed: {result.stderr[:200]}", file=sys.stderr)
            return ""
        return result.stdout.strip()
    except FileNotFoundError:
        sys.exit("Error: 'claude' CLI not found. Install Claude Code first.")
    except subprocess.TimeoutExpired:
        print("Warning: claude CLI timed out", file=sys.stderr)
        return ""


def _strip_code_fences(text: str) -> str:
    """Strip markdown code fences from LLM output."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]  # remove opening ```json
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def parse_json_response(text: str) -> list:
    """Parse a JSON array from Claude's response, handling markdown code blocks."""
    text = _strip_code_fences(text)
    if not text:
        return []
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass
    return []


def parse_json_object(text: str) -> dict:
    """Parse a JSON object from Claude's response, handling markdown code blocks."""
    text = _strip_code_fences(text)
    if not text:
        return {}
    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass
    return {}
