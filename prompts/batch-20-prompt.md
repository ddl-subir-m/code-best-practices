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
    "pr_number": 40491,
    "pr_title": "[DOM-52045] Update lint rules",
    "pr_author": "ddl-richard-tom",
    "file_path": "frontend/packages/ui/.eslintrc.json",
    "line": 19,
    "is_resolved": false,
    "comments": [
      {
        "author": "jenniferjfu2",
        "body": "Also View, Details"
      }
    ]
  },
  {
    "pr_number": 40496,
    "pr_title": "VULN-3250 dataSource: getActiveDataSourcesByUser check for mismatching userId - principal",
    "pr_author": "ddl-giuliocapolino",
    "file_path": "datasource/datasource-impl/src/main/scala/domino/datasource/impl/DataSourceServiceImpl.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-eric-jin",
        "body": "Super nit:\r\n```suggestion\r\n      authorizer.throwAuthorizationException(\"The principal used to make the request differs from the user ID in the request.\")\r\n```"
      }
    ]
  },
  {
    "pr_number": 40496,
    "pr_title": "VULN-3250 dataSource: getActiveDataSourcesByUser check for mismatching userId - principal",
    "pr_author": "ddl-giuliocapolino",
    "file_path": "datasource/datasource-adapter/src/main/scala/domino/datasource/adapter/DataSourceAuthorizerImpl.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-eric-jin",
        "body": "I think it can be useful to have a default value to maintain backwards compatibility and convenience.\r\n```suggestion\r\n  override def throwAuthorizationException(message: String = \"Your role does not authorize you to perform this action.\"): Unit =\r\n```"
      }
    ]
  },
  {
    "pr_number": 40499,
    "pr_title": "DOM-55488 (5.11) Update default flyte copilot image from 1.10.6 -> 1.11.0",
    "pr_author": "noahjax",
    "file_path": "server/app/domino/server/computegrid/ComputeGridSettingsAdapter.scala",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-ebrown",
        "body": "Oh whoops -- we should not be using this image reference.  We should be using the Domino version from quay as the fallback:\r\n\r\n```\r\nquay.io/domino/train-flytecopilot-docker:1.11.0-r1\r\n```\r\n\r\nhttps://quay.io/repository/domino/train-flytecopilot-docker"
      },
      {
        "author": "ddl-ebrown",
        "body": "Filed https://dominodatalab.atlassian.net/browse/DOM-55639 to track wiring this through the chart(s) properly in a subsequent PR"
      }
    ]
  },
  {
    "pr_number": 40502,
    "pr_title": "[DOM-55339] Fix Toastr zindex not effective after antd5",
    "pr_author": "gandavarapurajasekhar",
    "file_path": "frontend/apps/web/src/style.css",
    "line": 241,
    "is_resolved": false,
    "comments": [
      {
        "author": "jenniferjfu2",
        "body": "Can you use a constant? Add a note to explain why the number is set."
      },
      {
        "author": "jenniferjfu2",
        "body": "Well, I merge changes for now."
      }
    ]
  },
  {
    "pr_number": 40513,
    "pr_title": "DOM-55607 reverting git assert repo accessible retry logic",
    "pr_author": "ddl-roshikiri",
    "file_path": "repoman/repoman-service/src/main/scala/domino/repoman/service/utils/RepomanGitUtil.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "niole",
        "body": "Should validate remote refs actually be named something bitbucket datacenter specific? It looks like it only works for bitbucket datacenter"
      }
    ]
  },
  {
    "pr_number": 40513,
    "pr_title": "DOM-55607 reverting git assert repo accessible retry logic",
    "pr_author": "ddl-roshikiri",
    "file_path": "repoman/repoman-service/src/main/scala/domino/repoman/service/utils/RepomanGitUtil.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "niole",
        "body": "There is no need to catch and rethrow any exceptions if you're not going to do anything with the caught exception. In this block, you could just do the match on `GitAPIException`, remove all other cases, and the effect will be the same.\r\n\r\nIf you rethrow exceptions here, it sort of defeats the purpose of using an `Either`. Is it necessary to use an either?"
      }
    ]
  },
  {
    "pr_number": 40513,
    "pr_title": "DOM-55607 reverting git assert repo accessible retry logic",
    "pr_author": "ddl-roshikiri",
    "file_path": "repoman/repoman-service/src/main/scala/domino/repoman/service/utils/RepomanGitUtil.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "niole",
        "body": "remove? Also wondering about why we rethrow here instead of wrapping in a Left?"
      }
    ]
  },
  {
    "pr_number": 40514,
    "pr_title": "DOM-55659 Whitelabel LLM Endpoints tab in Workspace sidebar",
    "pr_author": "jenniferjfu2",
    "file_path": "frontend/apps/web/src/modules/workspace-session/components/SideNavContent/LlmEndpointsEmptyState.tsx",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-richard-tom",
        "body": "Why isn't this just a string template? "
      }
    ]
  },
  {
    "pr_number": 40519,
    "pr_title": "[QE-15328] RFQA ==>> cucu Datasets Admin page",
    "pr_author": "ddl-viniatska",
    "file_path": "e2e-tests/features/domino/datasets/admin_datasetrw.feature",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-eric-jin",
        "body": "Should the trailing space be removed?\r\n```suggestion\r\n      And I wait to click the button \"Create Usage Report CSV\"\r\n```"
      }
    ]
  },
  {
    "pr_number": 40519,
    "pr_title": "[QE-15328] RFQA ==>> cucu Datasets Admin page",
    "pr_author": "ddl-viniatska",
    "file_path": "e2e-tests/features/domino/datasets/admin_datasetrw.feature",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-eric-jin",
        "body": "I think this could be moved to background since it is repeated for the three tests."
      },
      {
        "author": "ddl-viniatska",
        "body": "makes sense "
      },
      {
        "author": "ddl-viniatska",
        "body": "Thank you!"
      }
    ]
  },
  {
    "pr_number": 40519,
    "pr_title": "[QE-15328] RFQA ==>> cucu Datasets Admin page",
    "pr_author": "ddl-viniatska",
    "file_path": "e2e-tests/features/domino/datasets/admin_datasetrw.feature",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-eric-jin",
        "body": "Nit:\r\n\r\n```suggestion\r\nFeature: Admin manages Read-Write Datasets\r\n```"
      }
    ]
  },
  {
    "pr_number": 40519,
    "pr_title": "[QE-15328] RFQA ==>> cucu Datasets Admin page",
    "pr_author": "ddl-viniatska",
    "file_path": "e2e-tests/features/domino/datasets/admin_datasetrw.feature",
    "line": 84,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-eric-jin",
        "body": "There might be a race condition here if the dataset gets deleted quickly. One potential remedy could be moving the admin deletion to the end. So, the admin can check they can make dataset Active -> MarkedForDeletion -> Active then at the end actually delete it."
      },
      {
        "author": "ddl-viniatska",
        "body": "@ddl-eric-jin I think this should be fine, we have grace period 15min"
      }
    ]
  },
  {
    "pr_number": 40519,
    "pr_title": "[QE-15328] RFQA ==>> cucu Datasets Admin page",
    "pr_author": "ddl-viniatska",
    "file_path": "e2e-tests/features/domino/datasets/admin_datasetrw.feature",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-eric-jin",
        "body": "Nit: potential simplification.\r\n\r\n```suggestion\r\n  Scenario: Dataset from the archived project should be showing in admin console\r\n```"
      }
    ]
  },
  {
    "pr_number": 40519,
    "pr_title": "[QE-15328] RFQA ==>> cucu Datasets Admin page",
    "pr_author": "ddl-viniatska",
    "file_path": "e2e-tests/features/domino/datasets/admin_datasetrw.feature",
    "line": 44,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-eric-jin",
        "body": "It seems this test is testing a few things. I'm not sure, but do you think it would be easier to isolate failures if it was broken into two tests: 1. mark for deletion + delete 2. mark for deletion -> set to active. It might also help reduce hidden failures if for example delete failed but set as active would also fail but isn't reported."
      },
      {
        "author": "ddl-viniatska",
        "body": "we usually group tests like this into one scenario, it would fail like one scenario. I prefer to keep it this way."
      }
    ]
  },
  {
    "pr_number": 40519,
    "pr_title": "[QE-15328] RFQA ==>> cucu Datasets Admin page",
    "pr_author": "ddl-viniatska",
    "file_path": "e2e-tests/features/domino/datasets/admin_datasetrw.feature",
    "line": 13,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-eric-jin",
        "body": "Realized this after approving, I think for these 3 tests we should add the new `@team-data`"
      }
    ]
  },
  {
    "pr_number": 40520,
    "pr_title": "[DOM-55649] Add checks to dissallow anonymous users to perform model registry calls",
    "pr_author": "ddl-s-ramirezayuso",
    "file_path": "registered-models/implementation/src/main/scala/domino/registeredmodels/implementation/RegisteredModelsAuthorizer.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-kartik-mathur",
        "body": "nit: shouldn't the error message be \"can't list model versions\" instead of stage?"
      },
      {
        "author": "ddl-s-ramirezayuso",
        "body": "Fixed"
      }
    ]
  },
  {
    "pr_number": 40520,
    "pr_title": "[DOM-55649] Add checks to dissallow anonymous users to perform model registry calls",
    "pr_author": "ddl-s-ramirezayuso",
    "file_path": "registered-models/implementation/src/main/scala/domino/registeredmodels/implementation/RegisteredModelsAuthorizer.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-kartik-mathur",
        "body": "nit: same here, incorrect error message?"
      },
      {
        "author": "ddl-s-ramirezayuso",
        "body": "Fixed"
      }
    ]
  },
  {
    "pr_number": 40520,
    "pr_title": "[DOM-55649] Add checks to dissallow anonymous users to perform model registry calls",
    "pr_author": "ddl-s-ramirezayuso",
    "file_path": "registered-models/implementation/src/main/scala/domino/registeredmodels/implementation/RegisteredModelsAuthorizer.scala",
    "line": 64,
    "is_resolved": false,
    "comments": [
      {
        "author": "fernandoacorreia",
        "body": "Is any user allowed to get any model? Why is the model not being checked? I.e. only \"global\" models can be viewed by any user, otherwise the user needs to have permission for that specific model.\r\n\r\nEither I'm missing something or there's a gap."
      },
      {
        "author": "ddl-s-ramirezayuso",
        "body": "We're delegating most of the authorization rules to the mlflow proxy so this is not actually validating that a user has access to a particular model but rather that it has access to the operation to get a model. After this check is successful if the model is not globally discoverable and the user does not have access to it the call to the mlflow proxy will correctly return 403."
      },
      {
        "author": "dmcwhorter-ddl",
        "body": "makes sense, can we add some comment here to explain this?"
      },
      {
        "author": "dmcwhorter-ddl",
        "body": "also -- I feel like there's an mlflow-proxy level ticket that needs to be created to gate anonymous access to query registered models"
      }
    ]
  },
  {
    "pr_number": 40522,
    "pr_title": "[DOM-55522] Aria roles added for aria-label elements",
    "pr_author": "sreeram-s-zessta",
    "file_path": "frontend/apps/web/src/modules/code/CodeBrowse.tsx",
    "line": 134,
    "is_resolved": true,
    "comments": [
      {
        "author": "jenniferjfu2",
        "body": "Should we create union to make sure role uses the proper syntax?"
      },
      {
        "author": "sreeram-s-zessta",
        "body": "as per my understanding, the roles & aria attributes added by Antd is sufficient & the most places where we added aria-label attribute is on `div or span` which are ignored by screen-readers unless it also has a role attribute. The actual interacting elements have aria values set by Antd, so the wrappers might not require these. "
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