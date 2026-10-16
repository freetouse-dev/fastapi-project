from project_management_api.models.otp import OTPPurpose, UserOTP
from project_management_api.models.user import User


def test_register_and_login_flow(client, db_session):
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

    # 3. Attempting login BEFORE email verification should be rejected with 403 Forbidden
    login_data = {
        "username": "testuser@example.com",
        "password": "strongpassword123",
    }
    unverified_login = client.post("/api/v1/auth/login", data=login_data)
    assert unverified_login.status_code == 403
    assert "Email address not verified" in unverified_login.json()["detail"]

    # 4. Mark user as verified to test verified login
    user = db_session.query(User).filter(User.email == "testuser@example.com").first()
    user.is_verified = True
    db_session.commit()

    # 5. Login now succeeds
    login_response = client.post("/api/v1/auth/login", data=login_data)
    assert login_response.status_code == 200
    token_json = login_response.json()
    assert "access_token" in token_json
    assert token_json["token_type"] == "bearer"
    token = token_json["access_token"]

    # 6. Access protected profile route
    headers = {"Authorization": f"Bearer {token}"}
    me_response = client.get("/api/v1/users/me", headers=headers)
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "testuser@example.com"


def test_login_invalid_password(client, db_session):
    register_payload = {
        "email": "anotheruser@example.com",
        "full_name": "Another User",
        "password": "correctpassword123",
    }
    client.post("/api/v1/auth/register", json=register_payload)

    # Verify user
    user = db_session.query(User).filter(User.email == "anotheruser@example.com").first()
    user.is_verified = True
    db_session.commit()

    # Login with wrong password
    bad_login = {
        "username": "anotheruser@example.com",
        "password": "wrongpassword",
    }
    response = client.post("/api/v1/auth/login", data=bad_login)
    assert response.status_code == 401
