Here's what a PR reviewer should flag:

---

### Critical Issues

**1. Polling form state every 100ms** (lines 60-68)
`setInterval` polling `form.getFieldsValue()` at 100ms is a performance disaster — it causes unnecessary re-renders and CPU churn. Use `Form.useWatch` instead, which reactively subscribes to field changes. The `useEffect` dependency array also omits `form`, which is a stale-closure bug.

**2. No error handling on fetch** (lines 30-33)
`fetchProjectFiles` calls `resp.json()` without checking `resp.ok`. A 4xx/5xx response will silently return an error body as if it were valid data. At minimum: check status and throw on failure.

**3. Ad-hoc `fetch` instead of `@domino/api`** (lines 30-33, 78-82)
Direct `fetch` calls bypass shared interceptors (auth headers, error normalization, retries). Use the shared API package so auth, base URL, and error handling are consistent.

### Design System Violations

**4. Direct Ant Design imports** (line 6)
Components should come from Domino's design system wrappers, not raw `antd`. The wrappers handle white-labeling, theming, and consistent behavior.

**5. Hardcoded product name** (lines 21-22)
`"Domino Data Lab"` and `"Domino"` are hardcoded strings. These must use the app-name getter to support white-labeling.

**6. Hardcoded colors and inline styles** (lines 41-50, 135-137)
Hex values like `#28A464`, `#C20A29`, `#F5F5F5` should use theme tokens via `themeHelper`. Inline styles should be `styled-components` for consistency and theming support. The hardcoded spacing values (`16px`, `24px`, `12px`) should use `spacing` design tokens.

### Architecture Issues

**7. Raw `_id` field in domain interface** (lines 98-106)
`_id` leaks MongoDB persistence details into the domain layer. Use a `DominoId` type alias to maintain the domain/persistence boundary.

**8. Hardcoded route paths** (lines 113-120)
Four different routes are string-interpolated inline. These should reference centralized route constants so renames don't break navigation silently. Also, `<a href>` tags cause full page reloads — use `<Link to>` from React Router.

**9. Prop-drilling the store** (lines 195-202)
`store` is passed as a prop when it's globally available. The component should call `useStore()` directly, which eliminates unnecessary coupling and simplifies the component tree.

**10. REST collection returns raw array** (lines 78-82)
API endpoints returning collections must use the standard wrapper format `{ totalCount, paginationDetails, items }` for consistent client-side pagination handling.

### Bundle / Dependency Issues

**11. `lodash` instead of `lodash-es`** (line 8)
Importing the full `lodash` bundle prevents tree-shaking. Use `lodash-es` or per-function imports (`lodash-es/sortBy`).

**12. `moment` instead of `useDate` hook** (lines 9, 150-152)
`moment` is a 300KB+ library that's deprecated. Use the project's `useDate` hook, which wraps a lighter date library and keeps formatting consistent.

**13. Upstream container images** (lines 89-90)
`python:3.11-slim` and `bitnami/spark:3.5` reference public registries. These should point to the internal registry (`quay.io/domino/...`) for supply-chain security and air-gapped deployments.

### Minor

**14. Microservice config overreach** (lines 160-168) — Feature flags and runtime config like `maxConcurrentJobs` belong in the parent platform (nucleus), not in a local service config file.

**15. `any` types** (lines 126, 195) — `projects: any[]` and `store: any` lose type safety. Define proper interfaces.
