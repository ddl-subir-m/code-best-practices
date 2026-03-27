# Pattern Validation Report — cerebrotech/domino

**Generated:** March 26, 2026
**Source:** 20 most-reviewed PRs merged in the last 2 weeks (77 human review threads, 155 comments)
**Raw patterns extracted:** 33
**Clusters after deduplication:** 15

---

## Go/No-Go Assessment

**Result: GO** — 9 recurring patterns (appearing in 2+ PRs) identified. Exceeds the 5-pattern threshold.

---

## Recurring Patterns (ranked by frequency)

These patterns appeared across multiple PRs — the strongest signal for team-wide conventions.

### 1. API Design Consistency (4 occurrences)
**Rule:** API documentation and payloads should be semantically accurate, future-proof, and include human-readable fields. Avoid implementation-specific details in docs, ensure required fields are never silently empty, and use consistent PATCH semantics.

| # | Evidence | PR | File |
|---|----------|-----|------|
| 1 | "can you take out 'by project id'? its true the upsert key includes project id for the two types of mount points we have now, but may not be the case for all types soon" | #47200 | `nucleus/api/public-api.json` |
| 2 | "calling out 'If uiMountPointTypeConfigs is provided...' makes it seem different, but really it is the same... how about: 'Absent fields are left unchanged'" | #47200 | `nucleus/api/public-api.json` |
| 3 | "The schema says id, label, and namespaceId as required, but here None gets mapped to ''. Could this be confusing to API consumers?" | #47212 | `apps/web/.../AppTransformer.scala` |
| 4 | "the guidance from Matt was that we should always include a name for readability" (human-readable names alongside IDs in audit events) | #47255 | `extensions/.../ExtensionEventTracker.scala` |

**Mode:** ambient
**Confidence:** high — consistent reviewer concern across multiple APIs and authors

---

### 2. Fail Explicitly — Don't Silently Return or Skip (3 occurrences)
**Rule:** When a method encounters an unsupported type, impossible state, or unresolvable required field, throw an explicit error rather than silently returning empty/no-op results or continuing execution.

| # | Evidence | PR | File |
|---|----------|-----|------|
| 1 | "what is the idea for the behaviour for other types, non app types? Should we explicitly restrict if we want to instead of silently returning?" | #47189 | `apps/.../InProcessModelProductService.scala` |
| 2 | "makes sense to just throw an error if we are unable to resolve the commit" | #47189 | `apps/.../ModelProductManager.scala` |
| 3 | "Should be an impossible case, but will switch to throwing instead of skipping silently" | #47216 | `apps/.../DefaultCommitResolver.scala` |

**Mode:** ambient
**Confidence:** high — three instances from two different reviewers, consistent principle

---

### 3. Push Sorting, Filtering, and Joins to the Database Layer (3 occurrences)
**Rule:** Sorting, pagination, and relational lookups should be performed in database queries, not in application memory. Avoid N+1 query patterns by combining lookups into single query pipelines.

| # | Evidence | PR | File |
|---|----------|-----|------|
| 1 | "this returns every single instance ever for the app, then we sort and take a single one... is there some better query or pattern we can use further down the stack?" | #47189 | `apps/.../DefaultAppInstanceService.scala` |
| 2 | "push _all_ sorting/paging logic down into one persister method db query to do that db side instead of scala in-memory, and also do the lookups/joins app => app_version => app_instance in the same query pipeline" | #47189 | `apps/.../AppController.scala` |
| 3 | "Move both the flag check and the taxonomy call inside the non-empty branch to avoid the flag lookup" (guard expensive calls behind data presence) | #47212 | `apps/.../AppController.scala` |

**Mode:** ambient
**Confidence:** high — performance concern raised by multiple reviewers, N+1 explicitly named

---

### 4. Logging Level Correctness (3 occurrences)
**Rule:** Routine operational messages should use DEBUG, not INFO. Warnings should only fire on genuinely unexpected conditions, and log messages must accurately reflect the condition that triggers them.

| # | Evidence | PR | File |
|---|----------|-----|------|
| 1 | "nit: maybe this and the log line below should be a debug level" | #47170 | `server/.../AppIndexer.scala` |
| 2 | "Maybe log a warning when the project is archived? Especially if we use this for other reasons" | #47216 | `apps/.../DefaultCommitResolver.scala` |
| 3 | "the warning log message suggests that might not be always expected" (warning was firing on legitimate empty results from a successful call) | #47233 | `apps/.../AppController.scala` |

**Mode:** ambient
**Confidence:** high — logging discipline enforced across multiple PRs

---

### 5. Handle Null/Absent/Archived Entities Gracefully (3 occurrences)
**Rule:** When code looks up an entity that may not exist (deleted, archived, never created), handle the absence explicitly — clean up stale references, provide fallback behavior, or defend against null returns.

| # | Evidence | PR | File |
|---|----------|-----|------|
| 1 | "I've fixed this so that when getApp returns None (archived/deleted), we now call deleteDocument to remove it from the ES index instead" | #47170 | `server/.../AppIndexer.scala` |
| 2 | "What would happen in the case where we wouldn't have an instance? It would be unusual but possible" | #47189 | `apps/.../AppController.scala` |
| 3 | "in a rare case where the branch/repo has no commits, this would return null. We should probably try to handle this" | #47216 | `apps/.../DefaultCommitResolver.scala` |

