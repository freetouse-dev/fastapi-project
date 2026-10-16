from datetime import datetime, timezone
from sqlalchemy import func
from sqlalchemy.orm import Session

from project_management_api.models.project import Project
from project_management_api.models.task import Task, TaskPriority, TaskStatus
from project_management_api.schemas.report import ProjectDashboardResponse


def get_project_dashboard_metrics(db: Session, project: Project) -> ProjectDashboardResponse:
    """Computes aggregate analytics and metrics for a project."""
    now = datetime.now(timezone.utc)

    # 1. Total tasks
    total_tasks = db.query(func.count(Task.id)).filter(Task.project_id == project.id).scalar() or 0

    # 2. Status distribution
    status_counts = (
        db.query(Task.status, func.count(Task.id))
        .filter(Task.project_id == project.id)
        .group_by(Task.status)
        .all()
    )
    status_map: dict[TaskStatus, int] = {s: 0 for s in TaskStatus}
    for status_enum, count in status_counts:
        status_map[status_enum] = count

    # 3. Priority distribution
    priority_counts = (
        db.query(Task.priority, func.count(Task.id))
        .filter(Task.project_id == project.id)
        .group_by(Task.priority)
        .all()
    )
    priority_map: dict[TaskPriority, int] = {p: 0 for p in TaskPriority}
    for priority_enum, count in priority_counts:
        priority_map[priority_enum] = count

    # 4. Completed tasks
    completed_tasks = status_map.get(TaskStatus.DONE, 0)

    # 5. Completion rate percentage
    completion_rate = round((completed_tasks / total_tasks * 100), 2) if total_tasks > 0 else 0.0

    # 6. Overdue tasks (due_date past now and not completed or cancelled)
    overdue_tasks = (
        db.query(func.count(Task.id))
        .filter(
            Task.project_id == project.id,
            Task.due_date.isnot(None),
            Task.due_date < now,
            Task.status.notin_([TaskStatus.DONE, TaskStatus.CANCELLED]),
        )
        .scalar()
        or 0
    )

    return ProjectDashboardResponse(
        project_id=project.id,
        project_key=project.key,
        project_name=project.name,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        completion_rate_percentage=completion_rate,
        overdue_tasks=overdue_tasks,
        tasks_by_status=status_map,
        tasks_by_priority=priority_map,
    )
