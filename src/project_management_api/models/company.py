import enum
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from project_management_api.db.session import Base


class CompanyStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    PENDING_APPROVAL = "PENDING_APPROVAL"


class CompanyRole(str, enum.Enum):
    COMPANY_OWNER = "COMPANY_OWNER"
    COMPANY_ADMIN = "COMPANY_ADMIN"
    MEMBER = "MEMBER"
    VIEWER = "VIEWER"


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[CompanyStatus] = mapped_column(
        Enum(CompanyStatus),
        default=CompanyStatus.ACTIVE,
        nullable=False,
    )
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    deleted_by_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    owner = relationship("User", foreign_keys=[owner_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
    deleted_by = relationship("User", foreign_keys=[deleted_by_id])
    members = relationship("CompanyMember", back_populates="company", cascade="all, delete-orphan")
    workspaces = relationship("Workspace", back_populates="company", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Company id={self.id} slug={self.slug} status={self.status}>"


class CompanyMember(Base):
    __tablename__ = "company_members"
    __table_args__ = (
        UniqueConstraint("company_id", "user_id", name="uq_company_user"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[CompanyRole] = mapped_column(
        Enum(CompanyRole),
        default=CompanyRole.MEMBER,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)
    can_create_workspace: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    invited_by_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    company = relationship("Company", back_populates="members")
    user = relationship("User", foreign_keys=[user_id])
    invited_by = relationship("User", foreign_keys=[invited_by_id])

    def __repr__(self) -> str:
        return f"<CompanyMember company_id={self.company_id} user_id={self.user_id} role={self.role}>"


class CompanyCreationRequest(Base):
    __tablename__ = "company_creation_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    company_name: Mapped[str] = mapped_column(String(100), nullable=False)
    company_slug: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    business_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False, index=True)
    reviewed_by_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    rejection_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    requester = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by_id])

    def __repr__(self) -> str:
        return f"<CompanyCreationRequest id={self.id} company_name={self.company_name} status={self.status}>"


class CompanyInvitation(Base):
    __tablename__ = "company_invitations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    role: Mapped[CompanyRole] = mapped_column(
        Enum(CompanyRole),
        default=CompanyRole.MEMBER,
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    invited_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    company = relationship("Company")
    inviter = relationship("User", foreign_keys=[invited_by_id])

    def __repr__(self) -> str:
        return f"<CompanyInvitation id={self.id} company_id={self.company_id} email={self.email} status={self.status}>"
