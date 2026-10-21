import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

from project_management_api.crud import audit as crud_audit
from project_management_api.models.company import (
    Company,
    CompanyCreationRequest,
    CompanyInvitation,
    CompanyMember,
    CompanyRole,
    CompanyStatus,
)
from project_management_api.models.user import User


def get_company_by_id(db: Session, company_id: int, include_deleted: bool = False) -> Company | None:
    query = db.query(Company).filter(Company.id == company_id)
    if not include_deleted:
        query = query.filter(Company.deleted_at.is_(None))
    return query.first()


def get_company_by_slug(db: Session, slug: str, include_deleted: bool = False) -> Company | None:
    query = db.query(Company).filter(Company.slug == slug)
    if not include_deleted:
        query = query.filter(Company.deleted_at.is_(None))
    return query.first()


def get_companies_for_user(db: Session, user_id: int) -> list[tuple[Company, CompanyMember]]:
    """Returns active companies where the user has an active membership."""
    return (
        db.query(Company, CompanyMember)
        .join(CompanyMember, CompanyMember.company_id == Company.id)
        .filter(
            CompanyMember.user_id == user_id,
            CompanyMember.status == "ACTIVE",
            Company.deleted_at.is_(None),
            Company.status == CompanyStatus.ACTIVE,
        )
        .all()
    )


def create_company(
    db: Session,
    name: str,
    slug: str,
    owner_id: int,
    description: str | None = None,
    created_by_id: int | None = None,
) -> Company:
    creator_id = created_by_id or owner_id
    company = Company(
        name=name,
        slug=slug,
        description=description,
        status=CompanyStatus.ACTIVE,
        owner_id=owner_id,
        created_by_id=creator_id,
    )
    db.add(company)
    db.flush()

    # Automatically add owner as COMPANY_OWNER
    owner_member = CompanyMember(
        company_id=company.id,
        user_id=owner_id,
        role=CompanyRole.COMPANY_OWNER,
        status="ACTIVE",
    )
    db.add(owner_member)

    crud_audit.create_audit_log(
        db,
        action="COMPANY_CREATED",
        resource_type="COMPANY",
        resource_id=company.id,
        actor_id=creator_id,
        details={"name": company.name, "slug": company.slug, "owner_id": owner_id},
    )
    db.commit()
    db.refresh(company)
    return company


def update_company(
    db: Session,
    company: Company,
    actor_id: int,
    name: str | None = None,
    description: str | None = None,
    status: CompanyStatus | None = None,
) -> Company:
    if name is not None:
        company.name = name
    if description is not None:
        company.description = description
    if status is not None:
        company.status = status

    crud_audit.create_audit_log(
        db,
        action="COMPANY_UPDATED",
        resource_type="COMPANY",
        resource_id=company.id,
        actor_id=actor_id,
        details={"name": company.name, "status": str(company.status)},
    )
    db.commit()
    db.refresh(company)
    return company


def soft_delete_company(db: Session, company: Company, deleted_by_id: int) -> Company:
    company.deleted_at = datetime.now(timezone.utc)
    company.deleted_by_id = deleted_by_id
    company.status = CompanyStatus.SUSPENDED

    crud_audit.create_audit_log(
        db,
        action="COMPANY_DELETED",
        resource_type="COMPANY",
        resource_id=company.id,
        actor_id=deleted_by_id,
        details={"name": company.name, "slug": company.slug},
    )
    db.commit()
    db.refresh(company)
    return company


def restore_company(db: Session, company: Company, restored_by_id: int) -> Company:
    company.deleted_at = None
    company.deleted_by_id = None
    company.status = CompanyStatus.ACTIVE

    crud_audit.create_audit_log(
        db,
        action="COMPANY_RESTORED",
        resource_type="COMPANY",
        resource_id=company.id,
        actor_id=restored_by_id,
        details={"name": company.name, "slug": company.slug},
    )
    db.commit()
    db.refresh(company)
    return company


def get_company_member(db: Session, company_id: int, user_id: int) -> CompanyMember | None:
    return (
        db.query(CompanyMember)
        .filter(CompanyMember.company_id == company_id, CompanyMember.user_id == user_id)
        .first()
    )


def get_company_members(db: Session, company_id: int) -> list[CompanyMember]:
    return (
        db.query(CompanyMember)
        .filter(CompanyMember.company_id == company_id)
        .order_by(CompanyMember.joined_at.asc())
        .all()
    )


