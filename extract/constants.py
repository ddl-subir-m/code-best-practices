"""Shared constants for the extraction pipeline."""

BOT_AUTHORS = {"coderabbitai", "codecov", "github-actions", "dependabot"}

VALID_CATEGORIES = {
    "error-handling", "naming", "architecture", "testing", "performance",
    "logging", "security", "api-design", "code-organization", "documentation",
}

STATE_FILE = "state.json"

GRAPHQL_SEARCH_QUERY = """
query($searchQuery: String!, $first: Int!, $after: String) {
  search(query: $searchQuery, type: ISSUE, first: $first, after: $after) {
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      ... on PullRequest {
        number
        title
        author { login }
        mergedAt
        reviewThreads(first: 50) {
          nodes {
            comments(first: 20) {
              nodes {
                author { login }
                body
                createdAt
              }
            }
            isResolved
            path
            line
          }
        }
      }
    }
  }
}
"""

MODULE_THRESHOLD = 5

DEFAULT_CATEGORY = "code-organization"
