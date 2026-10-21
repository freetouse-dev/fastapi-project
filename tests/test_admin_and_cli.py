import argparse
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from project_management_api.cli import create_superuser_command
from project_management_api.core.security import create_access_token
from project_management_api.crud.user import create_user, get_user_by_email
from project_management_api.models.user import User
from project_management_api.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from project_management_api.models.project import Project, ProjectStatus
from project_management_api.models.task import Task, TaskPriority, TaskStatus
from project_management_api.models.comment import TaskComment
from project_management_api.schemas.user import UserCreate


def test_cli_create_and_promote_superuser(db_session: Session):
    """Verifies that the CLI creates a new superuser and promotes an existing user."""
    # 1. Create new superuser via CLI args
    args = argparse.Namespace(
        email="clisuper@example.com",
        password="SuperPassword123!",
        full_name="CLI Administrator",
        promote=False,
    )
    result = create_superuser_command(args, db=db_session)
    assert result == 0

    user = get_user_by_email(db_session, "clisuper@example.com")
    assert user is not None
    assert user.is_superuser is True
    assert user.is_active is True
    assert user.is_verified is True

    # 2. Promote existing regular user
    reg_user = create_user(
        db_session,
        UserCreate(email="regular@example.com", full_name="Regular Member", password="Password123!"),
    )
    assert reg_user.is_superuser is False

    promote_args = argparse.Namespace(
        email="regular@example.com",
        password=None,
        full_name=None,
        promote=True,
    )
    res_promote = create_superuser_command(promote_args, db=db_session)
    assert res_promote == 0

    db_session.refresh(reg_user)
    assert reg_user.is_superuser is True


def test_cli_validation_failures(db_session: Session):
    """Verifies that the CLI safely handles duplicate accounts, invalid email, and short passwords."""
    create_user(
        db_session,
        UserCreate(email="dup_user@example.com", full_name="Existing User", password="Password123!"),
    )
    # 1. Duplicate user without --promote flag fails
    dup_args = argparse.Namespace(
        email="dup_user@example.com",
        password="ValidPassword123!",
        full_name="Duplicate User",
        promote=False,
    )
    assert create_superuser_command(dup_args, db=db_session) == 1

    # 2. Invalid email format fails
    invalid_email_args = argparse.Namespace(
        email="invalid-email-format",
        password="ValidPassword123!",
        full_name="Bad Email",
        promote=False,
    )
    assert create_superuser_command(invalid_email_args, db=db_session) == 1

    # 3. Short password (< 8 chars) fails
    short_pw_args = argparse.Namespace(
        email="newuser_pw@example.com",
        password="123",
        full_name="Short PW",
        promote=False,
    )
    assert create_superuser_command(short_pw_args, db=db_session) == 1

    # 4. Short full name (< 2 chars) fails
    short_name_args = argparse.Namespace(
        email="newuser_name@example.com",
        password="ValidPassword123!",
        full_name="A",
        promote=False,
    )
    assert create_superuser_command(short_name_args, db=db_session) == 1


def test_admin_endpoints_and_restore_workflow(client: TestClient, db_session: Session):
    """Verifies admin endpoints, soft-delete, restore, and last superuser protection."""
    # Create superuser
    admin = create_user(
        db_session,
        UserCreate(email="admin_test@example.com", full_name="Admin Test", password="Password123!"),
    )
    admin.is_superuser = True
    admin.is_verified = True
    db_session.commit()

    token = create_access_token(subject=admin.id)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Test GET /api/v1/admin/stats
    stats_resp = client.get("/api/v1/admin/stats", headers=headers)
    assert stats_resp.status_code == 200
    assert "total_users" in stats_resp.json()

    # 2. Test GET /api/v1/admin/roles
    roles_resp = client.get("/api/v1/admin/roles", headers=headers)
    assert roles_resp.status_code == 200
    assert len(roles_resp.json()["roles"]) >= 5

    # 3. Create a workspace, soft-delete it via admin, then restore it
    ws = Workspace(name="Admin WS", slug="admin-ws", owner_id=admin.id)
    db_session.add(ws)
    db_session.commit()
    db_session.refresh(ws)

    del_ws = client.delete(f"/api/v1/admin/workspaces/{ws.id}", headers=headers)
    assert del_ws.status_code == 200
    assert del_ws.json()["deleted_at"] is not None

    restore_ws = client.post(f"/api/v1/admin/workspaces/{ws.id}/restore", headers=headers)
    assert restore_ws.status_code == 200
    assert restore_ws.json()["deleted_at"] is None

    # 4. Test Last Superuser Demotion Protection
    demote_resp = client.patch(
        f"/api/v1/admin/users/{admin.id}",
        json={"is_superuser": False},
        headers=headers,
    )
    # Blocked by self-demotion or last-superuser guard
    assert demote_resp.status_code == 400

    # 5. Test User Dashboard API endpoint
    dash_resp = client.get("/api/v1/users/me/dashboard", headers=headers)
    assert dash_resp.status_code == 200
    assert "assigned_tasks" in dash_resp.json()
    assert "status_counts" in dash_resp.json()
