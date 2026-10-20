from datetime import datetime, timezone
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from project_management_api.crud.audit import create_audit_log
from project_management_api.models.activity import ActivityAction, TaskActivity
from project_management_api.models.comment import TaskComment
from project_management_api.models.project import Project
from project_management_api.models.task import Task, TaskPriority, TaskStatus
from project_management_api.schemas.task import TaskCreate, TaskUpdate


def get_next_task_number(db: Session, project_id: int) -> int:
    """Safely calculates the next sequential task number within a project."""
    max_num = db.query(func.max(Task.task_number)).filter(Task.project_id == project_id).scalar()
    return (max_num or 0) + 1


def create_task(
    db: Session,
    task_in: TaskCreate,
    project_id: int,
    creator_id: int,
    assignee_id: int | None = None,
) -> Task:
    """Creates a new task with sequential ticket numbering, task activity, and audit log."""
    db.query(Project).filter(Project.id == project_id).with_for_update().first()
    next_number = get_next_task_number(db, project_id=project_id)

    db_task = Task(
        project_id=project_id,
        task_number=next_number,
        title=task_in.title,
        description=task_in.description,
        status=task_in.status,
        priority=task_in.priority,
        creator_id=creator_id,
        assignee_id=assignee_id,
        due_date=task_in.due_date,
    )
    db.add(db_task)
    db.flush()

    activity = TaskActivity(
        task_id=db_task.id,
        actor_id=creator_id,
        action=ActivityAction.TASK_CREATED,
        new_value=db_task.title,
    )
    db.add(activity)

    create_audit_log(
        db,
        action="TASK_CREATED",
        resource_type="TASK",
        resource_id=db_task.id,
        actor_id=creator_id,
        details={"project_id": project_id, "task_number": next_number, "title": db_task.title},
    )

    db.commit()
    db.refresh(db_task)
    return db_task


def get_task_by_number(
    db: Session, project_id: int, task_number: int, include_deleted: bool = False
) -> Task | None:
    """Finds a task by its project-scoped task number (e.g. 1 for MOB-1)."""
    query = db.query(Task).filter(Task.project_id == project_id, Task.task_number == task_number)
    if not include_deleted:
        query = query.filter(Task.deleted_at.is_(None))
    return query.first()


def get_task_by_id(db: Session, task_id: int, include_deleted: bool = False) -> Task | None:
    query = db.query(Task).filter(Task.id == task_id)
    if not include_deleted:
        query = query.filter(Task.deleted_at.is_(None))
    return query.first()


def get_tasks_paginated(
    db: Session,
    project_id: int,
    search: str | None = None,
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    assignee_id: int | None = None,
    sort_by: str = "task_number",
    sort_order: str = "asc",
    page: int = 1,
    size: int = 20,
    include_deleted: bool = False,
) -> tuple[list[Task], int]:
    """
    Retrieves a paginated, filtered, and sorted list of tasks along with the total matching count.
    """
    query = db.query(Task).filter(Task.project_id == project_id)
    if not include_deleted:
        query = query.filter(Task.deleted_at.is_(None))

    # 1. Text Search across title and description
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Task.title.ilike(search_pattern),
                Task.description.ilike(search_pattern),
            )
        )

    # 2. Filtering
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    if assignee_id:
        query = query.filter(Task.assignee_id == assignee_id)

    # 3. Total Count
    total = query.count()

    # 4. Sorting
    sort_columns = {
        "task_number": Task.task_number,
        "title": Task.title,
        "status": Task.status,
        "priority": Task.priority,
        "created_at": Task.created_at,
        "due_date": Task.due_date,
    }
    sort_column = sort_columns.get(sort_by, Task.task_number)
    if sort_order.lower() == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # 5. Pagination
    offset = (page - 1) * size
    items = query.offset(offset).limit(size).all()

    return items, total


def get_all_tasks_paginated(
    db: Session,
    search: str | None = None,
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    project_id: int | None = None,
    page: int = 1,
    size: int = 20,
    include_deleted: bool = False,
) -> tuple[list[Task], int]:
    """Admin function: returns tasks across all projects with filters and pagination."""
    query = db.query(Task)
    if not include_deleted:
        query = query.filter(Task.deleted_at.is_(None))

    if project_id:
        query = query.filter(Task.project_id == project_id)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Task.title.ilike(search_pattern),
                Task.description.ilike(search_pattern),
            )
        )
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)

    total = query.count()
    items = query.order_by(Task.created_at.desc()).offset((page - 1) * size).limit(size).all()
    return items, total


def update_task(
    db: Session,
    db_task: Task,
    task_in: TaskUpdate,
    actor_id: int,
    assignee_id: int | None = None,
) -> Task:
    """Updates task fields, writes TaskActivity records and system audit log."""
    update_data = task_in.model_dump(exclude_unset=True, exclude={"assignee_email"})

    if "status" in update_data and update_data["status"] != db_task.status:
        db.add(
            TaskActivity(
                task_id=db_task.id,
                actor_id=actor_id,
                action=ActivityAction.STATUS_CHANGED,
                field_name="status",
                old_value=str(db_task.status.value),
                new_value=str(update_data["status"].value),
            )
        )

    if "priority" in update_data and update_data["priority"] != db_task.priority:
        db.add(
            TaskActivity(
                task_id=db_task.id,
                actor_id=actor_id,
                action=ActivityAction.PRIORITY_CHANGED,
                field_name="priority",
                old_value=str(db_task.priority.value),
                new_value=str(update_data["priority"].value),
            )
        )

    if "title" in update_data and update_data["title"] != db_task.title:
        db.add(
            TaskActivity(
                task_id=db_task.id,
                actor_id=actor_id,
                action=ActivityAction.TITLE_CHANGED,
                field_name="title",
                old_value=db_task.title,
                new_value=update_data["title"],
            )
        )

    if "assignee_email" in task_in.model_fields_set and assignee_id != db_task.assignee_id:
        db.add(
            TaskActivity(
                task_id=db_task.id,
                actor_id=actor_id,
                action=ActivityAction.ASSIGNEE_CHANGED,
                field_name="assignee_id",
                old_value=str(db_task.assignee_id) if db_task.assignee_id else None,
                new_value=str(assignee_id) if assignee_id else None,
            )
        )
        db_task.assignee_id = assignee_id

    for field, value in update_data.items():
        setattr(db_task, field, value)

    create_audit_log(
        db,
        action="TASK_UPDATED",
        resource_type="TASK",
        resource_id=db_task.id,
        actor_id=actor_id,
        details={"ticket_key": db_task.ticket_key, "changes": {k: str(v) for k, v in update_data.items()}},
    )

    db.commit()
    db.refresh(db_task)
    return db_task


def soft_delete_task(db: Session, db_task: Task, actor_id: int) -> Task:
    """Soft-deletes a task and cascades to its comments."""
    if db_task.deleted_at is not None:
        return db_task

    now = datetime.now(timezone.utc)
    db_task.deleted_at = now
    db_task.deleted_by_id = actor_id

    db.query(TaskComment).filter(
        TaskComment.task_id == db_task.id,
        TaskComment.deleted_at.is_(None),
    ).update(
        {"deleted_at": now, "deleted_by_id": actor_id},
        synchronize_session=False,
    )

    create_audit_log(
        db,
        action="TASK_DELETED",
        resource_type="TASK",
        resource_id=db_task.id,
        actor_id=actor_id,
        details={"ticket_key": db_task.ticket_key, "title": db_task.title},
    )

    db.commit()
    db.refresh(db_task)
    return db_task
