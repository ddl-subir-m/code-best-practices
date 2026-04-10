"""
Extraction pipeline for mining best practices from GitHub PR review threads.

Usage:
  python -m extract fetch --repo cerebrotech/domino --since 2024-01-01
  python -m extract analyze --input raw-reviews/ --output patterns.json
  python -m extract report --input patterns.json --output validation-report.md
"""
