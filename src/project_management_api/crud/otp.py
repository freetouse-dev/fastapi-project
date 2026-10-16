from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from project_management_api.config import get_settings
from project_management_api.core.security import generate_otp, hash_otp, verify_otp
from project_management_api.models.otp import OTPPurpose, UserOTP

settings = get_settings()


def invalidate_user_otps(db: Session, user_id: int, purpose: OTPPurpose) -> None:
    """Marks all pending OTPs for the user and purpose as used/invalid."""
    db.query(UserOTP).filter(
        UserOTP.user_id == user_id,
        UserOTP.purpose == purpose,
        UserOTP.is_used == False,
    ).update({"is_used": True}, synchronize_session=False)
    db.commit()


def create_user_otp(db: Session, user_id: int, purpose: OTPPurpose) -> tuple[UserOTP, str]:
    """
    Invalidates existing active OTPs for this purpose, generates a new secure 6-digit OTP,
    hashes it, and persists the record. Returns (UserOTP, plain_otp).
    """
    # 1. Invalidate any prior active OTPs
    invalidate_user_otps(db, user_id=user_id, purpose=purpose)

    # 2. Generate and hash OTP
    plain_otp = generate_otp(length=6)
    hashed_otp = hash_otp(plain_otp)

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.otp_expire_minutes)

    db_otp = UserOTP(
        user_id=user_id,
        hashed_otp=hashed_otp,
        purpose=purpose,
        expires_at=expires_at,
        attempts=0,
        is_used=False,
    )
    db.add(db_otp)
    db.commit()
    db.refresh(db_otp)
    return db_otp, plain_otp


def get_latest_active_otp(db: Session, user_id: int, purpose: OTPPurpose) -> UserOTP | None:
    """Finds the most recent unused OTP for the given user and purpose."""
    return (
        db.query(UserOTP)
        .filter(
            UserOTP.user_id == user_id,
            UserOTP.purpose == purpose,
            UserOTP.is_used == False,
        )
        .order_by(UserOTP.created_at.desc())
        .first()
    )


def verify_user_otp(db: Session, user_id: int, purpose: OTPPurpose, candidate_otp: str) -> tuple[bool, str]:
    """
    Validates a submitted candidate OTP against the active database record.
    Enforces expiration, attempt limits, and single-use invalidation.
    Returns (is_valid: bool, reason_message: str).
    """
    otp_record = get_latest_active_otp(db, user_id=user_id, purpose=purpose)
    if not otp_record:
        return False, "No active verification code found. Please request a new code."

    now = datetime.now(timezone.utc)
    # Ensure expires_at has timezone info
    record_expires_at = otp_record.expires_at
    if record_expires_at.tzinfo is None:
        record_expires_at = record_expires_at.replace(tzinfo=timezone.utc)

    # 1. Expiration Check
    if now > record_expires_at:
        otp_record.is_used = True
        db.commit()
        return False, "Verification code has expired. Please request a new code."

    # 2. Attempt Limit Check
    if otp_record.attempts >= settings.otp_max_attempts:
        otp_record.is_used = True
        db.commit()
        return False, "Maximum verification attempts exceeded. Please request a new code."

    # 3. Increment attempts
    otp_record.attempts += 1

    # 4. Check OTP match
    if not verify_otp(candidate_otp, otp_record.hashed_otp):
        db.commit()
        remaining = settings.otp_max_attempts - otp_record.attempts
        return False, f"Incorrect code. {remaining} attempt(s) remaining."

    # 5. Success -> Invalidate OTP
    otp_record.is_used = True
    db.commit()
    return True, "Verification successful."
