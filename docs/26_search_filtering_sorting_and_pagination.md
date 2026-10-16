# Step 26: Search, Filtering, Sorting & Pagination

## 1. Overview
In this step, we introduced scalable data-fetching capabilities to our task management API. We implemented a reusable generic Pydantic pagination model (`PaginatedResponse[T]`), keyword search across task titles and descriptions (`LIKE %search%`), dynamic multi-column sorting (ascending and descending), and page-based result chunking.

---

## 2. Concepts Learned

### 2.1 The Need for Pagination
- Without pagination, listing tasks from large enterprise projects loads thousands of database rows into application memory, degrades query performance, and slows client network transfers.
- **Offset-based pagination:**
  - `offset = (page - 1) * size`
  - `limit = size`
- Computes `total` records (before pagination) and derives `total_pages = ceil(total / size)`.

### 2.2 Generic Pydantic DTOs (`PaginatedResponse[Generic[T]]`)
- Instead of declaring separate pagination schemas for tasks, projects, and users, we defined a generic wrapper in `schemas/common.py`:
  ```python
  class PaginatedResponse(BaseModel, Generic[T]):
      items: list[T]
      total: int
      page: int
      size: int
      total_pages: int
  ```

### 2.3 Multi-Criteria Query Composition
- Composable SQLAlchemy queries:
  - **Search:** `or_(Task.title.ilike(pattern), Task.description.ilike(pattern))`.
  - **Filtering:** Optional filters for `status`, `priority`, and `assignee_id`.
  - **Sorting:** Safe dictionary-mapped column lookup (`task_number`, `title`, `status`, `priority`, `created_at`, `due_date`) with direction (`asc`/`desc`).

---

## 3. Implementation Details

- **Generic Schema:** `src/project_management_api/schemas/common.py`
  - `PaginatedResponse[T]` with factory helper `PaginatedResponse.create(...)`.
- **Package Exports:** Exported in `src/project_management_api/schemas/__init__.py`.
- **CRUD Query Engine:** `src/project_management_api/crud/task.py`
  - Replaced simple `all()` fetching with `get_tasks_paginated(...)`.
- **API Endpoint:** Enhanced `GET /{slug}/projects/{key}/tasks/` in `src/project_management_api/api/v1/endpoints/tasks.py`.

---

## 4. Verification & Testing
1. **Pagination Test (`?page=1&size=2`):**
   - Output: `{"items": [MOB-1, MOB-2], "total": 4, "page": 1, "size": 2, "total_pages": 2}`.
2. **Text Search Test (`?search=OAuth2`):**
   - Output: `{"items": [MOB-1], "total": 1, "page": 1, "size": 20, "total_pages": 1}`.
3. **Descending Sort Test (`?sort_by=task_number&sort_order=desc&size=2`):**
   - Output: Returned `MOB-4` followed by `MOB-3` with metadata preserved.
