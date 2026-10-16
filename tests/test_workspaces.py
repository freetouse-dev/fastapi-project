from project_management_api.models.user import User


def get_auth_token(client, db_session, email: str, password: str = "password123") -> str:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Workspace User", "password": password},
    )
    user = db_session.query(User).filter(User.email == email).first()
    user.is_verified = True
    db_session.commit()

    res = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    return res.json()["access_token"]


def test_create_and_access_workspace(client, db_session):
    token = get_auth_token(client, db_session, "workspaceowner@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create workspace
    create_payload = {
        "name": "Testing Workspace",
        "description": "Workspace for automated tests",
    }
    create_res = client.post("/api/v1/workspaces/", json=create_payload, headers=headers)
    assert create_res.status_code == 201
    ws_data = create_res.json()
    assert ws_data["slug"] == "testing-workspace"
    assert ws_data["name"] == "Testing Workspace"

    # 2. List my workspaces
    list_res = client.get("/api/v1/workspaces/", headers=headers)
    assert list_res.status_code == 200
    workspaces = list_res.json()
    assert len(workspaces) == 1
    assert workspaces[0]["slug"] == "testing-workspace"

    # 3. Unauthorized outsider cannot view workspace
    outsider_token = get_auth_token(client, db_session, "outsider@example.com")
    outsider_headers = {"Authorization": f"Bearer {outsider_token}"}
    forbidden_res = client.get("/api/v1/workspaces/testing-workspace", headers=outsider_headers)
    assert forbidden_res.status_code == 403
