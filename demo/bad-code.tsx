// Demo file: deliberately violates Domino-specific patterns mined from PR reviews.
// These are patterns Claude would NOT catch without the mined rules.
// Ask Claude to review this file WITH and WITHOUT the mined rules to see the difference.

import React, { useState, useEffect } from "react";
import { Button, Spinner, Form, Select, Menu, Tag, Tooltip, Modal } from "antd";
import { Link } from "react-router-dom";
import lodash from "lodash";
import moment from "moment";

// ============================================================
// 1. Direct Ant Design imports instead of Domino design system
//    Rule: "Import UI components from Domino's design system wrappers, not directly from antd"
//    Rule: "Use white-label-aware UI components (e.g., WaitSpinner) instead of brand-specific ones"
// ============================================================

// 2. Hardcoded product name instead of white-label getter
//    Rule: "Never hard-code the product name (e.g., 'Domino') in UI strings; always use the app name getter"
const WelcomeBanner = () => (
  <div>
    <h1>Welcome to Domino Data Lab</h1>
    <p>Domino helps you run experiments faster.</p>
  </div>
);

// ============================================================
// 3. Ad-hoc API call instead of @domino/api package
//    Rule: "Expose service endpoints through the shared API package (@domino/api)"
// ============================================================
async function fetchProjectFiles(projectId: string) {
  const resp = await fetch(`/v4/projects/${projectId}/files`);
  return resp.json();
}

// ============================================================
// 4. Hardcoded colors instead of theme tokens
//    Rule: "Use theme helper tokens and design system constants for styling values"
//    Rule: "Access colors through themeHelper utility rather than hardcoding hex values"
// ============================================================
const StatusBadge = ({ status }: { status: string }) => (
  <span style={{
    color: status === "active" ? "#28A464" : "#C20A29",
    backgroundColor: "#F5F5F5",
    padding: "4px 8px",
    borderRadius: "4px",
    fontSize: "12px",
    fontFamily: "Arial, sans-serif",
  }}>
    {status}
  </span>
);

// ============================================================
// 5. Using Form.getFieldsValue instead of Form.useWatch
//    Rule: "Use Ant Design's Form.useWatch hook instead of formInstance.getFieldsValue()"
// ============================================================
const EnvironmentSelector = ({ form }) => {
  const [selectedEnv, setSelectedEnv] = useState("");

  useEffect(() => {
    const interval = setInterval(() => {
      const values = form.getFieldsValue();
      if (values.environment !== selectedEnv) {
        setSelectedEnv(values.environment);
      }
    }, 100);
    return () => clearInterval(interval);
  }, [selectedEnv]);

  return <div>Selected: {selectedEnv}</div>;
};

// ============================================================
// 6. REST collection without standard wrapper format
//    Rule: "REST API endpoints returning collections must use a consistent wrapper
//           format with totalCount, paginationDetails, and items array"
// ============================================================
async function listDataSources(projectId: string) {
  const sources = await api.get(`/v4/projects/${projectId}/dataSources`);
  // Returns raw array instead of { totalCount, paginationDetails, items }
  return sources;
}

// ============================================================
// 7. Container image pointing to upstream instead of internal registry
//    Rule: "Default container image references should point to the organization's
//           own registry (e.g., quay.io/domino/) rather than upstream third-party images"
// ============================================================
const DEFAULT_IMAGE = "python:3.11-slim";
const SPARK_IMAGE = "bitnami/spark:3.5";

// ============================================================
// 8. Using raw ObjectId instead of DominoId domain type
//    Rule: "Use domain-level identifiers (e.g., DominoId) in service interfaces
//           and keep persistence-specific details (e.g., MongoDB ObjectId) confined
//           to the persistence implementation layer"
// ============================================================
interface ProjectConfig {
  _id: string; // raw MongoDB ObjectId string
  ownerId: string;
  environmentId: string;
}

