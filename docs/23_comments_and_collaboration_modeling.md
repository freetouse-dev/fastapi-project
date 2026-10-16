# Step 23: Task Comments & Collaboration Modeling

## 1. Overview
In this step, we introduced threaded discussions and task collaboration by designing the `TaskComment` model (`task_comments` table). We established relationships linking comments to parent tasks and user authors, with automated timestamps for tracking comment edits.

---

## 2. Concepts Learned

### 2.1 Collaborative Discussions on Issues
- Tasks in tools like Jira or Asana require rich discussions (pull request links, QA reports, progress updates).
- Comments are scoped directly to a `task_id` and authored by an `author_id`.

### 2.2 Foreign Key Cascading vs Restriction
- `task_id`: `ondelete="CASCADE"` -> If a task is deleted, all associated comments are deleted automatically, maintaining database cleanliness.
- `author_id`: `ondelete="RESTRICT"` -> Prevents hard-deletion of users who have authored historical comments, preserving audit trails.

### 2.3 Edit Tracking (`created_at` vs `updated_at`)
- MySQL automatically updates `updated_at` via `onupdate=func.now()`.
- Client applications compare `created_at` and `updated_at` to render an `(edited)` indicator when comments are modified.

---

## 3. Implementation Details

- **Model File:** `src/project_management_api/models/comment.py`
  - `TaskComment` model with relationships to `Task` and `User` (author).
- **Package Exports:** Updated `src/project_management_api/models/__init__.py`.
- **Migration:** Generated and applied `b49eafb1751f_create_task_comments_table.py` with indexes on `task_id` and `author_id`.

---

## 4. Verification
Migration `b49eafb1751f` verified in `alembic/versions/` and applied to MySQL.
