# Step 16: Workspaces, Membership, and Multi-Tenant RBAC Architecture

## 1. Overview
This document explains the mental model and business reasoning behind Users, Workspaces, Workspace Members, and the Role-Based Access Control (RBAC) API endpoints built for multi-tenancy.

---

## 2. Core Entities Explained

### 2.1 The User (`users` table)
- **What is it?** A person or identity with credentials (email, hashed password) who can authenticate to the system.
- **Why do we need it?** Establishes authentication (who is making the request).
- **Scope:** Global across the entire application.

### 2.2 The Workspace (`workspaces` table)
- **What is it?** An isolated organization, company, or department boundary (similar to a Slack workspace or Jira organization).
- **Why do we need it?** Provides multi-tenancy. Projects, tasks, and discussions belong to a workspace. Users in Company A cannot see data in Company B.
- **Key attributes:** `name`, `slug` (URL-friendly unique identifier like `alice-engineering`), and `owner_id`.

### 2.3 The WorkspaceMember (`workspace_members` table)
- **What is it?** The association record linking a `User` to a `Workspace` with a specific `WorkspaceRole` (`OWNER`, `ADMIN`, `MEMBER`).
- **Why do we need it?** A user can belong to multiple workspaces, and a workspace has multiple users. A user may be an `OWNER` in their own startup workspace, but only a `MEMBER` in a client's workspace.
- **Database Constraint:** `UniqueConstraint("workspace_id", "user_id")` ensures a user cannot be added twice to the same workspace.

---

## 3. Entity Relationships

```
┌──────────────────┐               ┌──────────────────────────────┐               ┌──────────────────┐
│      User        │ 1           * │       WorkspaceMember        │ *           1 │    Workspace     │
├──────────────────┤───────────────├──────────────────────────────┤───────────────├──────────────────┤
│ id (PK)          │               │ id (PK)                      │               │ id (PK)          │
│ email            │               │ user_id (FK -> users.id)     │               │ name             │
│ full_name        │               │ workspace_id (FK -> ws.id)   │               │ slug (unique)    │
│ hashed_password  │               │ role (OWNER / ADMIN / MEMBER)│               │ owner_id (FK)    │
└──────────────────┘               └──────────────────────────────┘               └──────────────────┘
```

---

## 4. API Endpoints & Business Purpose

### 4.1 `POST /api/v1/workspaces/` (Create Workspace)
- **Purpose:** Allows an authenticated user to start a new workspace.
- **Atomic Business Logic:**
  1. Creates the `Workspace` row with `owner_id = current_user.id`.
  2. Generates a unique `slug` (e.g. `alice-engineering`).
  3. Automatically inserts a `WorkspaceMember` row assigning the creator as `OWNER`.
  4. Both operations commit together in a single transaction.

### 4.2 `GET /api/v1/workspaces/` (List My Workspaces)
- **Purpose:** Returns only the workspaces where `current_user` is a member.
- **Multi-Tenancy Guard:** Uses a database `JOIN` with `workspace_members` filtered by `user_id == current_user.id`. Users never see other tenants' workspaces.

### 4.3 `GET /api/v1/workspaces/{slug}` (Get Workspace Details)
- **Purpose:** Fetches a workspace using its URL-friendly slug.
- **Security Guard (`require_workspace_membership`):** Verifies the workspace exists (404 if not) and checks that `current_user` is a member (403 Forbidden if not).

### 4.4 `GET /api/v1/workspaces/{slug}/members` (List Workspace Members)
- **Purpose:** Lists all users collaborating inside this workspace alongside their assigned roles.

### 4.5 `POST /api/v1/workspaces/{slug}/members` (Invite / Add Member)
- **Purpose:** Adds a user to the workspace by their registered email.
- **RBAC Guard:** Only users with `OWNER` or `ADMIN` roles in that workspace can invite new members. `MEMBER` attempts return `403 Forbidden`.
