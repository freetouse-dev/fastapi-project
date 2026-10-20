from datetime import datetime, timezone
from sqlalchemy.orm import Session

from project_management_api.crud.audit import create_audit_log
from project_management_api.models.comment import TaskComment
from project_management_api.models.project import Project, ProjectMember, ProjectRole, ProjectStatus
from project_management_api.models.task import Task
from project_management_api.models.workspace import Workspace
from project_management_api.schemas.project import ProjectCreate, ProjectUpdate


def get_project_by_key(
    db: Session, workspace_id: int, key: str, include_deleted: bool = False
) -> Project | None:
    """Finds a project by its short key within a specific workspace."""
    query = db.query(Project).filter(
        Project.workspace_id == workspace_id,
        Project.key == key.upper(),
    )
    if not include_deleted:
        query = query.filter(Project.deleted_at.is_(None))
    return query.first()


def get_project_by_id(db: Session, project_id: int, include_deleted: bool = False) -> Project | None:
    query = db.query(Project).filter(Project.id == project_id)
    if not include_deleted:
        query = query.filter(Project.deleted_at.is_(None))
    return query.first()


def get_all_projects(db: Session, include_deleted: bool = False) -> list[Project]:
    """Admin function: returns all projects."""
    query = db.query(Project)
    if not include_deleted:
        query = query.filter(Project.deleted_at.is_(None))
    return query.order_by(Project.created_at.desc()).all()


def create_project(
    db: Session, project_in: ProjectCreate, workspace_id: int, creator_id: int
) -> Project:
    """Creates a project and automatically assigns the creator as PROJECT_LEAD."""
    db_project = Project(
        workspace_id=workspace_id,
        name=project_in.name,
        key=project_in.key,
        description=project_in.description,
        status=ProjectStatus.ACTIVE,
        created_by_id=creator_id,
    )
    db.add(db_project)
    db.flush()

    membership = ProjectMember(
        project_id=db_project.id,
        user_id=creator_id,
        role=ProjectRole.PROJECT_LEAD,
    )
    db.add(membership)

    create_audit_log(
        db,
        action="PROJECT_CREATED",
        resource_type="PROJECT",
        resource_id=db_project.id,
        actor_id=creator_id,
        details={"name": db_project.name, "key": db_project.key, "workspace_id": workspace_id},
    )

    db.commit()
    db.refresh(db_project)
    return db_project


def get_projects_for_user(
    db: Session, workspace_id: int, user_id: int, is_workspace_admin_or_owner: bool
) -> list[Project]:
    """
    Returns active projects in the workspace.
    If user is OWNER or ADMIN in the workspace, returns all active projects.
    Otherwise, returns only projects where the user is a ProjectMember.
    """
    if is_workspace_admin_or_owner:
        return (
            db.query(Project)
            .filter(
                Project.workspace_id == workspace_id,
                Project.deleted_at.is_(None),
            )
            .all()
        )

    return (
        db.query(Project)
        .join(ProjectMember, Project.id == ProjectMember.project_id)
        .filter(
            Project.workspace_id == workspace_id,
            ProjectMember.user_id == user_id,
            Project.deleted_at.is_(None),
        )
        .all()
    )


def update_project(
    db: Session, db_project: Project, project_in: ProjectUpdate, actor_id: int
) -> Project:
    """Updates project attributes and logs audit trail."""
    old_data = {
        "name": db_project.name,
        "description": db_project.description,
        "status": db_project.status.value,
    }
    update_data = project_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_project, field, value)

    create_audit_log(
        db,
        action="PROJECT_UPDATED",
        resource_type="PROJECT",
        resource_id=db_project.id,
        actor_id=actor_id,
        details={"before": old_data, "after": {k: str(v) for k, v in update_data.items()}},
    )

    db.commit()
    db.refresh(db_project)
    return db_project


def soft_delete_project(db: Session, db_project: Project, actor_id: int) -> Project:
    """
    Soft-deletes a project and cascades soft-delete to its child tasks and comments
    within an atomic transaction.
    """
    if db_project.deleted_at is not None:
        return db_project

    now = datetime.now(timezone.utc)
    db_project.deleted_at = now
    db_project.deleted_by_id = actor_id

    # 1. Cascade to child tasks
    tasks = (
        db.query(Task)
        .filter(Task.project_id == db_project.id, Task.deleted_at.is_(None))
        .all()
    )
    for task in tasks:
        task.deleted_at = now
        task.deleted_by_id = actor_id

        # 2. Soft-delete comments
        db.query(TaskComment).filter(
            TaskComment.task_id == task.id,
            TaskComment.deleted_at.is_(None),
        ).update(
            {"deleted_at": now, "deleted_by_id": actor_id},
            synchronize_session=False,
        )

    create_audit_log(
        db,
        action="PROJECT_DELETED",
        resource_type="PROJECT",
        resource_id=db_project.id,
        actor_id=actor_id,
        details={"name": db_project.name, "key": db_project.key, "workspace_id": db_project.workspace_id, "tasks_count": len(tasks)},
    )

    db.commit()
    db.refresh(db_project)
    return db_project


def get_project_membership(db: Session, project_id: int, user_id: int) -> ProjectMember | None:
    """Checks whether a user is an active member of the project."""
    return (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
        .first()
    )


def get_project_members(db: Session, project_id: int) -> list[ProjectMember]:
    """Returns all members of a project."""
    return db.query(ProjectMember).filter(ProjectMember.project_id == project_id).all()


def add_project_member(
    db: Session, project_id: int, user_id: int, role: ProjectRole = ProjectRole.CONTRIBUTOR, actor_id: int | None = None
) -> ProjectMember:
    """Adds a user to a project with the given role and logs audit trail."""
    membership = ProjectMember(
        project_id=project_id,
        user_id=user_id,
        role=role,
    )
    db.add(membership)

    create_audit_log(
        db,
        action="PROJECT_MEMBER_ADDED",
        resource_type="MEMBERSHIP",
        resource_id=f"proj_{project_id}:{user_id}",
        actor_id=actor_id,
        details={"project_id": project_id, "user_id": user_id, "role": role.value},
    )

    db.commit()
    db.refresh(membership)
    return membership


def remove_project_member(db: Session, membership: ProjectMember, actor_id: int) -> None:
    """Removes a member from a project and logs audit trail."""
    create_audit_log(
        db,
        action="PROJECT_MEMBER_REMOVED",
        resource_type="MEMBERSHIP",
        resource_id=f"proj_{membership.project_id}:{membership.user_id}",
        actor_id=actor_id,
        details={"project_id": membership.project_id, "user_id": membership.user_id, "role": membership.role.value},
    )
    db.delete(membership)
    db.commit()