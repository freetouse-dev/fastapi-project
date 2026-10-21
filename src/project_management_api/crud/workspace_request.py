from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

from project_management_api.crud import audit as crud_audit
from project_management_api.models.company import CompanyMember
from project_management_api.models.workspace import (
    Workspace,
    WorkspaceAccessRequest,
    WorkspaceAccessRequestStatus,
    WorkspaceAccessRequestType,
    WorkspaceMember,
    WorkspaceRole,
)
from project_management_api.schemas.workspace_request import (
    WorkspaceAccessRequestCreate,
    WorkspaceAccessRequestReview,
)


def get_workspace_access_request_by_id(
    db: Session, request_id: int, company_id: int
) -> WorkspaceAccessRequest | None:
    return (
        db.query(WorkspaceAccessRequest)
        .filter(
            WorkspaceAccessRequest.id == request_id,
            WorkspaceAccessRequest.company_id == company_id,
        )
        .first()
    )


def get_workspace_access_requests(
    db: Session,
    company_id: int,
    user_id: int | None = None,
    status: WorkspaceAccessRequestStatus | None = None,
) -> list[WorkspaceAccessRequest]:
    query = db.query(WorkspaceAccessRequest).filter(
        WorkspaceAccessRequest.company_id == company_id
    )
    if user_id is not None:
        query = query.filter(WorkspaceAccessRequest.user_id == user_id)
    if status is not None:
        query = query.filter(WorkspaceAccessRequest.status == status)
    return query.order_by(WorkspaceAccessRequest.created_at.desc()).all()


def create_workspace_access_request(
    db: Session,
    company_id: int,
    user_id: int,
    request_in: WorkspaceAccessRequestCreate,
) -> WorkspaceAccessRequest:
    # Check if there is already a pending request of the same type for this user in this company
    existing_query = db.query(WorkspaceAccessRequest).filter(
        WorkspaceAccessRequest.company_id == company_id,
        WorkspaceAccessRequest.user_id == user_id,
        WorkspaceAccessRequest.request_type == request_in.request_type,
        WorkspaceAccessRequest.status == WorkspaceAccessRequestStatus.PENDING,
    )
    if request_in.request_type == WorkspaceAccessRequestType.JOIN_WORKSPACE:
        if not request_in.workspace_id:
            raise ValueError("workspace_id is required when requesting to join a workspace.")
        ws = (
            db.query(Workspace)
            .filter(
                Workspace.id == request_in.workspace_id,
                Workspace.company_id == company_id,
                Workspace.deleted_at.is_(None),
            )
            .first()
        )
        if not ws:
            raise ValueError("Target workspace not found in this company.")
        existing_query = existing_query.filter(
            WorkspaceAccessRequest.workspace_id == request_in.workspace_id
        )

    if existing_query.first():
        raise ValueError("You already have a pending request for this action.")

    req = WorkspaceAccessRequest(
        company_id=company_id,
        user_id=user_id,
        request_type=request_in.request_type,
        workspace_id=request_in.workspace_id if request_in.request_type == WorkspaceAccessRequestType.JOIN_WORKSPACE else None,
        requested_role=request_in.requested_role,
        reason=request_in.reason,
        status=WorkspaceAccessRequestStatus.PENDING,
    )
    db.add(req)
    db.flush()

    crud_audit.create_audit_log(
        db,
        action="WORKSPACE_ACCESS_REQUEST_CREATED",
        resource_type="WORKSPACE_ACCESS_REQUEST",
        resource_id=req.id,
        actor_id=user_id,
        details={
            "company_id": company_id,
            "request_type": req.request_type.value,
            "workspace_id": req.workspace_id,
        },
    )
    db.commit()
    db.refresh(req)
    return req


