Here are the issues a PR reviewer would flag, grouped by severity:

---

## High Severity

**1. Inline styles instead of styled-components** (lines 41-50, 135-137)
`StatusBadge` and `CardContainer` use inline `style={}`. Use styled-components for reusability, theming support, and consistency. Inline styles bypass the theme and can't respond to white-label overrides.

**2. Hardcoded hex colors** (lines 42-43)
`#28A464`, `#C20A29`, `#F5F5F5` should be palette tokens from the design system (e.g., `palette.green600`, `palette.red600`). Hardcoded colors break white-labeling and diverge from the design system. If no token matches, flag it to UX.

**3. Hardcoded font-family** (line 48)
`fontFamily: "Arial, sans-serif"` bypasses the design system typography. Use the `Typography` component or theme font tokens from Storybook foundations.

**4. Polling `form.getFieldsValue()` every 100ms** (lines 60-68)
This is a performance anti-pattern. Use `Form.useWatch` to reactively subscribe to form field changes instead of a `setInterval` poll. Also, the `useEffect` dependency array is missing `form`, which is a stale closure bug.

**5. Hardcoded route paths** (lines 115-118)
Paths like `/projects/${projectId}/overview` are scattered inline. Use centralized route helpers (e.g., `getProjectPath(projectId)`) so route changes propagate from a single source of truth.

**6. `<a href>` instead of `<Link to>`** (lines 115-118)
Plain anchor tags cause full page reloads. Use React Router's `<Link>` (already imported on line 7 but unused) for client-side navigation.

**7. Raw `fetch()` instead of shared API client** (line 31)
Use `@domino/api` or the project's shared API package. Raw `fetch` skips centralized auth headers, error handling, and base URL resolution.

**8. No error handling on API call** (lines 30-33)
`resp.json()` is called without checking `resp.ok`. A 404/500 will silently return an error body parsed as "valid" data.

---

## Medium Severity

**9. `any` types** (lines 126, 195)
`projects: any[]` and `store: any` defeat TypeScript's purpose. Use proper types or `ReturnType<typeof fn>` to derive them.

**10. Prop drilling store** (line 195)
`ProjectDetail` receives `store` as a prop. If a global store hook (`useStore`) exists, consume it directly in the component to avoid threading it through parent components.

**11. Hardcoded spacing values** (lines 135-137)
`margin: "16px"`, `padding: "24px"`, `gap: "8px"` should use the design system's spacing tokens via `themeHelper`.

**12. `lodash` import instead of `lodash-es`** (line 8)
Importing the full `lodash` bundle prevents tree-shaking. Use `import { sortBy } from "lodash-es"` or `import sortBy from "lodash/sortBy"`.

**13. `moment` instead of `useDate` hook** (lines 9, 151)
`moment` is a heavy dependency (300KB+). The project has a `useDate` hook with shared formatting helpers like `getFromNowString`. Use that instead.

**14. `_id` field leaking persistence details** (line 99)
`_id` is a MongoDB implementation detail. Use a domain-level identifier like `id: DominoId` in the interface to maintain proper layering.

**15. Hardcoded product name** (lines 21-22)
"Domino Data Lab" and "Domino" are hardcoded. Use the white-label app name getter so the string adapts per deployment.

**16. Unused import** (line 7)
`Link` is imported but never used (the nav uses `<a>` tags). Either use it or remove it — though the fix is to actually use `<Link>`.

---

## Low Severity

**17. Hardcoded container image references** (lines 89-90)
`python:3.11-slim` and `bitnami/spark:3.5` point to upstream registries. Default images should reference the organization's internal registry.

**18. `sortedProjects` defined as a const arrow function at module scope** (line 126)
This is fine functionally (correctly outside the component body), but the `any[]` type needs fixing.

**19. Magic numbers in config** (lines 161-168)
`maxConcurrentJobs: 10`, `defaultTimeout: 30000`, `retryAttempts: 3` should either be named constants or pulled from a centralized platform configuration, not hardcoded in a service config object.

**20. Missing `form` in useEffect deps** (line 68)
`[selectedEnv]` is incomplete — `form` is also read inside the effect. This is a React hooks lint violation that can cause stale closures.