function getProjectUrl(config: ProjectConfig) {
  return `/projects/${config._id}/overview`;
}

// ============================================================
// 9. Hardcoded route paths instead of centralized route constants
//    Rule: "Route paths should not be hardcoded in component files;
//           use constants or a route configuration"
// ============================================================
const ProjectNav = ({ projectId }: { projectId: string }) => (
  <nav>
    <a href={`/projects/${projectId}/overview`}>Overview</a>
    <a href={`/projects/${projectId}/files`}>Files</a>
    <a href={`/workspaces?projectId=${projectId}`}>Workspaces</a>
    <a href="/admin/hardware-tiers">Hardware Tiers</a>
  </nav>
);

// ============================================================
// 10. Using lodash instead of lodash-es (tree-shaking)
//     Rule: "Import from lodash-es instead of lodash to enable tree-shaking"
// ============================================================
const sortedProjects = (projects: any[]) =>
  lodash.sortBy(projects, "lastActivity");

// ============================================================
// 11. Using deprecated margins theme key and hardcoded spacing
//     Rule: "Use the `spacing` design token key for all spacing values;
//            the `margins` theme key is deprecated"
// ============================================================
const CardContainer = () => (
  <div style={{ margin: "16px", padding: "24px", gap: "8px" }}>
    <div style={{ marginBottom: "12px" }}>Content</div>
  </div>
);

// ============================================================
// 12. Using inline styles instead of styled-components
//     Rule: "Use styled-components for styling instead of inline styles"
// ============================================================

// ============================================================
// 13. Using moment instead of useDate hook
//     Rule: "Use the `useDate` hook for all date operations instead of
//            calling date libraries (dayjs, moment) directly"
// ============================================================
function formatLastRun(timestamp: string) {
  return moment(timestamp).format("YYYY-MM-DD HH:mm");
}

// ============================================================
// 14. Microservice config not in parent platform
//     Rule: "A microservice's local config file should only contain settings
//            required to bootstrap the service; all other settings must be defined
//            in the parent platform (nucleus)"
// ============================================================
const serviceConfig = {
  maxConcurrentJobs: 10,
  defaultTimeout: 30000,
  retryAttempts: 3,
  featureFlags: {
    enableNewUI: true,
    enableBatchProcessing: false,
  },
};

// ============================================================
// 15. Storybook using deprecated MDX format
//     Rule: "Write Storybook stories using CSF3 format instead of deprecated MDX format"
// ============================================================
// (This would be in a .stories.mdx file - noted here for the demo)

// ============================================================
// 16. Missing DominoContext extraction in controller
//     Rule: "All controller methods should extract DominoContext via
//            `implicit val dc: DominoContext = request.dominoContext`"
// ============================================================

// ============================================================
// 17. Using anchor tags instead of React Router Link
//     Rule: "Use React Router Link components for in-app navigation
//            instead of plain anchor tags"
// ============================================================
// (See ProjectNav component above using <a href> instead of <Link to>)

// ============================================================
// 18. Consuming store via prop drilling instead of useStore
//     Rule: "When a store (e.g., useStore) is globally accessible, consume
//            it directly in the component that needs it rather than threading
//            it through router or parent props"
// ============================================================
const ProjectDetail = ({ store, projectId }: { store: any; projectId: string }) => {
  const user = store.getState().currentUser;
  return (
    <div>
      <h2>{user.name}'s Project</h2>
    </div>
  );
};

// ============================================================
// 19. Not using existing shared test helpers
//     Rule: "Use existing shared test utility helpers (e.g., layoutTestUtils.checkBreadcrumbs
//            from @domino/test-utils) instead of reimplementing common test assertions inline"
// ============================================================

// ============================================================
// 20. Using DominoId.toString instead of proper accessor
//     Rule: "Do not call toString on strongly-typed identifiers;
//            use the appropriate accessor or conversion method"
// ============================================================
