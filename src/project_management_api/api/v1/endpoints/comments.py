from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from project_management_api.api.deps import get_current_user
from project_management_api.api.v1.endpoints.tasks import require_project_context
from project_management_api.crud import comment as crud_comment
from project_management_api.crud import project as crud_project
from project_management_api.crud import task as crud_task
from project_management_api.db.session import get_db
from project_management_api.models.comment import TaskComment
from project_management_api.models.project import Project, ProjectRole
from project_management_api.models.task import Task
from project_management_api.models.user import User
from project_management_api.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from project_management_api.schemas.comment import CommentCreate, CommentResponse

router = APIRouter()

def require_task_context(
    task_number: int,
    context: tuple[Workspace, WorkspaceMember, Project] = Depends(require_project_context),
    db: Session = Depends(get_db),
) -> tuple[Workspace, WorkspaceMember, Project, Task]:
    """Resolves task and validates multi-tenant project permissions."""
    workspace, ws_membership, project = context
    task = crud_task.get_task_by_number(db, project_id=project.id, task_number=task_number)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {project.key}-{task_number} not found.",
        )
    return workspace, ws_membership, project, task

@router.post(
    "/{slug}/projects/{key}/tasks/{task_number}/comments/",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add comment to task",
)
def add_comment(
    comment_in: CommentCreate,
    context: tuple[Workspace, WorkspaceMember, Project, Task] = Depends(require_task_context),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Adds a comment to the specified task."""
    _, ws_membership, project, task = context

    is_admin_or_owner = ws_membership.role in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]
    proj_membership = crud_project.get_project_membership(db, project.id, current_user.id)
    if not is_admin_or_owner and (not proj_membership or proj_membership.role == ProjectRole.VIEWER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Viewers cannot post comments in this project.",
        )

    return crud_comment.create_comment(
        db,
        comment_in=comment_in,
        task_id=task.id,
        author_id=current_user.id,
    )


@router.get(
    "/{slug}/projects/{key}/tasks/{task_number}/comments/",
    response_model=list[CommentResponse],
    summary="List comments on task",
)
def list_comments(
    context: tuple[Workspace, WorkspaceMember, Project, Task] = Depends(require_task_context),
    db: Session = Depends(get_db),
):
    """Returns all comments for the task in chronological order."""
    _, _, _, task = context
    return crud_comment.get_comments_for_task(db, task_id=task.id)


@router.delete(
    "/{slug}/projects/{key}/tasks/{task_number}/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete comment",
)
def delete_comment(
    comment_id: int,
    context: tuple[Workspace, WorkspaceMember, Project, Task] = Depends(require_task_context),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deletes a comment. Only the comment author, project lead, or workspace admin can delete."""
    _, ws_membership, project, task = context

    comment = crud_comment.get_comment_by_id(db, comment_id=comment_id)
    if not comment or comment.task_id != task.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found.",
        )

    is_author = comment.author_id == current_user.id
    is_admin_or_owner = ws_membership.role in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]
    proj_membership = crud_project.get_project_membership(db, project.id, current_user.id)
    is_lead = proj_membership and proj_membership.role == ProjectRole.PROJECT_LEAD

    if not (is_author or is_admin_or_owner or is_lead):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this comment.",
        )

    crud_comment.delete_comment(db, db_comment=comment)