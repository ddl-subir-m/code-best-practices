# Pattern Extraction Prompt v1

For each review thread, identify if the reviewer is enforcing a generalizable engineering pattern, convention, or best practice.

Skip threads that are:
- Simple acknowledgments ("LGTM", "Fixed", "Good catch")
- PR-specific discussion with no generalizable takeaway
- The PR author explaining their own code (not reviewer feedback)

For each pattern found, output JSON:
1. pattern_name: short, descriptive name
2. rule: one sentence describing what engineers should do
3. category: one of [error-handling, naming, architecture, testing, performance, logging, security, api-design, code-organization, documentation]
4. evidence: quote the reviewer's actual words
5. pr_number: the PR number
6. file_path: the file being reviewed

Only include genuinely generalizable patterns, not one-off code-specific comments.


---

## Review Threads to Analyze

[
  {
    "pr_number": 47265,
    "pr_title": "[DOM-75573] Fix bug in endpoints-apps interaction PR",
    "pr_author": "adrianrsy",
    "file_path": "apps/monolith-adapter/src/test/scala/domino/apps/services/DefaultCommitResolverSpec.scala",
    "line": 79,
    "is_resolved": true,
    "comments": [
      {
        "author": "adrianrsy",
        "body": "Done."
      }
    ]
  },
  {
    "pr_number": 47265,
    "pr_title": "[DOM-75573] Fix bug in endpoints-apps interaction PR",
    "pr_author": "adrianrsy",
    "file_path": "apps/monolith-adapter/src/main/scala/domino/apps/services/DefaultCommitResolver.scala",
    "line": 37,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-bira-ignacio",
        "body": "this assumes defaultRef is always present on a repo and if not, this would throw. Would that be a problem here?"
      },
      {
        "author": "adrianrsy",
        "body": "defaultRef is a required field and should always be present. Should be defaulting to the head ref."
      }
    ]
  },
  {
    "pr_number": 47266,
    "pr_title": "PLAT-9854: Update repo-standards-orb and use the new catalog v2 commands",
    "pr_author": "urianchang",
    "file_path": ".circleci/static-build.yml",
    "line": 947,
    "is_resolved": false,
    "comments": [
      {
        "author": "urianchang",
        "body": "This has been a no-op because the `build-test-and-sonar` job isn't a required job when creating catalogs, so the results haven't been used. "
      }
    ]
  },
  {
    "pr_number": 47266,
    "pr_title": "PLAT-9854: Update repo-standards-orb and use the new catalog v2 commands",
    "pr_author": "urianchang",
    "file_path": ".circleci/static-build.yml",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "urianchang",
        "body": "```suggestion\n  repo-standards: cerebrotech/repo-standards@1.2.0\n```"
      }
    ]
  },
  {
    "pr_number": 47277,
    "pr_title": "PLAT-9854: Update repo-standards-orb and use the new catalog v2 commands",
    "pr_author": "urianchang",
    "file_path": ".circleci/static-build.yml",
    "line": 977,
    "is_resolved": false,
    "comments": [
      {
        "author": "urianchang",
        "body": "@coderabbitai, This is inaccurate. The orb code is located in https://github.com/cerebrotech/repo-standards-orb. The `store_catalog_check` command from the orb copies XML files from `results_path` into `/tmp/catalog/checks/junit/build-test-and-publish/...` and persists to workspace with root set to `/tmp/catalog`. When the `create_catalog_check_v2` command from the orb runs, it attaches the workspace root path at `/tmp/catalog`, so the files should be in `/tmp/catalog/checks/junit/build-test-and-publish/`."
      }
    ]
  },
  {
    "pr_number": 47278,
    "pr_title": "[DOM-75659] Hotfix: revert dfsCommitId source to instance for backwards compatibility",
    "pr_author": "adrianrsy",
    "file_path": "apps/web/src/main/scala/domino/apps/web/transformers/AppVersionTransformer.scala",
    "line": 30,
    "is_resolved": true,
    "comments": [
      {
        "author": "adrianrsy",
        "body": "This is just a partial revert of https://github.com/cerebrotech/domino/commit/04b3d58db2dcc2c4a4014242bb367c65b509aa74\r\nNo need to handle that edge case"
      }
    ]
  },
  {
    "pr_number": 47285,
    "pr_title": "PLAT-9854: Update repo-standards-orb and use the new catalog v2 commands",
    "pr_author": "urianchang",
    "file_path": ".circleci/static-build.yml",
    "line": 917,
    "is_resolved": true,
    "comments": [
      {
        "author": "urianchang",
        "body": "@coderabbitai This is not a concern for this PR and target branch."
      }
    ]
  }
]

---

Return a JSON array of patterns found. Each pattern should have:
- pattern_name (string)
- rule (string)
- category (string, one of: api-design, architecture, code-organization, documentation, error-handling, logging, naming, performance, security, testing)
- evidence (string — quote the reviewer's actual words)
- pr_number (integer)
- file_path (string)

If no patterns are found in this batch, return an empty array: []

Return ONLY the JSON array, no other text.