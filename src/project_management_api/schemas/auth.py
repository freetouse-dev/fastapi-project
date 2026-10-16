from pydantic import BaseModel, EmailStr, Field


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$", description="6-digit verification code")


class ResendOTPRequest(BaseModel):
    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class VerifyResetOTPRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$", description="6-digit reset code")


class VerifyResetOTPResponse(BaseModel):
    reset_token: str
    token_type: str = "bearer"
    message: str = "OTP verified successfully. You may now submit your new password."


class ResetPasswordRequest(BaseModel):
    reset_token: str = Field(..., description="Short-lived reset authorization token")
    new_password: str = Field(..., min_length=8, max_length=128, description="New plaintext password (min 8 chars)")


class AuthMessageResponse(BaseModel):
    message: str
    detail: str | None = None
