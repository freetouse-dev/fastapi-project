import pytest
from project_management_api.models.project import ProjectRole
from project_management_api.models.user import User
from project_management_api.models.workspace import WorkspaceRole


def create_verified_user(db_session, email: str, full_name: str, is_superuser: bool = False) -> User:
    from project_management_api.core.security import hash_password
    user = User(
        email=email,
        full_name=full_name,
        hashed_password=hash_password("password123"),
        is_active=True,
        is_verified=True,
        is_superuser=is_superuser,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def get_token(client, email: str, password: str = "password123") -> str:
    res = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]


def test_workspace_rbac_and_owner_protection(client, db_session):
    # 1. Setup users: Owner, Admin, Member, Viewer, Superuser
    owner = create_verified_user(db_session, "owner@example.com", "Workspace Owner")
    admin = create_verified_user(db_session, "admin@example.com", "Workspace Admin")
    member = create_verified_user(db_session, "member@example.com", "Workspace Member")
    viewer = create_verified_user(db_session, "viewer@example.com", "Workspace Viewer")
    outsider = create_verified_user(db_session, "outsider@example.com", "Outsider User")

    owner_token = get_token(client, owner.email)
    admin_token = get_token(client, admin.email)
    member_token = get_token(client, member.email)
    viewer_token = get_token(client, viewer.email)
    outsider_token = get_token(client, outsider.email)

    # 2. Owner creates workspace
    create_res = client.post(
        "/api/v1/workspaces/",
        json={"name": "Alpha Corp", "description": "Primary workspace"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert create_res.status_code == 201
    slug = create_res.json()["slug"]

    # 3. Owner adds Admin, Member, Viewer
    client.post(
        f"/api/v1/workspaces/{slug}/members",
        json={"email": admin.email, "role": "ADMIN"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    client.post(
        f"/api/v1/workspaces/{slug}/members",
        json={"email": member.email, "role": "MEMBER"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    client.post(
        f"/api/v1/workspaces/{slug}/members",
        json={"email": viewer.email, "role": "VIEWER"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    # 4. Outsider cannot access workspace
    res = client.get(f"/api/v1/workspaces/{slug}", headers={"Authorization": f"Bearer {outsider_token}"})
    assert res.status_code == 403

    # 5. Member cannot update workspace
    res = client.patch(
        f"/api/v1/workspaces/{slug}",
        json={"name": "Hacked Name"},
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert res.status_code == 403

    # 6. Admin can update workspace
    res = client.patch(
        f"/api/v1/workspaces/{slug}",
        json={"name": "Alpha Corp Renamed"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    assert res.json()["name"] == "Alpha Corp Renamed"

    # 7. Admin CANNOT promote anyone to OWNER
    res = client.patch(
        f"/api/v1/workspaces/{slug}/members/{member.id}",
        json={"role": "OWNER"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 403

    # 8. Admin CANNOT remove or demote the OWNER
    res = client.delete(
        f"/api/v1/workspaces/{slug}/members/{owner.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 403

    # 9. Owner CANNOT demote themselves if they are the last active OWNER
    res = client.patch(
        f"/api/v1/workspaces/{slug}/members/{owner.id}",
        json={"role": "MEMBER"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res.status_code == 400
    assert "Cannot demote the last remaining owner" in res.json()["detail"]

    # 10. Owner CANNOT remove themselves if they are the last active OWNER
    res = client.delete(
        f"/api/v1/workspaces/{slug}/members/{owner.id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res.status_code == 400
    assert "Cannot remove the last remaining owner" in res.json()["detail"]


def test_project_and_task_crud_rbac(client, db_session):
    owner = create_verified_user(db_session, "pow@example.com", "Proj Owner")
    member = create_verified_user(db_session, "pmem@example.com", "Proj Member")
    viewer = create_verified_user(db_session, "pview@example.com", "Proj Viewer")

    owner_token = get_token(client, owner.email)
    member_token = get_token(client, member.email)
    viewer_token = get_token(client, viewer.email)

    # 1. Create workspace and add members
    ws_res = client.post(
        "/api/v1/workspaces/",
        json={"name": "Beta Workspace"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    slug = ws_res.json()["slug"]

    client.post(
        f"/api/v1/workspaces/{slug}/members",
        json={"email": member.email, "role": "MEMBER"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    client.post(
        f"/api/v1/workspaces/{slug}/members",
        json={"email": viewer.email, "role": "VIEWER"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    # 2. Member tries to create project -> rejected
    res = client.post(
        f"/api/v1/workspaces/{slug}/projects/",
        json={"name": "Beta Mobile", "key": "BMOB"},
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert res.status_code == 403

    # 3. Owner creates project
    res = client.post(
        f"/api/v1/workspaces/{slug}/projects/",
        json={"name": "Beta Mobile", "key": "BMOB"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res.status_code == 201

    # 4. Add member as CONTRIBUTOR to project
    client.post(
        f"/api/v1/workspaces/{slug}/projects/BMOB/members",
        json={"email": member.email, "role": "CONTRIBUTOR"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    # 5. Add viewer as VIEWER to project
    client.post(
        f"/api/v1/workspaces/{slug}/projects/BMOB/members",
        json={"email": viewer.email, "role": "VIEWER"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    # 6. Viewer cannot create task
    res = client.post(
        f"/api/v1/workspaces/{slug}/projects/BMOB/tasks/",
        json={"title": "Viewer task", "description": "Should fail"},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert res.status_code == 403

    # 7. Contributor creates task
    res = client.post(
        f"/api/v1/workspaces/{slug}/projects/BMOB/tasks/",
        json={"title": "Fix login bug", "description": "Issue with auth"},
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert res.status_code == 201
    task_num = res.json()["task_number"]
    assert task_num == 1

    # 8. Contributor updates task
    res = client.patch(
        f"/api/v1/workspaces/{slug}/projects/BMOB/tasks/{task_num}",
        json={"status": "IN_PROGRESS"},
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "IN_PROGRESS"

    # 9. Viewer posts comment -> rejected
    res = client.post(
        f"/api/v1/workspaces/{slug}/projects/BMOB/tasks/{task_num}/comments/",
        json={"content": "Looks good"},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert res.status_code == 403

    # 10. Contributor posts comment -> succeeds
    res = client.post(
        f"/api/v1/workspaces/{slug}/projects/BMOB/tasks/{task_num}/comments/",
        json={"content": "Working on it now"},
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert res.status_code == 201
    comment_id = res.json()["id"]

    # 11. Contributor updates own comment
    res = client.patch(
        f"/api/v1/workspaces/{slug}/projects/BMOB/tasks/{task_num}/comments/{comment_id}",
        json={"content": "Working on it now - updated"},
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert res.status_code == 200
    assert res.json()["content"] == "Working on it now - updated"
