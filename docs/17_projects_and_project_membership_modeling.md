# Step 17: Projects & Project Membership Modeling

## 1. Overview
In this step, we designed and implemented the database entities for **Projects** and **Project Membership** (`projects` and `project_members`). This establishes the second tier in our multi-tenant hierarchy (Workspace -> Projects -> Tasks).

---

## 2. Concepts Learned

### 2.1 The Project Entity & Workspace Scoping
- In tools like Jira and Asana, projects organize work for teams within an organization.
- Projects are strictly scoped to a `workspace_id`.
- Foreign key cascading (`ondelete="CASCADE"`) ensures that deleting a workspace automatically cleans up its associated projects.

### 2.2 The Project Key (The "Jira Key")
- A short uppercase identifier (e.g. `PROJ`, `MOB`, `API`).
- Used as the prefix for all tasks created under this project (e.g., `PROJ-1`, `PROJ-2`).
- **Composite Unique Constraint:** `UniqueConstraint("workspace_id", "key", name="uq_workspace_project_key")` guarantees that keys are unique within a single workspace, while allowing different workspaces to independently use the same key.

### 2.3 Project-Level RBAC (`ProjectRole`)
- Not all workspace members need equal access to every project.
- Roles:
  - `PROJECT_LEAD`: Full control over project settings, archiving, and project membership.
  - `CONTRIBUTOR`: Can create, edit, assign, and resolve tasks.
  - `VIEWER`: Read-only access to project boards and tasks.
- Association object `ProjectMember` with `UniqueConstraint("project_id", "user_id")` prevents duplicate memberships.

---

## 3. Implementation Details

- **Model File:** `src/project_management_api/models/project.py`
  - `ProjectStatus` enum (`ACTIVE`, `ARCHIVED`, `COMPLETED`).
  - `ProjectRole` enum (`PROJECT_LEAD`, `CONTRIBUTOR`, `VIEWER`).
  - `Project` entity with relationships to `Workspace`, `User` (creator), and `ProjectMember`.
  - `ProjectMember` association entity.
- **Package Exports:** Updated `src/project_management_api/models/__init__.py`.
- **Migration:** Generated and applied `a1c3f5a811d4_create_projects_and_project_members_.py`.

---

## 4. Verification & Testing
Migration verified in `alembic/versions/` and models validated with typed `Mapped` columns, composite uniqueness, and cascade policies.
