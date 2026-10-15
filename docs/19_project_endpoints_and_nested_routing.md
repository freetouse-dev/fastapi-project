# Step 19: Projects API Endpoints & Nested REST Routing

## 1. Overview
In this step, we built the nested REST API endpoints for Projects under Workspaces. We verified automatic project key capitalization, workspace role enforcement, project listing, and automatic `PROJECT_LEAD` assignment.

---

## 2. Concepts Learned

### 2.1 Nested REST Resource Design
- Projects belong to a Workspace:
  - `POST /api/v1/workspaces/{slug}/projects/`: Create project inside tenant.
  - `GET  /api/v1/workspaces/{slug}/projects/`: List projects inside tenant.
  - `GET  /api/v1/workspaces/{slug}/projects/{key}`: Retrieve project by its Jira-style key.
  - `GET  /api/v1/workspaces/{slug}/projects/{key}/members`: List project contributors.
  - `POST /api/v1/workspaces/{slug}/projects/{key}/members`: Add workspace member to project.

### 2.2 Hierarchical Authorization Guards
1. **Workspace Guard:** `require_workspace_membership` verifies the user belongs to `{slug}`.
2. **Project Creation Guard:** Verifies the user holds `OWNER` or `ADMIN` clearance in the workspace.
3. **Project Member Invitation Guard:** Enforces that the invited user must already be a member of the workspace before being assigned to an internal project.

---

## 3. Implementation Details

- **Router Module:** `src/project_management_api/api/v1/endpoints/projects.py`.
- **Router Mounting:** Mounted on `api_router` in `src/project_management_api/api/v1/api.py` with prefix `/workspaces`.

---

## 4. Verification & Testing
```bash
# 1. Project creation with lowercase key "mob"
POST /api/v1/workspaces/customer-portal-development/projects/
Payload: {"name": "Mobile Application", "key": "mob", "description": "iOS and Android client development"}
Response: 201 Created -> Key automatically uppercase: "MOB", status: "ACTIVE"

# 2. List projects
GET /api/v1/workspaces/customer-portal-development/projects/
Response: 200 OK -> [{"name": "Mobile Application", "key": "MOB", ...}]

# 3. Project membership check
GET /api/v1/workspaces/customer-portal-development/projects/MOB/members
Response: 200 OK -> [{"role": "PROJECT_LEAD", "user": {"email": "mary@gmail.com", ...}}]
```
