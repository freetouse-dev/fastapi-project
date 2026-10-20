from project_management_api.core.security import verify_otp
from project_management_api.crud import otp as crud_otp
from project_management_api.models.otp import OTPPurpose
from project_management_api.models.user import User


def test_email_verification_complete_flow(client, db_session):
    # 1. Register user (created with is_verified=False)
    reg_payload = {
        "email": "verifytest@example.com",
        "full_name": "Verify Tester",
        "password": "mypassword123",
    }
    res = client.post("/api/v1/auth/register", json=reg_payload)
    assert res.status_code == 201

    user = db_session.query(User).filter(User.email == "verifytest@example.com").first()
    assert user is not None
    assert user.is_verified is False

    # 2. Check that active OTP was generated and hashed
    otp_record = crud_otp.get_latest_active_otp(
        db_session, user_id=user.id, purpose=OTPPurpose.EMAIL_VERIFICATION
    )
    assert otp_record is not None
    assert otp_record.is_used is False
    assert len(otp_record.hashed_otp) == 64  # SHA-256 HMAC hex digest

    # 3. Test wrong OTP rejection
    wrong_payload = {"email": "verifytest@example.com", "otp": "000000"}
    bad_res = client.post("/api/v1/auth/verify-email", json=wrong_payload)
    assert bad_res.status_code == 400
    assert "Incorrect code" in bad_res.json()["detail"]

    # 4. Extract plain OTP from database candidate match for testing
    plain_otp = None
    for candidate in range(0, 1000000):
        cand_str = f"{candidate:06d}"
        if verify_otp(cand_str, otp_record.hashed_otp):
            plain_otp = cand_str
            break
    assert plain_otp is not None

    # 5. Submit valid OTP
    good_payload = {"email": "verifytest@example.com", "otp": plain_otp}
    good_res = client.post("/api/v1/auth/verify-email", json=good_payload)
    assert good_res.status_code == 200
    assert "Email verified successfully" in good_res.json()["message"]

    # 6. Verify user in database is now marked verified
    db_session.refresh(user)
    assert user.is_verified is True

    # 7. Submitting same OTP again fails (single-use enforcement)
    reused_res = client.post("/api/v1/auth/verify-email", json=good_payload)
    assert reused_res.status_code == 200  # Returns "Email is already verified"


def test_resend_verification_otp(client, db_session):
    # Register user
    reg_payload = {
        "email": "resendtest@example.com",
        "full_name": "Resend Tester",
        "password": "mypassword123",
    }
    client.post("/api/v1/auth/register", json=reg_payload)
    user = db_session.query(User).filter(User.email == "resendtest@example.com").first()

    first_otp = crud_otp.get_latest_active_otp(
        db_session, user_id=user.id, purpose=OTPPurpose.EMAIL_VERIFICATION
    )

    # Resend OTP
    resend_res = client.post(
        "/api/v1/auth/resend-verification-otp",
        json={"email": "resendtest@example.com"},
    )
    assert resend_res.status_code == 200

    # Old OTP must be invalidated
    db_session.refresh(first_otp)
    assert first_otp.is_used is True

    # New active OTP exists
    second_otp = crud_otp.get_latest_active_otp(
        db_session, user_id=user.id, purpose=OTPPurpose.EMAIL_VERIFICATION
    )
    assert second_otp.id != first_otp.id
    assert second_otp.is_used is False


def test_registration_and_resend_trigger_background_email(client, monkeypatch):
    """Verifies that registration and OTP resend dispatch emails asynchronously via BackgroundTasks."""
    sent_emails = []

    def fake_send_verification_email(to_email: str, full_name: str, otp: str):
        sent_emails.append({"to_email": to_email, "full_name": full_name, "otp": otp})
        return True

    monkeypatch.setattr(
        "project_management_api.api.v1.endpoints.auth.send_verification_email",
        fake_send_verification_email,
    )

    reg_payload = {
        "email": "bg_verify@example.com",
        "full_name": "Background User",
        "password": "securepassword123",
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    assert len(sent_emails) == 1
    assert sent_emails[0]["to_email"] == "bg_verify@example.com"
    assert sent_emails[0]["full_name"] == "Background User"
    assert len(sent_emails[0]["otp"]) == 6

    # Resend OTP
    resend_res = client.post(
        "/api/v1/auth/resend-verification-otp",
        json={"email": "bg_verify@example.com"},
    )
    assert resend_res.status_code == 200
    assert len(sent_emails) == 2
    assert sent_emails[1]["to_email"] == "bg_verify@example.com"
    assert len(sent_emails[1]["otp"]) == 6
