# Step 18: Project Schemas, Business Logic & Project-Level RBAC

## 1. Overview
In this step, we built the Pydantic schemas (DTOs) and CRUD database layer for Projects. We implemented field-level validation for Project Keys, atomic transactions for project creation with automatic `PROJECT_LEAD` assignment, and role-scoped project visibility rules.

---

## 2. Concepts Learned

### 2.1 Project Key Validation (`@field_validator`)
- Uses Pydantic V2 `@field_validator("key")` to strip whitespace, force uppercase, and validate against `^[A-Z0-9]{2,10}$`.
- Enforces consistency across all Jira-style task identifiers (e.g. `PROJ`, `API`).

### 2.2 Atomic Project Creation
- Ensures that when a Project is persisted:
  1. The `Project` row is inserted with `status = ACTIVE` and `workspace_id`.
  2. `db.flush()` supplies `project.id`.
  3. A `ProjectMember` row is inserted linking `creator_id` as `PROJECT_LEAD`.
  4. Both operations commit together atomically.

### 2.3 Tiered Visibility (Workspace Role vs Project Member)
- Workspace `OWNER` or `ADMIN` can view and manage all projects within their workspace.
- Workspace `MEMBER` users only have visibility into projects where they are explicitly registered in `project_members`.

---

## 3. Implementation Details

- **Schemas:** `src/project_management_api/schemas/project.py`
  - `ProjectBase`, `ProjectCreate` (with key validator), `ProjectUpdate`, `ProjectResponse`, `ProjectMemberAdd`, `ProjectMemberResponse`.
- **Package Exports:** Updated `src/project_management_api/schemas/__init__.py`.
- **CRUD Operations:** `src/project_management_api/crud/project.py`
  - `get_project_by_key`, `get_project_by_id`, `create_project`, `get_projects_for_user`, `get_project_membership`, `get_project_members`, `add_project_member`.

---

## 4. Verification
Schemas and CRUD functions verified with typed annotations, database transaction commit boundaries, and scoping rules.
