import json
from typing import Any
from sqlalchemy.orm import Session

from project_management_api.models.audit import AuditLog


def create_audit_log(
    db: Session,
    action: str,
    resource_type: str,
    resource_id: str | int,
    actor_id: int | None = None,
    details: dict[str, Any] | str | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """Creates and queues an audit log record within the current transaction."""
    details_str = None
    if isinstance(details, dict):
        sanitized = {
            k: v
            for k, v in details.items()
            if "password" not in k.lower()
            and "token" not in k.lower()
            and "secret" not in k.lower()
        }
        details_str = json.dumps(sanitized)
    elif details is not None:
        details_str = str(details)

    audit = AuditLog(
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id),
        details=details_str,
        ip_address=ip_address,
    )
    db.add(audit)
    return audit


def get_audit_logs(
    db: Session,
    actor_id: int | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[AuditLog], int]:
    """Retrieves paginated audit log entries with optional filters."""
    query = db.query(AuditLog)

    if actor_id is not None:
        query = query.filter(AuditLog.actor_id == actor_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if resource_id:
        query = query.filter(AuditLog.resource_id == resource_id)

    total = query.count()
    items = (
        query.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    return items, total