def approve_workspace_access_request(
    db: Session,
    req: WorkspaceAccessRequest,
    reviewer_id: int,
    review_in: WorkspaceAccessRequestReview | None = None,
) -> WorkspaceAccessRequest:
    if req.status != WorkspaceAccessRequestStatus.PENDING:
        raise ValueError(f"Cannot approve request with status {req.status.value}.")

    # Atomic execution
    if req.request_type == WorkspaceAccessRequestType.CREATE_WORKSPACE:
        # Grant explicit workspace creation permission to company member
        membership = (
            db.query(CompanyMember)
            .filter(
                CompanyMember.company_id == req.company_id,
                CompanyMember.user_id == req.user_id,
            )
            .first()
        )
        if membership:
            membership.can_create_workspace = True
    elif req.request_type == WorkspaceAccessRequestType.JOIN_WORKSPACE:
        if req.workspace_id:
            role_to_grant = WorkspaceRole.MEMBER
            if review_in and review_in.approved_role:
                try:
                    role_to_grant = WorkspaceRole(review_in.approved_role.upper())
                except ValueError:
                    role_to_grant = WorkspaceRole.MEMBER
            elif req.requested_role:
                try:
                    role_to_grant = WorkspaceRole(req.requested_role.upper())
                except ValueError:
                    role_to_grant = WorkspaceRole.MEMBER

            ws_member = (
                db.query(WorkspaceMember)
                .filter(
                    WorkspaceMember.workspace_id == req.workspace_id,
                    WorkspaceMember.user_id == req.user_id,
                )
                .first()
            )
            if ws_member:
                ws_member.role = role_to_grant
            else:
                ws_member = WorkspaceMember(
                    workspace_id=req.workspace_id,
                    user_id=req.user_id,
                    role=role_to_grant,
                )
                db.add(ws_member)

    req.status = WorkspaceAccessRequestStatus.APPROVED
    req.reviewer_id = reviewer_id
    req.reviewed_at = datetime.now(timezone.utc)
    if review_in and review_in.decision_reason:
        req.decision_reason = review_in.decision_reason

    crud_audit.create_audit_log(
        db,
        action="WORKSPACE_ACCESS_REQUEST_APPROVED",
        resource_type="WORKSPACE_ACCESS_REQUEST",
        resource_id=req.id,
        actor_id=reviewer_id,
        details={
            "company_id": req.company_id,
            "target_user_id": req.user_id,
            "request_type": req.request_type.value,
        },
    )
    db.commit()
    db.refresh(req)
    return req


def reject_workspace_access_request(
    db: Session,
    req: WorkspaceAccessRequest,
    reviewer_id: int,
    decision_reason: str | None = None,
) -> WorkspaceAccessRequest:
    if req.status != WorkspaceAccessRequestStatus.PENDING:
        raise ValueError(f"Cannot reject request with status {req.status.value}.")

    req.status = WorkspaceAccessRequestStatus.REJECTED
    req.reviewer_id = reviewer_id
    req.reviewed_at = datetime.now(timezone.utc)
    req.decision_reason = decision_reason

    crud_audit.create_audit_log(
        db,
        action="WORKSPACE_ACCESS_REQUEST_REJECTED",
        resource_type="WORKSPACE_ACCESS_REQUEST",
        resource_id=req.id,
        actor_id=reviewer_id,
        details={
            "company_id": req.company_id,
            "target_user_id": req.user_id,
            "decision_reason": decision_reason,
        },
    )
    db.commit()
    db.refresh(req)
    return req


def cancel_workspace_access_request(
    db: Session,
    req: WorkspaceAccessRequest,
    user_id: int,
) -> WorkspaceAccessRequest:
    if req.status != WorkspaceAccessRequestStatus.PENDING:
        raise ValueError(f"Cannot cancel request with status {req.status.value}.")
    if req.user_id != user_id:
        raise ValueError("Only the requester can cancel this request.")

    req.status = WorkspaceAccessRequestStatus.CANCELLED
    crud_audit.create_audit_log(
        db,
        action="WORKSPACE_ACCESS_REQUEST_CANCELLED",
        resource_type="WORKSPACE_ACCESS_REQUEST",
        resource_id=req.id,
        actor_id=user_id,
        details={"company_id": req.company_id},
    )
    db.commit()
    db.refresh(req)
    return req
