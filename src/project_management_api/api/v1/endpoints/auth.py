from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from project_management_api.core.security import create_access_token, verify_password
from project_management_api.crud import otp as crud_otp
from project_management_api.crud import user as crud_user
from project_management_api.db.session import get_db
from project_management_api.models.otp import OTPPurpose
from project_management_api.schemas.auth import (
    AuthMessageResponse,
    ForgotPasswordRequest,
    ResendOTPRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
    VerifyResetOTPRequest,
    VerifyResetOTPResponse,
)
from project_management_api.schemas.token import Token
from project_management_api.schemas.user import UserCreate, UserResponse
from project_management_api.services.email import send_verification_email

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user and initiate email verification",
)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """Registers a new user in unverified state and sends an email verification OTP."""
    existing_user = crud_user.get_user_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    # 1. Create user with is_verified=False
    db_user = crud_user.create_user(db, user_in=user_in)

    # 2. Generate and email verification OTP
    _, plain_otp = crud_otp.create_user_otp(
        db, user_id=db_user.id, purpose=OTPPurpose.EMAIL_VERIFICATION
    )
    send_verification_email(to_email=db_user.email, full_name=db_user.full_name, otp=plain_otp)

    return db_user


@router.post(
    "/verify-email",
    response_model=AuthMessageResponse,
    summary="Verify email address with OTP",
)
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    """Verifies the user's email address using the received OTP."""
    user = crud_user.get_user_by_email(db, email=payload.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    if user.is_verified:
        return AuthMessageResponse(
            message="Email is already verified. You can log in directly."
        )

    is_valid, message = crud_otp.verify_user_otp(
        db,
        user_id=user.id,
        purpose=OTPPurpose.EMAIL_VERIFICATION,
        candidate_otp=payload.otp,
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    # Mark user as verified
    user.is_verified = True
    db.commit()

    return AuthMessageResponse(
        message="Email verified successfully. You can now log in."
    )


@router.post(
    "/resend-verification-otp",
    response_model=AuthMessageResponse,
    summary="Resend verification OTP",
)
def resend_verification_otp(payload: ResendOTPRequest, db: Session = Depends(get_db)):
    """Invalidates old OTP and issues a fresh verification code."""
    user = crud_user.get_user_by_email(db, email=payload.email)
    if not user:
        # Generic message to avoid email enumeration
        return AuthMessageResponse(
            message="If your email is registered, a new verification code has been sent."
        )

    if user.is_verified:
        return AuthMessageResponse(
            message="Email is already verified. You can log in directly."
        )

    # Issue new OTP (automatically invalidates previous active OTPs)
    _, plain_otp = crud_otp.create_user_otp(
        db, user_id=user.id, purpose=OTPPurpose.EMAIL_VERIFICATION
    )
    send_verification_email(to_email=user.email, full_name=user.full_name, otp=plain_otp)

    return AuthMessageResponse(
        message="A new verification code has been sent to your email."
    )


@router.post(
    "/login",
    response_model=Token,
    summary="User Login",
)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Authenticates credentials and returns a JWT access token for active, verified users."""
    user = crud_user.get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account.",
        )

    # Check Email Verification
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email address not verified. Please verify your email before logging in.",
        )

    access_token = create_access_token(subject=user.id)
    return Token(access_token=access_token, token_type="bearer")


@router.post(
    "/forgot-password",
    response_model=AuthMessageResponse,
    summary="Request a password reset OTP",
)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Initiates password reset by emailing an OTP. Uses generic response to prevent email enumeration."""
    from project_management_api.services.email import send_password_reset_email

    generic_response = AuthMessageResponse(
        message="If your email address is registered, a password reset code has been sent."
    )

    user = crud_user.get_user_by_email(db, email=payload.email)
    if not user or not user.is_active:
        return generic_response

    # Generate and email password reset OTP
    _, plain_otp = crud_otp.create_user_otp(
        db, user_id=user.id, purpose=OTPPurpose.PASSWORD_RESET
    )
    send_password_reset_email(to_email=user.email, full_name=user.full_name, otp=plain_otp)

    return generic_response


@router.post(
    "/verify-reset-otp",
    response_model=VerifyResetOTPResponse,
    summary="Verify password reset OTP and receive reset authorization token",
)
def verify_reset_otp(payload: VerifyResetOTPRequest, db: Session = Depends(get_db)):
    """Validates password reset OTP and issues a short-lived reset token."""
    from project_management_api.core.security import create_password_reset_token

    user = crud_user.get_user_by_email(db, email=payload.email)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or verification code.",
        )

    is_valid, message = crud_otp.verify_user_otp(
        db,
        user_id=user.id,
        purpose=OTPPurpose.PASSWORD_RESET,
        candidate_otp=payload.otp,
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    # Issue short-lived, single-use password reset token
    reset_token = create_password_reset_token(user_id=user.id)
    return VerifyResetOTPResponse(reset_token=reset_token)


@router.post(
    "/reset-password",
    response_model=AuthMessageResponse,
    summary="Reset password using reset authorization token",
)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Validates reset authorization token and updates the user's password."""
    from project_management_api.core.security import (
        hash_password,
        verify_password_reset_token,
    )

    user_id = verify_password_reset_token(payload.reset_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token. Please restart the password reset process.",
        )

    user = crud_user.get_user_by_id(db, user_id=user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account not found or inactive.",
        )

    # Update password and invalidate any outstanding OTPs
    user.hashed_password = hash_password(payload.new_password)
    crud_otp.invalidate_user_otps(db, user_id=user.id, purpose=OTPPurpose.PASSWORD_RESET)
    db.commit()

    return AuthMessageResponse(
        message="Password has been reset successfully. You can now log in with your new password."
    )
