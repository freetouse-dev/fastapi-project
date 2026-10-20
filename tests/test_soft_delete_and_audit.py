import pytest
from project_management_api.models.audit import AuditLog
from project_management_api.models.comment import TaskComment
from project_management_api.models.project import Project
from project_management_api.models.task import Task
from project_management_api.models.user import User
from project_management_api.models.workspace import Workspace
from tests.conftest import create_verified_user, get_token


def test_soft_delete_cascades_and_audit_logs(client, db_session):
    # 1. Create Superuser and regular Owner
    superuser = create_verified_user(db_session, "super@example.com", "Super User", is_superuser=True)
    owner = create_verified_user(db_session, "wsowner@example.com", "Ws Owner")

    super_token = get_token(client, superuser.email)
    owner_token = get_token(client, owner.email)

    # 2. Owner creates workspace, project, task, comment
    ws_res = client.post(
        "/api/v1/workspaces/",
        json={"name": "Cascade Test Org"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    slug = ws_res.json()["slug"]
    ws_id = ws_res.json()["id"]

    proj_res = client.post(
        f"/api/v1/workspaces/{slug}/projects/",
        json={"name": "Project Cascade", "key": "CASC"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    proj_id = proj_res.json()["id"]

    task_res = client.post(
        f"/api/v1/workspaces/{slug}/projects/CASC/tasks/",
        json={"title": "Cascade Task", "description": "Will be soft deleted"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    task_id = task_res.json()["id"]

    comment_res = client.post(
        f"/api/v1/workspaces/{slug}/projects/CASC/tasks/1/comments/",
        json={"content": "Cascade Comment"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    comment_id = comment_res.json()["id"]

    # Verify rows exist in DB and active
    assert db_session.query(Workspace).filter(Workspace.id == ws_id, Workspace.deleted_at.is_(None)).count() == 1
    assert db_session.query(Project).filter(Project.id == proj_id, Project.deleted_at.is_(None)).count() == 1
    assert db_session.query(Task).filter(Task.id == task_id, Task.deleted_at.is_(None)).count() == 1
    assert db_session.query(TaskComment).filter(TaskComment.id == comment_id, TaskComment.deleted_at.is_(None)).count() == 1

    # 3. Soft-delete the Workspace
    del_res = client.delete(
        f"/api/v1/workspaces/{slug}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert del_res.status_code == 204

    # 4. Verify DB rows are NOT physically deleted, but soft-deleted with timestamps and deleted_by_id
    ws_row = db_session.query(Workspace).filter(Workspace.id == ws_id).first()
    assert ws_row is not None
    assert ws_row.deleted_at is not None
    assert ws_row.deleted_by_id == owner.id

    proj_row = db_session.query(Project).filter(Project.id == proj_id).first()
    assert proj_row is not None
    assert proj_row.deleted_at is not None
    assert proj_row.deleted_by_id == owner.id

    task_row = db_session.query(Task).filter(Task.id == task_id).first()
    assert task_row is not None
    assert task_row.deleted_at is not None
    assert task_row.deleted_by_id == owner.id

    comment_row = db_session.query(TaskComment).filter(TaskComment.id == comment_id).first()
    assert comment_row is not None
    assert comment_row.deleted_at is not None
    assert comment_row.deleted_by_id == owner.id

    # 5. Normal GET endpoints must return 404 for soft-deleted workspace
    get_res = client.get(f"/api/v1/workspaces/{slug}", headers={"Authorization": f"Bearer {owner_token}"})
    assert get_res.status_code == 404

    # 6. Verify Audit Logs were recorded
    audit_logs = db_session.query(AuditLog).filter(AuditLog.actor_id == owner.id).all()
    actions = [a.action for a in audit_logs]
    assert "WORKSPACE_CREATED" in actions
    assert "PROJECT_CREATED" in actions
    assert "TASK_CREATED" in actions
    assert "COMMENT_CREATED" in actions
    assert "WORKSPACE_DELETED" in actions


def test_admin_dashboard_endpoints_and_superuser_guard(client, db_session):
    superuser = create_verified_user(db_session, "superadmin@example.com", "Super Admin", is_superuser=True)
    regular_user = create_verified_user(db_session, "regular@example.com", "Regular User", is_superuser=False)

    super_token = get_token(client, superuser.email)
    regular_token = get_token(client, regular_user.email)

    # 1. Regular user trying to access admin endpoints -> 403 Forbidden
    res = client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {regular_token}"})
    assert res.status_code == 403

    res = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {regular_token}"})
    assert res.status_code == 403

    res = client.get("/api/v1/admin/audit-logs", headers={"Authorization": f"Bearer {regular_token}"})
    assert res.status_code == 403

    # 2. Superuser accessing stats
    res = client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {super_token}"})
    assert res.status_code == 200
    stats = res.json()
    assert "total_users" in stats
    assert "total_workspaces" in stats
    assert stats["total_users"] >= 2

    # 3. Superuser listing users
    res = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {super_token}"})
    assert res.status_code == 200
    users_data = res.json()
    assert users_data["total"] >= 2

    # 4. Superuser modifying user status
    res = client.patch(
        f"/api/v1/admin/users/{regular_user.id}",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {super_token}"},
    )
    assert res.status_code == 200
    assert res.json()["is_active"] is False

    # 5. Superuser cannot revoke their own superuser privileges
    res = client.patch(
        f"/api/v1/admin/users/{superuser.id}",
        json={"is_superuser": False},
        headers={"Authorization": f"Bearer {super_token}"},
    )
    assert res.status_code == 400
    assert "cannot revoke your own superuser privileges" in res.json()["detail"]

    # 6. Superuser viewing audit logs
    res = client.get("/api/v1/admin/audit-logs", headers={"Authorization": f"Bearer {super_token}"})
    assert res.status_code == 200
    logs_data = res.json()
    assert logs_data["total"] >= 1
