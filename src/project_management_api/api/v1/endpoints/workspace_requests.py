from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from project_management_api.api.deps import get_current_active_company, get_current_user
from project_management_api.core.permissions import can_manage_company
from project_management_api.crud import workspace_request as crud_ws_req
from project_management_api.db.session import get_db
from project_management_api.models.company import Company, CompanyMember
from project_management_api.models.user import User
from project_management_api.models.workspace import WorkspaceAccessRequestStatus
from project_management_api.schemas.workspace_request import (
    WorkspaceAccessRequestCreate,
    WorkspaceAccessRequestResponse,
    WorkspaceAccessRequestReview,
)

router = APIRouter()


@router.post(
    "/{slug}/workspace-requests",
    response_model=WorkspaceAccessRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a workspace access request",
)
def submit_workspace_access_request(
    slug: str,
    request_in: WorkspaceAccessRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    company_context: tuple[Company, CompanyMember] = Depends(get_current_active_company),
):
    company, membership = company_context
    if company.slug != slug and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Context mismatch with requested company slug.",
        )

    try:
        return crud_ws_req.create_workspace_access_request(
            db=db,
            company_id=company.id,
            user_id=current_user.id,
            request_in=request_in,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{slug}/workspace-requests",
    response_model=list[WorkspaceAccessRequestResponse],
    summary="List workspace access requests",
)
def list_workspace_access_requests(
    slug: str,
    status_filter: WorkspaceAccessRequestStatus | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    company_context: tuple[Company, CompanyMember] = Depends(get_current_active_company),
):
    company, membership = company_context
    if company.slug != slug and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Context mismatch with requested company slug.",
        )

    is_admin = can_manage_company(membership, current_user)
    user_filter = None if is_admin else current_user.id

    return crud_ws_req.get_workspace_access_requests(
        db=db,
        company_id=company.id,
        user_id=user_filter,
        status=status_filter,
    )


@router.post(
    "/{slug}/workspace-requests/{request_id}/approve",
    response_model=WorkspaceAccessRequestResponse,
    summary="Approve a workspace access request",
)
def approve_workspace_access_request(
    slug: str,
    request_id: int,
    review_in: WorkspaceAccessRequestReview | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    company_context: tuple[Company, CompanyMember] = Depends(get_current_active_company),
):
    company, membership = company_context
    if not can_manage_company(membership, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only company owners and administrators can review workspace requests.",
        )

    req = crud_ws_req.get_workspace_access_request_by_id(db, request_id=request_id, company_id=company.id)
    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace access request not found.",
        )

    try:
        return crud_ws_req.approve_workspace_access_request(
            db=db,
            req=req,
            reviewer_id=current_user.id,
            review_in=review_in,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{slug}/workspace-requests/{request_id}/reject",
    response_model=WorkspaceAccessRequestResponse,
    summary="Reject a workspace access request",
)
def reject_workspace_access_request(
    slug: str,
    request_id: int,
    review_in: WorkspaceAccessRequestReview | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    company_context: tuple[Company, CompanyMember] = Depends(get_current_active_company),
):
    company, membership = company_context
    if not can_manage_company(membership, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only company owners and administrators can review workspace requests.",
        )

    req = crud_ws_req.get_workspace_access_request_by_id(db, request_id=request_id, company_id=company.id)
    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace access request not found.",
        )

    decision_reason = review_in.decision_reason if review_in else None
    try:
        return crud_ws_req.reject_workspace_access_request(
            db=db,
            req=req,
            reviewer_id=current_user.id,
            decision_reason=decision_reason,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{slug}/workspace-requests/{request_id}/cancel",
    response_model=WorkspaceAccessRequestResponse,
    summary="Cancel a pending workspace access request",
)
def cancel_workspace_access_request(
    slug: str,
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    company_context: tuple[Company, CompanyMember] = Depends(get_current_active_company),
):
    company, membership = company_context
    req = crud_ws_req.get_workspace_access_request_by_id(db, request_id=request_id, company_id=company.id)
    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace access request not found.",
        )

    try:
        return crud_ws_req.cancel_workspace_access_request(
            db=db,
            req=req,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
