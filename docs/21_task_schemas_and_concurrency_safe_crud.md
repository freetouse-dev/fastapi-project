# Step 21: Task Schemas & Concurrency-Safe Sequence Generation

## 1. Overview
In this step, we built the Pydantic schemas (DTOs) and database CRUD operations for Task management. We implemented pessimistic row-level locking (`with_for_update()`) to guarantee concurrency-safe, gap-free Jira ticket numbering (`MOB-1`, `MOB-2`), flexible attribute updates, and multi-criteria task filtering.

---

## 2. Concepts Learned

### 2.1 Concurrency & Race Conditions in Ticket Numbering
- **The Problem:** In high-traffic environments, multiple developers or automated bots may create tasks at the exact same millisecond. Simple `SELECT MAX()` without locking causes two transactions to read the same max number and attempt duplicate insertions.
- **The Solution:** Pessimistic Row Locking (`with_for_update()`).
  - `db.query(Project).filter(Project.id == project_id).with_for_update().first()`
  - Acquires an exclusive write lock on the parent project row for the duration of the transaction.
  - Forces concurrent task creation requests to queue sequentially, guaranteeing strictly incrementing, non-colliding numbers (`1, 2, 3...`).

### 2.2 Dynamic Task Filtering
- `get_tasks_for_project` builds composable SQLAlchemy queries based on optional request query parameters (`status`, `priority`, `assignee_id`), allowing clients to power Kanban boards, sprint backlogs, and user assignment filters.

### 2.3 Partial Updates (`exclude_unset=True`)
- When updating tasks (`PATCH/PUT`), only fields explicitly provided by the client are mutated (`task_in.model_dump(exclude_unset=True)`), preventing accidental overwrites of existing task descriptions, statuses, or deadlines.

---

## 3. Implementation Details

- **Schemas File:** `src/project_management_api/schemas/task.py`
  - `TaskBase`, `TaskCreate`, `TaskUpdate`, `TaskResponse`.
- **Package Exports:** Updated `src/project_management_api/schemas/__init__.py`.
- **CRUD File:** `src/project_management_api/crud/task.py`
  - `get_next_task_number`, `create_task` (with pessimistic lock), `get_task_by_number`, `get_tasks_for_project`, `update_task`.

---

## 4. Verification
Schemas and CRUD methods verified with type annotations, `with_for_update()` synchronization, and Pydantic V2 `from_attributes=True` integration.
