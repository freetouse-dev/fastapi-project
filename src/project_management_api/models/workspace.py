import enum
from datetime import datetime
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from project_management_api.db.session import Base

class WorkspaceRole(str, enum.Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"
    VIEWER = "VIEWER"

class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    company_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True
    )
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

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
    company = relationship("Company", back_populates="workspaces")
    deleted_by = relationship("User", foreign_keys=[deleted_by_id])
    members = relationship("WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Workspace id={self.id} slug={self.slug}>"


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"
    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="uq_workspace_user"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workspace_id: Mapped[int] = mapped_column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[WorkspaceRole] = mapped_column(
        Enum(WorkspaceRole),
        default=WorkspaceRole.MEMBER,
        nullable=False,
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    workspace = relationship("Workspace", back_populates="members")
    user = relationship("User")

    def __repr__(self) -> str:
        return f"<WorkspaceMember workspace_id={self.workspace_id} user_id={self.user_id} role={self.role}>"


class WorkspaceAccessRequestType(str, enum.Enum):
    CREATE_WORKSPACE = "CREATE_WORKSPACE"
    JOIN_WORKSPACE = "JOIN_WORKSPACE"


class WorkspaceAccessRequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class WorkspaceAccessRequest(Base):
    __tablename__ = "workspace_access_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    request_type: Mapped[WorkspaceAccessRequestType] = mapped_column(
        Enum(WorkspaceAccessRequestType),
        default=WorkspaceAccessRequestType.CREATE_WORKSPACE,
        nullable=False,
    )
    workspace_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True
    )
    requested_role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[WorkspaceAccessRequestStatus] = mapped_column(
        Enum(WorkspaceAccessRequestStatus),
        default=WorkspaceAccessRequestStatus.PENDING,
        nullable=False,
        index=True,
    )
    reviewer_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    decision_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

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

    company = relationship("Company")
    user = relationship("User", foreign_keys=[user_id])
    workspace = relationship("Workspace", foreign_keys=[workspace_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])

    def __repr__(self) -> str:
        return f"<WorkspaceAccessRequest id={self.id} type={self.request_type} status={self.status}>"