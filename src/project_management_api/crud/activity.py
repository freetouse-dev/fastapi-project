from sqlalchemy.orm import Session
from project_management_api.models.activity import ActivityAction, TaskActivity


def log_activity(
    db: Session,
    task_id: int,
    actor_id: int,
    action: ActivityAction,
    field_name: str | None = None,
    old_value: str | None = None,
    new_value: str | None = None,
) -> TaskActivity:
    """Creates an audit log record for a task action."""
    activity = TaskActivity(
        task_id=task_id,
        actor_id=actor_id,
        action=action,
        field_name=field_name,
        old_value=str(old_value) if old_value is not None else None,
        new_value=str(new_value) if new_value is not None else None,
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


def get_activities_for_task(db: Session, task_id: int) -> list[TaskActivity]:
    """Retrieves all activity history for a task in chronological order."""
    return (
        db.query(TaskActivity)
        .filter(TaskActivity.task_id == task_id)
        .order_by(TaskActivity.created_at.asc())
        .all()
    )
