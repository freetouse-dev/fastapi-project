# Step 32: Email Verification Workflow Endpoints

## 1. Overview
In this step, we implemented the complete email verification lifecycle. Newly registered users are created with `is_verified = False`, issued a cryptographically secure 6-digit verification code, and sent an activation email. Login attempts by unverified accounts are strictly blocked with HTTP `403 Forbidden` until verified via `POST /api/v1/auth/verify-email`.

---

## 2. Concepts Learned

### 2.1 Unverified Account Lifecycle
1. **Registration:** `POST /api/v1/auth/register` creates the user account with `is_verified=False` and immediately dispatches an OTP.
2. **Access Control:** `POST /api/v1/auth/login` checks `if not user.is_verified` and raises `403 Forbidden` (`"Email address not verified. Please verify your email before logging in."`).
3. **Verification:** `POST /api/v1/auth/verify-email` verifies the submitted OTP, sets `is_verified = True`, and marks the OTP as used.
4. **Resend Invalidation:** `POST /api/v1/auth/resend-verification-otp` invalidates any previous active codes before issuing a new one, preventing replay attacks.

### 2.2 Attempt Limiting & Brute-Force Defense
- Each submission increments `otp_record.attempts`.
- If `attempts >= settings.otp_max_attempts` (default 5), the OTP is immediately invalidated.
- Response discloses only remaining attempts (`"Incorrect code. 4 attempt(s) remaining."`), protecting against automated guessing.

---

## 3. Implementation Details

- **Schemas:** `src/project_management_api/schemas/auth.py`:
  - `VerifyEmailRequest`, `ResendOTPRequest`, `AuthMessageResponse`.
- **CRUD Operations:** `src/project_management_api/crud/otp.py`:
  - `create_user_otp`, `get_latest_active_otp`, `verify_user_otp`, `invalidate_user_otps`.
- **Endpoints:** Updated `src/project_management_api/api/v1/endpoints/auth.py`:
  - `POST /register`: Issues verification OTP.
  - `POST /verify-email`: Validates OTP and updates account status.
  - `POST /resend-verification-otp`: Invalidates prior codes and sends fresh OTP.
  - `POST /login`: Enforces `is_verified` guard.
- **Automated Tests:** Added `tests/test_email_verification.py` and updated `tests/test_auth.py` and `tests/test_workspaces.py`.

---

## 4. Verification & Testing
```bash
uv run pytest -v
```
Output:
```
tests/test_auth.py::test_register_and_login_flow PASSED                  [ 14%]
tests/test_auth.py::test_login_invalid_password PASSED                   [ 28%]
tests/test_email_verification.py::test_email_verification_complete_flow PASSED [ 42%]
tests/test_email_verification.py::test_resend_verification_otp PASSED    [ 57%]
tests/test_health.py::test_root_endpoint PASSED                          [ 71%]
tests/test_health.py::test_health_check_endpoint PASSED                  [ 85%]
tests/test_workspaces.py::test_create_and_access_workspace PASSED        [100%]

========================= 7 passed, 1 warning in 6.09s =========================
```
