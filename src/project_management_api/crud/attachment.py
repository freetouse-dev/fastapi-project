from datetime import datetime, timezone
from sqlalchemy.orm import Session

from project_management_api.crud.audit import create_audit_log
from project_management_api.models.attachment import CommentAttachment

def create_attachment(
    db: Session,
    comment_id: int,
    original_filename: str,
    storage_key: str,
    mime_type: str,
    file_size: int,
    uploaded_by_id: int,
) -> CommentAttachment:
    """Creates a new comment attachment record and logs audit trail."""
    db_attachment = CommentAttachment(
        comment_id=comment_id,
        original_filename=original_filename,
        storage_key=storage_key,
        mime_type=mime_type,
        file_size=file_size,
        uploaded_by_id=uploaded_by_id,
    )
    db.add(db_attachment)
    db.flush()

    create_audit_log(
        db,
        action="ATTACHMENT_UPLOADED",
        resource_type="ATTACHMENT",
        resource_id=db_attachment.id,
        actor_id=uploaded_by_id,
        details={
            "comment_id": comment_id,
            "original_filename": original_filename,
            "mime_type": mime_type,
            "file_size": file_size,
        },
    )

    db.commit()
    db.refresh(db_attachment)
    return db_attachment


def get_attachment_by_id(
    db: Session, attachment_id: int, include_deleted: bool = False
) -> CommentAttachment | None:
    query = db.query(CommentAttachment).filter(CommentAttachment.id == attachment_id)
    if not include_deleted:
        query = query.filter(CommentAttachment.deleted_at.is_(None))
    return query.first()


def get_attachments_for_comment(
    db: Session, comment_id: int, include_deleted: bool = False
) -> list[CommentAttachment]:
    query = db.query(CommentAttachment).filter(CommentAttachment.comment_id == comment_id)
    if not include_deleted:
        query = query.filter(CommentAttachment.deleted_at.is_(None))
    return query.order_by(CommentAttachment.created_at.asc()).all()


def soft_delete_attachment(
    db: Session, db_attachment: CommentAttachment, actor_id: int
) -> CommentAttachment:
    """Soft-deletes a comment attachment without removing physical storage object immediately."""
    if db_attachment.deleted_at is not None:
        return db_attachment

    now = datetime.now(timezone.utc)
    db_attachment.deleted_at = now
    db_attachment.deleted_by_id = actor_id

    create_audit_log(
        db,
        action="ATTACHMENT_DELETED",
        resource_type="ATTACHMENT",
        resource_id=db_attachment.id,
        actor_id=actor_id,
        details={
            "comment_id": db_attachment.comment_id,
            "original_filename": db_attachment.original_filename,
        },
    )

    db.commit()
    db.refresh(db_attachment)
    return db_attachment
