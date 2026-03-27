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
    "pr_number": 40472,
    "pr_title": "DOM-55547 Fix Flaky Running a job with embedded spark cluster test",
    "pr_author": "ddl-cfuerst",
    "file_path": "e2e-tests/features/domino/environments/spark_environment.feature",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-xin",
        "body": "I fear that the order is not guaranteed but it seems like the following steps depend on the fact that the order is guaranteed.\r\n\r\nLGTM"
      },
      {
        "author": "ddl-cfuerst",
        "body": "I don't think the particular step `to see a table that contains rows matching` cares about order, but to your point the last two rows aren't really important for the test to see, just the top one. I'll remove the bottom two rows just because they're not needed."
      }
    ]
  },
  {
    "pr_number": 40477,
    "pr_title": "QE-15286 Qdrant datasource - workspace executions",
    "pr_author": "ddl-abishek",
    "file_path": "e2e-tests/features/domino/data_sources/qdrant/qdrant_datasource_executions.feature",
    "line": 102,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-joy-liao",
        "body": "Could you add some assertion steps? All of these step starters are 'And'. One of the 'wait to see text' steps in 97 - 99 should start with a 'Then'. Probably the first one on 97."
      },
      {
        "author": "ddl-abishek",
        "body": "Done \r\ncommit e0d4e356371a17bc363ebd6bf87aefdd7129564d (HEAD -> QE-15286, origin/QE-15286)\r\nAuthor: ddl-abishek <abishek.subramanian@dominodatalab.com>\r\nDate:   Mon Mar 18 17:28:44 2024 -0400\r\n\r\n    checking whether data source is actually deleted\r\n\r\n"
      },
      {
        "author": "ddl-abishek",
        "body": "https://github.com/cerebrotech/domino/pull/40477#discussion_r1529308067"
      }
    ]
  },
  {
    "pr_number": 40477,
    "pr_title": "QE-15286 Qdrant datasource - workspace executions",
    "pr_author": "ddl-abishek",
    "file_path": "e2e-tests/features/domino/data_sources/qdrant/qdrant_datasource_executions.feature",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-joy-liao",
        "body": "minor: typo"
      },
      {
        "author": "ddl-abishek",
        "body": "commit ff766dbdd7793b8b9a32d60343ba652e4d5f5a45\r\nAuthor: ddl-abishek <abishek.subramanian@dominodatalab.com>\r\nDate:   Mon Mar 18 17:18:57 2024 -0400\r\n\r\n    typo fix"
      }
    ]
  },
  {
    "pr_number": 40477,
    "pr_title": "QE-15286 Qdrant datasource - workspace executions",
    "pr_author": "ddl-abishek",
    "file_path": "e2e-tests/features/domino/data_sources/qdrant/qdrant_datasource_creation.feature",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-joy-liao",
        "body": "Also no assertion steps in this test. Clicking a button doesn't make sense as an assertion step, that's more of a 'When' type progression step. Add some assertions for when you expect to see certain text, I think line 39 makes sense as a 'Then' step, also line 42 as well. "
      },
      {
        "author": "ddl-abishek",
        "body": "<img width=\"1728\" alt=\"Screenshot 2024-03-18 at 5 27 25 PM\" src=\"https://github.com/cerebrotech/domino/assets/71837717/d8271744-0da6-45b1-962d-97f59c262820\">\r\nSo I followed your convention of cucu steps\r\n\r\nI modified the steps based on this commit \r\ncommit e0d4e356371a17bc363ebd6bf87aefdd7129564d (HEAD -> QE-15286, origin/QE-15286)\r\nAuthor: ddl-abishek <abishek.subramanian@dominodatalab.com>\r\nDate:   Mon Mar 18 17:28:44 2024 -0400\r\n\r\n    checking whether data source is actually deleted"
      }
    ]
  },
  {
    "pr_number": 40477,
    "pr_title": "QE-15286 Qdrant datasource - workspace executions",
    "pr_author": "ddl-abishek",
    "file_path": "e2e-tests/features/domino/data_sources/qdrant/qdrant_datasource_creation.feature",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-joy-liao",
        "body": "Typo in the scenario name 'Verify'"
      },
      {
        "author": "ddl-abishek",
        "body": "commit ff766dbdd7793b8b9a32d60343ba652e4d5f5a45\r\nAuthor: ddl-abishek <abishek.subramanian@dominodatalab.com>\r\nDate:   Mon Mar 18 17:18:57 2024 -0400\r\n\r\n    typo fix"
      }
    ]
  },
  {
    "pr_number": 40479,
    "pr_title": "[DOM-55579] Minor text edits for AI Gateway Admin UI",
    "pr_author": "vivekcalambur",
    "file_path": "frontend/packages/ui/src/ai-gateway/AIGatewayAdmin.tsx",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-galias",
        "body": "Besides the page title, AppContent adds the container styles to the page. Isn't any style getting broken when removing it?"
      },
      {
        "author": "vivekcalambur",
        "body": "I'm actually not seeing any styling being broken by removing it. The only reason I removed it was to fix the font size for the heading"
      }
    ]
  },
  {
    "pr_number": 40479,
    "pr_title": "[DOM-55579] Minor text edits for AI Gateway Admin UI",
    "pr_author": "vivekcalambur",
    "file_path": "server/app/domino/server/admin/ui/views/aiGatewayAdmin.scala.html",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-galias",
        "body": "There is a work in progress for removing the scala templates. Given that we should avoid adding new content to the scala template when possible. In this case the admin page component is defined right below this h1 element, so it should be possible to add this new title inside that component."
      },
      {
        "author": "DDL-Martin-Gazzara",
        "body": "What was the reason to add this header tag and remove the AppContent wrapper? Was the font size incorrect?"
      },
      {
        "author": "vivekcalambur",
        "body": "@DDL-Martin-Gazzara Yes that's correct - The font size was incorrect with the `AppContent` wrapper. If you take a look at other admin pages you can see the difference.\r\n\r\nPlease feel free to push changes to this branch if there's a way to keep the `AppContent` wrapper with the correct heading size :)"
      }
    ]
  },
  {
    "pr_number": 40480,
    "pr_title": "[DOM-55557] Fix for Project Template filters alignment issue",
    "pr_author": "gandavarapurajasekhar",
    "file_path": "frontend/apps/web/src/modules/templates/TemplatesFilter.tsx",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-galias",
        "body": "Not a big deal, but I think we should use `gap=\"0 16px\"` instead. Probably the prettier config is missing this. @ddl-richard-tom Do you think we should add a rule for that?"
      }
    ]
  },
  {
    "pr_number": 40483,
    "pr_title": "DOM-55045 Dom 55045 flows runs tab",
    "pr_author": "ddl-galias",
    "file_path": "frontend/apps/web/src/modules/domino-flows/views/flows-runs/components/flows-workflows-runs-table/FlowsRunsFlowCell.tsx",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "jenniferjfu2",
        "body": "import React from 'react';"
      }
    ]
  },
  {
    "pr_number": 40483,
    "pr_title": "DOM-55045 Dom 55045 flows runs tab",
    "pr_author": "ddl-galias",
    "file_path": "frontend/apps/web/src/modules/domino-flows/views/flows-runs/components/flows-workflows-runs-table/FlowsRunsTable.tsx",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "jenniferjfu2",
        "body": "No need for fragment"
      }
    ]
  },
  {
    "pr_number": 40483,
    "pr_title": "DOM-55045 Dom 55045 flows runs tab",
    "pr_author": "ddl-galias",
    "file_path": "frontend/apps/web/src/modules/domino-flows/views/flows-runs/components/flows-workflows-runs-table/FlowsRunsArchivedDateCell.tsx",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "jenniferjfu2",
        "body": "use getFromNowString in useDate"
      },
      {
        "author": "jenniferjfu2",
        "body": "Leave it as is, and I will fix it."
      },
      {
        "author": "ddl-galias",
        "body": "Applied getFromNowString, also changed flows table to use it at created at cell."
      }
    ]
  },
  {
    "pr_number": 40484,
    "pr_title": "DOM-55581 adding sorting params and totalCount",
    "pr_author": "ddl-aj-rossman",
    "file_path": "aigateway/implementation/src/main/scala/domino/aigateway/AIGatewayApiImpl.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "vivekcalambur",
        "body": "Could we potentially return this number with `endpoints`, so we don't have to make an additional call to the service and Mongo?"
      },
      {
        "author": "ddl-aj-rossman",
        "body": "Yup, I get what you're saying"
      }
    ]
  },
  {
    "pr_number": 40484,
    "pr_title": "DOM-55581 adding sorting params and totalCount",
    "pr_author": "ddl-aj-rossman",
    "file_path": "aigateway/implementation/src/main/scala/domino/aigateway/infrastructure/MongoAIGatewayPersister.scala",
    "line": 26,
    "is_resolved": true,
    "comments": [
      {
        "author": "vivekcalambur",
        "body": "I think we should always default to sorting by `created` timestamp"
      },
      {
        "author": "ddl-aj-rossman",
        "body": "I left it as None because making a mongo query without sorting at all is faster than with sorting. I think having a default is fine if we don't think performance will become an issue. What do you think?"
      },
      {
        "author": "vivekcalambur",
        "body": "I think given the projected size of even the largest collection we may see in real life usage, it should be fine to default to sorting on `Created`"
      },
      {
        "author": "ddl-aj-rossman",
        "body": "Cool"
      }
    ]
  },
  {
    "pr_number": 40484,
    "pr_title": "DOM-55581 adding sorting params and totalCount",
    "pr_author": "ddl-aj-rossman",
    "file_path": "aigateway/public/public-api.yaml",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "vivekcalambur",
        "body": "Descending by creation date should be the default, so I think we should default this to false"
      }
    ]
  },
  {
    "pr_number": 40484,
    "pr_title": "DOM-55581 adding sorting params and totalCount",
    "pr_author": "ddl-aj-rossman",
    "file_path": "aigateway/monolithadapter/src/main/scala/domino/aigateway/monolithadapter/EndpointsConfigAdapter.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "vivekcalambur",
        "body": "```suggestion\r\n    val (endpoints, _) = mongoAIGatewayPersister.findGatewayEndpointsByUserIds(None, None)\r\n```"
      },
      {
        "author": "vivekcalambur",
        "body": "If you don't want to create a new type called `EndpointsWithTotalCount`, I'd refactor to assign each return value to a variable like above wherever you're calling this method (but that doesn't seem pleasant \ud83d\ude06)"
      }
    ]
  },
  {
    "pr_number": 40484,
    "pr_title": "DOM-55581 adding sorting params and totalCount",
    "pr_author": "ddl-aj-rossman",
    "file_path": "aigateway/interface/src/main/scala/entities.scala",
    "line": 1,
    "is_resolved": true,
    "comments": [
      {
        "author": "vivekcalambur",
        "body": "It might make more sense to add a new entity called `EndpointsWithTotalCount` rather than passing a tuple around. The `._1`s make it a bit unreadable"
      }
    ]
  },
  {
    "pr_number": 40484,
    "pr_title": "DOM-55581 adding sorting params and totalCount",
    "pr_author": "ddl-aj-rossman",
    "file_path": "aigateway/implementation/src/main/scala/domino/aigateway/infrastructure/MongoAIGatewayPersister.scala",
    "line": 55,
    "is_resolved": true,
    "comments": [
      {
        "author": "vivekcalambur",
        "body": "nice work catching all the cases"
      }
    ]
  },
  {
    "pr_number": 40485,
    "pr_title": "[QE-15289] RFQA==>> cucu ",
    "pr_author": "ddl-viniatska",
    "file_path": "e2e-tests/features/steps/ui/rw_dataset.py",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-cedricyoung",
        "body": "is there a better alternative to just having indexes of things? \r\nalso is there a UI ticket to make these kebabs more testable?"
      },
      {
        "author": "ddl-viniatska",
        "body": "@ddl-cedricyoung I think there is no ticket"
      }
    ]
  },
  {
    "pr_number": 40487,
    "pr_title": "[DOM-55563] Automate project permissions tests",
    "pr_author": "ddl-mmahmoud",
    "file_path": "e2e-tests/features/domino/projects/project_permissions_private.feature",
    "line": 2,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-grequeni",
        "body": "Please make sure to tag features or scenarios with components according to https://dominodatalab.atlassian.net/wiki/spaces/ENG/pages/2760933411/Develop+Team+Tests+PR+Triggers (CUCU tests column).\r\n\r\nThere are also team tags added recently in another PR. \r\n\r\nI guess these would be at least `@team-develop` and `@projects`. Maybe `@dfs` too if these are DFS projects (not git based) and we do anything with files. Could be `@workspace` too, although I don't think the test is doing anything inside the workspace, if it's just checking it can be launched maybe not testing anything of the workspace itself."
      },
      {
        "author": "ddl-mmahmoud",
        "body": "Good suggestion, thank you Gaston \ud83d\udc4d "
      }
    ]
  },
  {
    "pr_number": 40487,
    "pr_title": "[DOM-55563] Automate project permissions tests",
    "pr_author": "ddl-mmahmoud",
    "file_path": "e2e-tests/features/domino/projects/project_permissions_private.feature",
    "line": 8,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-grequeni",
        "body": "I feel like permission related tests should be unit tests on the permission system and then make sure each domain service is asserting on the right permissions. It's a backend concept, so if we want to test E2E, probably system tests are less expensive and easier to maintain (we can have 1 test for each API we need to validate user has access to).\r\n\r\nMaybe CUCU would make sense for scala play templates or things executed inside workspaces that may be harder to test through API.\r\n\r\nHaving said that, testing multiple permission combinations of the same/similar user actions could be too expensive for CUCU tests. Do we really get value from each isolated scenario? or maybe we could do one or two representative and test other corner cases in unit tests?"
      },
      {
        "author": "ddl-mmahmoud",
        "body": "These tests are manual backlog paydown, so I need to either automate them now or continue to run them manually as I have been doing until we can say we have sufficient lower-level test coverage.\r\n\r\nI agree that the actual permission checks are better tested at a lower level, but right now the exposed API endpoints don't have parity with the internal ones used to upload files from the UI, for example, so the coverage isn't quite equivalent."
      },
      {
        "author": "ddl-grequeni",
        "body": "got it, yeah makes sense. Maybe we can create a follow up Jira to come back and move some of these tests to lower levels.\r\nBTW, we can use system tests to test internal APIs too, we've been doing that already. \"internal\" is just a name, they are all available publicly. The UI test is easier in some cases though, bc some of these old APIs are a little hard to call.\r\n"
      },
      {
        "author": "ddl-grequeni",
        "body": "I created https://dominodatalab.atlassian.net/browse/DOM-55739"
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