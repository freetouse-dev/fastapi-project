from datetime import datetime, timezone
from sqlalchemy.orm import Session

from project_management_api.crud.audit import create_audit_log
from project_management_api.models.comment import TaskComment
from project_management_api.models.task import Task
from project_management_api.schemas.comment import CommentCreate, CommentUpdate


def create_comment(
    db: Session, comment_in: CommentCreate, task_id: int, author_id: int
) -> TaskComment:
    """Creates a new comment on a task and logs audit trail."""
    db_comment = TaskComment(
        task_id=task_id,
        author_id=author_id,
        content=comment_in.content,
    )
    db.add(db_comment)
    db.flush()

    create_audit_log(
        db,
        action="COMMENT_CREATED",
        resource_type="COMMENT",
        resource_id=db_comment.id,
        actor_id=author_id,
        details={"task_id": task_id, "content_length": len(comment_in.content)},
    )

    db.commit()
    db.refresh(db_comment)
    return db_comment


def get_comments_for_task(
    db: Session, task_id: int, include_deleted: bool = False
) -> list[TaskComment]:
    """Retrieves active comments for a task in chronological order."""
    query = db.query(TaskComment).filter(TaskComment.task_id == task_id)
    if not include_deleted:
        query = query.filter(TaskComment.deleted_at.is_(None))
    return query.order_by(TaskComment.created_at.asc()).all()


def get_comment_by_id(
    db: Session, comment_id: int, include_deleted: bool = False
) -> TaskComment | None:
    query = db.query(TaskComment).filter(TaskComment.id == comment_id)
    if not include_deleted:
        query = query.filter(TaskComment.deleted_at.is_(None))
    return query.first()


def get_all_comments_paginated(
    db: Session,
    page: int = 1,
    size: int = 20,
    include_deleted: bool = False,
) -> tuple[list[TaskComment], int]:
    """Admin function: returns comments across all tasks with pagination."""
    query = db.query(TaskComment)
    if not include_deleted:
        query = query.filter(TaskComment.deleted_at.is_(None))
    total = query.count()
    items = query.order_by(TaskComment.created_at.desc()).offset((page - 1) * size).limit(size).all()
    return items, total


def update_comment(
    db: Session, db_comment: TaskComment, comment_in: CommentUpdate, actor_id: int
) -> TaskComment:
    """Updates a comment's content and logs audit trail."""
    old_length = len(db_comment.content)
    db_comment.content = comment_in.content

    create_audit_log(
        db,
        action="COMMENT_UPDATED",
        resource_type="COMMENT",
        resource_id=db_comment.id,
        actor_id=actor_id,
        details={"task_id": db_comment.task_id, "old_length": old_length, "new_length": len(comment_in.content)},
    )

    db.commit()
    db.refresh(db_comment)
    return db_comment


def soft_delete_comment(db: Session, db_comment: TaskComment, actor_id: int) -> TaskComment:
    """Soft-deletes a comment without physically removing the database row."""
    if db_comment.deleted_at is not None:
        return db_comment

    now = datetime.now(timezone.utc)
    db_comment.deleted_at = now
    db_comment.deleted_by_id = actor_id

    create_audit_log(
        db,
        action="COMMENT_DELETED",
        resource_type="COMMENT",
        resource_id=db_comment.id,
        actor_id=actor_id,
        details={"task_id": db_comment.task_id},
    )

    db.commit()
    db.refresh(db_comment)
    return db_comment


def restore_comment(db: Session, db_comment: TaskComment, actor_id: int) -> TaskComment:
    """Restores a soft-deleted comment and records an audit log."""
    if db_comment.deleted_at is None:
        return db_comment

    # Verify parent task is active
    task = db.query(Task).filter(Task.id == db_comment.task_id).first()
    if task and task.deleted_at is not None:
        raise ValueError("Cannot restore comment because its parent task is deleted. Restore the task first.")

    db_comment.deleted_at = None
    db_comment.deleted_by_id = None

    create_audit_log(
        db,
        action="COMMENT_RESTORED",
        resource_type="COMMENT",
        resource_id=db_comment.id,
        actor_id=actor_id,
        details={"task_id": db_comment.task_id},
    )

    db.commit()
    db.refresh(db_comment)
    return db_comment