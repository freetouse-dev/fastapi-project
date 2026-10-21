from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from project_management_api.api.deps import get_current_user
from project_management_api.core.permissions import (
    can_create_workspace,
    can_manage_company,
    can_manage_company_members,
)
from project_management_api.crud import company as crud_company
from project_management_api.crud import user as crud_user
from project_management_api.db.session import get_db
from project_management_api.models.company import Company, CompanyMember, CompanyRole, CompanyStatus
from project_management_api.models.user import User
from project_management_api.models.workspace import Workspace
from project_management_api.schemas.company import (
    CompanyCreationRequestCreate,
    CompanyCreationRequestResponse,
    CompanyInvitationAccept,
    CompanyInvitationCreate,
    CompanyInvitationResponse,
    CompanyMemberAdd,
    CompanyMemberResponse,
    CompanyMemberRoleUpdate,
    CompanyResponse,
    CompanyUpdate,
)

router = APIRouter()


def require_company_access(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> tuple[Company, CompanyMember | None]:
    """Validates that company exists and user is an active member or superuser."""
    company = crud_company.get_company_by_slug(db, slug=slug)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found.",
        )

    if company.status == CompanyStatus.SUSPENDED and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Company account is suspended.",
        )

    membership = crud_company.get_company_member(db, company_id=company.id, user_id=current_user.id)
    if not membership:
        if current_user.is_superuser:
            return company, None
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this company.",
        )

    if membership.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your membership in this company is not active.",
        )

    return company, membership


def build_company_response(company: Company, membership: CompanyMember | None, db: Session, user: User | None = None) -> CompanyResponse:
    members_count = (
        db.query(CompanyMember)
        .filter(CompanyMember.company_id == company.id, CompanyMember.status == "ACTIVE")
        .count()
    )
    workspaces_count = (
        db.query(Workspace)
        .filter(Workspace.company_id == company.id, Workspace.deleted_at.is_(None))
        .count()
    )

    can_create = False
    if user:
        can_create = can_create_workspace(membership, user)

    return CompanyResponse(
        id=company.id,
        name=company.name,
        slug=company.slug,
        description=company.description,
        status=company.status,
        owner_id=company.owner_id,
        created_by_id=company.created_by_id,
        deleted_at=company.deleted_at,
        created_at=company.created_at,
        updated_at=company.updated_at,
        members_count=members_count,
        workspaces_count=workspaces_count,
        my_role=membership.role if membership else (CompanyRole.COMPANY_OWNER if company.owner_id == getattr(membership, 'user_id', None) else None),
        can_create_workspace=can_create,
    )


# ============================================================================
# COMPANY MEMBERSHIP & OVERVIEW
# ============================================================================

@router.get("/me", response_model=list[CompanyResponse], summary="List companies for current user")
@router.get("/", response_model=list[CompanyResponse], summary="List companies for current user")
def list_my_companies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns all active companies where the current user holds an active membership."""
    user_companies = crud_company.get_companies_for_user(db, user_id=current_user.id)
    result = []
    for company, member in user_companies:
        members_count = (
            db.query(CompanyMember)
            .filter(CompanyMember.company_id == company.id, CompanyMember.status == "ACTIVE")
            .count()
        )
        workspaces_count = (
            db.query(Workspace)
            .filter(Workspace.company_id == company.id, Workspace.deleted_at.is_(None))
            .count()
        )
        result.append(
            CompanyResponse(
                id=company.id,
                name=company.name,
                slug=company.slug,
                description=company.description,
                status=company.status,
                owner_id=company.owner_id,
                created_by_id=company.created_by_id,
                deleted_at=company.deleted_at,
                created_at=company.created_at,
                updated_at=company.updated_at,
                members_count=members_count,
                workspaces_count=workspaces_count,
                my_role=member.role,
                can_create_workspace=can_create_workspace(member, current_user),
            )
        )
    return result


@router.get("/{slug}", response_model=CompanyResponse, summary="Get company details")
def get_company_details(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns details of a specific company if the caller has access."""
    company, membership = require_company_access(slug, db=db, current_user=current_user)
    return build_company_response(company, membership, db, user=current_user)


