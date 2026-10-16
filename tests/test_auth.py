def test_register_and_login_flow(client):
    # 1. Register a new user
    register_payload = {
        "email": "testuser@example.com",
        "full_name": "Test User",
        "password": "strongpassword123",
    }
    response = client.post("/api/v1/auth/register", json=register_payload)
    assert response.status_code == 201
    user_data = response.json()
    assert user_data["email"] == register_payload["email"]
    assert user_data["full_name"] == register_payload["full_name"]
    assert "hashed_password" not in user_data

    # 2. Duplicate registration should be rejected
    dup_response = client.post("/api/v1/auth/register", json=register_payload)
    assert dup_response.status_code == 400

    # 3. Login with credentials
    login_data = {
        "username": "testuser@example.com",
        "password": "strongpassword123",
    }
    login_response = client.post("/api/v1/auth/login", data=login_data)
    assert login_response.status_code == 200
    token_json = login_response.json()
    assert "access_token" in token_json
    assert token_json["token_type"] == "bearer"
    token = token_json["access_token"]

    # 4. Access protected profile route
    headers = {"Authorization": f"Bearer {token}"}
    me_response = client.get("/api/v1/users/me", headers=headers)
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "testuser@example.com"


def test_login_invalid_password(client):
    register_payload = {
        "email": "anotheruser@example.com",
        "full_name": "Another User",
        "password": "correctpassword123",
    }
    client.post("/api/v1/auth/register", json=register_payload)

    # Login with wrong password
    bad_login = {
        "username": "anotheruser@example.com",
        "password": "wrongpassword",
    }
    response = client.post("/api/v1/auth/login", data=bad_login)
    assert response.status_code == 401
