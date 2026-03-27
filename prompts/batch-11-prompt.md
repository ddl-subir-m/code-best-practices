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
    "pr_number": 40212,
    "pr_title": "DOM-54624 Dom 54624 flows landing page basic layout",
    "pr_author": "ddl-galias",
    "file_path": "frontend/apps/web/src/modules/domino-flows/views/flows-home/components/flows-home-empty-state/styles.ts",
    "line": 47,
    "is_resolved": false,
    "comments": [
      {
        "author": "DDL-Martin-Gazzara",
        "body": "We should use themeHelper "
      },
      {
        "author": "ddl-galias",
        "body": "There is not font size for 18px at the helper, and given the dimensions I don't think there is a proper key between medium and large:\r\n```\r\n/* font sizes */\r\nexport const EXTRA_TINY = '10px';\r\nexport const TINY = '12px';\r\nexport const SMALL = '14px';\r\nexport const MEDIUM = '16px';\r\nexport const LARGE = '20px';\r\nexport const EXTRA_LARGE = '48px';\r\n```"
      }
    ]
  },
  {
    "pr_number": 40212,
    "pr_title": "DOM-54624 Dom 54624 flows landing page basic layout",
    "pr_author": "ddl-galias",
    "file_path": "frontend/apps/web/src/modules/domino-flows/views/flows-home/styles.ts",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "DDL-Martin-Gazzara",
        "body": "Should we use themeHelper here?"
      },
      {
        "author": "ddl-galias",
        "body": "afaik there is no theme helper entry for the font family, please let me know if you have found one."
      },
      {
        "author": "jenniferjfu2",
        "body": "Isn't roboto the default font-family?\r\nWe should globally control the font-family. In visual refresh, we are going to change it to inter. cc: @ddl-g-chen "
      }
    ]
  },
  {
    "pr_number": 40213,
    "pr_title": "[DOM-55093] EDVs in APPs",
    "pr_author": "ddl-viniatska",
    "file_path": "e2e-tests/features/data/edv/app.sh",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-abishek",
        "body": "@ddl-viniatska Can we simply remove the python code related (commented) lines? It'll simply help with legibility when someone else runs the test and triages the result failure "
      },
      {
        "author": "ddl-viniatska",
        "body": "sure"
      },
      {
        "author": "SeanW-DDL",
        "body": "Is this app file tailored to the edv test? Otherwise, we already have it in the e2e tests here: https://github.com/cerebrotech/domino/blob/develop/e2e-tests/features/data/shiny-example-app/app.sh"
      },
      {
        "author": "ddl-viniatska",
        "body": "done, thank you"
      }
    ]
  },
  {
    "pr_number": 40213,
    "pr_title": "[DOM-55093] EDVs in APPs",
    "pr_author": "ddl-viniatska",
    "file_path": "e2e-tests/features/domino/external_volumes/dsp_view_and_mount_edv.feature",
    "line": 178,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-cedricyoung",
        "body": "can these API steps also replace others in this feature file?"
      }
    ]
  },
  {
    "pr_number": 40213,
    "pr_title": "[DOM-55093] EDVs in APPs",
    "pr_author": "ddl-viniatska",
    "file_path": "e2e-tests/features/domino/external_volumes/dsp_view_and_mount_edv.feature",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-cedricyoung",
        "body": "I like that this is short... but is it enough of a description?"
      }
    ]
  },
  {
    "pr_number": 40215,
    "pr_title": "DOM-55126 \u2022 Retry Nexus calls",
    "pr_author": "adp312",
    "file_path": "domino-kubernetes/interface/src/main/scala/domino/dataplane/client/DataPlaneException.scala",
    "line": 30,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-ssenecal",
        "body": "does dead letter really mean that the message expired?  Seems like it could also mean something like it failed to deserialize the request and therefore sent it to the deadletter or something"
      },
      {
        "author": "adp312",
        "body": "Based on the code, EXPIRED_DEAD_LETTER apparently means that the messaging library reached a retry limit triggered by receiving a dead letter response. "
      },
      {
        "author": "adp312",
        "body": "In fact, we probably need to prevent retries on this EXPIRED_* conditions, because they're likely already retried in the domino-messaging."
      },
      {
        "author": "ddl-ssenecal",
        "body": "ya, if something was already retried at a lower layer, and still failed, then definitely we dont want to retry again"
      }
    ]
  },
  {
    "pr_number": 40215,
    "pr_title": "DOM-55126 \u2022 Retry Nexus calls",
    "pr_author": "adp312",
    "file_path": "domino-kubernetes/interface/src/main/scala/domino/dataplane/client/DataPlaneMessagingClient.scala",
    "line": 121,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-ssenecal",
        "body": "a lot of this block is repeated.. wonder if there is a way to reuse it as a function or something"
      },
      {
        "author": "adp312",
        "body": "Generic parameters do not quite fit well. I tried a few things, and the current version is the reasonable trade-off between readability and mild duplication (note a number of utility methods)."
      }
    ]
  },
  {
    "pr_number": 40215,
    "pr_title": "DOM-55126 \u2022 Retry Nexus calls",
    "pr_author": "adp312",
    "file_path": "server/app/domino/server/lib/config/Settings.scala",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-ssenecal",
        "body": "I don't know if this matters or not, but I think most places in nucleus use 5 retries"
      }
    ]
  },
  {
    "pr_number": 40215,
    "pr_title": "DOM-55126 \u2022 Retry Nexus calls",
    "pr_author": "adp312",
    "file_path": "server/app/domino/server/lib/config/Settings.scala",
    "line": 1614,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-ssenecal",
        "body": "is this too much?  What do other policies use?"
      },
      {
        "author": "adp312",
        "body": "The Kubernetes retry policy uses 5 retries with 1 sec initial delay. I was just thinking that 1 sec is low comparing with our 5 min timeout."
      },
      {
        "author": "ddl-ssenecal",
        "body": "Should we at least move to 5 retries to be consistent there?"
      },
      {
        "author": "adp312",
        "body": "Yes, let's do 5."
      }
    ]
  },
  {
    "pr_number": 40215,
    "pr_title": "DOM-55126 \u2022 Retry Nexus calls",
    "pr_author": "adp312",
    "file_path": "domino-kubernetes/interface/src/main/scala/domino/dataplane/client/DataPlaneMessagingRetryPolicy.scala",
    "line": 10,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-ssenecal",
        "body": "I dont see this being used anywhere yet.. we should at least start using it in `BaseDataPlaneResourceCache` refreshing the caches.  Right now they are using some other retry policy, but should be using this one"
      }
    ]
  },
  {
    "pr_number": 40215,
    "pr_title": "DOM-55126 \u2022 Retry Nexus calls",
    "pr_author": "adp312",
    "file_path": "domino-kubernetes/interface/src/main/scala/domino/dataplane/client/DataPlaneMessagingClient.scala",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "dmcwhorter-ddl",
        "body": "diferent / more descriptive names for the `createException` functions here?  e.g `createStatusMismatchException`"
      },
      {
        "author": "adp312",
        "body": "Yes"
      }
    ]
  },
  {
    "pr_number": 40216,
    "pr_title": "[DOM-55164] File view old commits fix",
    "pr_author": "ddl-g-chen",
    "file_path": "frontend/packages/ui/src/core/routes.ts",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-galias",
        "body": "not necessary to change it now. We should try to avoid this kind of complex string interpolation and use qs for building the search expressions."
      }
    ]
  },
  {
    "pr_number": 40231,
    "pr_title": "[DOM-55009] White Labeling Dataset Mount Path in Domino Projects BE",
    "pr_author": "ddl-eric-jin",
    "file_path": "admin/admin-interface/src/main/scala/domino/admin/interface/dtos.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-richard-tom",
        "body": "make it optional"
      },
      {
        "author": "ddl-eric-jin",
        "body": "Good point, thanks!"
      }
    ]
  },
  {
    "pr_number": 40239,
    "pr_title": "[DOM-55233] move ESS into nucleus-develop",
    "pr_author": "ddl-mhito",
    "file_path": "server/app/domino/server/search/infrastructure/ElasticSearchServiceInjectionModule.scala",
    "line": 64,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-grequeni",
        "body": "Should we also change line 131? (the one we reverted a few days ago https://github.com/cerebrotech/domino/pull/40211/files)"
      },
      {
        "author": "ddl-mhito",
        "body": "Great catch. Concerning that the cucu test succeeded without this."
      },
      {
        "author": "ddl-grequeni",
        "body": "that's concerning. One thing we can do to be 100% sure that these services run where they should is to log something when they are initialized (they are likely already doing that, but we can add it if not) and then create a FC instance with new relic enabled. Then we just look for the initialization logs in the cluster and we should only see it in the right pods."
      }
    ]
  },
  {
    "pr_number": 40240,
    "pr_title": "DOM-55178 updating compatibility matrix for new MLFlow version",
    "pr_author": "ddl-aj-rossman",
    "file_path": "aigateway/implementation/src/main/scala/domino/aigateway/EndpointConstants.scala",
    "line": 29,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-aj-rossman",
        "body": "Tldr for my OpenAI testing: [This doc](https://platform.openai.com/docs/models/model-endpoint-compatibility) describes correct compatibility. Completions and Chat will work with any of the endpoints described in the /v1/chat/completions row, endpoints work according to the /v1/embeddings row. Since the user can also use specific dated model releases (ex: gpt-3.5-turbo-1106 vs gpt-3.5-turbo), I've decided to leave it open ended with no validation on model. Open to discussion/thoughts though\r\n\r\n\r\n<br class=\"Apple-interchange-newline\">"
      },
      {
        "author": "ddl-avanitanna",
        "body": "I agree. In fact, I think we should consider doing that for all providers as this can keep changing rapidly - we'll have to keep updating whenever there are changes on the mlflow/provider end."
      }
    ]
  },
  {
    "pr_number": 40256,
    "pr_title": "[DOM-55226] - Do not grant NET_ADMIN capabilities for model pod containers by default",
    "pr_author": "ddl-tnguyen",
    "file_path": "server/src/test/domino/server/modelmanager/infrastructure/service/KubernetesModelApiDeployerSpec.scala",
    "line": 427,
    "is_resolved": true,
    "comments": [
      {
        "author": "dmcwhorter-ddl",
        "body": "good add"
      }
    ]
  },
  {
    "pr_number": 40264,
    "pr_title": "Merge back releases-5.10.0",
    "pr_author": "urianchang",
    "file_path": "projects/monolith-adapter/src/main/scala/domino/projects/monoadapter/ProjectServiceAdapter.scala",
    "line": 26,
    "is_resolved": true,
    "comments": [
      {
        "author": "urianchang",
        "body": "```suggestion\r\n```\r\n\r\nhttps://app.circleci.com/pipelines/github/cerebrotech/domino/172500/workflows/79fc6b15-546e-4382-bc63-c4b541a60f77/jobs/3402100 shows this is an unused import and errors out."
      },
      {
        "author": "urianchang",
        "body": "Huh, I guess that was not the fix https://app.circleci.com/pipelines/github/cerebrotech/domino/172502/workflows/9eef4433-4b99-4050-8841-f07ea887b705/jobs/3402122\r\n\r\n```\r\n# Execution platform: @local_config_platform//:host\r\nprojects/monolith-adapter/src/main/scala/domino/projects/monoadapter/ProjectServiceAdapter.scala:425: error: not enough arguments for constructor ProjectSummary: (id: domino.common.DominoId, name: String, description: String, visibility: String, ownerId: domino.common.DominoId, ownerUsername: String, mainRepository: Option[domino.projects.api.ProjectGitRepositoryTemp], importedGitRepositories: Seq[domino.projects.api.repositories.GitRepositoryDTO], templateDetails: Option[domino.projects.api.ProjectTemplateDetails], collaboratorIds: Set[domino.common.DominoId], collaborators: Seq[domino.projects.api.CollaboratorDTO], tags: Seq[domino.projects.api.ProjectTagDTO], stageId: domino.common.DominoId, status: domino.projects.api.ProjectStatus, internalTags: Option[Seq[String]], billingTag: Option[domino.projects.api.BillingTag]): domino.projects.api.ProjectSummary.\r\nUnspecified value parameter billingTag.\r\n        DominoId(projectId) -> new ProjectSummary(\r\n                               ^\r\n1 error\r\nBuild failed\r\njava.lang.RuntimeException: Build failed\r\n        at io.bazel.rulesscala.scalac.ScalacWorker.compileScalaSources(ScalacWorker.java:324)\r\n        at io.bazel.rulesscala.scalac.ScalacWorker.work(ScalacWorker.java:72)\r\n        at io.bazel.rulesscala.worker.Worker.persistentWorkerMain(Worker.java:86)\r\n        at io.bazel.rulesscala.worker.Worker.workerMain(Worker.java:39)\r\n        at io.bazel.rulesscala.scalac.ScalacWorker.main(ScalacWorker.java:36)\r\n```"
      }
    ]
  },
  {
    "pr_number": 40276,
    "pr_title": "[DOM-55268] fix injection in classic-workspaces",
    "pr_author": "ddl-mhito",
    "file_path": "workspace-classic/monolith-adapter/src/main/scala/domino/workspaces/monoadapter/LongLivedWorkspaceNotifyOrShutdownScheduleManagerAdapter.scala",
    "line": 21,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-grequeni",
        "body": "I see 3 places that bind this interface, the 3 of them bind different implementations. One of them is named with \"monoadapter\". Adding the \"named\" here means now this code gets a different implementation injected. Is that intentional? How are we testing that this change in implementation doesn't break the scheduled service? Shouldn't we fix the injection to inject the right instance instead (the same instance used before)?"
      },
      {
        "author": "ddl-mhito",
        "body": "This is intentional. This is how it was before, I forgot to add the \"named\" when I was making my changes.\r\n\r\nhttps://github.com/cerebrotech/domino/pull/39571/files#diff-51afbc13b6fe0660642235116d9b4f1717393f8e73d4a981d6566bf1f107ee48L17\r\n"
      }
    ]
  },
  {
    "pr_number": 40277,
    "pr_title": "DOM-54753 Dom 54753 UI edit endpoint",
    "pr_author": "DDL-Martin-Gazzara",
    "file_path": "frontend/packages/ui/src/ai-gateway/components/add-new-endpoint-modal/AddNewEndpointModal.tsx",
    "line": 48,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-galias",
        "body": "just for double check, sometimes if loading is not immediately turned on it can give you a blink with the error."
      },
      {
        "author": "DDL-Martin-Gazzara",
        "body": "There is no blink when the modal is opened in editing mode"
      }
    ]
  },
  {
    "pr_number": 40277,
    "pr_title": "DOM-54753 Dom 54753 UI edit endpoint",
    "pr_author": "DDL-Martin-Gazzara",
    "file_path": "frontend/packages/ui/src/ai-gateway/AIGatewayAdmin.tsx",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-galias",
        "body": "I don't think we should add the react query provider at this level of the app.  I like react-query, but we should discuss at a arch/team level, specifically in terms of using it, how we orchestrate the keys and where we should place the provider (also how it will coexist with the twirl templates)."
      },
      {
        "author": "DDL-Martin-Gazzara",
        "body": "Removed from ai gateway"
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