from fastapi import Depends, HTTPException, status

from project_management_api.api.deps import get_current_user
from project_management_api.models.company import Company, CompanyMember, CompanyRole
from project_management_api.models.project import ProjectMember, ProjectRole
from project_management_api.models.user import User
from project_management_api.models.workspace import WorkspaceMember, WorkspaceRole


class Permissions:
    COMPANIES_CREATE_REQUEST = "companies.create_request"
    COMPANIES_MANAGE = "companies.manage"
    COMPANIES_INVITE = "companies.invite"
    COMPANIES_MEMBERS_MANAGE = "companies.members.manage"

    WORKSPACES_CREATE = "workspaces.create"
    WORKSPACES_READ = "workspaces.read"
    WORKSPACES_UPDATE = "workspaces.update"
    WORKSPACES_DELETE = "workspaces.delete"
    WORKSPACES_MEMBERS_MANAGE = "workspaces.members.manage"

    PROJECTS_CREATE = "projects.create"
    PROJECTS_READ = "projects.read"
    PROJECTS_UPDATE = "projects.update"
    PROJECTS_DELETE = "projects.delete"
    PROJECTS_MEMBERS_MANAGE = "projects.members.manage"

    TASKS_CREATE = "tasks.create"
    TASKS_READ = "tasks.read"
    TASKS_UPDATE = "tasks.update"
    TASKS_DELETE = "tasks.delete"

    COMMENTS_CREATE = "comments.create"
    COMMENTS_READ = "comments.read"
    COMMENTS_UPDATE = "comments.update"
    COMMENTS_DELETE = "comments.delete"

    USERS_READ = "users.read"
    USERS_MANAGE = "users.manage"
    ROLES_ASSIGN = "roles.assign"
    ROLES_REVOKE = "roles.revoke"
    AUDIT_LOGS_READ = "audit_logs.read"


def require_superuser(current_user: User = Depends(get_current_user)) -> User:
    """Ensures caller has platform-wide superuser privileges."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required.",
        )
    return current_user


def can_manage_company(membership: CompanyMember | None, user: User) -> bool:
    """Checks if user can update company settings (OWNER or ADMIN or superuser)."""
    if user.is_superuser:
        return True
    if not membership:
        return False
    return membership.role in [CompanyRole.COMPANY_OWNER, CompanyRole.COMPANY_ADMIN]


def can_manage_company_members(membership: CompanyMember | None, user: User) -> bool:
    """Checks if user can invite or manage members of the company (OWNER or ADMIN or superuser)."""
    if user.is_superuser:
        return True
    if not membership:
        return False
    return membership.role in [CompanyRole.COMPANY_OWNER, CompanyRole.COMPANY_ADMIN]


def can_create_workspace(membership: CompanyMember | None, user: User) -> bool:
    """Checks if user can create a workspace in the company (OWNER, ADMIN, explicitly granted, or superuser)."""
    if user.is_superuser:
        return True
    if not membership:
        return False
    if membership.role in [CompanyRole.COMPANY_OWNER, CompanyRole.COMPANY_ADMIN]:
        return True
    return bool(getattr(membership, "can_create_workspace", False))


def can_manage_workspace(membership: WorkspaceMember | None, user: User) -> bool:
    """Checks if user can update/delete the workspace (OWNER or ADMIN)."""
    if user.is_superuser:
        return True
    if not membership:
        return False
    return membership.role in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]


def can_manage_workspace_members(membership: WorkspaceMember | None, user: User) -> bool:
    """Checks if user can manage members of the workspace."""
    if user.is_superuser:
        return True
    if not membership:
        return False
    return membership.role in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]


def can_manage_project(
    ws_membership: WorkspaceMember | None,
    proj_membership: ProjectMember | None,
    user: User,
) -> bool:
    """Checks if user can update/delete a project."""
    if user.is_superuser:
        return True
    if ws_membership and ws_membership.role in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]:
        return True
    if proj_membership and proj_membership.role == ProjectRole.PROJECT_LEAD:
        return True
    return False

