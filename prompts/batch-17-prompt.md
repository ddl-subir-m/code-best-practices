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
    "pr_number": 40429,
    "pr_title": "QE-15076 Qe 15076 tag tests with teams",
    "pr_author": "ddl-bcolby",
    "file_path": "e2e-tests/features/domino/jobs/run_jobs_gbp.feature",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-cedricyoung",
        "body": "\n```suggestion\n  @jobs @gitlab\n```"
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
        "body": "\n```suggestion\n  @jobs\n```"
      }
    ]
  },
  {
    "pr_number": 40429,
    "pr_title": "QE-15076 Qe 15076 tag tests with teams",
    "pr_author": "ddl-bcolby",
    "file_path": "e2e-tests/features/domino/git_backed_projects_with_codesync/gbp_collaborator_creds.feature",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-cedricyoung",
        "body": "what is this?"
      },
      {
        "author": "ddl-bcolby",
        "body": "The comment? I have no idea, but it does look entirely redundant. We can go ahead and delete it while we are here."
      },
      {
        "author": "ddl-bcolby",
        "body": "```suggestion\r\n```"
      }
    ]
  },
  {
    "pr_number": 40433,
    "pr_title": "[DOM-55288] FileView render call moved",
    "pr_author": "ddl-g-chen",
    "file_path": "frontend/packages/ui/src/filebrowser/FileView.tsx",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-galias",
        "body": "This is a component on its own, we should move it to a separated file"
      }
    ]
  },
  {
    "pr_number": 40433,
    "pr_title": "[DOM-55288] FileView render call moved",
    "pr_author": "ddl-g-chen",
    "file_path": "frontend/packages/ui/src/filebrowser/FileView.tsx",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-galias",
        "body": "As `whiteLabelSettings` is an object that is not controlled by this component, it is likely to mutate and force an unwanted request. I suggest assigning the error message to a variable outside the use effect and use that variable both as dependency and and for calling `setRawContent` when the error happens.\r\n "
      }
    ]
  },
  {
    "pr_number": 40433,
    "pr_title": "[DOM-55288] FileView render call moved",
    "pr_author": "ddl-g-chen",
    "file_path": "frontend/packages/ui/src/filebrowser/FileView.tsx",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-galias",
        "body": "do you need the string template here, it looks like it is not interpolating text but only calling the function."
      },
      {
        "author": "ddl-g-chen",
        "body": "i ended up removing the error message since the component will default to the iframe if the raw content API call fails"
      }
    ]
  },
  {
    "pr_number": 40434,
    "pr_title": "[DOM-55342] Cucu test for EDV error feedback in workspace startup UI",
    "pr_author": "ddl-ryan-connor",
    "file_path": "e2e-tests/features/domino/workspaces/startup_ui.feature",
    "line": 174,
    "is_resolved": false,
    "comments": [
      {
        "author": "SeanW-DDL",
        "body": "These tests might need to be separated into multiple files: the waits and the time taken by the env builds and workspace starts add up quickly and if a test spec takes longer than (I think) 30 minutes to execute, it may break CI allotted time and not get reported to testrail."
      }
    ]
  },
  {
    "pr_number": 40434,
    "pr_title": "[DOM-55342] Cucu test for EDV error feedback in workspace startup UI",
    "pr_author": "ddl-ryan-connor",
    "file_path": "e2e-tests/features/domino/workspaces/startup_ui.feature",
    "line": 101,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-grequeni",
        "body": "What is an EDV?"
      },
      {
        "author": "ddl-ryan-connor",
        "body": "external data volume https://docs.dominodatalab.com/en/5.10/admin_guide/053e1f/external-data-volumes/"
      }
    ]
  },
  {
    "pr_number": 40436,
    "pr_title": "DOM-54210 bitbucket PAT sslVerify",
    "pr_author": "ddl-roshikiri",
    "file_path": "repoman/repoman-service/src/main/scala/domino/repoman/service/utils/RepomanGitUtil.scala",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "niole",
        "body": "could just return `List.empty` or `Nil`"
      }
    ]
  },
  {
    "pr_number": 40436,
    "pr_title": "DOM-54210 bitbucket PAT sslVerify",
    "pr_author": "ddl-roshikiri",
    "file_path": "server/app/domino/server/repositories/RepositoryService.scala",
    "line": 27,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-roshikiri",
        "body": "removing this check because the credential isn't applied to the URI for bitbucket data center but we add the credential to check later in this flow"
      }
    ]
  },
  {
    "pr_number": 40438,
    "pr_title": "DOM-54506: Model Deployment CRUD",
    "pr_author": "ddl-yaniv-amar",
    "file_path": "model-serving/domain/src/main/scala/domino/modelserving/entities/modeldeployment/ModelDeploymentOperatorStatus.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "adrianrsy",
        "body": "Should the operation value be an enum?\r\nFrom the example, I'm guessing this is the CREATE, UPDATE, etc. one"
      },
      {
        "author": "ddl-yaniv-amar",
        "body": "Yeah I think I am going to change it to an enum in the spec too. FYI @dmcwhorter-ddl "
      }
    ]
  },
  {
    "pr_number": 40438,
    "pr_title": "DOM-54506: Model Deployment CRUD",
    "pr_author": "ddl-yaniv-amar",
    "file_path": "model-serving/infrastructure/src/it/scala/domino/modelserving/persistence/MongoModelDeploymentPersisterSpec.scala",
    "line": 48,
    "is_resolved": true,
    "comments": [
      {
        "author": "adrianrsy",
        "body": "What's the expected behavior for `getModelDeploymentById` if there are multiple versions?"
      },
      {
        "author": "ddl-yaniv-amar",
        "body": "Just created another story for it to address it properly. We will have to record multiple versions so that we can recall them properly. I recorded this in https://dominodatalab.atlassian.net/browse/DOM-55483"
      }
    ]
  },
  {
    "pr_number": 40438,
    "pr_title": "DOM-54506: Model Deployment CRUD",
    "pr_author": "ddl-yaniv-amar",
    "file_path": "model-serving/infrastructure/src/main/scala/domino/modelserving/persistence/MongoModelDeploymentPersister.scala",
    "line": 47,
    "is_resolved": true,
    "comments": [
      {
        "author": "adrianrsy",
        "body": "Should this exclude archived deployments? Iirc you can use `dao.findById` or something like that if you don't need to fetch the archived ones. Maybe also make it clear in the method name if you intend to include archived deployments."
      }
    ]
  },
  {
    "pr_number": 40438,
    "pr_title": "DOM-54506: Model Deployment CRUD",
    "pr_author": "ddl-yaniv-amar",
    "file_path": "model-serving/infrastructure/src/main/scala/domino/modelserving/persistence/MongoModelDeploymentPersister.scala",
    "line": 66,
    "is_resolved": true,
    "comments": [
      {
        "author": "adrianrsy",
        "body": "Does this delete the old version?"
      },
      {
        "author": "ddl-yaniv-amar",
        "body": "No. We don't want to delete old versions for now. "
      }
    ]
  },
  {
    "pr_number": 40438,
    "pr_title": "DOM-54506: Model Deployment CRUD",
    "pr_author": "ddl-yaniv-amar",
    "file_path": "model-serving/infrastructure/src/main/scala/domino/modelserving/persistence/MongoModelDeploymentPersister.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "adrianrsy",
        "body": "You can probably do something like below to avoid duplication:\r\n\r\n```\r\nval query = BsonDocument(\"isArchived\" -> false)\r\nSeq(nameQuery, registeredModelsQuery).flatten.foreach(criteria => $and(criteria :+ query))\r\n```"
      }
    ]
  },
  {
    "pr_number": 40438,
    "pr_title": "DOM-54506: Model Deployment CRUD",
    "pr_author": "ddl-yaniv-amar",
    "file_path": "model-serving/infrastructure/src/main/scala/domino/modelserving/persistence/MongoModelDeploymentPersister.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "adrianrsy",
        "body": "Sortby should be used here"
      },
      {
        "author": "ddl-yaniv-amar",
        "body": "good catch! thanks."
      }
    ]
  },
  {
    "pr_number": 40438,
    "pr_title": "DOM-54506: Model Deployment CRUD",
    "pr_author": "ddl-yaniv-amar",
    "file_path": "model-serving/infrastructure/src/main/scala/domino/modelserving/persistence/MongoModelDeploymentPersister.scala",
    "line": 49,
    "is_resolved": true,
    "comments": [
      {
        "author": "adrianrsy",
        "body": "I'm not sure if we differentiate between archived vs non-existent in other parts of the code. Not a big deal either way."
      },
      {
        "author": "ddl-yaniv-amar",
        "body": "I actually pulled this from the way we do models, specifically the modelapirepository - unsafeRetrieve method. I think for now this should be ok because we are still figuring out how we want model deployments to behave. I may remove this in the next sprint \ud83d\udc4d "
      }
    ]
  },
  {
    "pr_number": 40440,
    "pr_title": "[QE-15219] [Datasets in Executions] Convert RFQA Tests to E2E Tests",
    "pr_author": "ddl-viniatska",
    "file_path": "e2e-tests/features/domino/datasets/datasets_in_executions.feature",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-cfuerst",
        "body": "Might be best to have this be a `wait to click` step, as the previous step changes what's seen on the page by clicking the Domino Datasets a tab"
      }
    ]
  },
  {
    "pr_number": 40440,
    "pr_title": "[QE-15219] [Datasets in Executions] Convert RFQA Tests to E2E Tests",
    "pr_author": "ddl-viniatska",
    "file_path": "e2e-tests/features/domino/datasets/datasets_in_executions.feature",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-cfuerst",
        "body": "Should probably be a `wait to click` step"
      },
      {
        "author": "ddl-viniatska",
        "body": "thank you, that makes sense."
      }
    ]
  },
  {
    "pr_number": 40440,
    "pr_title": "[QE-15219] [Datasets in Executions] Convert RFQA Tests to E2E Tests",
    "pr_author": "ddl-viniatska",
    "file_path": "e2e-tests/features/domino/datasets/datasets_in_executions.feature",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-cfuerst",
        "body": "Change to a `navigate to the url` step"
      },
      {
        "author": "ddl-viniatska",
        "body": "fixed"
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