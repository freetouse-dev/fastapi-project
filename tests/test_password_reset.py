from project_management_api.core.security import verify_otp
from project_management_api.crud import otp as crud_otp
from project_management_api.models.otp import OTPPurpose
from project_management_api.models.user import User


def setup_verified_user(client, db_session, email="resetuser@example.com", password="oldpassword123"):
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Reset User", "password": password},
    )
    user = db_session.query(User).filter(User.email == email).first()
    user.is_verified = True
    db_session.commit()
    return user


def test_password_reset_complete_flow(client, db_session):
    email = "resetflow@example.com"
    old_pw = "initialPassword123"
    new_pw = "newBrandPassword123"
    user = setup_verified_user(client, db_session, email=email, password=old_pw)

    # 1. Initiate forgot-password
    forgot_res = client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert forgot_res.status_code == 200
    assert "If your email address is registered" in forgot_res.json()["message"]

    # 2. Extract generated OTP
    otp_record = crud_otp.get_latest_active_otp(
        db_session, user_id=user.id, purpose=OTPPurpose.PASSWORD_RESET
    )
    assert otp_record is not None
    assert otp_record.is_used is False

    plain_otp = None
    for candidate in range(0, 1000000):
        cand_str = f"{candidate:06d}"
        if verify_otp(cand_str, otp_record.hashed_otp):
            plain_otp = cand_str
            break
    assert plain_otp is not None

    # 3. Verify OTP and receive reset_token
    verify_res = client.post(
        "/api/v1/auth/verify-reset-otp",
        json={"email": email, "otp": plain_otp},
    )
    assert verify_res.status_code == 200
    token_data = verify_res.json()
    assert "reset_token" in token_data
    reset_token = token_data["reset_token"]

    # 4. Reset password with reset_token
    reset_res = client.post(
        "/api/v1/auth/reset-password",
        json={"reset_token": reset_token, "new_password": new_pw},
    )
    assert reset_res.status_code == 200
    assert "Password has been reset successfully" in reset_res.json()["message"]

    # 5. Old password no longer works
    old_login = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": old_pw},
    )
    assert old_login.status_code == 401

    # 6. New password works
    new_login = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": new_pw},
    )
    assert new_login.status_code == 200
    assert "access_token" in new_login.json()


def test_forgot_password_unknown_email_returns_generic_message(client):
    # Non-existent email should still return 200 generic message (prevents enumeration)
    res = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "nonexistent_email_12345@example.com"},
    )
    assert res.status_code == 200
    assert "If your email address is registered" in res.json()["message"]


def test_verify_reset_otp_invalid_code(client, db_session):
    email = "badotpuser@example.com"
    setup_verified_user(client, db_session, email=email)
    client.post("/api/v1/auth/forgot-password", json={"email": email})

    # Submit wrong OTP
    bad_verify = client.post(
        "/api/v1/auth/verify-reset-otp",
        json={"email": email, "otp": "000000"},
    )
    assert bad_verify.status_code == 400
    assert "Incorrect code" in bad_verify.json()["detail"]


def test_reset_password_invalid_token(client):
    res = client.post(
        "/api/v1/auth/reset-password",
        json={"reset_token": "fake_or_tampered_token", "new_password": "newpassword123"},
    )
    assert res.status_code == 400
    assert "Invalid or expired password reset token" in res.json()["detail"]


def test_forgot_password_triggers_background_email(client, db_session, monkeypatch):
    """Verifies that forgot-password dispatches emails asynchronously via BackgroundTasks."""
    sent_emails = []

    def fake_send_password_reset_email(to_email: str, full_name: str, otp: str):
        sent_emails.append({"to_email": to_email, "full_name": full_name, "otp": otp})
        return True

    monkeypatch.setattr(
        "project_management_api.api.v1.endpoints.auth.send_password_reset_email",
        fake_send_password_reset_email,
    )

    email = "bg_reset@example.com"
    setup_verified_user(client, db_session, email=email)

    forgot_res = client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert forgot_res.status_code == 200
    assert len(sent_emails) == 1
    assert sent_emails[0]["to_email"] == email
    assert len(sent_emails[0]["otp"]) == 6
