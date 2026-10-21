from tests.conftest import create_verified_user, get_token


def test_create_and_access_workspace(client, db_session):
    owner = create_verified_user(db_session, "workspaceowner@example.com", "Workspace Owner", with_company=True)
    token = get_token(client, owner.email)
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
    outsider = create_verified_user(db_session, "outsider@example.com", "Outsider", with_company=True)
    outsider_token = get_token(client, outsider.email)
    outsider_headers = {"Authorization": f"Bearer {outsider_token}"}
    forbidden_res = client.get("/api/v1/workspaces/testing-workspace", headers=outsider_headers)
    assert forbidden_res.status_code == 403
