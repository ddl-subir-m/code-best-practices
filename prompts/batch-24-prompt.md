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
    "pr_number": 40598,
    "pr_title": "[DOM-54528] Create and Update APIs for Compute Providers Admin API",
    "pr_author": "adrianrsy",
    "file_path": "compute-providers/implementation/src/main/scala/domino/computeproviders/implementation/ComputeProvidersServiceImpl.scala",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "adrianrsy",
        "body": "This is placeholder for now.\r\nDo we have a pattern on how to return batched validation errors?\r\nI'm considering creating a dto with a map/list of errors but not sure what the ideal approach is."
      },
      {
        "author": "dmcwhorter-ddl",
        "body": "I can see pros & cons of both approaches.  Wrapping them into one exception seems fine to me."
      }
    ]
  },
  {
    "pr_number": 40598,
    "pr_title": "[DOM-54528] Create and Update APIs for Compute Providers Admin API",
    "pr_author": "adrianrsy",
    "file_path": "compute-providers/implementation/src/main/scala/domino/computeproviders/implementation/ComputeProvidersServiceImpl.scala",
    "line": 267,
    "is_resolved": false,
    "comments": [
      {
        "author": "adrianrsy",
        "body": "This method also fetches values from the schema's default if provided. Is that something that should be possible for secrets or should we only use the configured value and ignore the default if any?"
      }
    ]
  },
  {
    "pr_number": 40598,
    "pr_title": "[DOM-54528] Create and Update APIs for Compute Providers Admin API",
    "pr_author": "adrianrsy",
    "file_path": "compute-providers/implementation/src/main/scala/domino/computeproviders/implementation/ComputeProvidersServiceImpl.scala",
    "line": 336,
    "is_resolved": true,
    "comments": [
      {
        "author": "dmcwhorter-ddl",
        "body": "should there be a check on the length of a secret (like does vault have a max length)?"
      },
      {
        "author": "adrianrsy",
        "body": "I don't see anything in our internal docs, but found this in what is hopefully the right docs page: https://developer.hashicorp.com/vault/docs/internals/limits#entity-and-group-limits\r\n\r\nShould the length field for text entries be used for secrets as well or no?"
      },
      {
        "author": "dmcwhorter-ddl",
        "body": "oh, that does make sense to me -- just use the length field to validate the length of the secret like we do for a text field"
      }
    ]
  },
  {
    "pr_number": 40600,
    "pr_title": "DOM-55672 Grequeni.dom 55672.cust templates base",
    "pr_author": "ddl-grequeni",
    "file_path": "projects/projects-web/app/domino/projects/templates/api/ProjectTemplatesController.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "niole",
        "body": "I think you need to implement a querybindable for the query parameters and then they will get parsed automatically. Add it like this:\r\n-  https://github.com/cerebrotech/domino/blob/develop/projects/projects-web/app/domino/projects/web/Binders.scala#L9, \r\n- https://github.com/cerebrotech/domino/blob/develop/projects/projects-web/BUILD#L11"
      },
      {
        "author": "ddl-grequeni",
        "body": "Good idea! I tried to implement the binder, but it's a bit different from the other one. The `order_by` parameter according to the standard should be of type string of the format `field direction` (field - 1 or more spaces - direction). Good thing about this design is that it allows to concatenate multiple sorts, like\r\n`order_by=hub asc&order_by=name asc` which could be useful for us for the screen that lists templates by hub (sort first by hub asc and then break ties sorting by name ascending).\r\n\r\nSo the binder needs to map the string to a `Seq[BaseTemplatesCollectionOrderByDto]` having \r\n```\r\ncase class BaseTemplatesCollectionOrderByDto(sortField: BaseTemplateSortFieldDto.Value, sortOrder: SortOrder.Value)\r\n```\r\nBut when I did this, it builds but the swagger generator from the routes files is putting `BaseTemplatesCollectionOrderByDto` as a model and specifying the query param to have this type, which doesn't make sense from OAS perspective. I guess it's a corner case in the swagger generator? or maybe I'm doing something wrong. "
      },
      {
        "author": "ddl-grequeni",
        "body": "This is the part of the generated swagger that looks weird: (type string but with a ref to an object)\r\n```\r\n\"schema\": {\r\n                            \"default\": [\r\n                                \"updated desc\"\r\n                            ],\r\n                            \"type\": \"array\",\r\n                            \"items\": {\r\n                                \"type\": \"string\",\r\n                                \"$ref\": \"#/components/schemas/domino.projects.templates.api.models.BaseTemplatesCollectionOrderByDto\"\r\n                            }\r\n                        },\r\n```\r\nI'll push the changes to another branch"
      },
      {
        "author": "ddl-grequeni",
        "body": "Here https://github.com/cerebrotech/domino/pull/40613/files"
      }
    ]
  },
  {
    "pr_number": 40600,
    "pr_title": "DOM-55672 Grequeni.dom 55672.cust templates base",
    "pr_author": "ddl-grequeni",
    "file_path": "projects/projects-web/app/domino/projects/templates/api/ProjectTemplatesController.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "niole",
        "body": "Ik it doesn't really matter, but you can use `DominoId.fromString` for this"
      }
    ]
  },
  {
    "pr_number": 40600,
    "pr_title": "DOM-55672 Grequeni.dom 55672.cust templates base",
    "pr_author": "ddl-grequeni",
    "file_path": "projects/projects-web/app/domino/projects/templates/api/models/ProjectTemplateSourceProjectDto.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "niole",
        "body": "You might not need to add the type for each val: https://github.com/cerebrotech/domino/blob/develop/common-core/src/main/scala/domino/common/models/RunStatus.scala#L57"
      }
    ]
  },
  {
    "pr_number": 40600,
    "pr_title": "DOM-55672 Grequeni.dom 55672.cust templates base",
    "pr_author": "ddl-grequeni",
    "file_path": "projects/projects-web/app/domino/projects/templates/api/models/ProjectTemplateSourceProjectDto.scala",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "niole",
        "body": "This is very verbose. Is it possible to shorten this? `IncludedTemplateFeatureType` (still pretty verbose)?"
      },
      {
        "author": "ddl-grequeni",
        "body": "Yeah they are all pretty verbose. Making them simpler and relying on package name is an option, but the downside is that when you search for a class across the entire codebase you need to pay attention to packages, and can be harder to find a specific class definition. But this is also going to be in the swagger definitions, so it's probably worth it to make them all shorter (packages are also going to the swagger, so it should be fine). I'll give it a shot.\r\n\r\nOnly thing I'm trying to keep consistent is the \"Dto\" suffix, because I saw in other places we usually use \"Dto\" for API models. Another option is to use the \"Model\" suffix. All model classes should only be used in the controller/API, and nowhere else in the code. To keep the API changes contained in that layer.\r\n\r\nThe pattern I'm using with these models is similar to what swagger code generator does. So if we ever migrate this to spec first approach, we only need to make changes to the controller and mappers between domain entities and models."
      }
    ]
  },
  {
    "pr_number": 40601,
    "pr_title": "[DOM-55511] - Update Model API validation for uwsgi. Use curl instead of wget",
    "pr_author": "ddl-tnguyen",
    "file_path": "server/app/domino/server/modelmanager/infrastructure/service/deployment/DeploymentScriptGenerator.scala",
    "line": 123,
    "is_resolved": true,
    "comments": [
      {
        "author": "fernandoacorreia",
        "body": "This is a backward incompatible change.\r\n\r\nIt will break model API deployment for customers using environments that have `wget` but not `curl`. This has been the case for many environments that were shipped with Domino."
      },
      {
        "author": "fernandoacorreia",
        "body": "I verified that `curl` is available at least as far back as Domino 4.4."
      }
    ]
  },
  {
    "pr_number": 40601,
    "pr_title": "[DOM-55511] - Update Model API validation for uwsgi. Use curl instead of wget",
    "pr_author": "ddl-tnguyen",
    "file_path": "server/app/domino/server/modelmanager/infrastructure/service/deployment/HealthcheckGenerator.scala",
    "line": 37,
    "is_resolved": true,
    "comments": [
      {
        "author": "fernandoacorreia",
        "body": "same"
      }
    ]
  },
  {
    "pr_number": 40602,
    "pr_title": "[DOM-55895] System test for a Job's saga execution monitoring ",
    "pr_author": "ddl-ryan-connor",
    "file_path": "system-tests/tests/test_jobs.py",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "noahjax",
        "body": "Nit; typo in checkpoint"
      }
    ]
  },
  {
    "pr_number": 40603,
    "pr_title": "DOM-55901 Fixing returned model config keys",
    "pr_author": "ddl-aj-rossman",
    "file_path": "aigateway/monolithadapter/src/main/scala/domino/aigateway/monolithadapter/EndpointsConfigAdapter.scala",
    "line": 70,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-aj-rossman",
        "body": "Both maps should have the \"secret\" key. When using \"++\", the second map will override the value of the first (which is what we want)"
      }
    ]
  },
  {
    "pr_number": 40607,
    "pr_title": "[QE-15351] RFQA ==>> cucu Datasets Tests",
    "pr_author": "ddl-viniatska",
    "file_path": "e2e-tests/features/domino/datasets/manage_permissions.feature",
    "line": 21,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-cedricyoung",
        "body": "I find that the section headers (i.e. comment steps) incredibly useful during triage, like this one.\r\nWould you add any relevant section headers to the new tests?"
      },
      {
        "author": "ddl-viniatska",
        "body": "sure! Thank you for the review!"
      }
    ]
  },
  {
    "pr_number": 40608,
    "pr_title": "[DOM-55953] Test fix: view extended search results when searching for projects",
    "pr_author": "ddl-mmahmoud",
    "file_path": "e2e-tests/features/domino/projects/project_permissions_private.feature",
    "line": 36,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-xin",
        "body": "I'm a little confused. How is it possible to have more than one project with the same name?"
      },
      {
        "author": "ddl-mmahmoud",
        "body": "The project name is `project-{nonce}`, and the search tokenizer splits on the `-` so it finds all projects with \"project\" in the name \ud83e\udd26 "
      },
      {
        "author": "ddl-xin",
        "body": "Can we maybe just use {SCENARIO_ID} in the input? So only the {nonce} part. I fear this change in test may hide potential search bugs"
      },
      {
        "author": "ddl-mmahmoud",
        "body": "The point of this test is to see if the project is searchable by the given user, it is not a test of the search functionality itself.  That should be covered elsewhere."
      },
      {
        "author": "ddl-mmahmoud",
        "body": "Also this is a pretty new test (merged last week?), we are not reducing coverage we had historically with this change."
      }
    ]
  },
  {
    "pr_number": 40611,
    "pr_title": "[DOM-55972] Write flyte config in StartRunScriptResolver",
    "pr_author": "noahjax",
    "file_path": "server/app/domino/server/dispatcher/infrastructure/StartRunScriptResolver.scala",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "noahjax",
        "body": "This weirdness is necessary because the start run script can either be running as the desired ubuntu user or as root"
      }
    ]
  },
  {
    "pr_number": 40611,
    "pr_title": "[DOM-55972] Write flyte config in StartRunScriptResolver",
    "pr_author": "noahjax",
    "file_path": "server/app/domino/server/dispatcher/infrastructure/StartRunScriptResolver.scala",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-ryan-connor",
        "body": "should we only write this if flows are enabled? (`settings.Flows.isEnabled`)"
      },
      {
        "author": "noahjax",
        "body": "Yeah I considered that but figured there is no downside to writing it if flows is disabled. Happy to change if you feel strongly"
      },
      {
        "author": "ddl-ryan-connor",
        "body": "ive been trying to only add volumes, env vars, etc to the pod yaml (k8s config generator) if flows are enabled. but this is pretty harmless i dont feel strongly about it"
      }
    ]
  },
  {
    "pr_number": 40611,
    "pr_title": "[DOM-55972] Write flyte config in StartRunScriptResolver",
    "pr_author": "noahjax",
    "file_path": "server/app/domino/server/dispatcher/infrastructure/StartRunScriptResolver.scala",
    "line": 236,
    "is_resolved": false,
    "comments": [
      {
        "author": "noahjax",
        "body": "I considered removing the existing file instead, but that felt less flexible in the long run. This approach will be slightly more painful in the short run as many images already have a config file baked in without a flyte console endpoint"
      },
      {
        "author": "ddl-ebrown",
        "body": "Would users ever make their own config file modifications that we don't want to overwrite?"
      }
    ]
  },
  {
    "pr_number": 40613,
    "pr_title": "POC Use binder for order_by query param",
    "pr_author": "ddl-grequeni",
    "file_path": "projects/projects-web/app/domino/projects/templates/api/ProjectTemplatesController.scala",
    "line": 27,
    "is_resolved": false,
    "comments": [
      {
        "author": "niole",
        "body": "everythin should be camel case, since that is the best practice in scala"
      }
    ]
  },
  {
    "pr_number": 40617,
    "pr_title": "QE-15404 Generate a json file for each system test",
    "pr_author": "ddl-xin",
    "file_path": "system-tests/tests/conftest.py",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-cedricyoung",
        "body": "let's exit early instead\r\n```suggestion\r\n    if not config.getoption(\"--html-report-dir\"):\r\n        return\r\n\r\n    if call.when == \"setup\":\r\n        testrail_id = \"\"\r\n```"
      }
    ]
  },
  {
    "pr_number": 40622,
    "pr_title": "QE-15428 Adjust expectation for Spark Job re-run test",
    "pr_author": "ddl-kgarton",
    "file_path": "e2e-tests/features/global_config/clusters/spark_remote.feature",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-xin",
        "body": "nit: please add spaces in the header row to match the content row"
      }
    ]
  },
  {
    "pr_number": 40623,
    "pr_title": "[DOM-52765] Handle events with exact same timestamp in execution startup monitoring",
    "pr_author": "ddl-ryan-connor",
    "file_path": "server/app/domino/server/saga/domain/services/ExecutionCheckpointRulesEngine.scala",
    "line": 110,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-ryan-connor",
        "body": "no changes to logic in this file, just cleaning up some code and using `ExecutionNodeMonitor.handledEventReasons` like for all the other monitors"
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