def add_company_member(
    db: Session,
    company_id: int,
    user_id: int,
    role: CompanyRole,
    invited_by_id: int | None = None,
    actor_id: int | None = None,
) -> CompanyMember:
    inviter = invited_by_id or actor_id
    member = CompanyMember(
        company_id=company_id,
        user_id=user_id,
        role=role,
        status="ACTIVE",
        invited_by_id=inviter,
    )
    db.add(member)
    crud_audit.create_audit_log(
        db,
        action="COMPANY_MEMBER_ADDED",
        resource_type="COMPANY",
        resource_id=company_id,
        actor_id=inviter,
        details={"user_id": user_id, "role": role.value},
    )
    db.commit()
    db.refresh(member)
    return member


def update_company_member_role(
    db: Session,
    membership: CompanyMember,
    new_role: CompanyRole,
    actor_id: int,
) -> CompanyMember:
    old_role = membership.role.value
    membership.role = new_role
    crud_audit.create_audit_log(
        db,
        action="COMPANY_MEMBER_ROLE_UPDATED",
        resource_type="COMPANY",
        resource_id=membership.company_id,
        actor_id=actor_id,
        details={"user_id": membership.user_id, "old_role": old_role, "new_role": new_role.value},
    )
    db.commit()
    db.refresh(membership)
    return membership


def remove_company_member(db: Session, membership: CompanyMember, actor_id: int) -> None:
    company_id = membership.company_id
    user_id = membership.user_id
    db.delete(membership)
    crud_audit.create_audit_log(
        db,
        action="COMPANY_MEMBER_REMOVED",
        resource_type="COMPANY",
        resource_id=company_id,
        actor_id=actor_id,
        details={"removed_user_id": user_id},
    )
    db.commit()


# Company Creation Requests
def create_company_creation_request(
    db: Session,
    user_id: int,
    company_name: str,
    company_slug: str,
    business_description: str | None = None,
) -> CompanyCreationRequest:
    req = CompanyCreationRequest(
        user_id=user_id,
        company_name=company_name,
        company_slug=company_slug,
        business_description=business_description,
        status="PENDING",
    )
    db.add(req)
    crud_audit.create_audit_log(
        db,
        action="COMPANY_CREATION_REQUESTED",
        resource_type="COMPANY_REQUEST",
        resource_id=0,
        actor_id=user_id,
        details={"company_name": company_name, "company_slug": company_slug},
    )
    db.commit()
    db.refresh(req)
    return req


def get_company_creation_requests(
    db: Session,
    status: str | None = None,
    user_id: int | None = None,
) -> list[CompanyCreationRequest]:
    query = db.query(CompanyCreationRequest)
    if status:
        query = query.filter(CompanyCreationRequest.status == status)
    if user_id:
        query = query.filter(CompanyCreationRequest.user_id == user_id)
    return query.order_by(CompanyCreationRequest.created_at.desc()).all()


def get_company_creation_request_by_id(db: Session, request_id: int) -> CompanyCreationRequest | None:
    return db.query(CompanyCreationRequest).filter(CompanyCreationRequest.id == request_id).first()


def approve_company_creation_request(
    db: Session,
    req: CompanyCreationRequest,
    reviewer_id: int,
) -> Company:
    # 1. Update request status
    req.status = "APPROVED"
    req.reviewed_by_id = reviewer_id
    req.reviewed_at = datetime.now(timezone.utc)

    # 2. Check if slug exists; if so, make unique
    slug = req.company_slug
    existing = get_company_by_slug(db, slug=slug, include_deleted=True)
    if existing:
        slug = f"{slug}-{req.id}"

    # 3. Create the Company
    company = Company(
        name=req.company_name,
        slug=slug,
        description=req.business_description,
        status=CompanyStatus.ACTIVE,
        owner_id=req.user_id,
        created_by_id=reviewer_id,
    )
    db.add(company)
    db.flush()

    # 4. Assign requester as COMPANY_OWNER
    member = CompanyMember(
        company_id=company.id,
        user_id=req.user_id,
        role=CompanyRole.COMPANY_OWNER,
        status="ACTIVE",
    )
    db.add(member)

    # 5. Audit logs
    crud_audit.create_audit_log(
        db,
        action="COMPANY_REQUEST_APPROVED",
        resource_type="COMPANY_REQUEST",
        resource_id=req.id,
        actor_id=reviewer_id,
        details={"company_id": company.id, "approved_user_id": req.user_id},
    )
    crud_audit.create_audit_log(
        db,
        action="COMPANY_CREATED",
        resource_type="COMPANY",
        resource_id=company.id,
        actor_id=reviewer_id,
        details={"name": company.name, "slug": company.slug, "owner_id": req.user_id},
    )
    db.commit()
    db.refresh(company)
    return company


