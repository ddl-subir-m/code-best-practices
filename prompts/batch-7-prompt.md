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
    "pr_number": 40041,
    "pr_title": "QE-11672 Add a helper function in system tests",
    "pr_author": "ddl-xin",
    "file_path": "system-tests/common/api_client.py",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-kgarton",
        "body": "This may be splitting hairs, but it matters to me: a URL is a Universal Resource Locator, a complete name that can be used to locate a resource from anywhere on the Internet. But the argument here is only a part of a URL, a path to a resource on a specific hostname. I think it would be good to rename it.\r\n```suggestion\r\n        path: str,\r\n```"
      }
    ]
  },
  {
    "pr_number": 40041,
    "pr_title": "QE-11672 Add a helper function in system tests",
    "pr_author": "ddl-xin",
    "file_path": "system-tests/common/api_client.py",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-kgarton",
        "body": "Would it be good to use the same names for these that the `requests` module does? Those are the names I would guess to use if I were encountering this function in the wild.\r\n```suggestion\r\n        headers: dict | None = None,\r\n        params: list[tuple] | None = None,\r\n        body: list[tuple] | None = None,\r\n```"
      },
      {
        "author": "ddl-xin",
        "body": "In the generated api_client, these are the params for the `call_api()` function. I mainly follow the same params.\r\n<img width=\"608\" alt=\"image\" src=\"https://github.com/cerebrotech/domino/assets/104880864/231c876d-5af6-4622-b8ca-f2c0fbb6ad13\">\r\n \r\n Specifically, `body` is different than `post_params` and I expect I'll add `body` in the future when it needs to be used."
      },
      {
        "author": "ddl-kgarton",
        "body": "OK, that makes sense."
      }
    ]
  },
  {
    "pr_number": 40041,
    "pr_title": "QE-11672 Add a helper function in system tests",
    "pr_author": "ddl-xin",
    "file_path": "system-tests/common/api_client.py",
    "line": 54,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-kgarton",
        "body": "If the user passes in a value for the `Cookie` header, do we want to replace that cookie? Is it possible to add the default cookie, instead of replacing it?"
      },
      {
        "author": "ddl-xin",
        "body": "The main purpose is that the user shouldn't worry about cookies when making the requests. The cookies are managed by the `api_client`"
      },
      {
        "author": "ddl-kgarton",
        "body": "Does that mean that we just expect people not to pass in a `Cookie` value in the `headers` dict? That feels like setting a landmine. I expect in two years, someone is going to have to write a test for some specific `Cookie` value, and will go nuts trying to figure out why they're not getting the expected results. I think the pain an automatic replacement could cause is great enough that it's worth building in a simple detection now. The least we can do is emit a warning that we're replacing the `Cookie` value if we detect one that already exists in the `headers` dict. That should at least give people a clue that their values are being tampered with."
      },
      {
        "author": "ddl-xin",
        "body": "So I expect this function to be used like you are using your browser. You shouldn't worry about cookie management when you're using your browser.\r\n\r\nIf the user wants to have a test to play with cookies, they should use lower level libraries like `requests` or `urllib3`"
      },
      {
        "author": "ddl-xin",
        "body": "Actually, I think I'll change the args to remove `header_params` and replace it with `content_type` and `accept_type`. These should be the only two headers the user can provide."
      }
    ]
  },
  {
    "pr_number": 40041,
    "pr_title": "QE-11672 Add a helper function in system tests",
    "pr_author": "ddl-xin",
    "file_path": "system-tests/common/api_client.py",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-kgarton",
        "body": "Do we want to manage trailing slashes here? If we do check to see if the base URL ends with one, or the path passed in by the caller starts with one, then that might avoid some head-slapping errors or bugs."
      },
      {
        "author": "ddl-xin",
        "body": "`base_url` doesn't have one. That's given. I could check to make sure `url` starts with one"
      }
    ]
  },
  {
    "pr_number": 40052,
    "pr_title": "[DOM-54714] Validate attached projects to a billing tag",
    "pr_author": "ddl-juan-cistaro",
    "file_path": "domino-cost/impl/src/main/scala/domino/cost/impl/billingtags/BillingTagServiceImpl.scala",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-olsonJD",
        "body": "Maybe something like this:\r\n`s\"Billing Tag '$tag' deactivation Failed! '$tag' is assigned to ${projects.totalMatches} project(s).\"`"
      }
    ]
  },
  {
    "pr_number": 40052,
    "pr_title": "[DOM-54714] Validate attached projects to a billing tag",
    "pr_author": "ddl-juan-cistaro",
    "file_path": "domino-cost/impl/src/main/scala/domino/cost/impl/billingtags/BillingTagServiceImpl.scala",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-olsonJD",
        "body": "nit: space"
      }
    ]
  },
  {
    "pr_number": 40052,
    "pr_title": "[DOM-54714] Validate attached projects to a billing tag",
    "pr_author": "ddl-juan-cistaro",
    "file_path": "domino-cost/impl/src/main/scala/domino/cost/impl/billingtags/BillingTagServiceImpl.scala",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-olsonJD",
        "body": "the persisting call can be outside of the future, as we are only returning the Future[BillingTagDto]"
      }
    ]
  },
  {
    "pr_number": 40052,
    "pr_title": "[DOM-54714] Validate attached projects to a billing tag",
    "pr_author": "ddl-juan-cistaro",
    "file_path": "domino-cost/impl/src/main/scala/domino/cost/impl/billingtags/BillingTagServiceImpl.scala",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-olsonJD",
        "body": "`Deleting BillingTag $billingTagName Failed! Billing tag $billingTagName not found.`"
      }
    ]
  },
  {
    "pr_number": 40052,
    "pr_title": "[DOM-54714] Validate attached projects to a billing tag",
    "pr_author": "ddl-juan-cistaro",
    "file_path": "domino-cost/impl/src/main/scala/domino/cost/io/RestCallHelper.scala",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-olsonJD",
        "body": "Nit:\r\nwe can even further decrease the number of records that we want to retrieve by limiting the page size. "
      }
    ]
  },
  {
    "pr_number": 40067,
    "pr_title": "QE-15074 Qe 15074 add firefox specific workflow",
    "pr_author": "ddl-michael-noonan",
    "file_path": ".circleci/static-build.yml",
    "line": 1096,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-cedricyoung",
        "body": "are you saying to have all the ff tests in this separate folder? Just wondering since it makes tests more separated by type rather than \"Feature\". "
      },
      {
        "author": "ddl-michael-noonan",
        "body": "all of the firefox-only tests would be in this folder yes."
      },
      {
        "author": "ddl-michael-noonan",
        "body": "I added the ability to tag though, idk what the best design choice to trigger this though\r\n"
      }
    ]
  },
  {
    "pr_number": 40067,
    "pr_title": "QE-15074 Qe 15074 add firefox specific workflow",
    "pr_author": "ddl-michael-noonan",
    "file_path": ".circleci/static-build.yml",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-cedricyoung",
        "body": "I think you may need a shorter prefix....\n```suggestion\n      deployment_prefix: run-ff-only\n```"
      },
      {
        "author": "ddl-michael-noonan",
        "body": "I don't think making it ff is a great idea, I thought about this too, but this conflicts with the \"Feature Flag\" terminology."
      },
      {
        "author": "ddl-michael-noonan",
        "body": "I set it to `firefox`"
      }
    ]
  },
  {
    "pr_number": 40067,
    "pr_title": "QE-15074 Qe 15074 add firefox specific workflow",
    "pr_author": "ddl-michael-noonan",
    "file_path": ".circleci/static-build.yml",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-cedricyoung",
        "body": "sorry, let's not add yet another param, but key off the test type instead\n```suggestion\n```"
      }
    ]
  },
  {
    "pr_number": 40067,
    "pr_title": "QE-15074 Qe 15074 add firefox specific workflow",
    "pr_author": "ddl-michael-noonan",
    "file_path": ".circleci/static-build.yml",
    "line": 1220,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-cedricyoung",
        "body": "```suggestion\r\n```"
      }
    ]
  },
  {
    "pr_number": 40067,
    "pr_title": "QE-15074 Qe 15074 add firefox specific workflow",
    "pr_author": "ddl-michael-noonan",
    "file_path": ".circleci/static-build.yml",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-cedricyoung",
        "body": "\n```suggestion\n```"
      }
    ]
  },
  {
    "pr_number": 40067,
    "pr_title": "QE-15074 Qe 15074 add firefox specific workflow",
    "pr_author": "ddl-michael-noonan",
    "file_path": "e2e-tests/features/steps/ui/image_steps.py",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-bcolby",
        "body": "Why the five second sleep? And I think it shouldn't be a numeral 5, but rather a well named argument in cucurc."
      },
      {
        "author": "ddl-michael-noonan",
        "body": "I believe it is a time used to wait for the window to finish its render after the change in window size. Will say that this is a branch that was merged from @ddl-galias 's work for setting up the test for firefox. I believe I took a cursory glance at this at CKO. So, I may need to get in touch with him on this choice. "
      },
      {
        "author": "ddl-xin",
        "body": "I also don't like the sleep. There is no guarantee that the time is enough. It would be better if we can check the current window size"
      },
      {
        "author": "ddl-xin",
        "body": "Also, I think it would be nice to have the reset window size as a context manger such that after taking the screenshot, you will restore the window size.\r\n\r\nSo, what I have in mind is for the function `wait_to_compare_source_displayed_embed`, you can do:\r\n```\r\nwith resize_window():\r\n    display_embed_filepath = retry(get_embed_screenshot)(ctx)\r\n```\r\n\r\nAlso, why do you have `retry` wrapped of `get_embed_screenshot`? "
      },
      {
        "author": "ddl-galias",
        "body": "We applied some changes with @ddl-michael-noonan:\r\n- Moved the retry to an intermediate function that is fully wrapped by the retry at the step definition.\r\n- Removed the sleep as it was not necessary. It remained from when I was testing this out.\r\n- Used the cucu config default browser size as a way to ensure the default viewport dimensions are used. The magic numbers are not there anymore and also it is not necessary to reset it back to the default as we are currently forcing the config's default."
      }
    ]
  },
  {
    "pr_number": 40067,
    "pr_title": "QE-15074 Qe 15074 add firefox specific workflow",
    "pr_author": "ddl-michael-noonan",
    "file_path": "e2e-tests/features/steps/ui/image_steps.py",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-bcolby",
        "body": "Is this actually true of this function? Isn't this comment more about the example renders that you are source controlling to be compared against?"
      },
      {
        "author": "ddl-michael-noonan",
        "body": "peep this comment -> https://github.com/cerebrotech/domino/pull/40067/files#r1520539651\r\n\r\nBut it genuinely seems like firefox-117 has nothing to do with this function in reality. I will have to have @ddl-galias walk me through this reasoning. Because I believe we just upgraded to 122 and it still worked. "
      },
      {
        "author": "ddl-galias",
        "body": "The comment was wrongly placed by me. It should be at the step at line 86-89.\r\n\r\nIn the context of that other step, the reason why Fifefox is needed (we can remove the version) is that chromium headless wont render the embed, so you might try this in Chrome with UI and then it will fail either at the CI or in headless mode.\r\n\r\nI moved the comment to the correct place and checked the wording with @ddl-michael-noonan and enhanced it too."
      }
    ]
  },
  {
    "pr_number": 40067,
    "pr_title": "QE-15074 Qe 15074 add firefox specific workflow",
    "pr_author": "ddl-michael-noonan",
    "file_path": ".circleci/static-build.yml",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-xin",
        "body": "You are removing the system tests changes that @ddl-kgarton just made"
      }
    ]
  },
  {
    "pr_number": 40076,
    "pr_title": "DOM-54752 Dom 54752 UI add new endpoint modal",
    "pr_author": "DDL-Martin-Gazzara",
    "file_path": "frontend/packages/test-utils/src/components/FormWrapper.tsx",
    "line": 7,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-galias",
        "body": "We can do it later: A way for achieving this should be by wrapping the form methods with a function that calls the spy (with the full args list) and then calling the regular implementation"
      }
    ]
  },
  {
    "pr_number": 40076,
    "pr_title": "DOM-54752 Dom 54752 UI add new endpoint modal",
    "pr_author": "DDL-Martin-Gazzara",
    "file_path": "frontend/packages/ui/src/ai-gateway/AIGatewayAdminContainer.tsx",
    "line": 9,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-galias",
        "body": "Is the modal visibility state necessary at this scope? I think it can live at the view scope"
      },
      {
        "author": "DDL-Martin-Gazzara",
        "body": "I think the state should be in the container component. The view component should be just the dummy part of the component"
      },
      {
        "author": "ddl-galias",
        "body": "yeah it is not a big deal, I try to always have the state as close as possible to the component that concerns about it to avoid unnecessary prop drilling. Not necessary to change it though."
      }
    ]
  },
  {
    "pr_number": 40076,
    "pr_title": "DOM-54752 Dom 54752 UI add new endpoint modal",
    "pr_author": "DDL-Martin-Gazzara",
    "file_path": "frontend/packages/ui/src/ai-gateway/components/add-new-endpoint-modal/AddNewEndpointModal.tsx",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-galias",
        "body": "It is usually a nice to have for the variable to be self descriptive, instead of setting px a as comment you can name de var: `ADD_MODAL_WIDTH_PX`"
      },
      {
        "author": "DDL-Martin-Gazzara",
        "body": "Agree"
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