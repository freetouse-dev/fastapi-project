from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from project_management_api.api.deps import get_current_user
from project_management_api.core.permissions import Permissions, require_superuser
from project_management_api.crud import audit as crud_audit
from project_management_api.crud import comment as crud_comment
from project_management_api.crud import company as crud_company
from project_management_api.crud import project as crud_project
from project_management_api.crud import task as crud_task
from project_management_api.crud import user as crud_user
from project_management_api.crud import workspace as crud_workspace
from project_management_api.db.session import get_db
from project_management_api.models.company import (
    Company,
    CompanyCreationRequest,
    CompanyMember,
    CompanyRole,
    CompanyStatus,
)
from project_management_api.models.task import TaskPriority, TaskStatus
from project_management_api.models.user import User
from project_management_api.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from project_management_api.schemas.audit import AdminStatsResponse, AuditLogResponse
from project_management_api.schemas.comment import CommentResponse
from project_management_api.schemas.common import PaginatedResponse
from project_management_api.schemas.company import (
    CompanyCreationRequestResponse,
    CompanyCreationRequestReview,
    CompanyResponse,
    CompanyUpdate,
)
from project_management_api.schemas.project import ProjectResponse
from project_management_api.schemas.role import PermissionDetail, RoleDefinition, RolesResponse
from project_management_api.schemas.task import TaskResponse
from project_management_api.schemas.user import UserAdminUpdate, UserResponse
from project_management_api.schemas.workspace import (
    WorkspaceMemberAdd,
    WorkspaceMemberResponse,
    WorkspaceResponse,
)

router = APIRouter(dependencies=[Depends(require_superuser)])


@router.get("/stats", response_model=AdminStatsResponse, summary="Admin Dashboard overview stats")
def get_stats(db: Session = Depends(get_db)):
    """Computes high-level counts and statistics for the Admin Dashboard."""
    return crud_user.get_admin_stats(db)


# ============================================================================
# COMPANY MANAGEMENT (MULTI-TENANT SAAS)
# ============================================================================

@router.get("/companies", response_model=list[CompanyResponse], summary="List all companies")
def list_companies_admin(
    include_deleted: bool = Query(False, description="Include soft-deleted companies"),
    search: str | None = Query(None, description="Search by company name or slug"),
    status: CompanyStatus | None = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
):
    """Admin endpoint: lists all companies across the platform with metrics."""
    query = db.query(Company)
    if not include_deleted:
        query = query.filter(Company.deleted_at.is_(None))
    if status is not None:
        query = query.filter(Company.status == status)
    if search:
        search_fmt = f"%{search.strip().lower()}%"
        query = query.filter(
            or_(
                func.lower(Company.name).like(search_fmt),
                func.lower(Company.slug).like(search_fmt),
            )
        )
    companies = query.order_by(Company.created_at.desc()).all()

    result = []
    for comp in companies:
        members_count = (
            db.query(CompanyMember)
            .filter(CompanyMember.company_id == comp.id, CompanyMember.status == "ACTIVE")
            .count()
        )
        workspaces_count = (
            db.query(Workspace)
            .filter(Workspace.company_id == comp.id, Workspace.deleted_at.is_(None))
            .count()
        )
        result.append(
            CompanyResponse(
                id=comp.id,
                name=comp.name,
                slug=comp.slug,
                description=comp.description,
                status=comp.status,
                owner_id=comp.owner_id,
                created_by_id=comp.created_by_id,
                deleted_at=comp.deleted_at,
                created_at=comp.created_at,
                updated_at=comp.updated_at,
                members_count=members_count,
                workspaces_count=workspaces_count,
            )
        )
    return result


