Here's the review — organized by severity:

---

## High Severity

**1. Direct Ant Design imports (line 6)**
Import from Domino's design system wrappers, not directly from `antd`. Direct imports bypass white-label theming and any org-wide component overrides. Use the equivalent Domino components (e.g., `WaitSpinner` instead of `Spinner`).

**2. Hardcoded product name (lines 21-22)**
`"Welcome to Domino Data Lab"` and `"Domino helps you..."` must use the app name getter for white-label support. If this ships to a white-labeled deployment, the branding is wrong.

**3. Ad-hoc `fetch` call (line 31)**
Use `@domino/api` instead of raw `fetch`. The shared API package handles auth headers, base URL, error normalization, and retry logic. This bypasses all of that.

**4. Hardcoded hex colors (lines 42-47)**
`#28A464`, `#C20A29`, `#F5F5F5`, hardcoded `fontFamily` — all must come from theme tokens via `themeHelper`. This breaks when the theme changes and violates the design system.

**5. Polling `form.getFieldsValue` on a 100ms interval (lines 60-68)**
This is a performance problem. Replace with `Form.useWatch` which is reactive and doesn't require polling. The 100ms `setInterval` will cause unnecessary renders and is a code smell.

**6. Raw anchor tags for in-app navigation (lines 115-118)**
`<a href=...>` causes full page reloads. Use React Router `<Link to=...>` for SPA navigation. The `Link` import is already present (line 7) but unused.

**7. `lodash` instead of `lodash-es` (line 8, 127)**
`import lodash from "lodash"` pulls the entire library into the bundle. Use `import { sortBy } from "lodash-es"` for tree-shaking.

**8. `moment` usage (line 9, 151)**
`moment` is a 300KB+ library and is deprecated. Use the `useDate` hook per org convention. This also ensures consistent date formatting across the app.

---

## Medium Severity

**9. Hardcoded route paths (lines 115-118)**
`/projects/${projectId}/overview`, `/workspaces?projectId=...`, `/admin/hardware-tiers` — these should come from centralized route constants. Hardcoded paths break silently when routes change.

**10. Raw MongoDB `_id` in interface (line 99)**
Use `DominoId` domain type instead of exposing `_id: string`. Persistence details shouldn't leak into service interfaces — this couples the frontend to the DB schema.

**11. Prop-drilled store (line 195)**
`store` is passed as a prop instead of consumed directly via `useStore`. This creates unnecessary coupling between parent and child components and makes refactoring harder.

**12. REST endpoint returning raw array (lines 78-82)**
Collection endpoints must return `{ totalCount, paginationDetails, items }` wrapper format. A raw array prevents pagination and breaks client expectations.

**13. Container images pointing to upstream registries (lines 89-90)**
`python:3.11-slim` and `bitnami/spark:3.5` should reference the internal registry (e.g., `quay.io/domino/...`). Upstream images can be pulled/rate-limited and aren't scanned by your security pipeline.

---

## Low Severity

**14. Inline styles everywhere (lines 41-48, 135-137)**
Use `styled-components` per org convention. Inline styles can't use theme tokens, aren't reusable, and don't support pseudo-selectors or media queries.

**15. Hardcoded spacing values (lines 135-137)**
`margin: "16px"`, `padding: "24px"`, `gap: "8px"` — use `spacing` design tokens. The `margins` theme key is deprecated.

**16. Feature flags in local service config (lines 164-167)**
`enableNewUI`, `enableBatchProcessing` belong in the parent platform (nucleus), not in a local config object. Local config should only contain bootstrap settings.

**17. `useEffect` dependency array is incomplete (line 68)**
`[selectedEnv]` is listed but `form` is missing. This is a React hooks rule violation that can cause stale closures. (Moot if you replace with `Form.useWatch`, but worth noting.)

**18. No error handling on API calls (lines 31-33, 79)**
`fetchProjectFiles` calls `.json()` without checking `resp.ok`. A 4xx/5xx response will silently return an error body as if it were data. The `@domino/api` package would handle this — another reason to use it.
