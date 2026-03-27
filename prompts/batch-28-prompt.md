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
    "pr_number": 47216,
    "pr_title": "[DOM-75531] Support reproducibility of imported projects and repos for app versions",
    "pr_author": "adrianrsy",
    "file_path": "apps/monolith-adapter/src/main/scala/domino/apps/services/DefaultCommitResolver.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-ryan-connor",
        "body": "does this break the spirit of this feature? should we fail if an imported project is archived? or is this OK?"
      },
      {
        "author": "adrianrsy",
        "body": "Should be an impossible case, but will switch to throwing instead of skipping silently."
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
        "author": "ddl-ryan-connor",
        "body": "nit, hard to read -- else would typically be on the previous line"
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
        "author": "ddl-ryan-connor",
        "body": "what is a `release`? is this better/more correct than just do the `filesService.getHeadCommitIdForProject()` below? this feels weird that we're getting the resolved commit from a `run`"
      },
      {
        "author": "adrianrsy",
        "body": "Similar to a tag in git if I'm not mistaken but explicitly tied to a run. This should be the correct way to get the commit if the imported project settings specify a release rather than head or a commit."
      },
      {
        "author": "ddl-ryan-connor",
        "body": "still feels weird -- why is a \"run\" the source of truth for a release?\r\n\r\nbut i'll trust that this is the right way"
      }
    ]
  },
  {
    "pr_number": 47216,
    "pr_title": "[DOM-75531] Support reproducibility of imported projects and repos for app versions",
    "pr_author": "adrianrsy",
    "file_path": "apps/monolith-adapter/src/main/scala/domino/apps/services/ModelProductManager.scala",
    "line": 343,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-bira-ignacio",
        "body": "question: I assume we'll rely on migration to always have `resolvedCommitId` for existing apps?"
      },
      {
        "author": "adrianrsy",
        "body": "Yes."
      }
    ]
  },
  {
    "pr_number": 47216,
    "pr_title": "[DOM-75531] Support reproducibility of imported projects and repos for app versions",
    "pr_author": "adrianrsy",
    "file_path": "apps/interface/src/main/scala/domino/apps/model/AppVersion.scala",
    "line": 24,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-bira-ignacio",
        "body": "nice documentation!"
      }
    ]
  },
  {
    "pr_number": 47216,
    "pr_title": "[DOM-75531] Support reproducibility of imported projects and repos for app versions",
    "pr_author": "adrianrsy",
    "file_path": "apps/interface/src/main/scala/domino/apps/model/AppVersion.scala",
    "line": 24,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-ryan-connor",
        "body": "my other comment about the docs was more high level. in general i feel like docstrings on classes or methods in a `/PROJECT/INTERFACE` kind of directory -- like `/apps/interface` -- should not talk about low level implementation that depends on _other_ projects. `/apps/interface` technically has _no idea_ about runs etc. It's only the monolith-adapter that knows about things like `ExecutionSpecificationBuilder` etc.\n\nso im not convinced this is the best place for these docs, but im fine with it if you can't think of a better place that is closer to the point in the code where all this stuff comes together."
      },
      {
        "author": "ddl-ryan-connor",
        "body": "and i really do mean im fine with it! i just wanted to make the more general point clearer"
      },
      {
        "author": "adrianrsy",
        "body": "Closer to the execution layer of things would be nice, but the edge cases are only relevant to apps for now and I'm not sure we have a good enough reproducibility story for dependencies across all execution types to make any comments generic to all of them.\r\n\r\nI think I'll leave it in here for now.\r\n"
      }
    ]
  },
  {
    "pr_number": 47224,
    "pr_title": "DOM-75386 Preserve route and query params in extended identity propagation consent callback",
    "pr_author": "ddl-ryan-connor",
    "file_path": "server/src/test/domino/server/dispatcher/service/ExecutionResourceParamsMakerSpec.scala",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-eric-jin",
        "body": "I think we should also check that the query parameters are added as expected."
      },
      {
        "author": "ddl-ryan-connor",
        "body": "that's not possible here. this is a unit test spec for the execution resource params maker. the query params and route come from an actual app request via `your browser => ... some hops ... => app nginx lua code`\r\n\r\ni already linked it to the e2e test ticket and the AC there, it's something we can and should test there. https://dominodatalab.atlassian.net/browse/DOM-75049"
      },
      {
        "author": "ddl-ryan-connor",
        "body": "oh, and if we had \"integration\" tests for apps, we could test it there -- so best we can do is an e2e test"
      }
    ]
  },
  {
    "pr_number": 47229,
    "pr_title": "[DOM-75403] Cleanup n+1 queries in Apps",
    "pr_author": "adrianrsy",
    "file_path": "apps/implementation/src/main/scala/domino/apps/implementation/DefaultAppUsageService.scala",
    "line": 50,
    "is_resolved": true,
    "comments": [
      {
        "author": "adrianrsy",
        "body": "Does not need a fix. The canReadUsageStatistics gate only exists on the dedicated single-app usage statistics endpoint (getTotalViews), not on the summary view counts shown in the listing page. Our batch refactoring preserved this existing behavior exactly."
      }
    ]
  },
  {
    "pr_number": 47233,
    "pr_title": "DOM-75428 Add tag ID filtering to listApps API",
    "pr_author": "ddl-aj-rossman",
    "file_path": "apps/web/src/main/scala/domino/apps/web/controllers/AppController.scala",
    "line": 160,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-bira-ignacio",
        "body": "question: is it ok to just return empty here if none of the tags match? \nIt seems, functionally, correct to me, it's just that the warning log message suggests that might not be always expected."
      },
      {
        "author": "ddl-aj-rossman",
        "body": "IMO I think we should keep this log since this case happens when there is a taxonomy service failure, not if none of the tags match. If the call succeeds but returns an empty list of entityIds, then this error won't be logged"
      }
    ]
  },
  {
    "pr_number": 47233,
    "pr_title": "DOM-75428 Add tag ID filtering to listApps API",
    "pr_author": "ddl-aj-rossman",
    "file_path": "apps/implementation/src/main/scala/domino/apps/implementation/DefaultAppService.scala",
    "line": 156,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-bira-ignacio",
        "body": "question: any concerns with this being a large list of `allowedAppIds` that could make this problematic Unlike the other things in this filter, I assume a search coming from tags could return a number of ids.\n\nHonestly I wouldn't be too worried if this is in the dozens but I also don't know how large a list of params we can pass to mongo (I'm assuming that's what this does).\n\nCC: @ddl-ryan-connor "
      },
      {
        "author": "ddl-aj-rossman",
        "body": "Good question- a few points:\r\n- generally, Mongo's `$in` can handle large lists. There is a 16 MiB limit for the size of the query document, but even with thousands of AppIDs, we won't approach it\r\n- Performance wise, we should be ok since we're querying on the app's ID, which is indexed."
      }
    ]
  },
  {
    "pr_number": 47240,
    "pr_title": "DOM-74899 Populate taxonomy tag labels and descriptions in App search index",
    "pr_author": "ddl-aj-rossman",
    "file_path": "server/app/domino/server/search/types/app/AppIndexer.scala",
    "line": 161,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-ryan-connor",
        "body": "how are tags added to apps?"
      },
      {
        "author": "ddl-ryan-connor",
        "body": "a little more color: i think maybe \"tagging apps\" used to be a sort of broken functionality before the apps refresh for domino 6.1.0, and during that i believe we did not refactor/modernize the app tagging functionality, so im not aware of a way to tag apps in the UI today"
      },
      {
        "author": "ddl-aj-rossman",
        "body": "Ah, sorry, should have given more context. For the new tagging microservice we've created, users can add tags to apps. This will call our microservice to fetch the tags for given apps"
      }
    ]
  },
  {
    "pr_number": 47250,
    "pr_title": "[DOM-75231|DOM-75232] Filters, sorting and pagination info for PAT's GET endpoints",
    "pr_author": "ddl-juan-cistaro",
    "file_path": "personalaccesstoken/repositories/src/scala/domino/personalaccesstoken/repositories/PersonalAccessTokenMetadataPersisterImpl.scala",
    "line": 50,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-martin-currao",
        "body": "By default it will sort by Mongo ID, which is equivalent to creation date, right? "
      },
      {
        "author": "ddl-juan-cistaro",
        "body": "Yes, that's right"
      }
    ]
  },
  {
    "pr_number": 47250,
    "pr_title": "[DOM-75231|DOM-75232] Filters, sorting and pagination info for PAT's GET endpoints",
    "pr_author": "ddl-juan-cistaro",
    "file_path": "personalaccesstoken/public/public-api.yaml",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-martin-currao",
        "body": "Personally I like more the `sortBy` naming than the `sortField`, but that is as opinionated as it comes."
      }
    ]
  },
  {
    "pr_number": 47250,
    "pr_title": "[DOM-75231|DOM-75232] Filters, sorting and pagination info for PAT's GET endpoints",
    "pr_author": "ddl-juan-cistaro",
    "file_path": "personalaccesstoken/domain/src/scala/domino/personalaccesstoken/domain/services/PatStatus.scala",
    "line": 6,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-martin-currao",
        "body": "To be honest, I'm completely against handling expiringSoon as a status. \r\n\r\nI expect the API to return `active` if the token is active, and when I filter tokens (once we have filters) I expect `?status=active` to include those expiring soon. Considering that \"soon\" is a criteria defined by my  administrator, so it may be a month, I want to still be able to interact with that token as if it is functional. \r\n\r\nInstead, I would add another field on the response, so that it is:\r\n\r\n```json\r\n{\r\n  \"name\": \"my-token\",\r\n  // ...\r\n  \"status\": \"active\",\r\n  \"expiringSoon\": true\r\n} \r\n```\r\n\r\n----\r\n\r\nComment update: Realized my comment does not apply, as we are not even including it in the response.\r\n\r\nThe status enum apparently only applies to the filter, which ends up relating to this:\r\n\r\n```\r\n      case PatStatus.Active => BsonDocument(\"isValid\" -> true)\r\n      case PatStatus.ExpiringSoon => BsonDocument(\"isValid\" -> true, \"expiresAt\" -> BsonDocument(\"$gt\" -> nowBson, \"$lte\" -> expiringSoonLimit))\r\n```\r\n\r\nMy bad. I see now that you mapped `active` to `isValid` and `expiringSoon` also to valid. \r\nWe definitively will need to document it, but as the actual field in the response is called `isActive` and not status, it is not _that_ conflicting. "
      },
      {
        "author": "ddl-juan-cistaro",
        "body": "Yes, I know this is kinda confusing, but this Statuses are the combination of both fields that are required by the UI. This will be part of the docs that we are going to create for PATs, but I haven't added this as a comment because I thought that the conditions were self-explained and if I added this as a comment in a different part of the code where the enum is define and then the conditions are changed because a future requirement the one doing that was never going to remember to change the comment in the other place and that's where everything starts falling down haha. But as for now the status align with these conditions:\r\n  `active` - Valid token to be used.\r\n  `expiringSoon` - Valid token to be used but its expiration time is in less than 7 days.\r\n  `expired` - Already expired token.\r\n  `revoked` - Token that has been revoked and is no longer valid, despite its expiration time."
      }
    ]
  },
  {
    "pr_number": 47250,
    "pr_title": "[DOM-75231|DOM-75232] Filters, sorting and pagination info for PAT's GET endpoints",
    "pr_author": "ddl-juan-cistaro",
    "file_path": "model-serving/web/main/domino/modelserving/web/loading/NoOpPersonalAccessTokenService.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-martin-currao",
        "body": "I think these two may be leftover from the old name. \n"
      },
      {
        "author": "ddl-martin-currao",
        "body": "ModelServing strikes again. \ud83d\ude05 "
      },
      {
        "author": "ddl-juan-cistaro",
        "body": "I love ModelServing <3\r\n"
      }
    ]
  },
  {
    "pr_number": 47250,
    "pr_title": "[DOM-75231|DOM-75232] Filters, sorting and pagination info for PAT's GET endpoints",
    "pr_author": "ddl-juan-cistaro",
    "file_path": "personalaccesstoken/repositories/src/scala/domino/personalaccesstoken/repositories/PersonalAccessTokenMetadataPersisterImpl.scala",
    "line": 101,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-juan-cistaro",
        "body": "This is expected due to how the \"status\" works in the UI and has been discussed."
      }
    ]
  },
  {
    "pr_number": 47255,
    "pr_title": "[DOM-74661] Add create, patch, and delete Extension audit events ",
    "pr_author": "ddl-eric-jin",
    "file_path": "dependencies.yaml",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-eric-jin",
        "body": "Will update before merging this PR once https://github.com/cerebrotech/idsm-audit-trail-openapi-library/pull/119 is merged."
      },
      {
        "author": "ddl-eric-jin",
        "body": "Updated!"
      }
    ]
  },
  {
    "pr_number": 47255,
    "pr_title": "[DOM-74661] Add create, patch, and delete Extension audit events ",
    "pr_author": "ddl-eric-jin",
    "file_path": "extensions/implementation/src/main/scala/domino/extensions/implementation/ExtensionEventTracker.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-awroblicky",
        "body": "any concerns with including `appName` like in other places\n\nhttps://github.com/cerebrotech/domino/blob/827ab1408055847e96c312f0cc62af599adf4888/server/app/domino/server/user/domain/UserConsentEventFactory.scala#L32"
      },
      {
        "author": "ddl-eric-jin",
        "body": "My main concern with including it would be the additional performance overhead of an additional DB query to retrieve `appName` so I decided to only include the ID. But if it is important for auditing, I can make the changes."
      },
      {
        "author": "ddl-awroblicky",
        "body": "yeah that's a reasonable concern but unfortunately the guidance from Matt was that we should always include a name for readability"
      },
      {
        "author": "ddl-eric-jin",
        "body": "I see, that makes sense. I'll make the changes, thanks!"
      },
      {
        "author": "ddl-eric-jin",
        "body": "Now updated to include app name."
      }
    ]
  },
  {
    "pr_number": 47258,
    "pr_title": "DOM-75511 Add appInfo to app search results",
    "pr_author": "ddl-aj-rossman",
    "file_path": "server/app/domino/server/search/Results.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-aj-rossman",
        "body": "Fixed \ud83d\udc4d "
      }
    ]
  },
  {
    "pr_number": 47260,
    "pr_title": "DOM-75558 fix: fix error when deleting project tags [DOM-75558]",
    "pr_author": "ddl-bira-ignacio",
    "file_path": "server/app/domino/server/projecttags/ProjectTagController.scala",
    "line": 100,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-bira-ignacio",
        "body": "Not necessary to change the error handling method for now"
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