@router.patch("/companies/{company_id}", response_model=CompanyResponse, summary="Modify company (admin)")
def update_company_admin(
    company_id: int,
    company_in: CompanyUpdate,
    status_change: CompanyStatus | None = Query(None, alias="status", description="Change status to ACTIVE or SUSPENDED"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admin endpoint to update company profile or suspend/reactivate company account."""
    target_company = crud_company.get_company_by_id(db, company_id=company_id, include_deleted=True)
    if not target_company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found.",
        )

    updated = crud_company.update_company(
        db,
        company=target_company,
        actor_id=current_user.id,
        name=company_in.name,
        description=company_in.description,
        status=status_change,
    )
    members_count = (
        db.query(CompanyMember)
        .filter(CompanyMember.company_id == updated.id, CompanyMember.status == "ACTIVE")
        .count()
    )
    workspaces_count = (
        db.query(Workspace)
        .filter(Workspace.company_id == updated.id, Workspace.deleted_at.is_(None))
        .count()
    )
    return CompanyResponse(
        id=updated.id,
        name=updated.name,
        slug=updated.slug,
        description=updated.description,
        status=updated.status,
        owner_id=updated.owner_id,
        created_by_id=updated.created_by_id,
        deleted_at=updated.deleted_at,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
        members_count=members_count,
        workspaces_count=workspaces_count,
    )


@router.delete("/companies/{company_id}", response_model=CompanyResponse, summary="Soft delete company (admin)")
def delete_company_admin(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admin endpoint to soft-delete a company."""
    target_company = crud_company.get_company_by_id(db, company_id=company_id, include_deleted=False)
    if not target_company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found or already deleted.",
        )

    deleted = crud_company.soft_delete_company(db, company=target_company, deleted_by_id=current_user.id)
    return CompanyResponse.model_validate(deleted)


@router.post("/companies/{company_id}/restore", response_model=CompanyResponse, summary="Restore company (admin)")
def restore_company_admin(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admin endpoint to restore a soft-deleted company."""
    target_company = crud_company.get_company_by_id(db, company_id=company_id, include_deleted=True)
    if not target_company or target_company.deleted_at is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deleted company not found.",
        )

    restored = crud_company.restore_company(db, company=target_company, restored_by_id=current_user.id)
    return CompanyResponse.model_validate(restored)


# ============================================================================
# COMPANY CREATION REQUESTS APPROVAL (HYBRID ONBOARDING)
# ============================================================================

@router.get("/company-requests", response_model=list[CompanyCreationRequestResponse], summary="List company creation requests")
def list_company_requests_admin(
    status_filter: str | None = Query(None, description="Filter by status (PENDING, APPROVED, REJECTED)"),
    db: Session = Depends(get_db),
):
    """Lists company creation requests awaiting admin review."""
    return crud_company.get_company_creation_requests(db, status=status_filter)


@router.post("/company-requests/{request_id}/approve", response_model=CompanyResponse, summary="Approve company creation request")
def approve_company_request_admin(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approves a company creation request, creating the company and assigning owner role."""
    request_obj = crud_company.get_company_creation_request_by_id(db, request_id=request_id)
    if not request_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company creation request not found.",
        )

    try:
        new_company = crud_company.approve_company_creation_request(
            db,
            req=request_obj,
            reviewer_id=current_user.id,
        )
        return CompanyResponse(
            id=new_company.id,
            name=new_company.name,
            slug=new_company.slug,
            description=new_company.description,
            status=new_company.status,
            owner_id=new_company.owner_id,
            created_by_id=new_company.created_by_id,
            deleted_at=new_company.deleted_at,
            created_at=new_company.created_at,
            updated_at=new_company.updated_at,
            members_count=1,
            workspaces_count=0,
            my_role=CompanyRole.COMPANY_OWNER,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/company-requests/{request_id}/reject", response_model=CompanyCreationRequestResponse, summary="Reject company creation request")
def reject_company_request_admin(
    request_id: int,
    review_in: CompanyCreationRequestReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Rejects a company creation request with an optional reason."""
    request_obj = crud_company.get_company_creation_request_by_id(db, request_id=request_id)
    if not request_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company creation request not found.",
        )

    try:
        rejected = crud_company.reject_company_creation_request(
            db,
            req=request_obj,
            reviewer_id=current_user.id,
            rejection_reason=review_in.rejection_reason,
        )
        return rejected
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================================
# USER MANAGEMENT
# ============================================================================

@router.get("/users", response_model=PaginatedResponse[UserResponse], summary="List all users")
def list_users(
    search: str | None = Query(None, description="Search by name or email"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    is_verified: bool | None = Query(None, description="Filter by verified status"),
    is_superuser: bool | None = Query(None, description="Filter by superuser role"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Returns a paginated list of all registered platform users."""
    items, total = crud_user.get_users_paginated(
        db,
        search=search,
        is_active=is_active,
        is_verified=is_verified,
        is_superuser=is_superuser,
        page=page,
        size=size,
    )
    return PaginatedResponse.create(items=items, total=total, page=page, size=size)


@router.patch("/users/{user_id}", response_model=UserResponse, summary="Modify user status or role")
def update_user_status(
    user_id: int,
    user_in: UserAdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admin endpoint to activate/deactivate users or toggle superuser privileges."""
    target_user = crud_user.get_user_by_id(db, user_id=user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    # Prevent a superuser from removing their own superuser privileges accidentally
    if target_user.id == current_user.id and user_in.is_superuser is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot revoke your own superuser privileges.",
        )

    try:
        return crud_user.update_user_admin(
            db, db_user=target_user, user_in=user_in, actor_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/users/{user_id}", response_model=UserResponse, summary="Deactivate user (admin)")
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admin endpoint to deactivate a user account with safeguards for the last superuser."""
    target_user = crud_user.get_user_by_id(db, user_id=user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own account from the admin dashboard.",
        )

    try:
        return crud_user.soft_delete_user(db, db_user=target_user, actor_id=current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================================
# WORKSPACE MANAGEMENT & RESTORE
# ============================================================================

@router.get("/workspaces", response_model=list[WorkspaceResponse], summary="List all workspaces (admin)")
def list_all_workspaces(
    include_deleted: bool = Query(True, description="Include soft-deleted workspaces"),
    db: Session = Depends(get_db),
):
    """Returns all workspaces across the platform."""
    return crud_workspace.get_all_workspaces(db, include_deleted=include_deleted)


@router.delete("/workspaces/{workspace_id}", response_model=WorkspaceResponse, summary="Soft-delete workspace (admin)")
def admin_delete_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-deletes a workspace from the admin dashboard."""
    ws = crud_workspace.get_workspace_by_id(db, workspace_id=workspace_id, include_deleted=True)
    if not ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found.")
    return crud_workspace.soft_delete_workspace(db, db_workspace=ws, actor_id=current_user.id)


@router.post("/workspaces/{workspace_id}/restore", response_model=WorkspaceResponse, summary="Restore workspace (admin)")
def admin_restore_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Restores a soft-deleted workspace."""
    ws = crud_workspace.get_workspace_by_id(db, workspace_id=workspace_id, include_deleted=True)
    if not ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found.")
    return crud_workspace.restore_workspace(db, db_workspace=ws, actor_id=current_user.id)


@router.get("/workspaces/{workspace_id}/members", response_model=list[WorkspaceMemberResponse], summary="List workspace members (admin)")
def admin_list_workspace_members(
    workspace_id: int,
    db: Session = Depends(get_db),
):
    """Retrieves all members belonging to a workspace."""
    ws = crud_workspace.get_workspace_by_id(db, workspace_id=workspace_id, include_deleted=True)
    if not ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found.")
    return crud_workspace.get_workspace_members(db, workspace_id=workspace_id)


@router.post("/workspaces/{workspace_id}/members", response_model=WorkspaceMemberResponse, summary="Add or update workspace member (admin)")
def admin_manage_workspace_member(
    workspace_id: int,
    member_in: WorkspaceMemberAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admin function: assign or update a user's role in a workspace."""
    ws = crud_workspace.get_workspace_by_id(db, workspace_id=workspace_id, include_deleted=False)
    if not ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active workspace not found.")

    target_user = crud_user.get_user_by_email(db, email=member_in.email)
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    membership = crud_workspace.get_workspace_membership(db, workspace_id=workspace_id, user_id=target_user.id)
    if membership:
        return crud_workspace.update_member_role(
            db, membership=membership, new_role=member_in.role, actor_id=current_user.id
        )
    return crud_workspace.add_workspace_member(
        db, workspace_id=workspace_id, user_id=target_user.id, role=member_in.role, actor_id=current_user.id
    )


@router.delete("/workspaces/{workspace_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove workspace member (admin)")
def admin_remove_workspace_member(
    workspace_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admin function: removes a user from a workspace."""
    membership = crud_workspace.get_workspace_membership(db, workspace_id=workspace_id, user_id=user_id)
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found.")
    crud_workspace.remove_workspace_member(db, membership=membership, actor_id=current_user.id)


# ============================================================================
# PROJECT MANAGEMENT & RESTORE
# ============================================================================

@router.get("/projects", response_model=list[ProjectResponse], summary="List all projects (admin)")
def list_all_projects(
    workspace_id: int | None = Query(None, description="Filter by workspace ID"),
    include_deleted: bool = Query(True, description="Include soft-deleted projects"),
    db: Session = Depends(get_db),
):
    """Returns all projects across the platform."""
    projects = crud_project.get_all_projects(db, include_deleted=include_deleted)
    if workspace_id:
        projects = [p for p in projects if p.workspace_id == workspace_id]
    return projects


@router.delete("/projects/{project_id}", response_model=ProjectResponse, summary="Soft-delete project (admin)")
def admin_delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-deletes a project and its tasks/comments from the admin dashboard."""
    project = crud_project.get_project_by_id(db, project_id=project_id, include_deleted=True)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return crud_project.soft_delete_project(db, db_project=project, actor_id=current_user.id)


@router.post("/projects/{project_id}/restore", response_model=ProjectResponse, summary="Restore project (admin)")
def admin_restore_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Restores a soft-deleted project."""
    project = crud_project.get_project_by_id(db, project_id=project_id, include_deleted=True)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    try:
        return crud_project.restore_project(db, db_project=project, actor_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================================
# TASK MANAGEMENT & RESTORE
# ============================================================================

@router.get("/tasks", response_model=PaginatedResponse[TaskResponse], summary="List all tasks (admin)")
def list_all_tasks(
    search: str | None = Query(None),
    status: TaskStatus | None = Query(None),
    priority: TaskPriority | None = Query(None),
    project_id: int | None = Query(None),
    include_deleted: bool = Query(True),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Returns paginated tasks across all projects."""
    items, total = crud_task.get_all_tasks_paginated(
        db,
        search=search,
        status=status,
        priority=priority,
        project_id=project_id,
        page=page,
        size=size,
        include_deleted=include_deleted,
    )
    return PaginatedResponse.create(items=items, total=total, page=page, size=size)


@router.delete("/tasks/{task_id}", response_model=TaskResponse, summary="Soft-delete task (admin)")
def admin_delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-deletes a task from the admin dashboard."""
    task = crud_task.get_task_by_id(db, task_id=task_id, include_deleted=True)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    return crud_task.soft_delete_task(db, db_task=task, actor_id=current_user.id)


@router.post("/tasks/{task_id}/restore", response_model=TaskResponse, summary="Restore task (admin)")
def admin_restore_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Restores a soft-deleted task."""
    task = crud_task.get_task_by_id(db, task_id=task_id, include_deleted=True)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    try:
        return crud_task.restore_task(db, db_task=task, actor_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================================
# COMMENT MODERATION & RESTORE
# ============================================================================

@router.get("/comments", response_model=PaginatedResponse[CommentResponse], summary="List all comments (admin)")
def list_all_comments(
    include_deleted: bool = Query(True),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Returns paginated comments for moderation."""
    items, total = crud_comment.get_all_comments_paginated(
        db, page=page, size=size, include_deleted=include_deleted
    )
    return PaginatedResponse.create(items=items, total=total, page=page, size=size)


@router.delete("/comments/{comment_id}", response_model=CommentResponse, summary="Soft-delete comment (admin)")
def admin_delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-deletes a comment from the admin dashboard."""
    comment = crud_comment.get_comment_by_id(db, comment_id=comment_id, include_deleted=True)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found.")
    return crud_comment.soft_delete_comment(db, db_comment=comment, actor_id=current_user.id)


@router.post("/comments/{comment_id}/restore", response_model=CommentResponse, summary="Restore comment (admin)")
def admin_restore_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Restores a soft-deleted comment."""
    comment = crud_comment.get_comment_by_id(db, comment_id=comment_id, include_deleted=True)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found.")
    try:
        return crud_comment.restore_comment(db, db_comment=comment, actor_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================================
# ROLES & PERMISSIONS
# ============================================================================

@router.get("/roles", response_model=RolesResponse, summary="List roles and permissions matrix")
def get_roles_and_permissions():
    """Returns the platform and workspace role definitions and permission matrix."""
    roles = [
        RoleDefinition(
            role="SUPERUSER",
            scope="GLOBAL",
            description="Global platform administrator with unrestricted access across all workspaces, users, settings, and audit logs.",
            permissions=[
                "users.manage", "users.read", "workspaces.manage", "workspaces.delete",
                "workspaces.restore", "projects.manage", "projects.delete", "projects.restore",
                "tasks.manage", "tasks.delete", "tasks.restore", "comments.moderate",
                "comments.restore", "roles.assign", "audit_logs.read",
            ],
        ),
        RoleDefinition(
            role="OWNER",
            scope="WORKSPACE",
            description="Workspace creator or designated owner with full authority over workspace settings, members, and all projects.",
            permissions=[
                "workspaces.update", "workspaces.delete", "workspaces.members.manage",
                "projects.create", "projects.manage", "projects.delete",
                "tasks.create", "tasks.manage", "tasks.delete", "comments.manage",
            ],
        ),
        RoleDefinition(
            role="ADMIN",
            scope="WORKSPACE",
            description="Workspace administrator capable of managing projects, tasks, and non-owner member roles.",
            permissions=[
                "workspaces.update", "workspaces.members.manage", "projects.create",
                "projects.manage", "projects.delete", "tasks.create", "tasks.manage", "comments.manage",
            ],
        ),
        RoleDefinition(
            role="MEMBER",
            scope="WORKSPACE",
            description="Standard team collaborator who can participate in projects, create and update assigned tasks, and write comments.",
            permissions=[
                "workspaces.read", "projects.read", "tasks.create", "tasks.update_assigned",
                "comments.create", "comments.edit_own",
            ],
        ),
        RoleDefinition(
            role="COMPANY_OWNER",
            scope="COMPANY",
            description="Company creator or designated owner with full administrative control over company settings, billing, members, and workspace creation.",
            permissions=[
                "companies.manage", "companies.invite", "companies.members.manage",
                "workspaces.create", "workspaces.manage", "workspaces.delete",
            ],
        ),
        RoleDefinition(
            role="COMPANY_ADMIN",
            scope="COMPANY",
            description="Company administrator with permission to manage company members, teams, and create workspaces.",
            permissions=[
                "companies.invite", "companies.members.manage", "workspaces.create",
            ],
        ),
        RoleDefinition(
            role="COMPANY_MEMBER",
            scope="COMPANY",
            description="Regular company employee or contractor eligible for assignment to workspaces and projects.",
            permissions=["workspaces.read"],
        ),
        RoleDefinition(
            role="COMPANY_VIEWER",
            scope="COMPANY",
            description="Read-only participant across assigned company workspaces and projects.",
            permissions=["workspaces.read"],
        ),
        RoleDefinition(
            role="VIEWER",
            scope="WORKSPACE",
            description="Read-only participant who can inspect workspace resources, project boards, and task details without write access.",
            permissions=["workspaces.read", "projects.read", "tasks.read", "comments.read"],
        ),
    ]

    permissions = [
        PermissionDetail(code=Permissions.COMPANIES_MANAGE, description="Update company settings, profile, and administrative options", roles=["SUPERUSER", "COMPANY_OWNER"]),
        PermissionDetail(code=Permissions.COMPANIES_INVITE, description="Send expiring invitation links to new company members", roles=["SUPERUSER", "COMPANY_OWNER", "COMPANY_ADMIN"]),
        PermissionDetail(code=Permissions.COMPANIES_MEMBERS_MANAGE, description="Modify company member roles or remove members", roles=["SUPERUSER", "COMPANY_OWNER", "COMPANY_ADMIN"]),
        PermissionDetail(code=Permissions.USERS_MANAGE, description="Activate, deactivate, promote, or edit user profiles", roles=["SUPERUSER"]),
        PermissionDetail(code=Permissions.USERS_READ, description="View platform-wide user lists and registration details", roles=["SUPERUSER"]),
        PermissionDetail(code=Permissions.WORKSPACES_CREATE, description="Create new workspaces within the company", roles=["SUPERUSER", "COMPANY_OWNER", "COMPANY_ADMIN"]),
        PermissionDetail(code=Permissions.WORKSPACES_MEMBERS_MANAGE, description="Add, update role, or remove workspace members", roles=["SUPERUSER", "OWNER", "ADMIN"]),
        PermissionDetail(code=Permissions.WORKSPACES_DELETE, description="Soft-delete workspaces and cascade deletion", roles=["SUPERUSER", "OWNER"]),
        PermissionDetail(code=Permissions.PROJECTS_CREATE, description="Create new projects within an authorized workspace", roles=["SUPERUSER", "OWNER", "ADMIN"]),
        PermissionDetail(code=Permissions.PROJECTS_DELETE, description="Soft-delete projects and cascade deletion", roles=["SUPERUSER", "OWNER", "ADMIN"]),
        PermissionDetail(code=Permissions.TASKS_CREATE, description="Create new tasks in project boards", roles=["SUPERUSER", "OWNER", "ADMIN", "MEMBER"]),
        PermissionDetail(code=Permissions.TASKS_DELETE, description="Soft-delete tasks and their comments", roles=["SUPERUSER", "OWNER", "ADMIN"]),
        PermissionDetail(code=Permissions.COMMENTS_CREATE, description="Post comments and file attachments on tasks", roles=["SUPERUSER", "OWNER", "ADMIN", "MEMBER"]),
        PermissionDetail(code=Permissions.COMMENTS_DELETE, description="Soft-delete or moderate task comments", roles=["SUPERUSER", "OWNER", "ADMIN"]),
        PermissionDetail(code=Permissions.AUDIT_LOGS_READ, description="Inspect platform-wide security and mutation audit logs", roles=["SUPERUSER"]),
    ]

    return RolesResponse(roles=roles, permissions=permissions)


# ============================================================================
# AUDIT LOGS
# ============================================================================

@router.get("/audit-logs", response_model=PaginatedResponse[AuditLogResponse], summary="View system audit logs")
def list_audit_logs(
    actor_id: int | None = Query(None, description="Filter by actor ID"),
    action: str | None = Query(None, description="Filter by action name"),
    resource_type: str | None = Query(None, description="Filter by resource type"),
    resource_id: str | None = Query(None, description="Filter by resource ID"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Returns paginated, searchable system audit trails for administrative review."""
    items, total = crud_audit.get_audit_logs(
        db,
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        page=page,
        size=size,
    )
    return PaginatedResponse.create(items=items, total=total, page=page, size=size)
