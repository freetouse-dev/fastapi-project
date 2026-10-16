# Step 25: Task Activity History & Audit Logging

## 1. Overview
In this step, we designed and implemented automated audit logging for tasks. Every significant event—task creation, status progression, priority adjustment, reassignment, or title change—is captured in the `task_activities` table with `old_value`, `new_value`, the acting user (`actor_id`), and an exact timestamp.

---

## 2. Concepts Learned

### 2.1 The Audit Trail Pattern
- High-integrity project management tools (Jira, Asana, Linear) require an immutable activity log.
- Rather than overwriting state silently, changes generate event records capturing:
  - `action`: e.g. `TASK_CREATED`, `STATUS_CHANGED`, `PRIORITY_CHANGED`, `ASSIGNEE_CHANGED`.
  - `field_name`: Field that was modified.
  - `old_value` and `new_value`: Values before and after the modification.
  - `actor_id`: User who initiated the change.

### 2.2 Atomic Logging in CRUD Operations
- `create_task()` automatically emits a `TASK_CREATED` record inside the same transaction.
- `update_task()` compares the incoming delta against current attributes (`status != db_task.status`, `priority != db_task.priority`) and inserts individual audit entries atomically before committing.

---

## 3. Implementation Details

- **Model File:** `src/project_management_api/models/activity.py`
  - `ActivityAction` enum.
  - `TaskActivity` model with foreign keys to `tasks.id` (cascade delete) and `users.id` (restrict delete).
- **Migration:** Generated and applied `97c4eb71a7fe_create_task_activities_table.py`.
- **Schemas:** Created `src/project_management_api/schemas/activity.py` defining `TaskActivityResponse` with nested `UserResponse` actor.
- **CRUD:**
  - Created `src/project_management_api/crud/activity.py` with `log_activity` and `get_activities_for_task`.
  - Updated `src/project_management_api/crud/task.py` to automatically record audit events on creation and update.
- **Endpoint:** Added `GET /{slug}/projects/{key}/tasks/{task_number}/activities/` to `src/project_management_api/api/v1/endpoints/tasks.py`.

---

## 4. Verification & Testing
1. **Created Task:** `POST .../tasks/` -> Created task `MOB-4` (`id: 5`).
2. **Updated Task:** `PATCH .../tasks/4` with `status: IN_PROGRESS`, `priority: URGENT`.
3. **Queried Activities:** `GET .../tasks/4/activities/` returned:
   ```json
   [
     {"action": "TASK_CREATED", "new_value": "Audit Trail Feature Test"},
     {"action": "STATUS_CHANGED", "field_name": "status", "old_value": "TODO", "new_value": "IN_PROGRESS"},
     {"action": "PRIORITY_CHANGED", "field_name": "priority", "old_value": "MEDIUM", "new_value": "URGENT"}
   ]
   ```
