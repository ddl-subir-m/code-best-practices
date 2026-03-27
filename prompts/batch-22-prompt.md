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
    "pr_number": 40550,
    "pr_title": "[DOM-54527] Fetch API Service Layer",
    "pr_author": "adrianrsy",
    "file_path": "compute-providers/monolithadapter/src/main/scala/domino/computeproviders/monolithadapter/ComputeProvidersOrganizationAdapter.scala",
    "line": 10,
    "is_resolved": true,
    "comments": [
      {
        "author": "fernandoacorreia",
        "body": "This should be a singleton."
      }
    ]
  },
  {
    "pr_number": 40550,
    "pr_title": "[DOM-54527] Fetch API Service Layer",
    "pr_author": "adrianrsy",
    "file_path": "compute-providers/monolithadapter/src/main/scala/domino/computeproviders/monolithadapter/ComputeProvidersUserAdapter.scala",
    "line": 11,
    "is_resolved": true,
    "comments": [
      {
        "author": "fernandoacorreia",
        "body": "This should be a singleton."
      }
    ]
  },
  {
    "pr_number": 40555,
    "pr_title": "DOM-55442 update restart run with dependent repos from og job",
    "pr_author": "ddl-amodi",
    "file_path": "jobs/jobs-monolith-adapter/src/main/scala/domino/jobs/monoadapter/JobLauncherAdapter.scala",
    "line": 178,
    "is_resolved": true,
    "comments": [
      {
        "author": "niole",
        "body": "Will this work for rerunning jobs that depended on feature store?"
      },
      {
        "author": "ddl-amodi",
        "body": "From what I can tell, FeatureStore is not relevant for the restart/launch job workflow. We always default this value to None when launching jobs."
      }
    ]
  },
  {
    "pr_number": 40555,
    "pr_title": "DOM-55442 update restart run with dependent repos from og job",
    "pr_author": "ddl-amodi",
    "file_path": "run/run-adapter/src/main/scala/domino/run/adapter/RunFactory.scala",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "niole",
        "body": "uriPath and uriHost are different from a full uri. Do the runs work?"
      },
      {
        "author": "ddl-amodi",
        "body": "updated the logic here to take the repos from the project like before, however we will only persist the ref which is needed from importedGitRepoOverrides"
      }
    ]
  },
  {
    "pr_number": 40555,
    "pr_title": "DOM-55442 update restart run with dependent repos from og job",
    "pr_author": "ddl-amodi",
    "file_path": "run/run-adapter/src/test/scala/domino/run/adapter/RunFactorySpec.scala",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "niole",
        "body": "Can you make a test data fixture for creating RunImportedGitRepo objects that is shareable between all these tests? Maybe add it to a shareable TestUtil file"
      },
      {
        "author": "ddl-amodi",
        "body": "Updated with a new TestUtils file"
      }
    ]
  },
  {
    "pr_number": 40555,
    "pr_title": "DOM-55442 update restart run with dependent repos from og job",
    "pr_author": "ddl-amodi",
    "file_path": "run/run-adapter/src/test/scala/domino/run/adapter/RunFactorySpec.scala",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "niole",
        "body": "Can you also make a shareable test data fixture creator for PreparedRepository?"
      },
      {
        "author": "ddl-amodi",
        "body": "Updated with a new TestUtils file"
      }
    ]
  },
  {
    "pr_number": 40556,
    "pr_title": "DOM-55613  Parameterize individual generated tests in test ai hub e2e",
    "pr_author": "niole",
    "file_path": "system-tests/tests/aihub/test_ai_hub_templates_e2e.py",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-xin",
        "body": "I'm not sure about the default value. In my opinion, it's better to not have a default value so that if some new test is added and it doesn't have an entry in the dict, line 308 will fail. In this way, we can enforce unique testrail ids for test cases"
      },
      {
        "author": "niole",
        "body": "that makes a lot of sense. will update"
      },
      {
        "author": "niole",
        "body": "done"
      }
    ]
  },
  {
    "pr_number": 40559,
    "pr_title": "DOM-55769: Delete Model Deployment Endpoint",
    "pr_author": "ddl-yaniv-amar",
    "file_path": "model-serving/infrastructure/src/main/scala/domino/modelserving/persistence/MongoModelDeploymentPersister.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "dmcwhorter-ddl",
        "body": "hmm, doesn't this need to do something like set archived = true?"
      },
      {
        "author": "ddl-yaniv-amar",
        "body": "it does, I moved it up before this for some reason. Good catch! fixing."
      }
    ]
  },
  {
    "pr_number": 40560,
    "pr_title": "[DOM-53479] mapping error message when transfering project fails",
    "pr_author": "DDL-Martin-Gazzara",
    "file_path": "frontend/packages/test-utils/src/component-test-utils/form-test-utils.ts",
    "line": 318,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-galias",
        "body": "this command seems simple enough for not being needed"
      },
      {
        "author": "DDL-Martin-Gazzara",
        "body": "Let's keep it. I think to have `await writeTextInput(...)` is more readable than the line it contains. And we can improve this command by resetting the input content before writing."
      }
    ]
  },
  {
    "pr_number": 40561,
    "pr_title": "QE-15398: fixing modelAPI and adding stop modelAPI version",
    "pr_author": "polovinko1980",
    "file_path": "system-tests/tests/test_cli_more.py",
    "line": 217,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-mmahmoud",
        "body": "It is sufficient to start the first line on the line after `\"\"\"` but with the same indent.\r\n\r\n```suggestion\r\n        \"\"\"\r\n        #!/usr/bin/env python\r\n        def main(**kwargs):\r\n            return {\"good\": \"stuff\"}\r\n```\r\nDemo:\r\n![image](https://github.com/cerebrotech/domino/assets/67887898/487a0d00-fbbc-433a-8e6d-5183f8b6b789)\r\n```\r\n(venv) albatross 545$ python /tmp/wrap.py\r\nfoo\r\n        bar\r\n        baz\r\n\r\n\r\nfoo\r\nbar\r\nbaz\r\n```"
      },
      {
        "author": "polovinko1980",
        "body": "@ddl-mmahmoud could you check also this comment?\r\n```\r\n    # Can't separate the \"\"\" and the #! because then the shebang line won't be\r\n    # the first line as is required.\r\n```\r\n\r\nI have concerns about your suggestion, that is why I did not separate `\"\"\"` and `#! `"
      },
      {
        "author": "ddl-mmahmoud",
        "body": "Yeah if you have tested your adjustment to work I will drop these comments, apparently I got it wrong then and I am maybe getting it wrong again now."
      }
    ]
  },
  {
    "pr_number": 40561,
    "pr_title": "QE-15398: fixing modelAPI and adding stop modelAPI version",
    "pr_author": "polovinko1980",
    "file_path": "system-tests/tests/test_cli_more.py",
    "line": 285,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-mmahmoud",
        "body": "It is sufficient to start the first line on the line after `\"\"\"` but with the same indent.\r\n\r\n```suggestion\r\n        \"\"\"\r\n        #!/usr/bin/env python\r\n        def main(**kwargs):\r\n            return {\"good\": \"stuff\"}\r\n```"
      }
    ]
  },
  {
    "pr_number": 40561,
    "pr_title": "QE-15398: fixing modelAPI and adding stop modelAPI version",
    "pr_author": "polovinko1980",
    "file_path": "system-tests/tests/test_cli_more.py",
    "line": 344,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-mmahmoud",
        "body": "It is sufficient to start the first line on the line after `\"\"\"` but with the same indent.\r\n\r\n```suggestion\r\n        \"\"\"\r\n        #!/usr/bin/env python\r\n        def main(**kwargs):\r\n            return {\"good\": \"stuff\"}\r\n```"
      }
    ]
  },
  {
    "pr_number": 40561,
    "pr_title": "QE-15398: fixing modelAPI and adding stop modelAPI version",
    "pr_author": "polovinko1980",
    "file_path": "system-tests/tests/test_cli_more.py",
    "line": 425,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-mmahmoud",
        "body": "It is sufficient to start the first line on the line after `\"\"\"` but with the same indent.\r\n\r\n```suggestion\r\n        \"\"\"\r\n        #!/usr/bin/env python\r\n        def main(**kwargs):\r\n            return {\"good\": \"stuff\"}\r\n```"
      }
    ]
  },
  {
    "pr_number": 40561,
    "pr_title": "QE-15398: fixing modelAPI and adding stop modelAPI version",
    "pr_author": "polovinko1980",
    "file_path": "system-tests/helpers/quick_start_lookalike.py",
    "line": 52,
    "is_resolved": false,
    "comments": [
      {
        "author": "polovinko1980",
        "body": "Fixing this:\r\n<img width=\"1586\" alt=\"Screenshot 2024-03-23 at 5 24 51 PM\" src=\"https://github.com/cerebrotech/domino/assets/95386764/79f8db85-93ef-4484-95c3-557dc4084bf9\">\r\n"
      }
    ]
  },
  {
    "pr_number": 40561,
    "pr_title": "QE-15398: fixing modelAPI and adding stop modelAPI version",
    "pr_author": "polovinko1980",
    "file_path": "system-tests/tests/test_user_access_control_model_api.py",
    "line": 188,
    "is_resolved": false,
    "comments": [
      {
        "author": "polovinko1980",
        "body": "After stop model version call the correct status is `Ready to run` Never saw `Stopped`"
      }
    ]
  },
  {
    "pr_number": 40561,
    "pr_title": "QE-15398: fixing modelAPI and adding stop modelAPI version",
    "pr_author": "polovinko1980",
    "file_path": "system-tests/tests/test_dominodatalab.py",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-mmahmoud",
        "body": "Maybe this doesn't matter since it is just best-effort, but if the test fails, this line will not run.  To get this line to run even if the test fails, the test must appear in a `try/finally` block, and the `finally` branch should have the cleanup.  I.E.\r\n\r\n```python\r\ntry:\r\n    all_testing_goes_here()\r\nfinally:\r\n    stop_model()\r\n```\r\n\r\nBut most of the time the tests pass, so most of the time this cleanup will occur, and perhaps that is sufficient    \r\n"
      },
      {
        "author": "polovinko1980",
        "body": "Addressed"
      }
    ]
  },
  {
    "pr_number": 40563,
    "pr_title": "[DOM-55393] UI add pagination support to endpoints table",
    "pr_author": "DDL-Martin-Gazzara",
    "file_path": "frontend/packages/ui/src/ai-gateway/AIGatewayAdminContainer.tsx",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-galias",
        "body": "It concerns me a bit the way in which pagination is handled here. What happens if the pagination changes while loading is on? is that page going to be missed? Also something important is that when you work with the prev-curr schema you should not dismiss setting the prev to the curr because of an external condition (in this case loading)\r\n\r\nI was thinking that you might be also able to get rid of this prev check by calling the refetch when calling on change pagination, but I am not sure how is that going to work with useRemoteData"
      },
      {
        "author": "DDL-Martin-Gazzara",
        "body": "Removed loading from fetching condition "
      }
    ]
  },
  {
    "pr_number": 40563,
    "pr_title": "[DOM-55393] UI add pagination support to endpoints table",
    "pr_author": "DDL-Martin-Gazzara",
    "file_path": "frontend/packages/ui/src/ai-gateway/AIGatewayAdminContainer.tsx",
    "line": 22,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-galias",
        "body": "why does pagination contains the sorter and filter (I saw it adds it below) state? I assume it has everything as mechanism for being able to refetch when any of the sort, filter or page state changes. If that's the case, the state should not be called `pagination` as it is misleading.\r\n\r\nAlso a note,  between this state object and the arrangement for checking the prev and current state, it makes me think that we are doing all this things just for making it match with the `useRemoteData` use case. If that's the case, is what useRemoteData offers for the use case here (a loading state) worth all this hacks?"
      },
      {
        "author": "DDL-Martin-Gazzara",
        "body": "Removed `useRemoteData` to handling the fetch operation by myself"
      }
    ]
  },
  {
    "pr_number": 40563,
    "pr_title": "[DOM-55393] UI add pagination support to endpoints table",
    "pr_author": "DDL-Martin-Gazzara",
    "file_path": "frontend/packages/ui/src/ai-gateway/__tests__/asd.tsx",
    "line": 1,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-galias",
        "body": "empty file :P "
      },
      {
        "author": "DDL-Martin-Gazzara",
        "body": "Deleted"
      }
    ]
  },
  {
    "pr_number": 40563,
    "pr_title": "[DOM-55393] UI add pagination support to endpoints table",
    "pr_author": "DDL-Martin-Gazzara",
    "file_path": "frontend/packages/ui/src/ai-gateway/api-services.ts",
    "line": 35,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-galias",
        "body": "I assume this is an api thing, can you leave a comment for the future here? I assume that true == asc, false == desc and undefined  == none"
      },
      {
        "author": "DDL-Martin-Gazzara",
        "body": "Done"
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