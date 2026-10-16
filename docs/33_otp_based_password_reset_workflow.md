# Step 33: OTP-Based Password Reset Workflow

## 1. Overview
In this step, we designed and implemented a secure, 3-phase password recovery mechanism. Users initiate a password reset request via `POST /forgot-password`, verify the 6-digit email-delivered code via `POST /verify-reset-otp` to receive a short-lived authorization token, and submit their new password via `POST /reset-password`.

---

## 2. Concepts Learned

### 2.1 Defense Against Account Enumeration
- If an endpoint returns `"User with this email not found"`, malicious actors can automate dictionary attacks to discover which email addresses possess registered accounts.
- `POST /forgot-password` always returns a generic response:
  ```json
  {
    "message": "If your email address is registered, a password reset code has been sent."
  }
  ```
  This preserves user privacy while informing legitimate users.

### 2.2 Short-Lived Single-Use Reset Tokens
- After successfully validating the OTP, the server issues a signed JWT (`type="password_reset"`, valid for 15 minutes).
- `POST /reset-password` requires this `reset_token`. This decouples OTP validation from password submission while guaranteeing that only users who passed the OTP challenge can mutate passwords.

### 2.3 Post-Reset Invalidation
- Once the new password is encrypted with bcrypt and persisted, all prior active reset challenges for that user are marked `is_used = True`, preventing replay or replay reuse.
- The previous password immediately ceases to work.

---

## 3. Implementation Details

- **Schemas:** `src/project_management_api/schemas/auth.py`:
  - `ForgotPasswordRequest`, `VerifyResetOTPRequest`, `VerifyResetOTPResponse`, `ResetPasswordRequest`.
- **Endpoints:** `src/project_management_api/api/v1/endpoints/auth.py`:
  - `POST /forgot-password`: Issues OTP with `purpose=PASSWORD_RESET`.
  - `POST /verify-reset-otp`: Validates code, invalidates OTP, issues signed `reset_token`.
  - `POST /reset-password`: Validates `reset_token`, hashes new password, updates database.
- **Automated Tests:** `tests/test_password_reset.py`:
  - `test_password_reset_complete_flow`
  - `test_forgot_password_unknown_email_returns_generic_message`
  - `test_verify_reset_otp_invalid_code`
  - `test_reset_password_invalid_token`

---

## 4. Verification & Testing
```bash
uv run pytest -v
```
Output:
```
tests/test_auth.py::test_register_and_login_flow PASSED                  [  9%]
tests/test_auth.py::test_login_invalid_password PASSED                   [ 18%]
tests/test_email_verification.py::test_email_verification_complete_flow PASSED [ 27%]
tests/test_email_verification.py::test_resend_verification_otp PASSED    [ 36%]
tests/test_health.py::test_root_endpoint PASSED                          [ 45%]
tests/test_health.py::test_health_check_endpoint PASSED                  [ 54%]
tests/test_password_reset.py::test_password_reset_complete_flow PASSED   [ 63%]
tests/test_password_reset.py::test_forgot_password_unknown_email_returns_generic_message PASSED [ 72%]
tests/test_password_reset.py::test_verify_reset_otp_invalid_code PASSED  [ 81%]
tests/test_password_reset.py::test_reset_password_invalid_token PASSED   [ 90%]
tests/test_workspaces.py::test_create_and_access_workspace PASSED        [100%]

======================== 11 passed, 1 warning in 9.27s =========================
```
All 11 tests passed with 100% success.
