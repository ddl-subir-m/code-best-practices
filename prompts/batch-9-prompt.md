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
    "pr_number": 40124,
    "pr_title": "[DOM-55073] Flows: executor writes outputs success flag file instead of user code",
    "pr_author": "ddl-ryan-connor",
    "file_path": "server/app/domino/server/dispatcher/infrastructure/KubernetesConfigurationGenerator.scala",
    "line": 942,
    "is_resolved": false,
    "comments": [
      {
        "author": "noahjax",
        "body": "Lol congrats, you now own all of this code"
      },
      {
        "author": "ddl-ryan-connor",
        "body": "\ud83d\udc94 "
      }
    ]
  },
  {
    "pr_number": 40128,
    "pr_title": "DOM-52828 Make workflow job inputs explicit",
    "pr_author": "noahjax",
    "file_path": "server/app/domino/server/runs/ExecutionSpecificationBuilder.scala",
    "line": 366,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-rliu",
        "body": "This line had me think \u2013 would there be much benefit in defining a new `RunType.Workflow`? If so, can be in a separate PR, but perhaps not."
      },
      {
        "author": "noahjax",
        "body": "Yeah I might push this to another PR...I'm not yet sure we have enough of a reason to create a new type, and we'd have to update a bunch of logic now to treat workflow runs like jobs if we did create a new type."
      }
    ]
  },
  {
    "pr_number": 40128,
    "pr_title": "DOM-52828 Make workflow job inputs explicit",
    "pr_author": "noahjax",
    "file_path": "dataset-rw/dataset-rw-impl/src/main/scala/domino/datasetrw/impl/DatasetRwMountManager.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-rliu",
        "body": "```suggestion\r\n      val rwAllowed = includeRwMounts || !mount.snapshot.isReadWrite\r\n```\r\nnit: I think it reads slightly clearer to have the conditional this way"
      }
    ]
  },
  {
    "pr_number": 40128,
    "pr_title": "DOM-52828 Make workflow job inputs explicit",
    "pr_author": "noahjax",
    "file_path": "dataset-rw/dataset-rw-impl/src/main/scala/domino/datasetrw/impl/DatasetRwServiceImpl.scala",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-rliu",
        "body": "```suggestion\r\n      !filteredMounts.exists(mount => mount.dataset.id == snapshot.datasetId && mount.snapshot.version == snapshot.snapshotVersion)\r\n```\r\nMaybe worth adding a test for this function. Seems like `filteredMounts` is mounts that match the `snapshots` input, and `missingMounts` is `snapshots` that match `filteredMounts`? I'm wondering if there's a missing `not` here."
      },
      {
        "author": "noahjax",
        "body": "Good catch, I do need to add test cases here"
      }
    ]
  },
  {
    "pr_number": 40128,
    "pr_title": "DOM-52828 Make workflow job inputs explicit",
    "pr_author": "noahjax",
    "file_path": "jobs/jobs-monolith-adapter/src/main/scala/domino/jobs/monoadapter/JobLauncherAdapter.scala",
    "line": 185,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-rliu",
        "body": "In the Flows context, I assume that `restartJob` is basically never called, instead it looks like calling `launchJob` with the same inputs. So I guess this TODO item is more relevant to non-Flows cases."
      },
      {
        "author": "noahjax",
        "body": "Correct, for flows we wouldn't restart a job so much as create a new job using the original inputs."
      }
    ]
  },
  {
    "pr_number": 40128,
    "pr_title": "DOM-52828 Make workflow job inputs explicit",
    "pr_author": "noahjax",
    "file_path": "dataset-rw/dataset-rw-api/src/main/scala/domino/datasetrw/api/DatasetRwService.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-rliu",
        "body": "```suggestion\r\n   * Provisions the mounts to start an arbitrary run based on the principal's permissions, the project,\r\n   * and the dataset snapshots to include.\r\n```"
      }
    ]
  },
  {
    "pr_number": 40128,
    "pr_title": "DOM-52828 Make workflow job inputs explicit",
    "pr_author": "noahjax",
    "file_path": "dataset-rw/dataset-rw-api/src/main/scala/domino/datasetrw/api/dto.scala",
    "line": 445,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-ebrown",
        "body": "@noahjax to file a quick ticket about adding an endpoint that makes it easy for users to specify datasets they want to consume by name / id in the invocation of a `DominoJobTask`"
      },
      {
        "author": "noahjax",
        "body": "https://dominodatalab.atlassian.net/browse/DOM-55215"
      }
    ]
  },
  {
    "pr_number": 40130,
    "pr_title": "QE-15098 add before action screenshots",
    "pr_author": "ddl-cedricyoung",
    "file_path": ".pre-commit-config.yaml",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-michael-noonan",
        "body": "This needs to be 190 if we want the new screenshot behavior\r\nhttps://github.com/cerebrotech/cucu/pull/438/files#diff-50c86b7ed8ac2cf95bd48334961bf0530cdc77b5a56f852c5c61b89d735fd711R3\r\n```suggestion\r\n            \"git+ssh://git@github.com/cerebrotech/cucu@0.190.0#egg=cucu\",\r\n```"
      }
    ]
  },
  {
    "pr_number": 40130,
    "pr_title": "QE-15098 add before action screenshots",
    "pr_author": "ddl-cedricyoung",
    "file_path": "e2e-tests/requirements.txt",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-michael-noonan",
        "body": "This needs to be 190 if we want the new screenshot behavior\r\nhttps://github.com/cerebrotech/cucu/pull/438/files#diff-50c86b7ed8ac2cf95bd48334961bf0530cdc77b5a56f852c5c61b89d735fd711R3\r\n\r\n```suggestion\r\ngit+ssh://git@github.com/cerebrotech/cucu@0.190.0#egg=cucu\r\n```"
      }
    ]
  },
  {
    "pr_number": 40132,
    "pr_title": "datasource: removing unnecessary project calls",
    "pr_author": "ddl-giuliocapolino",
    "file_path": "datasource/datasource-adapter/src/main/scala/domino/datasource/adapter/DataSourceProjectManagerAdapter.scala",
    "line": 22,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-eric-jin",
        "body": "If `fullInfo` is always set to false for `getProjectSummariesInternal` should we remove `fullInfo` from the `getProjectSummaries` parameters?"
      },
      {
        "author": "ddl-eric-jin",
        "body": "Additionally, just wondering is there a case where all summary info is required?"
      },
      {
        "author": "ddl-giuliocapolino",
        "body": "yes actually! good point. \r\n\r\nand to the additional question, maybe? we will revisit this once we have more time - gut feeling is not, but since that code is used also in datasets and featurestore and this is just a patch, I won\u2019t add it here"
      }
    ]
  },
  {
    "pr_number": 40132,
    "pr_title": "datasource: removing unnecessary project calls",
    "pr_author": "ddl-giuliocapolino",
    "file_path": "datasource/datasource-impl/src/main/scala/domino/datasource/impl/DataSourceServiceImpl.scala",
    "line": 398,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-eric-jin",
        "body": "Nice!"
      }
    ]
  },
  {
    "pr_number": 40134,
    "pr_title": "[DOM-55010] Load favicon after whitelabel settings fetch",
    "pr_author": "gandavarapurajasekhar",
    "file_path": "frontend/apps/web/src/components/App.tsx",
    "line": 48,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-galias",
        "body": "Just a heads up.\r\n\r\nThe changes are ok but I think this won't resolve the original issue. Even if we await for the white label settings to load, then the whitelabel settings will bring this for domino:\r\n![image](https://github.com/cerebrotech/domino/assets/142441807/751eede0-d2a6-47cb-8a0a-309dc677bf8c)\r\nI would give a try to this solution and in addition either keeping the nucleus favicon or modifying the path that is returned by `/v4/admin/whitelabel/configurations`\r\n\r\ncc @jenniferjfu2 \r\n\r\n"
      },
      {
        "author": "jenniferjfu2",
        "body": "I am going to build a deployment"
      }
    ]
  },
  {
    "pr_number": 40140,
    "pr_title": "DOM-54734 Fix broken projectId based authz for jobs",
    "pr_author": "noahjax",
    "file_path": "projects/monolith-adapter/src/main/scala/domino/projects/monoadapter/ProjectLaunchersManagerAdapter.scala",
    "line": 31,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-rliu",
        "body": "I'm not familiar with what `servicePrincipalMaker.makeServicePrincipal` does, I'm assuming some users will be able to make a service principal that has permissions to get jobs here, while other users will fail."
      },
      {
        "author": "noahjax",
        "body": "ServicePrincipal is a Principal with elevated permissions that basically allow it to bypass authz...it is used for calls from one service to another where authz checks have already taken place in the first service. In this case it `InProcessAssetPortfolioService` has already done authz by explicitly looking up only project ids that the principal has access to, so we don't need to do another round of authz checks here.\r\n\r\nThe nice thing about using a ServicePrincipal is it allowed me to update the jobs code to only allow access to service principals, which guards against someone accidentally exposing this endpoint directly to users later."
      }
    ]
  },
  {
    "pr_number": 40141,
    "pr_title": "[QE-15113] Added step to slow down the click and also to make sure the correct pvc is selected ",
    "pr_author": "ddl-viniatska",
    "file_path": "e2e-tests/features/domino/external_volumes/admin_register_edv.feature",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-xin",
        "body": "```suggestion\r\n      And I should see the radio button \"{PVC_NAME}\" is selected\r\n```\r\nLet's hope when it fails we can get an mht file"
      }
    ]
  },
  {
    "pr_number": 40144,
    "pr_title": "DOM-55099 - domino-cost cannot tolerate malformed organization records",
    "pr_author": "ddl-juan-cistaro",
    "file_path": "server/src/test/domino/server/admin/implementation/DominoAdminServiceSpec.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-olsonJD",
        "body": "let's create a variable for these IDs and reuse them instead."
      }
    ]
  },
  {
    "pr_number": 40145,
    "pr_title": "[DOM-55121] Remove wrongly injected padding to the icon only button t\u2026",
    "pr_author": "ddl-galias",
    "file_path": "frontend/packages/ui/src/project-settings-goal-stages/styles.ts",
    "line": 15,
    "is_resolved": false,
    "comments": [
      {
        "author": "jenniferjfu2",
        "body": "The change is okay here.\r\n\r\n@sreeram-s-zessta, can we check all buttons and make changes at Button.tsx if needed?"
      }
    ]
  },
  {
    "pr_number": 40156,
    "pr_title": "[DOM-55105] Project code pages can be detected by cucu",
    "pr_author": "ddl-g-chen",
    "file_path": "frontend/apps/web/src/modules/code/CodeBrowse.tsx",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-galias",
        "body": "Is this being applied at the DOM? If the component is not forwarding it to a real html element it should no be appearing.\r\n\r\nAlso suggest not using \"test\" at the aria-label attribute unless it points to something that is really related to a test action or similar in the UI. This is mainly because they have accessibility concerns and they are meant to give a name the element to which they are applied to. "
      }
    ]
  },
  {
    "pr_number": 40156,
    "pr_title": "[DOM-55105] Project code pages can be detected by cucu",
    "pr_author": "ddl-g-chen",
    "file_path": "frontend/apps/web/src/modules/code/CreateOrEditCode.tsx",
    "line": 138,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-galias",
        "body": "same comment about the aria label (both test and check if it is being applied)"
      }
    ]
  },
  {
    "pr_number": 40156,
    "pr_title": "[DOM-55105] Project code pages can be detected by cucu",
    "pr_author": "ddl-g-chen",
    "file_path": "frontend/apps/web/src/modules/code/GBPCodeBrowse.tsx",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-galias",
        "body": "isn't the previous data test being used by the tests?"
      }
    ]
  },
  {
    "pr_number": 40156,
    "pr_title": "[DOM-55105] Project code pages can be detected by cucu",
    "pr_author": "ddl-g-chen",
    "file_path": "frontend/apps/web/src/modules/code/SharedView.tsx",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-galias",
        "body": "same here"
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