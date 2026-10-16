# Step 22: Task API Endpoints & State Machine Workflow

## 1. Overview
In this step, we built the nested REST API endpoints for Task management under Projects. We tested end-to-end task creation with automatic sequential ticket keys (`MOB-1`, `MOB-2`), individual task lookups, state transitions (`TODO` -> `IN_PROGRESS`), and status-based Kanban filtering.

---

## 2. Concepts Learned

### 2.1 Nested Project Context Dependency (`require_project_context`)
- Chains multi-tenant authorization in a single reusable FastAPI dependency:
  1. Validates workspace existence and membership via `require_workspace_membership`.
  2. Resolves project by its unique key (`key="MOB"`) within the workspace.
  3. Enforces that non-admin users must be registered in `project_members`.
  4. Returns `(workspace, ws_membership, project)` directly to the task route.

### 2.2 Task State Transitions & Workflow Engine
- `PATCH /api/v1/workspaces/{slug}/projects/{key}/tasks/{task_number}`:
  - Supports partial updates via Pydantic (`exclude_unset=True`).
  - Enables moving tasks through lifecycle stages (`TODO` -> `IN_PROGRESS` -> `IN_REVIEW` -> `DONE`).
  - Enforces that any assigned user (`assignee_email`) must be an existing member of the parent workspace.

### 2.3 Query Parameter Filtering (Kanban Boards)
- Query parameters `?status=IN_PROGRESS` and `?priority=HIGH` allow clients to retrieve filtered task slices without loading unnecessary records.

---

## 3. Implementation Details

- **Router Module:** `src/project_management_api/api/v1/endpoints/tasks.py`.
- **Router Mounting:** Mounted on `api_router` in `src/project_management_api/api/v1/api.py` with prefix `/workspaces`.

---

## 4. Verification & Testing
```bash
# 1. Create first task
POST /api/v1/workspaces/alice-engineering/projects/MOB/tasks/
Payload: {"title": "Setup OAuth2 Login with Google", "priority": "HIGH", "status": "TODO"}
Response: 201 Created -> ticket_key: "MOB-1", task_number: 1

# 2. Create second task
POST /api/v1/workspaces/alice-engineering/projects/MOB/tasks/
Payload: {"title": "Design Profile Settings UI", "priority": "MEDIUM", "status": "TODO"}
Response: 201 Created -> ticket_key: "MOB-2", task_number: 2

# 3. Retrieve single task
GET /api/v1/workspaces/alice-engineering/projects/MOB/tasks/1
Response: 200 OK -> MOB-1 details

# 4. State transition (TODO -> IN_PROGRESS)
PATCH /api/v1/workspaces/alice-engineering/projects/MOB/tasks/1
Payload: {"status": "IN_PROGRESS"}
Response: 200 OK -> status: "IN_PROGRESS"

# 5. Filter tasks by status
GET /api/v1/workspaces/alice-engineering/projects/MOB/tasks/?status=IN_PROGRESS
Response: 200 OK -> returns only MOB-1
```
