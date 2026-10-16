from sqlalchemy.orm import Session
from project_management_api.models.comment import TaskComment
from project_management_api.schemas.comment import CommentCreate

def create_comment(db: Session, comment_in: CommentCreate, task_id: int, author_id: int) -> TaskComment:
    """Creates a new comment on a task."""
    db_comment = TaskComment(
        task_id=task_id,
        author_id=author_id,
        content=comment_in.content,
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

def get_comments_for_task(db: Session, task_id: int) -> list[TaskComment]:
    """Retrieves all comments for a task in chronological order."""
    return (
        db.query(TaskComment)
        .filter(TaskComment.task_id == task_id)
        .order_by(TaskComment.created_at.asc())
        .all()
    )

def get_comment_by_id(db: Session, comment_id: int) -> TaskComment | None:
    return db.query(TaskComment).filter(TaskComment.id == comment_id).first()

def delete_comment(db: Session, db_comment: TaskComment) -> None:
    """Deletes a comment."""
    db.delete(db_comment)
    db.commit()