# Step 20: Task Management Modeling & Lifecycle State Machine

## 1. Overview
In this step, we introduced the core heart of our project management platform: the **Task** model (`tasks` table). We established task lifecycle workflow states, priority tiers, assignees, deadlines, and Jira-style scoped ticket keys (`{project_key}-{task_number}`).

---

## 2. Concepts Learned

### 2.1 Jira Ticket Numbering Pattern
- Rather than exposing global database primary keys (`id=142`), tasks are identified by their human-readable project ticket identifier (e.g. `MOB-1`, `MOB-2`).
- Each task maintains a sequential `task_number` scoped to its `project_id`.
- Composite unique constraint: `UniqueConstraint("project_id", "task_number", name="uq_project_task_number")`.

### 2.2 Task Lifecycle Stages & Enums
- **Status Enum (`TaskStatus`):**
  - `BACKLOG`: Unplanned work ideas.
  - `TODO`: Planned and queued.
  - `IN_PROGRESS`: Actively underway.
  - `IN_REVIEW`: Quality verification / peer review.
  - `DONE`: Completed.
  - `CANCELLED`: Closed without implementation.
- **Priority Enum (`TaskPriority`):**
  - `LOW`, `MEDIUM`, `HIGH`, `URGENT`.

### 2.3 Foreign Key Cascades & Nullability
- `project_id`: `ondelete="CASCADE"` -> If a project is removed, its tasks are removed automatically.
- `creator_id`: `ondelete="RESTRICT"` -> A user who authored tasks cannot be hard-deleted, preserving audit history.
- `assignee_id`: `ondelete="SET NULL"` -> If an assigned user is removed from the system, the task is safely unassigned rather than deleted.

---

## 3. Implementation Details

- **Model File:** `src/project_management_api/models/task.py`
  - `TaskStatus` and `TaskPriority` enums.
  - `Task` entity with relationships to `Project`, `User` (creator), and `User` (assignee).
  - Derived `@property def ticket_key` (e.g., `MOB-1`).
- **Package Exports:** Updated `src/project_management_api/models/__init__.py`.
- **Migration:** Generated and applied `1b63f5b5e93e_create_tasks_table.py` with indexes on `project_id`, `status`, `priority`, and `assignee_id`.

---

## 4. Verification & Testing
```bash
uv run alembic current
```
Output:
`1b63f5b5e93e (head)` confirming the `tasks` table is active in MySQL.
