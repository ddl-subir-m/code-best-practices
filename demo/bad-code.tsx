// Demo file: deliberately violates patterns mined from cerebrotech/domino PR reviews.
// Ask Claude to review this file WITH and WITHOUT the mined rules to see the difference.

import { useState } from "react";
import lodash from "lodash";
import { fetchProject, fetchMembers } from "../../api/projects";
import { Button } from "antd";
import { WaitSpinner } from "@domino/ui";

// --- Violation: constructor-dependency-injection (3x) ---
class ProjectService {
  private db = new MongoClient("mongodb://localhost:27017");
  private cache = new RedisClient();

  async getProject(id: string) {
    return this.db.collection("projects").findOne({ _id: id });
  }
}

// --- Violation: handle-absent-entities (3x) ---
async function getProjectOwner(projectId: string) {
  const project = await fetchProject(projectId);
  // If project was deleted, this will throw a cryptic "Cannot read property 'ownerId' of null"
  const owner = await fetchUser(project.ownerId);
  return owner.name;
}

// --- Violation: fail-explicitly (3x) ---
function parseExecutionStatus(status: string): string {
  switch (status) {
    case "running":
      return "In Progress";
    case "completed":
      return "Done";
    case "failed":
      return "Error";
    default:
      return ""; // silently returns empty string for unknown statuses
  }
}

// --- Violation: push-sorting-filtering-to-db (3x) ---
async function getTopProjects() {
  const allProjects = await db.query("SELECT * FROM projects");
  const sorted = lodash.sortBy(allProjects, "lastActivity");
  return sorted.slice(0, 10);
}

// --- Violation: actionable-user-error-messages (2x) ---
async function launchWorkspace(config: WorkspaceConfig) {
  try {
    await api.post("/v4/workspaces", config);
  } catch (err) {
    throw new Error(`Failed: ${err.message}`);
  }
}

// --- Violation: use-object-params-for-multi-arg-functions (2x) ---
function createEnvironment(
  name: string,
  dockerImage: string,
  pluginVersions: string[],
  description: string,
  visibility: string,
  owner: string,
) {
  // ...
}

// --- Violation: await-async-functions-in-try-catch (2x) ---
async function saveAndNotify(data: any) {
  try {
    saveToDatabase(data); // missing await — error won't be caught!
    sendNotification(data.userId);
  } catch (err) {
    console.error("Save failed", err);
  }
}

// --- Violation: pass-function-references-directly (3x) ---
const ProjectList = ({ projects, onSelect }) => {
  return (
    <ul>
      {projects.map((p, idx) => (
        // Violation: use-unique-ids-as-react-list-keys (2x) — using array index as key
        <li key={idx} onClick={() => onSelect(p.id)}>
          {/* Violation: aria-labels-must-be-human-readable (2x) */}
          <Button
            aria-label={`select-project-${p.id}`}
            onClick={() => onSelect(p.id)}
            style={{ color: "blue", padding: "8px 16px", borderRadius: "4px" }}
          >
            {p.name}
          </Button>
        </li>
      ))}
    </ul>
  );
};

// --- Violation: use-ref-for-non-reactive-values (2x) ---
const Timer = () => {
  const [intervalId, setIntervalId] = useState<number | null>(null);
  // intervalId never renders in the UI — should be useRef

  const start = () => {
    const id = setInterval(() => console.log("tick"), 1000);
    setIntervalId(id);
  };

  const stop = () => {
    if (intervalId) clearInterval(intervalId);
    setIntervalId(null);
  };

  return (
    <div>
      <button onClick={start}>Start</button>
      <button onClick={stop}>Stop</button>
    </div>
  );
};

// --- Violation: logging-level-correctness (3x) ---
function processJob(job: Job) {
  console.info(`Processing job ${job.id}`); // routine message should be debug
  console.warn(`Job ${job.id} is queued`); // not a warning condition
  // ...
}

// --- Violation: no-commented-out-code (2x) ---
// function oldImplementation() {
//   const result = await legacyApi.fetch();
//   return transform(result);
// }

// --- Violation: use-strict-equality (2x) ---
function isActive(status: string) {
  if (status == "active") return true;
  if (status == null) return false;
  return status == "1";
}
