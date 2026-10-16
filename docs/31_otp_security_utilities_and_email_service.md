# Step 31: OTP Security Utilities & Reusable Email Service

## 1. Overview
In this step, we built the security foundation for one-time passwords and created a reusable email service. We implemented cryptographically secure OTP generation, constant-time HMAC-SHA256 digest hashing, short-lived password reset tokens, and professional HTML/plain-text email templates with graceful development/testing fallbacks.

---

## 2. Concepts Learned

### 2.1 Cryptographically Secure Entropy (`secrets`)
- Standard pseudo-random number generators (`random`) are deterministic and predictable.
- `secrets.choice()` sources entropy directly from the OS kernel (`/dev/urandom`), producing unpredictable 6-digit codes resistant to guessing attacks.

### 2.2 Constant-Time HMAC Verification
- `hash_otp(otp)` computes an HMAC-SHA256 signature using `settings.secret_key` as salt.
- `verify_otp()` uses `hmac.compare_digest()` to compare candidate hashes in constant time, preventing timing-attack vulnerabilities.

### 2.3 Short-Lived Password Reset Tokens
- After verifying an OTP, issuing a short-lived signed JWT (`type="password_reset"`) grants the user a one-time window to submit their new password without exposing raw user IDs or relying on persistent database session states.

### 2.4 Decoupled Email Architecture
- `src/project_management_api/services/email.py` separates message construction (HTML + plain text) and transport (SMTP) from business routes.
- When running in `development` or `testing`, missing SMTP credentials fall back to structured console logging, preventing test failures or API hangs while maintaining visibility into issued OTPs.

---

## 3. Implementation Details

- **Security Utilities:** `src/project_management_api/core/security.py`:
  - `generate_otp(length=6) -> str`
  - `hash_otp(otp: str) -> str`
  - `verify_otp(plain_otp: str, hashed_otp: str) -> bool`
  - `create_password_reset_token(user_id: int) -> str`
  - `verify_password_reset_token(token: str) -> int | None`
- **Email Service:** `src/project_management_api/services/email.py`:
  - `send_email(to_email, subject, html_content, text_content) -> bool`
  - `send_verification_email(to_email, full_name, otp) -> bool`
  - `send_password_reset_email(to_email, full_name, otp) -> bool`

---

## 4. Verification & Testing
- Executed unit verification script:
  - OTP generation produced 6-digit numeric string.
  - Hashing and constant-time verification passed for matching and mismatched codes.
  - Password reset token was signed, decoded, and validated.
  - Email templates rendered and logged cleanly under `development` mode.
- Executed Pytest suite: `uv run pytest -v` -> 5 passed (100% success rate, no regression).