def reject_company_creation_request(
    db: Session,
    req: CompanyCreationRequest,
    reviewer_id: int,
    rejection_reason: str | None = None,
) -> CompanyCreationRequest:
    req.status = "REJECTED"
    req.reviewed_by_id = reviewer_id
    req.reviewed_at = datetime.now(timezone.utc)
    req.rejection_reason = rejection_reason

    crud_audit.create_audit_log(
        db,
        action="COMPANY_REQUEST_REJECTED",
        resource_type="COMPANY_REQUEST",
        resource_id=req.id,
        actor_id=reviewer_id,
        details={"rejection_reason": rejection_reason},
    )
    db.commit()
    db.refresh(req)
    return req


# Company Invitations
def create_company_invitation(
    db: Session,
    company_id: int,
    email: str,
    role: CompanyRole,
    invited_by_id: int,
) -> tuple[CompanyInvitation, str]:
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    invitation = CompanyInvitation(
        company_id=company_id,
        email=email.strip().lower(),
        role=role,
        token_hash=token_hash,
        invited_by_id=invited_by_id,
        status="PENDING",
        expires_at=expires_at,
    )
    db.add(invitation)
    crud_audit.create_audit_log(
        db,
        action="COMPANY_INVITATION_CREATED",
        resource_type="COMPANY_INVITATION",
        resource_id=0,
        actor_id=invited_by_id,
        details={"company_id": company_id, "email": email, "role": role.value},
    )
    db.commit()
    db.refresh(invitation)
    return invitation, raw_token


def get_company_invitations(
    db: Session,
    company_id: int,
    status: str | None = None,
) -> list[CompanyInvitation]:
    query = db.query(CompanyInvitation).filter(CompanyInvitation.company_id == company_id)
    if status:
        query = query.filter(CompanyInvitation.status == status)
    return query.order_by(CompanyInvitation.created_at.desc()).all()


def revoke_company_invitation(db: Session, invitation_id: int, company_id: int, actor_id: int) -> bool:
    invitation = (
        db.query(CompanyInvitation)
        .filter(CompanyInvitation.id == invitation_id, CompanyInvitation.company_id == company_id)
        .first()
    )
    if not invitation or invitation.status != "PENDING":
        return False
    invitation.status = "REVOKED"
    crud_audit.create_audit_log(
        db,
        action="COMPANY_INVITATION_REVOKED",
        resource_type="COMPANY_INVITATION",
        resource_id=invitation.id,
        actor_id=actor_id,
        details={"company_id": company_id, "email": invitation.email},
    )
    db.commit()
    return True


def accept_company_invitation(db: Session, raw_token: str, user: User) -> CompanyMember:
    token_hash = hashlib.sha256(raw_token.strip().encode()).hexdigest()
    invitation = (
        db.query(CompanyInvitation)
        .filter(CompanyInvitation.token_hash == token_hash, CompanyInvitation.status == "PENDING")
        .first()
    )
    if not invitation:
        raise ValueError("Invalid or expired invitation token.")

    now = datetime.now(timezone.utc)
    exp = invitation.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if exp < now:
        invitation.status = "EXPIRED"
        db.commit()
        raise ValueError("Invitation has expired.")

    # Validate recipient email matches accepting user
    if invitation.email.lower() != user.email.lower():
        raise ValueError(f"This invitation was sent to {invitation.email}, not your current account.")

    # Check if user already belongs to this company
    existing = get_company_member(db, company_id=invitation.company_id, user_id=user.id)
    if existing:
        invitation.status = "ACCEPTED"
        db.commit()
        return existing

    member = CompanyMember(
        company_id=invitation.company_id,
        user_id=user.id,
        role=invitation.role,
        status="ACTIVE",
        invited_by_id=invitation.invited_by_id,
    )
    db.add(member)
    invitation.status = "ACCEPTED"

    crud_audit.create_audit_log(
        db,
        action="COMPANY_INVITATION_ACCEPTED",
        resource_type="COMPANY_INVITATION",
        resource_id=invitation.id,
        actor_id=user.id,
        details={"company_id": invitation.company_id, "role": invitation.role.value},
    )
    db.commit()
    db.refresh(member)
    return member
