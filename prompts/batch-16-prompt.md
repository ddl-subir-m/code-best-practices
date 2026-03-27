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
    "pr_number": 40402,
    "pr_title": "[DOM-55256] Adding extra validation for audit reports",
    "pr_author": "ldebello-ddl",
    "file_path": "audit_trail/impl/src/main/scala/domino/audit/impl/AuditTrailServiceImpl.scala",
    "line": 207,
    "is_resolved": false,
    "comments": [
      {
        "author": "niole",
        "body": "You can feel free to use the projectAuthorizer directly. I think the develop team would prefer that you call the project service in order to get the project information, since that includes authorization. I realize that this code has already been here for a while and refactoring it may take some time. If you need more data to be exposed on the projects info returned from the project service, I think it would be reasonable to add it."
      }
    ]
  },
  {
    "pr_number": 40404,
    "pr_title": "DOM-55337 convert App.tsx from classic component to functional component",
    "pr_author": "jenniferjfu2",
    "file_path": "frontend/apps/web/src/components/App.tsx",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-richard-tom",
        "body": "move to a useCallback"
      },
      {
        "author": "ddl-richard-tom",
        "body": "alternative may consider using a library react-helmet like https://www.npmjs.com/package/react-helmet"
      },
      {
        "author": "jenniferjfu2",
        "body": "Done"
      }
    ]
  },
  {
    "pr_number": 40404,
    "pr_title": "DOM-55337 convert App.tsx from classic component to functional component",
    "pr_author": "jenniferjfu2",
    "file_path": "frontend/apps/web/src/components/App.tsx",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-richard-tom",
        "body": "Move to a use callback"
      },
      {
        "author": "jenniferjfu2",
        "body": "Done"
      }
    ]
  },
  {
    "pr_number": 40404,
    "pr_title": "DOM-55337 convert App.tsx from classic component to functional component",
    "pr_author": "jenniferjfu2",
    "file_path": "frontend/apps/web/src/components/App.tsx",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-richard-tom",
        "body": "seems like we could just use a pick for this https://ramdajs.com/docs/#pick"
      },
      {
        "author": "jenniferjfu2",
        "body": "Done"
      }
    ]
  },
  {
    "pr_number": 40404,
    "pr_title": "DOM-55337 convert App.tsx from classic component to functional component",
    "pr_author": "jenniferjfu2",
    "file_path": "frontend/apps/web/src/components/App.tsx",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-richard-tom",
        "body": "can probably wrap this with a useMemo"
      },
      {
        "author": "jenniferjfu2",
        "body": "Done"
      }
    ]
  },
  {
    "pr_number": 40415,
    "pr_title": "[DOM-55288] Allow /render to return raw content",
    "pr_author": "ddl-g-chen",
    "file_path": "nucleus/app/domino/nucleus/files/ui/FilesController.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-grequeni",
        "body": "Could you please add the jira ticket to all the new TODO comments? otherwise it's easy to lose track of them."
      }
    ]
  },
  {
    "pr_number": 40415,
    "pr_title": "[DOM-55288] Allow /render to return raw content",
    "pr_author": "ddl-g-chen",
    "file_path": "server/app/domino/server/files/domain/FileRetriever.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-grequeni",
        "body": "```suggestion\r\n    val fileRenderer = if (renderRaw) {\r\n      fileRendererFactory.makeRawDfsRenderer(path, signature, new FileContentRetriever(fileStorageManager, signature), renderUnknownTypesAsText)\r\n    } else {\r\n       fileRendererFactory.makeDfsRenderer(path, signature, new FileContentRetriever(fileStorageManager, signature), renderUnknownTypesAsText)\r\n    }\r\n```"
      }
    ]
  },
  {
    "pr_number": 40415,
    "pr_title": "[DOM-55288] Allow /render to return raw content",
    "pr_author": "ddl-g-chen",
    "file_path": "server/app/domino/server/files/domain/renderer/FileRendererFactory.scala",
    "line": 52,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-amodi",
        "body": "Do we need the tooBigAlert function? What is the difference between this and `renderTooBigAlert`"
      },
      {
        "author": "ddl-g-chen",
        "body": "renderTooBigAlert has a message meant to be inside an iframe so there's added html. tooBigAlert is just the error message and nothing else"
      }
    ]
  },
  {
    "pr_number": 40415,
    "pr_title": "[DOM-55288] Allow /render to return raw content",
    "pr_author": "ddl-g-chen",
    "file_path": "frontend/packages/ui/src/filebrowser/FileEditorComponent.tsx",
    "line": 85,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-galias",
        "body": "minor, it should probably be good to return an empty render or a spinner until the data is fully loaded."
      }
    ]
  },
  {
    "pr_number": 40415,
    "pr_title": "[DOM-55288] Allow /render to return raw content",
    "pr_author": "ddl-g-chen",
    "file_path": "frontend/packages/ui/src/filebrowser/FileEditorComponent.tsx",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "jenniferjfu2",
        "body": "Can be simplified to: import React from 'react';"
      }
    ]
  },
  {
    "pr_number": 40419,
    "pr_title": "DOM-53234 Add Telemetry (mix panel) for file rendering",
    "pr_author": "ddl-amodi",
    "file_path": "frontend/packages/ui/src/filebrowser/filesBrowserUtil.tsx",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-galias",
        "body": "I am not a big fan of mixing the MP logic inside the components. In general I prefer moving it to a hook un just function a method like `trackFileRender` that should receive the filename and the location. Then it should take care of getting the file extension and building the event.\r\nThat would also avoid repetition of the same logic in both usages."
      }
    ]
  },
  {
    "pr_number": 40429,
    "pr_title": "QE-15076 Qe 15076 tag tests with teams",
    "pr_author": "ddl-bcolby",
    "file_path": "e2e-tests/features/domino/control_center/control_center_basic.feature",
    "line": 11,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-mmahmoud",
        "body": "```suggestion\r\n  @team-control\r\n```"
      }
    ]
  },
  {
    "pr_number": 40429,
    "pr_title": "QE-15076 Qe 15076 tag tests with teams",
    "pr_author": "ddl-bcolby",
    "file_path": "e2e-tests/features/domino/control_center/control_center_basic.feature",
    "line": 23,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-mmahmoud",
        "body": "```suggestion\r\n  @team-control\r\n```"
      }
    ]
  },
  {
    "pr_number": 40429,
    "pr_title": "QE-15076 Qe 15076 tag tests with teams",
    "pr_author": "ddl-bcolby",
    "file_path": "e2e-tests/features/domino/model_registry/activity_log.feature",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-cedricyoung",
        "body": "\n```suggestion\n      And I set the variable \"PROJECT_NAME\" to \"Model-Review-Project-{SCENARIO_RUN_ID}\"\n\n  @team-pham\n  @testrail(823307)\n```"
      }
    ]
  },
  {
    "pr_number": 40429,
    "pr_title": "QE-15076 Qe 15076 tag tests with teams",
    "pr_author": "ddl-bcolby",
    "file_path": "e2e-tests/features/domino/model_registry/custom_stages.feature",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-cedricyoung",
        "body": "\n```suggestion\n      And I set the variable \"PROJECT_NAME\" to \"Model-Review-Project-{SCENARIO_RUN_ID}\"\n\n  @team-pham\n  @testrail(822578)\n```"
      }
    ]
  },
  {
    "pr_number": 40429,
    "pr_title": "QE-15076 Qe 15076 tag tests with teams",
    "pr_author": "ddl-bcolby",
    "file_path": "e2e-tests/features/domino/model_registry/model_review.feature",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-cedricyoung",
        "body": "\n```suggestion\n      And I set the variable \"USER_NAME_REVIEWER2\" to \"reviewer2-model-pract-{SCENARIO_RUN_ID}\"\n\n  @team-pham\n  @testrail(778022)\n```"
      }
    ]
  },
  {
    "pr_number": 40429,
    "pr_title": "QE-15076 Qe 15076 tag tests with teams",
    "pr_author": "ddl-bcolby",
    "file_path": "e2e-tests/features/domino/model_registry/user_permissions.feature",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-cedricyoung",
        "body": "\n```suggestion\n      And I set the variable \"PROJECT_NAME\" to \"Model-Review-Project-{SCENARIO_RUN_ID}\"\n\n  @team-pham\n  @testrail(823308)\n  Scenario: Model Registry Permissions for Domino Admin\n```"
      }
    ]
  },
  {
    "pr_number": 40429,
    "pr_title": "QE-15076 Qe 15076 tag tests with teams",
    "pr_author": "ddl-bcolby",
    "file_path": "e2e-tests/features/domino/jobs/run_jobs_gbp.feature",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-cedricyoung",
        "body": "\n```suggestion\n  @jobs @bitbucket\n  @team-develop\n```"
      }
    ]
  },
  {
    "pr_number": 40429,
    "pr_title": "QE-15076 Qe 15076 tag tests with teams",
    "pr_author": "ddl-bcolby",
    "file_path": "e2e-tests/features/domino/jobs/run_jobs_gbp.feature",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-cedricyoung",
        "body": "\n```suggestion\n  @jobs\n  @team-develop\n```"
      }
    ]
  },
  {
    "pr_number": 40429,
    "pr_title": "QE-15076 Qe 15076 tag tests with teams",
    "pr_author": "ddl-bcolby",
    "file_path": "e2e-tests/features/domino/jobs/run_jobs_gbp.feature",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-cedricyoung",
        "body": "\n```suggestion\n  @jobs @gitlab\n  @team-develop\n```"
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