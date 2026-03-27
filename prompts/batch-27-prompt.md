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
    "pr_number": 47200,
    "pr_title": "[DOM-75072][DOM-74981] Refactor patch Extensions API for persister to handle patch logic",
    "pr_author": "ddl-eric-jin",
    "file_path": "extensions/implementation/src/main/scala/domino/extensions/implementation/DefaultExtensionService.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-ryan-connor",
        "body": "i dont think we need this check.\n\ncan you explain a bit about it's purpose?"
      },
      {
        "author": "ddl-eric-jin",
        "body": "This is to verify that resulting mount config from the patch does not include both allProjects=true and mount points. I add this to mainly to guard against client error as setting allProjects and having mount points is usually not intended. However, I can also see how it's convenient to just set allProjects to true without needing to turn off all the mount points. I can remove these checks for both create and patch."
      },
      {
        "author": "ddl-ryan-connor",
        "body": "ok yeah, i understand the concern but i think since it doesnt actually affect \"correctness\", best at this point to remove the code -- less to maintain, less complexity"
      }
    ]
  },
  {
    "pr_number": 47200,
    "pr_title": "[DOM-75072][DOM-74981] Refactor patch Extensions API for persister to handle patch logic",
    "pr_author": "ddl-eric-jin",
    "file_path": "extensions/implementation/src/main/scala/domino/extensions/implementation/DefaultExtensionService.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-ryan-connor",
        "body": "i dont think we actually need to explicitly prevent this\n\neverything still works if there are mount points and allProjects=true"
      }
    ]
  },
  {
    "pr_number": 47200,
    "pr_title": "[DOM-75072][DOM-74981] Refactor patch Extensions API for persister to handle patch logic",
    "pr_author": "ddl-eric-jin",
    "file_path": "nucleus/api/public-api.json",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-ryan-connor",
        "body": "can you take out \"by project id\"? its true the upsert key includes project id for the two types of mount points we have now, but may not be the case for all types soon"
      }
    ]
  },
  {
    "pr_number": 47200,
    "pr_title": "[DOM-75072][DOM-74981] Refactor patch Extensions API for persister to handle patch logic",
    "pr_author": "ddl-eric-jin",
    "file_path": "nucleus/api/public-api.json",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-ryan-connor",
        "body": "can you take out \"by project id\"? its true the upsert key includes project id for the two types of mount points we have now, but may not be the case for all types soon"
      },
      {
        "author": "ddl-eric-jin",
        "body": "Good point \ud83d\udc4d"
      },
      {
        "author": "ddl-ryan-connor",
        "body": "i checked the query, and it really is a true patch -- that's great\n\nso i think this is a little bit confusing. calling out \"If `uiMountPointTypeConfigs` is provided, top-level config fields are updated\" makes it seems different, but really it is the same -- if fields in there are provided, they are patched, but if None, then nothing happens.\n\nso how about this:\n\"Partially update an Extension. Absent fields are left unchanged. Any mount points within any `uiMountPointTypeConfig` are upserted.\"\n\nsame comment for the other description in these docs"
      },
      {
        "author": "ddl-eric-jin",
        "body": "Yes I agree, I think that's more clear!"
      }
    ]
  },
  {
    "pr_number": 47200,
    "pr_title": "[DOM-75072][DOM-74981] Refactor patch Extensions API for persister to handle patch logic",
    "pr_author": "ddl-eric-jin",
    "file_path": "extensions/interface/src/main/scala/domino/extensions/infrastructure/ExtensionPersister.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-ryan-connor",
        "body": "arg should start with lowercase"
      },
      {
        "author": "ddl-eric-jin",
        "body": "Good catch!"
      }
    ]
  },
  {
    "pr_number": 47200,
    "pr_title": "[DOM-75072][DOM-74981] Refactor patch Extensions API for persister to handle patch logic",
    "pr_author": "ddl-eric-jin",
    "file_path": "extensions/implementation/src/main/scala/domino/extensions/infrastructure/MongoExtensionPersister.scala",
    "line": 67,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-ryan-connor",
        "body": "query looks great!"
      }
    ]
  },
  {
    "pr_number": 47202,
    "pr_title": "DOM-74865 fetch projcollab with org and members",
    "pr_author": "ddl-skale",
    "file_path": "projects/monolith-adapter/src/main/scala/domino/projects/monoadapter/ProjectServiceAdapter.scala",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-amodi",
        "body": "The logic here and in toOrgRows can be done inline since its only used once. It would be a smaller change and cleaner imo to keep it in getProjectSettingsCollaborators."
      },
      {
        "author": "ddl-skale",
        "body": "I keep it outside to maintain the code flow since it is easier to distinguish between them org vs individual.\r\n"
      }
    ]
  },
  {
    "pr_number": 47202,
    "pr_title": "DOM-74865 fetch projcollab with org and members",
    "pr_author": "ddl-skale",
    "file_path": "projects/interface/src/main/scala/domino/projects/api/dtos.scala",
    "line": 515,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-amodi",
        "body": "Was this so you don't have to pass this to FE for the new endpoint? Lets just make sure this doesn't break anything on the FE as this changes an existing value. Lets run the project e2e tests."
      },
      {
        "author": "ddl-skale",
        "body": "yes i just made it optional, so if it was passed in before it still works and if it was skipped it is skipped now.\r\n\r\nmaking it optional is 100% backward compatible (earlier if was guaranteed to have value so this will not fail\r\nbased on the [comment here](https://github.com/cerebrotech/domino/pull/47202#issuecomment-4042772947) you see the original payload is not changed"
      }
    ]
  },
  {
    "pr_number": 47212,
    "pr_title": "DOM-75309 Add taxonomy tags to list apps public API",
    "pr_author": "ddl-aj-rossman",
    "file_path": "taxonomy/implementation/src/main/scala/domino/taxonomy/implementation/TaxonomyApiImpl.scala",
    "line": 28,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-bira-ignacio",
        "body": "question (non-blocking): I'm not super familiar with the actor system but I noticed in [some places](https://github.com/cerebrotech/domino/blob/b702b1e35ba57a0941c1a3525eefbaac3121a416/guardrails/implementation/src/main/scala/domino/guardrails/GuardrailsApiImpl.scala#L20) we do have a shutdown hook.\n\nFrom my understanding, it would be needed only to allow clean and graceful shutdowns though we don't use it normally.\nSo my guess is it wouldn't be an issue but I thought I should mention it.\n"
      },
      {
        "author": "ddl-aj-rossman",
        "body": "Will add!"
      }
    ]
  },
  {
    "pr_number": 47212,
    "pr_title": "DOM-75309 Add taxonomy tags to list apps public API",
    "pr_author": "ddl-aj-rossman",
    "file_path": "taxonomy/implementation/src/main/scala/domino/taxonomy/implementation/TaxonomyApiImpl.scala",
    "line": 34,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-bira-ignacio",
        "body": "thought: maybe `apiInvoker` and `apiInstance` should be private"
      }
    ]
  },
  {
    "pr_number": 47212,
    "pr_title": "DOM-75309 Add taxonomy tags to list apps public API",
    "pr_author": "ddl-aj-rossman",
    "file_path": "apps/web/src/main/scala/domino/apps/web/controllers/AppController.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-bira-ignacio",
        "body": "suggestion (non-blocking): The flag check runs even when there are zero apps. \nMaybe move both the flag check and the taxonomy call inside the non-empty branch to avoid the flag lookup"
      },
      {
        "author": "ddl-aj-rossman",
        "body": "good call \ud83d\udc4d "
      }
    ]
  },
  {
    "pr_number": 47212,
    "pr_title": "DOM-75309 Add taxonomy tags to list apps public API",
    "pr_author": "ddl-aj-rossman",
    "file_path": "apps/web/src/main/scala/domino/apps/web/transformers/AppTransformer.scala",
    "line": 123,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-bira-ignacio",
        "body": "question: The schema says id, label, and namespaceId as required, but here None gets mapped to \"\". Could this be confusing to API consumers that could be expecting values given those are required fields?\nI assume that's for backwards compatibility of some kind?"
      },
      {
        "author": "ddl-aj-rossman",
        "body": "Good catch: it's just defensive handling of the generated client model which types these as Option[String]. In practice, all of these fields should be present"
      }
    ]
  },
  {
    "pr_number": 47212,
    "pr_title": "DOM-75309 Add taxonomy tags to list apps public API",
    "pr_author": "ddl-aj-rossman",
    "file_path": "apps/web/src/test/scala/domino/apps/AppControllerSpec.scala",
    "line": 183,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-bira-ignacio",
        "body": "suggestion: Nice coverage!!\nOne case might be missing, if I read things right. \nIn `getTagsForEntities`, it can throw but we handle it as `NonFatal`. \nMaybe it would be good to verify the controller still returns apps with `taxonomyTags = None` in such cases."
      }
    ]
  },
  {
    "pr_number": 47216,
    "pr_title": "[DOM-75531] Support reproducibility of imported projects and repos for app versions",
    "pr_author": "adrianrsy",
    "file_path": "apps/interface/src/main/scala/domino/apps/services/AppVersionService.scala",
    "line": 72,
    "is_resolved": true,
    "comments": [
      {
        "author": "adrianrsy",
        "body": "Main relevant caller sets this value already."
      }
    ]
  },
  {
    "pr_number": 47216,
    "pr_title": "[DOM-75531] Support reproducibility of imported projects and repos for app versions",
    "pr_author": "adrianrsy",
    "file_path": "apps/interface/src/main/scala/domino/apps/services/CommitResolver.scala",
    "line": 55,
    "is_resolved": true,
    "comments": [
      {
        "author": "adrianrsy",
        "body": "Done"
      }
    ]
  },
  {
    "pr_number": 47216,
    "pr_title": "[DOM-75531] Support reproducibility of imported projects and repos for app versions",
    "pr_author": "adrianrsy",
    "file_path": "projects/monolith-adapter/src/main/scala/domino/projects/monoadapter/ProjectForkerAndCopier.scala",
    "line": 896,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-bira-ignacio",
        "body": "question: If I read this right, setting these to None means any new app version will immediately fail.\nDo we need to keep the distinction `None = legacy` X `Some(empty) = \"no repos\"` here?\nOr make these `Some(Seq.empty)`, to be safe, and let the copier resolve it later.\n\n"
      },
      {
        "author": "adrianrsy",
        "body": "This app version created by ProjectForkerAndCopier is already non-fuctional due to the main commit fields being set to None.\r\nConsidering the migration which should handle the majority of legacy cases, None represents \"we don't have reproducibility information so we won't allow this to be reproduced\". "
      }
    ]
  },
  {
    "pr_number": 47216,
    "pr_title": "[DOM-75531] Support reproducibility of imported projects and repos for app versions",
    "pr_author": "adrianrsy",
    "file_path": "apps/monolith-adapter/src/main/scala/domino/apps/services/DefaultCommitResolver.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-bira-ignacio",
        "body": "note: in a rare case where the branch/repo has no commits, this would return null. If easy, we should probably try to handle this, just in case this method gets used for other more general purpose"
      }
    ]
  },
  {
    "pr_number": 47216,
    "pr_title": "[DOM-75531] Support reproducibility of imported projects and repos for app versions",
    "pr_author": "adrianrsy",
    "file_path": "apps/monolith-adapter/src/main/scala/domino/apps/services/DefaultCommitResolver.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-bira-ignacio",
        "body": "suggestion: Maybe log a warning when the project is archived? \nIt's probably impossible to happen in the context of apps but then, all the more reason for some logging. Especially if we use this for other reasons"
      }
    ]
  },
  {
    "pr_number": 47216,
    "pr_title": "[DOM-75531] Support reproducibility of imported projects and repos for app versions",
    "pr_author": "adrianrsy",
    "file_path": "apps/interface/src/main/scala/domino/apps/model/AppVersion.scala",
    "line": 39,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-bira-ignacio",
        "body": "question: These methods also served as the fallback for `startVersion` on older persisted versions that only have `commitId` set. I assume we're relying on the migration to account for this case?"
      },
      {
        "author": "adrianrsy",
        "body": "Yes, the migration should set these fields for legacy apps."
      }
    ]
  },
  {
    "pr_number": 47216,
    "pr_title": "[DOM-75531] Support reproducibility of imported projects and repos for app versions",
    "pr_author": "adrianrsy",
    "file_path": "apps/interface/src/main/scala/domino/apps/services/CommitResolver.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-ryan-connor",
        "body": "a lot of this feels like the wrong place, talking about RunStarter and ProjectDependencyGetter in a docstring in the apps/interface directory"
      },
      {
        "author": "adrianrsy",
        "body": "Moving the edge case description to ImportedProjectSnapshot model instead and simplifying this scaladoc."
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