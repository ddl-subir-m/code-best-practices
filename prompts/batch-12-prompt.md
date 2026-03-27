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
    "pr_number": 40277,
    "pr_title": "DOM-54753 Dom 54753 UI edit endpoint",
    "pr_author": "DDL-Martin-Gazzara",
    "file_path": "frontend/packages/ui/src/ai-gateway/components/add-new-endpoint-modal/gateway-endpoint-form/GatewayEndpointForm.tsx",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-galias",
        "body": "can't you resolve this with useWatch? setting a dynamic form item at this level might leave to a large amount of unnecessary re renders."
      },
      {
        "author": "DDL-Martin-Gazzara",
        "body": "I moved the stepper into a child component. Then inside this one I used useWatch and useFormInstance properly"
      }
    ]
  },
  {
    "pr_number": 40277,
    "pr_title": "DOM-54753 Dom 54753 UI edit endpoint",
    "pr_author": "DDL-Martin-Gazzara",
    "file_path": "frontend/packages/test-utils/src/components/QueryClientProvider.tsx",
    "line": 1,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-galias",
        "body": "Do you still need this component?"
      },
      {
        "author": "DDL-Martin-Gazzara",
        "body": "Actually, I don't. But I deleted it in [this PR](https://github.com/cerebrotech/domino/pull/40369)"
      }
    ]
  },
  {
    "pr_number": 40279,
    "pr_title": "[DOM-54985] Capitalize Data Source Name for Error Toast",
    "pr_author": "ddl-eric-jin",
    "file_path": "datasource/datasource-layout/src/main/scala/domino/datasource/layout/DataSourceRuleService.scala",
    "line": 82,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-eric-jin",
        "body": "\"Data Source\" aligns with other UI messages to the user and public docs."
      }
    ]
  },
  {
    "pr_number": 40282,
    "pr_title": "DOM-55137 Harden budget UI tests",
    "pr_author": "ddl-cfuerst",
    "file_path": "e2e-tests/features/domino/domino_cost/budget_ui.feature",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-xin",
        "body": "The indentation is weird"
      },
      {
        "author": "ddl-cfuerst",
        "body": "Is this better? I'm not sure which part is weird to you. All the examples I'm seeing in other places look ugly, too"
      },
      {
        "author": "ddl-cfuerst",
        "body": "I found some example elsewhere and copied it, beauty be damned."
      },
      {
        "author": "ddl-xin",
        "body": "Yeah. I thought we always have some indentation in the block, like: https://github.com/cerebrotech/domino/blob/develop/e2e-tests/features/domino/apps/publish_app.feature#L64\r\n\r\nBut I guess that's not required. Your format is fine then"
      }
    ]
  },
  {
    "pr_number": 40290,
    "pr_title": "[QE-15196] Added sleep to make sure we wait for the size to be calculated",
    "pr_author": "ddl-viniatska",
    "file_path": "e2e-tests/features/domino/datasets/dataset_storage_threshold_limits.feature",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-xin",
        "body": "```suggestion\r\n      And I wait up to \"{CHANGE_ME}\" seconds to see the following steps succeed\r\n      \"\"\"\r\n      When I refresh the browser\r\n      Then I wait to see the text \"The allowed storage quota across all Datasets that you own in one or more projects is almost reached. Check notifications for more details.\"\r\n      \"\"\"\r\n```"
      },
      {
        "author": "ddl-viniatska",
        "body": "Great solution, thank you so much!!!!"
      }
    ]
  },
  {
    "pr_number": 40290,
    "pr_title": "[QE-15196] Added sleep to make sure we wait for the size to be calculated",
    "pr_author": "ddl-viniatska",
    "file_path": "e2e-tests/features/domino/datasets/dataset_storage_threshold_limits.feature",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-xin",
        "body": "Deleting this line?"
      }
    ]
  },
  {
    "pr_number": 40295,
    "pr_title": "[DOM-54608] Raw endpoint updated to respect allowHtmlFilesToRender flag",
    "pr_author": "ddl-g-chen",
    "file_path": "server/app/domino/server/blobstore/api/BlobController.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "niole",
        "body": "How do we know that this is html and should be escaped?\r\n\r\nAlso, I think the concern of escaping the content of the file, given that it is html, shouldn't be handled by the BlobController. Can we do this in a FileService? Whether or not the blob should be encoded has more to do with if the blob is a file and not something else\r\n\r\nThe blob controller is also used for things that are not files"
      },
      {
        "author": "ddl-g-chen",
        "body": "filesController checks if the file type is html & if the flag is false to set `cannotRenderHtml`. i was having trouble breaking down the return type in filesController so i made the changes here. \r\nif this function ends up getting called outside of filesController, the default is to skip the conditional"
      },
      {
        "author": "ddl-g-chen",
        "body": "i could make a separate function in blobController just for filesController to call but currently, i don't know how to move the encoding outside of blobController"
      },
      {
        "author": "niole",
        "body": "Although it's not used in the code base, it might still be used by another team/service. The BlobController is supposed to work for all blobs, regardless of what they actually are.\r\n\r\nSince this is an http endpoint, I guess it also has the XSS vuln in it. Maybe what we should do is read the cc flag inside of this endpoint and only encode the content if the content is html.\r\n\r\nAnother thing is that this logic reads the content out of the stream into memory without checking to see how big it is, which will OOM kill the server if the file is multiple gbs in size.\r\n\r\nIt's probably impossble to check if the file contents are html without reading it all into memory though...\r\n\r\n"
      }
    ]
  },
  {
    "pr_number": 40296,
    "pr_title": "DOM-54673 add CC flag to set max file sizes",
    "pr_author": "ddl-amodi",
    "file_path": "server/app/domino/server/lib/config/Settings.scala",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-jrakos",
        "body": "Is it possible that maxFileSizeOverridesForExtensions is read by the UI code to provide client-side enforcement of upload size?\r\n\r\nI feel like we should understand exactly what it does before we commit to the way the newly-added code is structured. "
      },
      {
        "author": "ddl-amodi",
        "body": "I do see this flag being used in the BE however when i try to set a value the input is rejected. Im not sure what the usage of this flag is as it does not accept a string and why i had to create a new one."
      },
      {
        "author": "ddl-grequeni",
        "body": "What do you mean by rejected? This other config looks exactly equal to the one we are adding here, and the PR where it was added looks like it had the same intention of this PR https://github.com/cerebrotech/domino/pull/10936/\r\nI think we should extend the behavior of this and document it properly (I see it's an undocumented CC)."
      },
      {
        "author": "ddl-grequeni",
        "body": "Who is the PM behind this? They should be aware of the existence of this other CC. Maybe it needs to be deprecated in favor of a new one. But please let's avoid having 2 CCs that are almost equal, it looks simple to add now, but it will be hard to maintain."
      },
      {
        "author": "ddl-amodi",
        "body": "Everytime i add a value for this CC Flag the input is invalid as it is expecting an Object, however all CC Flag values are recognized as strings. I am open to completely deprecating this Flag tbh since it does not work but idk who the right person is to make this call. The flag is so old that no one today will know the usage :/ "
      },
      {
        "author": "ddl-grequeni",
        "body": "Yeah makes sense. I wonder if anyone is using it since it's incompatible with today's CCs. Maybe in the past they set them using Mongo directly and Objects could be used as data type? Or maybe nobody ever used this/tested it in the APP so it never worked. \r\n\r\nTo be on the safe side, I think we shouldn't delete it unless we know that nobody is using it. Imagine if some customer was relying on it and suddenly it doesn't work any more. So we need to either migrate its values (preferred, transparent to customer, but probably hard/not worth the time if we cannot figure out how to make it work) or add a release note for 5.11 saying `frontend.maxFileSizeOverridesForExtensions` was replaced by `com.cerebro.domino.frontend.configuredMaxFileSizes` with the link to how to set the new CC, and mention the old one will be removed in the next Domino minor release (5.12 ?). So we can create 2 follow up tickets, one for the release notes and one to delete this config in 5.12. This way customers are warned that they need to manually migrate the config or they will lose it next release. We should check this approach with Ahmet/Murat."
      }
    ]
  },
  {
    "pr_number": 40301,
    "pr_title": "QE-14941 Restore AI Hub tests, with CircleCI workflow",
    "pr_author": "ddl-kgarton",
    "file_path": ".circleci/static-build.yml",
    "line": 3761,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-cedricyoung",
        "body": "two issues\n1. the `when` condition of `pre-merge` needs to be updated to exclude your new workflow\n2. this `pre-merge-system` worflow needs to be split into the specific workflows `pre-merge-system-standard` and `pre-merge-system-ai-hub`"
      },
      {
        "author": "ddl-kgarton",
        "body": "Changed."
      }
    ]
  },
  {
    "pr_number": 40301,
    "pr_title": "QE-14941 Restore AI Hub tests, with CircleCI workflow",
    "pr_author": "ddl-kgarton",
    "file_path": "build/ci/run_e2e_test_ci.py",
    "line": 63,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-cedricyoung",
        "body": "probably should also make a `system-ai-hub-vcluster` to be consistent"
      },
      {
        "author": "ddl-kgarton",
        "body": "Added."
      }
    ]
  },
  {
    "pr_number": 40301,
    "pr_title": "QE-14941 Restore AI Hub tests, with CircleCI workflow",
    "pr_author": "ddl-kgarton",
    "file_path": "system-tests/setup/setup_test_deployment.py",
    "line": 93,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-cedricyoung",
        "body": "was this part of debugging code that didn't get reverted?"
      },
      {
        "author": "ddl-kgarton",
        "body": "I think we should keep it. It makes setup idempotent, where without it, setup fails if you run it twice on the same deployment."
      }
    ]
  },
  {
    "pr_number": 40302,
    "pr_title": "DOM-55282  Add a project authorizer that can be used in non-adapters and use for activity endpoints",
    "pr_author": "niole",
    "file_path": "projects/interface/src/main/scala/domino/projects/api/ProjectAuthorizer.scala",
    "line": 9,
    "is_resolved": false,
    "comments": [
      {
        "author": "niole",
        "body": "Added this authorizer in api, because the activity service is not an adapter module and doesn't have access to server.\r\n\r\none day we should refactor all of the project authorizer to move out of server, but that won't happen until we can move it's dependencies out of there, like projectpersister, user, settings, etc.."
      }
    ]
  },
  {
    "pr_number": 40315,
    "pr_title": "[DOM-55009] Use whitelabel setting for rename modal",
    "pr_author": "ddl-richard-tom",
    "file_path": "frontend/package.json",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-galias",
        "body": "Have you run the update script for domino api? It looks like it has not been updated at all the package json files."
      }
    ]
  },
  {
    "pr_number": 40318,
    "pr_title": "[DOM-55307] Feature flag test for disabling Datasets ",
    "pr_author": "ddl-viniatska",
    "file_path": "e2e-tests/features/domino/datasets/disable_datasets_feature_flag.feature",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-cedricyoung",
        "body": "In general let's not use `wait` to not see something (unless the page dynamically updates), and instead have a step that ensures the page has loaded and then check with `I should not see` step.\r\n```suggestion\r\n      And I navigate to the url \"{BASEURL}/data\"\r\n      # please add a check to verify that the page has loaded\r\n     Then I should not see the tab \"Domino Datasets\"\r\n```"
      },
      {
        "author": "ddl-viniatska",
        "body": "thank you, fixed"
      }
    ]
  },
  {
    "pr_number": 40325,
    "pr_title": "[DOM-55305] We need to filter in the poll, not just before we start polling",
    "pr_author": "ddl-mmahmoud",
    "file_path": "e2e-tests/features/domino/roles/limited_admin_actions.feature",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-xin",
        "body": "You may want to change this line to `Then I should not see ..`, otherwise the test won't refresh the bowser since this wait is 35s and the outer wait is also 35s"
      }
    ]
  },
  {
    "pr_number": 40328,
    "pr_title": "QE-15202 - releases-5.10.0 - Workspace pluggable tools yaml start scripts need change",
    "pr_author": "ddl-abishek",
    "file_path": "system-tests/tests/dco/configs/sanity.yml",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-xin",
        "body": "Just want to point this odd change out and ask you to double check. Let's start a system test run and see what happens"
      },
      {
        "author": "ddl-abishek",
        "body": "commit 1564a7c2d750f27357c0dfcf6fa7cc6d7a8d9793 (HEAD -> QE-15202, origin/QE-15202)\r\nAuthor: ddl-abishek <abishek.subramanian@dominodatalab.com>\r\nDate:   Fri Mar 8 18:03:47 2024 -0500\r\n\r\n    add_base_dependencies False for MPI - missed earlier"
      }
    ]
  },
  {
    "pr_number": 40333,
    "pr_title": "[DOM-55259] (5.9.2) Bump domino-pytk to include fixes",
    "pr_author": "ddl-mmahmoud",
    "file_path": "e2e-tests/requirements.txt",
    "line": 7,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-xin",
        "body": "If you want to test it out, you should use something like the the previous line for cucu, the version number should be the commit SHA of the PR in domino-pytk"
      }
    ]
  },
  {
    "pr_number": 40342,
    "pr_title": "[DOM-54526] Create persistence layer for Compute Provider Types, Compute Providers, and Compute Tiers",
    "pr_author": "adrianrsy",
    "file_path": "compute-providers/implementation/src/main/scala/domino/computeproviders/implementation/domain/entities/SchemaDefinitionItem.scala",
    "line": 7,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-yaniv-amar",
        "body": "Nit: Is it frowned upon to use reserved keywords? If yes, maybe change it to SchemaDefinitionItemType, if no, ignore me :) "
      },
      {
        "author": "adrianrsy",
        "body": "Doesn't seem like it. It's used in several other places in the codebase."
      }
    ]
  },
  {
    "pr_number": 40342,
    "pr_title": "[DOM-54526] Create persistence layer for Compute Provider Types, Compute Providers, and Compute Tiers",
    "pr_author": "adrianrsy",
    "file_path": "compute-providers/implementation/src/main/scala/domino/computeproviders/implementation/infrastructure/ComputeTierBson.scala",
    "line": 31,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-yaniv-amar",
        "body": "see previous nit pick item :) "
      }
    ]
  },
  {
    "pr_number": 40345,
    "pr_title": "[DOM-54794] Adding notification config service",
    "pr_author": "DDL-Martin-Gazzara",
    "file_path": "frontend/packages/ui/src/admin-advanced/billing-tags/store/BillingTagsStore.tsx",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-galias",
        "body": "nit, you can use noop"
      },
      {
        "author": "DDL-Martin-Gazzara",
        "body": "done"
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