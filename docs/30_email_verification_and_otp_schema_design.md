# Step 30: Email Verification & OTP Database Schema Design

## 1. Overview
In this step, we updated our configuration and database schema to support secure, OTP-based authentication workflows. We added `is_verified` to the `User` model, introduced a dedicated `UserOTP` model for cryptographic OTP storage, configured email and OTP settings, and applied migration `070f62f02a7b` without affecting any existing features.

---

## 2. Concepts Learned

### 2.1 Hashed OTP Storage vs Plaintext
- **Security Vulnerability of Plaintext OTPs:** Storing raw 6-digit codes in the database leaves users vulnerable if a read replica or database backup is exposed.
- **Hashed OTPs:** Like passwords, OTPs are stored as one-way cryptographic hashes. When a user submits an OTP, it is hashed and compared against the stored hash.

### 2.2 Dedicated `user_otps` Table vs Adding Columns to `users`
- Users require OTPs for multiple distinct purposes (`EMAIL_VERIFICATION`, `PASSWORD_RESET`).
- Storing OTPs in a dedicated association table keeps the `users` model clean, allows querying active challenges by purpose, tracks verification attempts, and enforces single-use invalidation (`is_used`).

### 2.3 Brute-Force & Replay Protection
- `expires_at`: Timestamp (e.g. 10 minutes) after which the code is strictly rejected.
- `attempts`: Counter tracking consecutive failed attempts. Once `attempts >= otp_max_attempts` (default 5), the OTP is locked.
- `is_used`: Marked `True` upon successful verification to prevent replay attacks.

---

## 3. Implementation Details

- **Configuration:** Updated `src/project_management_api/config.py`:
  - `smtp_host`, `smtp_port`, `smtp_user`, `smtp_password`, `smtp_tls`
  - `emails_from_email`, `emails_from_name`
  - `otp_expire_minutes` (default 10)
  - `otp_max_attempts` (default 5)
  - `password_reset_token_expire_minutes` (default 15)
- **User Model:** Added `is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)` in `src/project_management_api/models/user.py`.
- **OTP Model:** Created `src/project_management_api/models/otp.py`:
  - `OTPPurpose` enum (`EMAIL_VERIFICATION`, `PASSWORD_RESET`).
  - `UserOTP` model with foreign key to `users.id` (`ondelete="CASCADE"`).
- **Package Exports:** Exported in `src/project_management_api/models/__init__.py`.
- **Migration:** Generated and applied `070f62f02a7b_add_is_verified_to_user_and_create_user_.py`.

---

## 4. Verification & Testing
- Ran migration: `070f62f02a7b (head)` applied to MySQL successfully.
- Ran automated test suite: `uv run pytest -v` -> 5 passed (100% success rate, no regression in existing features).