**Mode:** ambient
**Confidence:** high — defensive coding pattern enforced by multiple reviewers

---

### 6. Documentation Discipline (3 occurrences)
**Rule:** TODOs must reference tracked tickets. Forward-looking assumptions must be documented inline. Interface-layer docs must not reference implementation details from other modules.

| # | Evidence | PR | File |
|---|----------|-----|------|
| 1 | "is there a ticket for this TODO?" | #47178 | `server/.../UserKeycloakHelper.scala` |
| 2 | "can you put a comment: '// this assumes there is only one running version of the app'" | #47189 | `apps/.../ModelProductManager.scala` |
| 3 | "docstrings in /apps/interface should not talk about low level implementation that depends on other projects" | #47216 | `apps/.../AppVersion.scala` |

**Mode:** ambient
**Confidence:** medium-high — consistent but spans different sub-patterns

---

### 7. User-Facing Error Messages Must Be Actionable (2 occurrences)
**Rule:** Error messages shown to users should explain the probable cause in plain language and suggest resolution steps. Don't surface raw internal errors.

| # | Evidence | PR | File |
|---|----------|-----|------|
| 1 | "Can we perhaps say 'User hasn't logged in yet' so it's clear to customers how they can resolve it themselves" | #47178 | `server/.../users.scala.html` |
| 2 | "maybe we need to make the error message a little more clear and/or user friendly if it's going to be shown in the UI" | #47189 | `apps/.../ModelProductManager.scala` |

**Mode:** ambient
**Confidence:** medium — aligns with Domino UX design principles

---

### 8. Encode Required Fields as Non-Optional / Persist Resolved Values (2 occurrences)
**Rule:** Fields required for operation should be non-optional types. When fields are nullable at creation but resolved at runtime, resolve and persist them before execution to ensure reproducibility.

| # | Evidence | PR | File |
|---|----------|-----|------|
| 1 | "did you think about making the now-non-optional fields actually non optional in the case class?" | #47189 | `apps/.../ModelProductManager.scala` |
| 2 | "to ensure 'reproducible' versions, all such fields must receive the same 'resolve' treatment — resolve and persist before launching" | #47189 | `apps/.../ModelProductManager.scala` |

**Mode:** ambient
**Confidence:** medium — same reviewer, same PR, but strong architectural principle

---

### 9. Test Edge Cases and New State Transitions (2 occurrences)
**Rule:** When introducing new allowed behaviors or wrapping service calls in NonFatal recovery, add explicit tests for those specific scenarios.

| # | Evidence | PR | File |
|---|----------|-----|------|
| 1 | "can we add a test that starting an 'older' version stops a running 'newer' version? that's new allowed behavior" | #47189 | `server/.../ExecutionStarterSpec.scala` |
| 2 | "Maybe it would be good to verify the controller still returns apps with taxonomyTags = None when taxonomy service fails" | #47212 | `apps/.../AppControllerSpec.scala` |

**Mode:** active (skill: "how to write tests for new behaviors")
**Confidence:** medium

---

## Single-Occurrence Patterns (6 patterns)

These appeared once — worth noting but need more data to confirm as team-wide conventions.

| # | Pattern | Category | PR |
|---|---------|----------|-----|
| 10 | Stream large collections instead of loading all into memory | performance | #47170 |
| 11 | Verify new code paths cover same guardrails as existing paths | architecture | #47189 |
| 12 | Remove unused parameters from method signatures | code-organization | #47189 |
| 13 | Don't add validation that doesn't affect correctness | code-organization | #47200 |
| 14 | Use camelCase (lowercase-first) for argument names | naming | #47200 |
| 15 | Restrict internal class members to private visibility | code-organization | #47212 |

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| PRs analyzed | 20 |
| Human review threads | 77 |
| Human comments | 155 |
| Raw patterns extracted | 33 |
| Clusters after dedup | 15 |
| **Recurring patterns (2+ PRs)** | **9** |
| Single-occurrence patterns | 6 |
| Yield rate | 33 raw / 77 threads = **43%** |

### Category Distribution

| Category | Count |
|----------|-------|
| error-handling | 8 |
| performance | 6 |
| api-design | 5 |
| documentation | 3 |
| architecture | 3 |
| logging | 3 |
| code-organization | 3 |
| testing | 2 |
| naming | 1 |

### Top Reviewers by Pattern Enforcement

These reviewers are the primary "pattern enforcers" — the ones whose knowledge should be captured first.

(To be filled in during senior engineer review — reviewers should identify which patterns they enforce most and whether any are missing.)

---

## For Senior Engineer Blind Review

**Instructions for reviewers:**

For each of the 9 recurring patterns above, please rate:

1. **Accurate?** (Yes/No) — Does this correctly describe a pattern we enforce?
2. **Actionable?** (Yes/No) — Is the rule specific enough to be a useful guide for a new engineer?
3. **Priority** (High/Medium/Low) — How important is this pattern for code quality?
4. **Missing patterns?** — Are there recurring patterns you enforce that aren't captured here?

Please do this review **without** looking at the other reviewer's responses (blind review).