@router.patch("/{slug}", response_model=CompanyResponse, summary="Update company settings")
def update_company_settings(
    slug: str,
    company_in: CompanyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Allows company owner or admin to update company profile details."""
    company, membership = require_company_access(slug, db=db, current_user=current_user)
    if not can_manage_company(membership, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only company owners or administrators can modify company settings.",
        )

    updated = crud_company.update_company(
        db,
        company=company,
        actor_id=current_user.id,
        name=company_in.name,
        description=company_in.description,
    )
    return build_company_response(updated, membership, db, user=current_user)


# ============================================================================
# COMPANY MEMBERSHIP MANAGEMENT
# ============================================================================

@router.get("/{slug}/members", response_model=list[CompanyMemberResponse], summary="List company members")
def list_company_members(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lists all members of the company."""
    company, _ = require_company_access(slug, db=db, current_user=current_user)
    return crud_company.get_company_members(db, company_id=company.id)


@router.post("/{slug}/members", response_model=CompanyMemberResponse, status_code=status.HTTP_201_CREATED, summary="Add user to company")
def add_member_to_company(
    slug: str,
    member_in: CompanyMemberAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Allows company admin to directly add an existing registered user to the company."""
    company, membership = require_company_access(slug, db=db, current_user=current_user)
    if not can_manage_company_members(membership, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to manage company members.",
        )

    if member_in.role == CompanyRole.COMPANY_OWNER and membership.role != CompanyRole.COMPANY_OWNER and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only company owners can assign the company owner role.",
        )

    target_user = crud_user.get_user_by_email(db, email=member_in.email)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No registered user found with email '{member_in.email}'.",
        )

    try:
        return crud_company.add_company_member(
            db,
            company_id=company.id,
            user_id=target_user.id,
            role=member_in.role,
            actor_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.patch("/{slug}/members/{user_id}", response_model=CompanyMemberResponse, summary="Update member role")
def update_company_member_role(
    slug: str,
    user_id: int,
    role_in: CompanyMemberRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Updates a company member's role."""
    company, membership = require_company_access(slug, db=db, current_user=current_user)
    if not can_manage_company_members(membership, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update company member roles.",
        )

    target_membership = crud_company.get_company_member(db, company_id=company.id, user_id=user_id)
    if not target_membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company member not found.",
        )

    if (role_in.role == CompanyRole.COMPANY_OWNER or target_membership.role == CompanyRole.COMPANY_OWNER) and membership.role != CompanyRole.COMPANY_OWNER and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only company owners can modify company owner roles.",
        )

    try:
        return crud_company.update_company_member_role(
            db,
            membership=target_membership,
            new_role=role_in.role,
            actor_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{slug}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove company member")
def remove_company_member(
    slug: str,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Removes a user from the company."""
    company, membership = require_company_access(slug, db=db, current_user=current_user)
    
    # User can remove themselves or caller must have manage_members permission
    if user_id != current_user.id and not can_manage_company_members(membership, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to remove company members.",
        )

    target_membership = crud_company.get_company_member(db, company_id=company.id, user_id=user_id)
    if not target_membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company member not found.",
        )

    if target_membership.role == CompanyRole.COMPANY_OWNER and membership.role != CompanyRole.COMPANY_OWNER and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only company owners can remove a company owner.",
        )

    try:
        crud_company.remove_company_member(db, membership=target_membership, actor_id=current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================================
# INVITATIONS
# ============================================================================

@router.get("/{slug}/invitations", response_model=list[CompanyInvitationResponse], summary="List company invitations")
def list_company_invitations(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lists pending invitations for the company."""
    company, membership = require_company_access(slug, db=db, current_user=current_user)
    if not can_manage_company_members(membership, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view company invitations.",
        )
    return crud_company.get_company_invitations(db, company_id=company.id)


@router.post("/{slug}/invitations", response_model=CompanyInvitationResponse, status_code=status.HTTP_201_CREATED, summary="Invite member to company")
def invite_member_to_company(
    slug: str,
    invitation_in: CompanyInvitationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Creates a secure, single-use, expiring invitation link to join the company."""
    company, membership = require_company_access(slug, db=db, current_user=current_user)
    if not can_manage_company_members(membership, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to invite members.",
        )

    if invitation_in.role == CompanyRole.COMPANY_OWNER and membership.role != CompanyRole.COMPANY_OWNER and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only company owners can invite another company owner.",
        )

    try:
        invitation, raw_token = crud_company.create_company_invitation(
            db,
            company_id=company.id,
            email=invitation_in.email,
            role=invitation_in.role,
            invited_by_id=current_user.id,
        )
        return CompanyInvitationResponse(
            id=invitation.id,
            company_id=invitation.company_id,
            email=invitation.email,
            role=invitation.role,
            status=invitation.status,
            expires_at=invitation.expires_at,
            created_at=invitation.created_at,
            token=raw_token,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{slug}/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Revoke company invitation")
def revoke_invitation(
    slug: str,
    invitation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Revokes a pending company invitation."""
    company, membership = require_company_access(slug, db=db, current_user=current_user)
    if not can_manage_company_members(membership, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to revoke invitations.",
        )

    success = crud_company.revoke_company_invitation(
        db,
        invitation_id=invitation_id,
        company_id=company.id,
        actor_id=current_user.id,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found or cannot be revoked.",
        )


@router.post("/invitations/accept", response_model=CompanyMemberResponse, summary="Accept company invitation")
def accept_invitation(
    accept_in: CompanyInvitationAccept,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Validates the invitation token and joins the company as the authenticated user."""
    try:
        membership = crud_company.accept_company_invitation(
            db,
            raw_token=accept_in.token,
            user=current_user,
        )
        return membership
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================================
# COMPANY CREATION REQUESTS (HYBRID ONBOARDING)
# ============================================================================

@router.post("/requests", response_model=CompanyCreationRequestResponse, status_code=status.HTTP_201_CREATED, summary="Submit company creation request")
def submit_company_creation_request(
    request_in: CompanyCreationRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submits a new company creation request for review by platform superusers."""
    try:
        req = crud_company.create_company_creation_request(
            db,
            user_id=current_user.id,
            company_name=request_in.company_name,
            company_slug=request_in.company_slug,
            business_description=request_in.business_description,
        )
        return req
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/requests/mine", response_model=list[CompanyCreationRequestResponse], summary="List my company creation requests")
def list_my_creation_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns all company creation requests submitted by the current user."""
    return crud_company.get_company_creation_requests(db, user_id=current_user.id)
