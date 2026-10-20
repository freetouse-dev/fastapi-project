from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from project_management_api.api.deps import get_current_user
from project_management_api.api.v1.endpoints.tasks import require_project_context
from project_management_api.crud import attachment as crud_attachment
from project_management_api.crud import comment as crud_comment
from project_management_api.crud import project as crud_project
from project_management_api.crud import task as crud_task
from project_management_api.db.session import get_db
from project_management_api.models.comment import TaskComment
from project_management_api.models.project import Project, ProjectRole
from project_management_api.models.task import Task
from project_management_api.models.user import User
from project_management_api.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from project_management_api.schemas.attachment import CommentAttachmentResponse
from project_management_api.schemas.comment import CommentCreate, CommentResponse, CommentUpdate
from project_management_api.services.storage import StorageService

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

    is_admin_or_owner = current_user.is_superuser or ws_membership.role in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]
    proj_membership = crud_project.get_project_membership(db, project.id, current_user.id)
    if not is_admin_or_owner and (
        not proj_membership
        or proj_membership.role == ProjectRole.VIEWER
        or ws_membership.role == WorkspaceRole.VIEWER
    ):
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
    """Returns all active comments for the task in chronological order."""
    _, _, _, task = context
    return crud_comment.get_comments_for_task(db, task_id=task.id)


@router.patch(
    "/{slug}/projects/{key}/tasks/{task_number}/comments/{comment_id}",
    response_model=CommentResponse,
    summary="Update comment",
)
def update_comment(
    comment_id: int,
    comment_in: CommentUpdate,
    context: tuple[Workspace, WorkspaceMember, Project, Task] = Depends(require_task_context),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Updates a comment. Allowed for comment author or moderator."""
    _, ws_membership, project, task = context

    comment = crud_comment.get_comment_by_id(db, comment_id=comment_id)
    if not comment or comment.task_id != task.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found.",
        )

    is_author = comment.author_id == current_user.id
    is_admin_or_owner = current_user.is_superuser or ws_membership.role in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]
    proj_membership = crud_project.get_project_membership(db, project.id, current_user.id)
    is_lead = proj_membership and proj_membership.role == ProjectRole.PROJECT_LEAD

    if not (is_author or is_admin_or_owner or is_lead):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to edit this comment.",
        )

    return crud_comment.update_comment(
        db, db_comment=comment, comment_in=comment_in, actor_id=current_user.id
    )


@router.delete(
    "/{slug}/projects/{key}/tasks/{task_number}/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete comment",
)
def delete_comment(
    comment_id: int,
    context: tuple[Workspace, WorkspaceMember, Project, Task] = Depends(require_task_context),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-deletes a comment without removing the database row."""
    _, ws_membership, project, task = context

    comment = crud_comment.get_comment_by_id(db, comment_id=comment_id)
    if not comment or comment.task_id != task.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found.",
        )

    is_author = comment.author_id == current_user.id
    is_admin_or_owner = current_user.is_superuser or ws_membership.role in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]
    proj_membership = crud_project.get_project_membership(db, project.id, current_user.id)
    is_lead = proj_membership and proj_membership.role == ProjectRole.PROJECT_LEAD

    if not (is_author or is_admin_or_owner or is_lead):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this comment.",
        )

    crud_comment.soft_delete_comment(db, db_comment=comment, actor_id=current_user.id)


@router.post(
    "/{slug}/projects/{key}/tasks/{task_number}/comments/{comment_id}/attachments",
    response_model=list[CommentAttachmentResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload and attach files to comment",
)
async def upload_comment_attachments(
    comment_id: int,
    files: list[UploadFile] = File(...),
    context: tuple[Workspace, WorkspaceMember, Project, Task] = Depends(require_task_context),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Uploads and attaches allowed files to a comment."""
    _, ws_membership, project, task = context

    comment = crud_comment.get_comment_by_id(db, comment_id=comment_id)
    if not comment or comment.task_id != task.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found.",
        )

    is_author = comment.author_id == current_user.id
    is_admin_or_owner = current_user.is_superuser or ws_membership.role in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]
    proj_membership = crud_project.get_project_membership(db, project.id, current_user.id)
    is_lead = proj_membership and proj_membership.role == ProjectRole.PROJECT_LEAD

    if not (is_author or is_admin_or_owner or is_lead):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to attach files to this comment.",
        )

    # Check maximum attachments count
    existing_attachments = crud_attachment.get_attachments_for_comment(db, comment_id=comment.id)
    if len(existing_attachments) + len(files) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot exceed limit of 5 attachments per comment. (Current: {len(existing_attachments)}, Adding: {len(files)})",
        )

    results = []
    for file in files:
        content = await file.read()
        if not content:
            continue
        mime_type, ext = StorageService.validate_attachment(content, file.filename or "file")
        storage_key = StorageService.save_attachment(content, ext)
        clean_name = file.filename or f"attachment{ext}"
        attachment_record = crud_attachment.create_attachment(
            db=db,
            comment_id=comment.id,
            original_filename=clean_name,
            storage_key=storage_key,
            mime_type=mime_type,
            file_size=len(content),
            uploaded_by_id=current_user.id,
        )
        results.append(attachment_record)

    return results


@router.get(
    "/{slug}/projects/{key}/tasks/{task_number}/comments/{comment_id}/attachments",
    response_model=list[CommentAttachmentResponse],
    summary="List attachments for a comment",
)
def list_comment_attachments(
    comment_id: int,
    context: tuple[Workspace, WorkspaceMember, Project, Task] = Depends(require_task_context),
    db: Session = Depends(get_db),
):
    """Retrieves all active attachments for a comment."""
    _, _, _, task = context

    comment = crud_comment.get_comment_by_id(db, comment_id=comment_id)
    if not comment or comment.task_id != task.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found.",
        )

    return crud_attachment.get_attachments_for_comment(db, comment_id=comment.id)


@router.delete(
    "/{slug}/projects/{key}/tasks/{task_number}/comments/{comment_id}/attachments/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a comment attachment",
)
def delete_comment_attachment(
    comment_id: int,
    attachment_id: int,
    context: tuple[Workspace, WorkspaceMember, Project, Task] = Depends(require_task_context),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-deletes an attachment from a comment."""
    _, ws_membership, project, task = context

    comment = crud_comment.get_comment_by_id(db, comment_id=comment_id)
    if not comment or comment.task_id != task.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found.",
        )

    attachment = crud_attachment.get_attachment_by_id(db, attachment_id=attachment_id)
    if not attachment or attachment.comment_id != comment.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found.",
        )

    is_uploader = attachment.uploaded_by_id == current_user.id
    is_author = comment.author_id == current_user.id
    is_admin_or_owner = current_user.is_superuser or ws_membership.role in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]
    proj_membership = crud_project.get_project_membership(db, project.id, current_user.id)
    is_lead = proj_membership and proj_membership.role == ProjectRole.PROJECT_LEAD

    if not (is_uploader or is_author or is_admin_or_owner or is_lead):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this attachment.",
        )

    crud_attachment.soft_delete_attachment(db, db_attachment=attachment, actor_id=current_user.id)