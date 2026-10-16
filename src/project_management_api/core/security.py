import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

from project_management_api.config import get_settings

settings = get_settings()
password_hash = PasswordHash((BcryptHasher(),))


def hash_password(password: str) -> str:
    """Hashes a plaintext password using bcrypt."""
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a stored hash."""
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(subject: str | int, expires_delta: timedelta | None = None) -> str:
    """Creates a signed JSON Web Token (JWT) for user authentication."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode = {
        "sub": str(subject),
        "type": "access",
        "exp": expire,
        "iat": now,
    }
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def generate_otp(length: int = 6) -> str:
    """Generates a cryptographically secure numeric OTP."""
    digits = "0123456789"
    return "".join(secrets.choice(digits) for _ in range(length))


def hash_otp(otp: str) -> str:
    """Computes a SHA-256 HMAC digest of an OTP salted with the application secret key."""
    return hmac.new(
        settings.secret_key.encode("utf-8"),
        otp.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_otp(plain_otp: str, hashed_otp: str) -> bool:
    """Compares a plain OTP with its stored HMAC digest using constant-time comparison."""
    computed_hash = hash_otp(plain_otp)
    return hmac.compare_digest(computed_hash, hashed_otp)


def create_password_reset_token(user_id: int) -> str:
    """Creates a short-lived, single-use JWT granting permission to reset password."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.password_reset_token_expire_minutes)
    to_encode = {
        "sub": str(user_id),
        "type": "password_reset",
        "exp": expire,
        "iat": now,
    }
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def verify_password_reset_token(token: str) -> int | None:
    """Validates a password reset token and returns the user_id if valid."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        if payload.get("type") != "password_reset":
            return None
        user_id_str = payload.get("sub")
        return int(user_id_str) if user_id_str else None
    except (InvalidTokenError, ValueError):
        return None
