# Step 24: Comment Schemas, CRUD & Moderation Endpoints

## 1. Overview
In this step, we built the schemas, CRUD logic, and REST API endpoints for task comments. We tested adding comments, listing comments chronologically with author profiles, and deleting comments with ownership and role-based moderation checks.

---

## 2. Concepts Learned

### 2.1 Deeply Nested Dependency Chains (`require_task_context`)
- Reusable composition pattern:
  ```
  require_workspace_membership
             │ (validates workspace tenant & user membership)
             ▼
  require_project_context
             │ (validates project key & project-level permissions)
             ▼
  require_task_context
             │ (fetches task by project-scoped task_number)
             ▼
  Comment Endpoint Handler
  ```
- Ensures complete security isolation without repetitive boilerplate in route handlers.

### 2.2 Fine-Grained Comment Moderation
- **Author Control:** A user can delete their own comments (`comment.author_id == current_user.id`).
- **Administrative Moderation:** Project Leads (`PROJECT_LEAD`) or Workspace Admins (`OWNER`/`ADMIN`) can delete inappropriate or stale comments.
- **Unauthorized Deletion:** Any other user receives HTTP `403 Forbidden`.

### 2.3 HTTP 204 No Content
- Standard REST status code for successful deletions where no JSON body needs to be returned to the client.

---

## 3. Implementation Details

- **Schemas File:** `src/project_management_api/schemas/comment.py`
  - `CommentBase`, `CommentCreate`, `CommentUpdate`, `CommentResponse` (with nested `UserResponse` author).
- **CRUD File:** `src/project_management_api/crud/comment.py`
  - `create_comment`, `get_comments_for_task`, `get_comment_by_id`, `delete_comment`.
- **Router Module:** `src/project_management_api/api/v1/endpoints/comments.py`.
- **Router Mounting:** Mounted on `api_router` in `src/project_management_api/api/v1/api.py`.

---

## 4. Verification & Testing
```bash
# 1. Post comment
POST /api/v1/workspaces/alice-engineering/projects/MOB/tasks/1/comments/
Payload: {"content": "I have created the Google Developer Console project..."}
Response: 201 Created -> comment id: 1 with author details

# 2. List comments
GET /api/v1/workspaces/alice-engineering/projects/MOB/tasks/1/comments/
Response: 200 OK -> [{"id": 1, "content": "...", "author": {"full_name": "Admin", ...}}]

# 3. Delete comment
DELETE /api/v1/workspaces/alice-engineering/projects/MOB/tasks/1/comments/1
Response: 204 No Content -> Successfully removed

# 4. Post replacement comment
POST /api/v1/workspaces/alice-engineering/projects/MOB/tasks/1/comments/
Response: 201 Created -> comment id: 2 assigned
```
