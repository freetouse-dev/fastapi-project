from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from project_management_api.api.deps import get_current_user, get_current_user_from_token_or_param
from project_management_api.db.session import get_db
from project_management_api.models.attachment import CommentAttachment
from project_management_api.models.comment import TaskComment
from project_management_api.models.project import Project
from project_management_api.models.task import Task
from project_management_api.models.user import User
from project_management_api.models.workspace import WorkspaceMember
from project_management_api.schemas.attachment import CommentAttachmentResponse
from project_management_api.services.storage import StorageService

router = APIRouter()


def get_authorized_attachment(
    attachment_id: int,
    db: Session,
    current_user: User,
) -> CommentAttachment:
    """Verifies that the attachment exists, is not soft-deleted, and the user belongs to its workspace."""
    attachment = (
        db.query(CommentAttachment)
        .filter(CommentAttachment.id == attachment_id, CommentAttachment.deleted_at.is_(None))
        .first()
    )
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found.",
        )

    # Resolve comment, task, project
    comment = (
        db.query(TaskComment)
        .filter(TaskComment.id == attachment.comment_id, TaskComment.deleted_at.is_(None))
        .first()
    )
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated comment not found or deleted.",
        )

    task = db.query(Task).filter(Task.id == comment.task_id, Task.deleted_at.is_(None)).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated task not found or deleted.",
        )

    project = db.query(Project).filter(Project.id == task.project_id, Project.deleted_at.is_(None)).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated project not found or deleted.",
        )

    # Permission check: superuser or workspace member
    if not current_user.is_superuser:
        is_member = (
            db.query(WorkspaceMember)
            .filter(
                WorkspaceMember.workspace_id == project.workspace_id,
                WorkspaceMember.user_id == current_user.id,
            )
            .first()
        )
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access attachments in this workspace.",
            )

    return attachment


@router.get(
    "/{attachment_id}",
    response_model=CommentAttachmentResponse,
    summary="Get Attachment Metadata",
)
def get_attachment_metadata(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieves metadata of an authorized attachment."""
    return get_authorized_attachment(attachment_id, db, current_user)


@router.get(
    "/{attachment_id}/download",
    summary="Download Attachment",
)
def download_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token_or_param),
):
    """Securely downloads an authorized attachment with forced Content-Disposition."""
    attachment = get_authorized_attachment(attachment_id, db, current_user)
    file_path = StorageService.get_file_path(attachment.storage_key)

    return FileResponse(
        path=file_path,
        media_type=attachment.mime_type,
        filename=attachment.original_filename,
        headers={
            "Content-Disposition": f'attachment; filename="{attachment.original_filename}"',
        },
    )


@router.get(
    "/{attachment_id}/preview",
    summary="Preview Attachment Inline",
)
def preview_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token_or_param),
):
    """Serves an authorized attachment inline for images and PDFs."""
    attachment = get_authorized_attachment(attachment_id, db, current_user)
    file_path = StorageService.get_file_path(attachment.storage_key)

    return FileResponse(
        path=file_path,
        media_type=attachment.mime_type,
        headers={
            "Content-Disposition": f'inline; filename="{attachment.original_filename}"',
            "Cache-Control": "private, max-age=3600",
        },
    )
