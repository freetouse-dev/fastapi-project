from sqlalchemy.orm import Session

from project_management_api.models.project import Project, ProjectMember, ProjectRole, ProjectStatus
from project_management_api.models.workspace import WorkspaceMember, WorkspaceRole
from project_management_api.schemas.project import ProjectCreate, ProjectUpdate

def get_project_by_key(db: Session, workspace_id: int, key: str) -> Project | None:
    """Finds a project by its short key within a specific workspace."""
    return (
        db.query(Project)
        .filter(Project.workspace_id == workspace_id, Project.key == key.upper())
        .first()
    )

def get_project_by_id(db: Session, project_id: int) -> Project | None:
    return db.query(Project).filter(Project.id == project_id).first()

def create_project(db: Session, project_in: ProjectCreate, workspace_id: int, creator_id: int) -> Project:
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
    db.commit()
    db.refresh(db_project)
    return db_project


def get_projects_for_user(
    db: Session, workspace_id: int, user_id: int, is_workspace_admin_or_owner: bool
) -> list[Project]:
    """
    Returns projects in the workspace.
    If the user is OWNER or ADMIN in the workspace, returns all projects.
    Otherwise, returns only projects where the user is a ProjectMember.
    """
    if is_workspace_admin_or_owner:
        return db.query(Project).filter(Project.workspace_id == workspace_id).all()

    return (
        db.query(Project)
        .join(ProjectMember, Project.id == ProjectMember.project_id)
        .filter(Project.workspace_id == workspace_id, ProjectMember.user_id == user_id)
        .all()
    )

def get_project_membership(db: Session, project_id: int, user_id: int) -> ProjectMember | None:
    """Checks whether a user is a member of the project."""
    return (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
        .first()
    )


def get_project_members(db: Session, project_id: int) -> list[ProjectMember]:
    """Returns all members of a project."""
    return db.query(ProjectMember).filter(ProjectMember.project_id == project_id).all()


def add_project_member(
    db: Session, project_id: int, user_id: int, role: ProjectRole = ProjectRole.CONTRIBUTOR
) -> ProjectMember:
    """Adds a user to a project with the given role."""
    membership = ProjectMember(
        project_id=project_id,
        user_id=user_id,
        role=role,
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership