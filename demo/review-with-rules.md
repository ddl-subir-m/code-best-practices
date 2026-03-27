Here's my review. I'm grouping by severity.

---

## High Severity

**1. Polling form state every 100ms instead of using `Form.useWatch`** (lines 60-68)

This is a performance disaster. Polling with `setInterval` every 100ms to read form state causes unnecessary re-renders and CPU load. Use Ant Design's `Form.useWatch` hook, which reactively subscribes to field changes. The `useEffect` dependency array also omits `form`, which is a bug.

**2. `any` types throughout** (lines 126, 195)

`sortedProjects` takes `any[]` and `ProjectDetail` receives `store: any`. Use proper types (`Project[]`, the actual store type). Per project rules: use `unknown` instead of `any` when the type isn't known.

**3. Inline styles instead of styled-components** (lines 41-48, 135-137)

Multiple components use inline `style` props with hardcoded hex colors and pixel values. Per project rules:
- Use styled-components for all styling
- Use `themeHelper` tokens for colors (not `#28A464`, `#C20A29`, `#F5F5F5`)
- Use the design system's spacing tokens instead of raw `16px`, `24px`, etc.
- Use the `Typography` component for text styling instead of custom `fontSize`/`fontFamily`

**4. Hardcoded route paths** (lines 104-106, 113-120)

Routes like `/projects/${projectId}/overview` are scattered as string literals. Use centralized route helpers (e.g., `core/routes.ts`) to avoid duplication and drift.

**5. Plain `<a href>` instead of React Router `<Link>`** (lines 115-118)

Anchor tags cause full page reloads. Use `<Link to={...}>` for in-app navigation.

---

## Medium Severity

**6. Direct `fetch()` call instead of shared API client** (lines 30-33)

Ad-hoc `fetch` bypasses shared auth headers, error handling, and base URL config from `@domino/api`. Also missing error handling — `resp.json()` is called without checking `resp.ok`.

**7. Raw MongoDB `_id` in domain interface** (lines 98-102)

`ProjectConfig._id` leaks persistence details. Use a domain-specific type like `DominoId` and name the field `id` or `projectId`.

**8. Importing `lodash` instead of `lodash-es`** (line 8)

`import lodash from "lodash"` pulls the entire library. Use named imports from `lodash-es` for tree-shaking:
```tsx
import { sortBy } from "lodash-es";
```

**9. Using `moment` directly** (lines 9, 150-152)

`moment` is a large, mutable library. Use the project's `useDate` hook (e.g., `getFromNowString`) for date formatting, which is the established shared utility.

**10. `useEffect` + `useState` to derive state** (lines 58-68)

`selectedEnv` is derived from form values. Per project rules: derive state from props/state directly or use `useMemo`, not `useEffect` + `useState` sync patterns.

**11. Hardcoded product name "Domino Data Lab"** (lines 21-22)

Hardcoded brand strings break white-label deployments. Use the app name getter so the name adapts per deployment.

**12. Prop drilling `store`** (line 195)

`ProjectDetail` receives `store` as a prop. If the store is globally accessible via a hook (e.g., `useStore`), consume it directly in the component.

---

## Low Severity

**13. Missing error status check on fetch** (line 32)

`resp.json()` is called without checking `resp.ok`. Network errors will produce confusing failures.

**14. Hardcoded config object** (lines 160-168)

`serviceConfig` with `featureFlags` baked into the source — these should come from platform config, not be hardcoded.

**15. Unnecessary React fragment / wrapping** — The `WelcomeBanner` and `CardContainer` use single-child `<div>` wrappers that may be unnecessary depending on usage context.

**16. Missing `form` in `useEffect` dependency array** (line 68) — ESLint `react-hooks/exhaustive-deps` would flag this. The dependency array lists `[selectedEnv]` but uses `form`.

---

**Summary**: The most impactful fixes are replacing the 100ms polling with `Form.useWatch`, replacing inline styles with styled-components + theme tokens, using the shared API client, and switching `<a>` to `<Link>`. These address performance, maintainability, and white-label correctness.
