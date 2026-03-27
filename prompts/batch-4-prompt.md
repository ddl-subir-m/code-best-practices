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
    "pr_number": 39799,
    "pr_title": "DOM-54060: address tech debt from apps subdomain feature",
    "pr_author": "steved",
    "file_path": "compute-grid/interface/src/main/scala/domino/computegrid/provisional/ComputeGridSettings.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-ssenecal",
        "body": "what is a \"Control Plane URL\"?  Is it just the URL to the nucleus UI?   Should this maybe be called \"nucleusUrl\" or \"dominoUrl\" or something?"
      },
      {
        "author": "steved",
        "body": "Yeah, had a tough time thinking of a good name. It's more than nucleus since it's used for keycloak downstream (whether or not that's a good idea). I'm ok with `dominoUrl`, I just wasn't sure if that was clear enough in a data-plane context."
      },
      {
        "author": "ddl-ssenecal",
        "body": "I guess my assumption is that we expose multiple services from a control plane (nucleus/keycloak/domino, rabbitmq, vault, etc), and in that environment a \"control plane url\" could refer to any one of those.  Perhaps `dominoUrl` would be the best fit in that case?  I don't love that either, but it may be more specific."
      }
    ]
  },
  {
    "pr_number": 39799,
    "pr_title": "DOM-54060: address tech debt from apps subdomain feature",
    "pr_author": "steved",
    "file_path": "server/app/domino/server/dispatcher/infrastructure/compute/ComputeClusterUrlBuilder.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-ssenecal",
        "body": "seems like we are always returning a full URL now, but before we might have only been returning a path in the case of a local data plane... Does this break anything?"
      },
      {
        "author": "steved",
        "body": "I'll run e2e tests, but the workspaces in dev work ok."
      },
      {
        "author": "ddl-ssenecal",
        "body": "I assume that if there were to be an issue, it would be on the local data plane, where it previously was just relying on a path."
      },
      {
        "author": "steved",
        "body": "Ditto. `notebookPublicUrl` did return a full URL and the iframe `src` was the full URL vs. a path. I think the fewer branches here outweigh my general inclination to only use paths where we can."
      },
      {
        "author": "steved",
        "body": "Oh, I guess similar to the model API one, the scheme could be incorrect. Particularly for local data planes, because we do \"technically\" support HTTP. \r\n\r\nFor data planes, do we always assume HTTPS? Does that mean that RoutesPresenter should also? Or should data planes track a scheme?"
      },
      {
        "author": "ddl-ssenecal",
        "body": "For remote data planes, ya, we likely always assumed HTTPS because part of the design required TLS termination in the load balancers for security reasons.  For the local data plane, since it would not be traversing an ELB, ya, it could be hitting an HTTP (plaintext) endpoint."
      }
    ]
  },
  {
    "pr_number": 39799,
    "pr_title": "DOM-54060: address tech debt from apps subdomain feature",
    "pr_author": "steved",
    "file_path": "server/app/domino/server/modelmanager/domain/services/routing/RoutesPresenter.scala",
    "line": 52,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-ssenecal",
        "body": "is this safe to assume?  I've see hosting TLS on port `8080` and other such weirdness.  Should we be using some other mechanism to determine the scheme?"
      },
      {
        "author": "steved",
        "body": "I think because the data plane address doesn't cover HTTPS vs. not. What would be ideal here? Having the data plane config capture HTTPS vs. not? Whatever it is, I probably need to create a follow-up ticket for Compute or PHaM."
      },
      {
        "author": "ddl-ssenecal",
        "body": "Ideally, I think we would know what the scheme was for a given data plan without making assumptions, but if that is not already available, then, ya, another ticket may be required."
      }
    ]
  },
  {
    "pr_number": 39799,
    "pr_title": "DOM-54060: address tech debt from apps subdomain feature",
    "pr_author": "steved",
    "file_path": "server/app/domino/server/notebooks/NotebookUrlResolver.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-ssenecal",
        "body": "looks like previously this was sometimes a path, sometimes a URL.  Now its always a URL.  Is this safe?"
      }
    ]
  },
  {
    "pr_number": 39799,
    "pr_title": "DOM-54060: address tech debt from apps subdomain feature",
    "pr_author": "steved",
    "file_path": "server/app/domino/server/dispatcher/infrastructure/compute/ComputeClusterUrlBuilder.scala",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-ssenecal",
        "body": "should we do any normalization here?  Could the path end up with `//`?"
      }
    ]
  },
  {
    "pr_number": 39799,
    "pr_title": "DOM-54060: address tech debt from apps subdomain feature",
    "pr_author": "steved",
    "file_path": "server/app/domino/server/lib/play/SessionDomainFilter.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-ssenecal",
        "body": "does it matter that the cookie has changed here?  Looks like it was previously just `data`, and now its `data - \"_session_domain\"`"
      },
      {
        "author": "steved",
        "body": "nope, just happened to notice it was extraneous info sent down in the cookie."
      }
    ]
  },
  {
    "pr_number": 39799,
    "pr_title": "DOM-54060: address tech debt from apps subdomain feature",
    "pr_author": "steved",
    "file_path": "server/app/domino/server/notebooks/NotebookUrlResolver.scala",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-ssenecal",
        "body": "do we need to normalize the URL here as well to ensure we don't end up with `//` somewhere?"
      },
      {
        "author": "steved",
        "body": "good question, we control both sides of this url right now. what did you have in mind?"
      },
      {
        "author": "ddl-ssenecal",
        "body": "something like `new URL(s\"$dataPlaneUrl$notebookPublicPath\").toString` or similar.  Since we weren't doing this before I suspect we're no worse off than we were before, but it would be nice to ensure we have clean URLs"
      }
    ]
  },
  {
    "pr_number": 39799,
    "pr_title": "DOM-54060: address tech debt from apps subdomain feature",
    "pr_author": "steved",
    "file_path": "server/src/test/domino/server/notebooks/NotebookUrlResolverSpec.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-grequeni",
        "body": "nit: We can put this in a fixture attribute `localhostUrl` (a `NotebookTest` attribute I think) and reuse. "
      },
      {
        "author": "steved",
        "body": "DRY it is!"
      }
    ]
  },
  {
    "pr_number": 39799,
    "pr_title": "DOM-54060: address tech debt from apps subdomain feature",
    "pr_author": "steved",
    "file_path": "nucleus/test/domino/nucleus/modelproduct/lib/ConsumerModelProductUrlMapperSpec.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "ddl-grequeni",
        "body": "I think this file should be owned by pham too (like the class being tested), not develop, right?"
      }
    ]
  },
  {
    "pr_number": 39892,
    "pr_title": "DOM-54760 Download AI Gateway Audit Data API",
    "pr_author": "ddl-aj-rossman",
    "file_path": "aigateway/web/conf/aigateway.api.routes",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "vivekcalambur",
        "body": "I think a better name for this would be `useJson`"
      }
    ]
  },
  {
    "pr_number": 39906,
    "pr_title": "[DOM-54004] Scoped Flows Storage Credentials for Run Container",
    "pr_author": "ddl-ryan-connor",
    "file_path": "executor/app/app/domino/executor/infrastructure/initialization/ExecutorInjectionModule.scala",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-ebrown",
        "body": "FYI @pocheung1 this will be a place for you to integrate things for Azure when you get this far"
      }
    ]
  },
  {
    "pr_number": 39906,
    "pr_title": "[DOM-54004] Scoped Flows Storage Credentials for Run Container",
    "pr_author": "ddl-ryan-connor",
    "file_path": "server/app/domino/server/dispatcher/infrastructure/KubernetesConfigurationGenerator.scala",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "ddl-ebrown",
        "body": "Another spot @pocheung1 "
      }
    ]
  },
  {
    "pr_number": 39906,
    "pr_title": "[DOM-54004] Scoped Flows Storage Credentials for Run Container",
    "pr_author": "ddl-ryan-connor",
    "file_path": "executor/app/app/domino/executor/infrastructure/initialization/ExecutorInjectionModule.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "noahjax",
        "body": "Why is the `@Named` necessary?"
      },
      {
        "author": "ddl-ryan-connor",
        "body": "it's not; changed"
      }
    ]
  },
  {
    "pr_number": 39906,
    "pr_title": "[DOM-54004] Scoped Flows Storage Credentials for Run Container",
    "pr_author": "ddl-ryan-connor",
    "file_path": "executor/app/app/domino/executor/run/KubernetesRunExecutionPolicy.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "noahjax",
        "body": "Could we just pass in if flows is enabled instead of the full settings object? Should make it nicer to test this class. Ideally we also wouldn't depend on it in the `KubernetesWithVolumesRunExecutionPolicy`, but at least you aren't introducing it there."
      },
      {
        "author": "ddl-ryan-connor",
        "body": "changed it for `KubernetesRunExecutionPolicy`"
      }
    ]
  },
  {
    "pr_number": 39906,
    "pr_title": "[DOM-54004] Scoped Flows Storage Credentials for Run Container",
    "pr_author": "ddl-ryan-connor",
    "file_path": "executor/app/app/domino/executor/run/WorkflowsAwsStorageUserCredentialsManager.scala",
    "line": 74,
    "is_resolved": false,
    "comments": [
      {
        "author": "noahjax",
        "body": "Does it make sense to have some internal mechanism here to determine if this can be a noop? Like if somehow we request to refresh creds but creds have more time left than the refresh interval, we don't actually need to refresh them again. Curious because this could help us hedge against some failure case where we start spamming cred refreshes and get into trouble."
      },
      {
        "author": "ddl-ryan-connor",
        "body": "i dont think so. i initially did just that, but it adds complexity to the code and i dont think gets us anything so i removed it. the refresh frequency (period in which this func is called) is generally going to be relatively long (like at least an hour), and i don't think there's a chance of spamming requests"
      }
    ]
  },
  {
    "pr_number": 39906,
    "pr_title": "[DOM-54004] Scoped Flows Storage Credentials for Run Container",
    "pr_author": "ddl-ryan-connor",
    "file_path": "server/app/domino/server/computegrid/ComputeGridSettingsAdapter.scala",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "noahjax",
        "body": "When would `defaultWorkflowStorageOrchestratorAuthRoleId` and `defaultWorkflowStorageExecutorAuthRoleId` ever be different?"
      },
      {
        "author": "ddl-ebrown",
        "body": "I don't think there's ever a sensible default here that looks like this. `153827342122` is our account id"
      },
      {
        "author": "ddl-ryan-connor",
        "body": "it's sensible for all our internal deployments.\r\n\r\nwould you rather there be no default? like `\"\"`?"
      },
      {
        "author": "ddl-ryan-connor",
        "body": "> When would `defaultWorkflowStorageOrchestratorAuthRoleId` and `defaultWorkflowStorageExecutorAuthRoleId` ever be different?\r\n\r\ni dont know, but this provides flexibility for it to work if needed for development, debugging, whatever.\r\n\r\nalso, \r\n`defaultWorkflowStorageOrchestratorAuthRoleId` == role that init container and sidecar use\r\n`defaultWorkflowStorageExecutorAuthRoleId` == role that executor uses when getting creds for the run container.\r\n\r\ni thought those might conceivably be different, but i dont have an example.\r\n\r\nwould you rather we not distinguish between these and just use one CC?"
      },
      {
        "author": "ddl-ebrown",
        "body": "> it's sensible for all our internal deployments.\r\n> \r\n> would you rather there be no default? like `\"\"`?\r\n\r\nMy point here is that we should *never* use this fallback default in the real world, so IMHO it doesn't belong in code. Since it's set like this, it might actually mask a real failure to propagate values properly through our charts, etc because it will always work in our environment / tests."
      },
      {
        "author": "noahjax",
        "body": "> would you rather we not distinguish between these and just use one CC\r\n\r\nNot worth blocking this PR, but seems like it would be nice to have a single CC in prod if these things are always the same"
      },
      {
        "author": "ddl-ryan-connor",
        "body": "filed https://dominodatalab.atlassian.net/browse/DOM-55668"
      }
    ]
  },
  {
    "pr_number": 39906,
    "pr_title": "[DOM-54004] Scoped Flows Storage Credentials for Run Container",
    "pr_author": "ddl-ryan-connor",
    "file_path": "server/app/domino/server/dispatcher/infrastructure/KubernetesConfigurationGenerator.scala",
    "line": null,
    "is_resolved": true,
    "comments": [
      {
        "author": "noahjax",
        "body": "Nit: you could just yield a V1EnvVar here and then call .toSeq at the end instead of getOrElse"
      },
      {
        "author": "ddl-ryan-connor",
        "body": "done"
      }
    ]
  },
  {
    "pr_number": 39906,
    "pr_title": "[DOM-54004] Scoped Flows Storage Credentials for Run Container",
    "pr_author": "ddl-ryan-connor",
    "file_path": "server/app/domino/server/dispatcher/infrastructure/KubernetesConfigurationGenerator.scala",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "noahjax",
        "body": "Seems like you do this a lot; could be nice to have a helper that took in (settings, computeGridSettings) and returned Option[StorageType] (i.e. Some(\"aws\") if flows is enabled, None if it's disabled)"
      },
      {
        "author": "ddl-ryan-connor",
        "body": "i put a helper in `KubernetesConfigurationGenerator`. but i do the same check in executor injection module, and we might be doing the same check elsewhere, not sure if its the best place for the helper, but i couldn't think of a more central location that made sense"
      }
    ]
  },
  {
    "pr_number": 39906,
    "pr_title": "[DOM-54004] Scoped Flows Storage Credentials for Run Container",
    "pr_author": "ddl-ryan-connor",
    "file_path": "server/app/domino/server/dispatcher/service/ExecutionResourceParamsMaker.scala",
    "line": 714,
    "is_resolved": false,
    "comments": [
      {
        "author": "noahjax",
        "body": "Don't we want this to be the data container? Or is this fine because other params like rawOutputPrefix tell the sidecar to write output to the data container?"
      },
      {
        "author": "ddl-ryan-connor",
        "body": "it should be the metadata container. thats where everything the init container and sidecar container touch are, except yes the raw output prefix, which is provided separately via the jobs api call"
      }
    ]
  },
  {
    "pr_number": 39906,
    "pr_title": "[DOM-54004] Scoped Flows Storage Credentials for Run Container",
    "pr_author": "ddl-ryan-connor",
    "file_path": "server/src/test/domino/server/dispatcher/service/ExecutionResourceParamsMakerSpec.scala",
    "line": null,
    "is_resolved": false,
    "comments": [
      {
        "author": "noahjax",
        "body": "Why the change to the Fixture here?"
      },
      {
        "author": "ddl-ryan-connor",
        "body": "no real reason. a lot of our spec classes that extend `AnyFlatSpec` use `trait` instead of `class`. i dont think there's a difference for these test purposes. but i switched it back"
      },
      {
        "author": "noahjax",
        "body": "I was asking because of the removal of the `withFixture`, which I thought was related. In my rudimentary understanding the old way was using the same fixture across all tests, whereas the new one creates a new fixture for each. Not super important, but seems like the tests would run faster if they could share a fixture, so was curious why you opted for the latter approach."
      },
      {
        "author": "ddl-ryan-connor",
        "body": "i could be wrong but i believe even in the `withFixture` style that has the `in { fixture =>` syntax, a new fixture is created each time. if not, then stuff like `verify(mocked.foo, times(1))` wouldn't work correctly -- you need a whole new `mocked` instance for each test to ensure `times(1)` since i believe the arbitrary mocks/spys arent automatically (or can't?) be \"reset\".\r\n\r\nmore reading \r\nhttps://www.scalatest.org/user_guide/sharing_fixtures\r\nhttps://www.scalatest.org/scaladoc/3.2.18/org/scalatest/flatspec/FixtureAnyFlatSpec.html\r\n\r\nthe docs about \"FixtureAnyFlatSpec\" are cryptic and dont really say anything helpful to me, and nothing about single-instantiation of the Fixture param\r\n\r\n\"Recommended Usage: Use class\u00a0FixtureAnyFlatSpec\u00a0in situations for which\u00a0AnyFlatSpec\u00a0would be a good choice, when all or most tests need the same fixture objects that must be cleaned up afterwards.\u00a0Note:\u00a0FixtureAnyFlatSpec\u00a0is intended for use in special situations, with class\u00a0AnyFlatSpec\u00a0used for general needs. For more insight into where\u00a0FixtureAnyFlatSpec\u00a0fits in the big picture, see the\u00a0withFixture(OneArgTest)\u00a0subsection of the\u00a0Shared fixtures\u00a0section in the documentation for class\u00a0AnyFlatSpec.\"\r\n\r\na problem ive found with the FixtureAnyFlatSpec's `in { fixture =>` style is that it is hard to use with table-driven tests. here's the basic structural problem:\r\n```\r\n\"theMethod\" should \"should work\" in { fixture =>\r\n  import fixture._\r\n  // say you need to specify a return value for a mock, different for each test in the table-driven test cases\r\n  // well, you can't do it here, because we already passed in the one fixture param we get to use\r\n  forAll (testCases) { (argOne, argTwo) =>\r\n    // well here's where you'd actually want to do it, because presumably your test cases have the values you want the mock to return. but same problem -- once the mock is set the first time, can't change the return value, because it's all that same fixture arg\r\n    // do and assert stuff for each test\r\n  }\r\n}\r\n```\r\n\r\nin the past, i've also tried inverting so the `forAll` is on the \"outside\", but ran into issues, i think with test naming, or it wouldn't compile, or something\r\n\r\nthat problem goes away using `AnyFlatSpec` instead.\r\n\r\nif you dig in more here and have other questions or better info, let me know!"
      },
      {
        "author": "ddl-ryan-connor",
        "body": "i found an example (that i wrote actually, lol) of doing mock return stuff when using `FixtureAnyWordSpec` -- maybe a similar syntax might work for `FixtureAnyFlatSpec`? i'll try it out next time https://github.com/cerebrotech/domino/blob/d4f7827489a39fd6d272fbf9816906ec2098bd9b/server/src/test/domino/server/hardwaretiermanager/application/HardwareTierServiceSpec.scala#L106"
      },
      {
        "author": "ddl-ryan-connor",
        "body": "oh wait, that's not a valid example, it just does the same return value each time"
      },
      {
        "author": "ddl-ryan-connor",
        "body": ".."
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