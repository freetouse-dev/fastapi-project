# Step 27: Reports & Dashboard Analytics

## 1. Overview
In this step, we built an aggregation engine to provide real-time dashboard analytics for projects. Instead of loading and iterating over tasks in application memory, the backend issues high-performance SQL aggregate queries (`COUNT`, `GROUP BY`) to calculate total tasks, status breakdowns, priority breakdowns, overdue task counts, and completion percentages.

---

## 2. Concepts Learned

### 2.1 Database-Level Aggregation vs Application-Level Iteration
- Fetching 10,000 tasks and counting them with Python loops wastes memory and network bandwidth.
- SQL aggregation (`func.count()`, `group_by(Task.status)`) lets MySQL compute summaries directly on indexed columns, returning compact summary rows in milliseconds.

### 2.2 Project Health Metrics
- **Completion Rate:** `round((completed_tasks / total_tasks * 100), 2)`.
- **Status Distribution:** Maps counts across all statuses (`BACKLOG`, `TODO`, `IN_PROGRESS`, `IN_REVIEW`, `DONE`, `CANCELLED`).
- **Priority Distribution:** Tracks task distribution across `LOW`, `MEDIUM`, `HIGH`, `URGENT`.
- **Overdue Detection:** Counts non-completed tasks whose `due_date < NOW()`.

---

## 3. Implementation Details

- **Schemas:** `src/project_management_api/schemas/report.py`
  - `ProjectDashboardResponse` schema with status and priority distribution mappings.
- **CRUD Aggregation:** `src/project_management_api/crud/report.py`
  - `get_project_dashboard_metrics(db, project)`.
- **Endpoint:** Added `GET /{slug}/projects/{key}/dashboard` in `src/project_management_api/api/v1/endpoints/projects.py`.

---

## 4. Verification & Testing
1. **Initial State:**
   - Queried `GET .../projects/MOB/dashboard`:
     - `total_tasks: 4`, `completed_tasks: 0`, `completion_rate_percentage: 0.0%`.
2. **State Mutation:**
   - Moved task `MOB-1` to `status: DONE`.
3. **Recalculated Metrics:**
   - Queried `GET .../projects/MOB/dashboard`:
     - `completed_tasks: 1`
     - `completion_rate_percentage: 25.0%`
     - `tasks_by_status.DONE: 1`, `tasks_by_status.IN_PROGRESS: 1`, `tasks_by_status.TODO: 2`.
