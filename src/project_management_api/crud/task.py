from sqlalchemy import func
from sqlalchemy.orm import Session

from project_management_api.models.project import Project
from project_management_api.models.task import Task, TaskPriority, TaskStatus
from project_management_api.schemas.task import TaskCreate, TaskUpdate

def get_next_task_number(db: Session, project_id: int) -> int:
    """Safely calculates the next sequential task number within a project."""
    max_num = db.query(func.max(Task.task_number)).filter(Task.project_id == project_id).scalar()
    return (max_num or 0) + 1

def create_task(db: Session, task_in: TaskCreate, project_id: int, creator_id: int, assignee_id: int | None = None) -> Task:
    """Creates a new task with sequential ticket numbering."""
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
    db.commit()
    db.refresh(db_task)
    return db_task

def get_task_by_number(db: Session, project_id: int, task_number: int) -> Task | None:
    """Finds a task by its project-scoped task number (e.g. 1 for MOB-1)."""
    return (
        db.query(Task)
        .filter(Task.project_id == project_id, Task.task_number == task_number)
        .first()
    )

def get_tasks_for_project(
    db: Session,
    project_id: int,
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    assignee_id: int | None = None,
) -> list[Task]:
    """Filters tasks within a project with optional status, priority, and assignee parameters."""
    query = db.query(Task).filter(Task.project_id == project_id)

    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    if assignee_id:
        query = query.filter(Task.assignee_id == assignee_id)

    return query.order_by(Task.task_number.asc()).all()

def update_task(db: Session, db_task: Task, task_in: TaskUpdate, assignee_id: int | None = None) -> Task:
    """Updates task fields (status, priority, assignee, etc.)."""
    update_data = task_in.model_dump(exclude_unset=True, exclude={"assignee_email"})

    for field, value in update_data.items():
        setattr(db_task, field, value)

    if "assignee_email" in task_in.model_fields_set:
        db_task.assignee_id = assignee_id

    db.commit()
    db.refresh(db_task)
    return db_task