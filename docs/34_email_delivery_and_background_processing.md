# Step 34: Email Delivery Audit and Background Processing

## 1. Context and Problem Statement
During our backend performance and security audit, we investigated email dispatch across authentication workflows:
- **User Registration** (`POST /api/v1/auth/register`)
- **Resending Verification OTP** (`POST /api/v1/auth/resend-verification-otp`)
- **Password Reset OTP Requests** (`POST /api/v1/auth/forgot-password`)

### Audit Finding
Previously, email functions (`send_verification_email`, `send_password_reset_email`) were called synchronously in the body of route handlers. Because `services/email.py` uses `smtplib.SMTP(..., timeout=10)`:
1. Every API call was blocked during DNS resolution, TCP handshake, TLS negotiation, SMTP authentication, and MIME data transmission.
2. Under production network conditions, this added between 500ms and 3,000ms (and up to 10s upon network stalls) to user-facing response times.
3. Synchronous blocking inside FastAPI worker threads exposed the application to thread-pool exhaustion under concurrent authentication traffic.

---

## 2. Solution: FastAPI `BackgroundTasks`
Rather than introducing heavy distributed task brokers (like Celery, Redis, or RabbitMQ) for transactional email notifications, we implemented FastAPI's native `BackgroundTasks`.

### How It Works
1. FastAPI injects a `BackgroundTasks` instance into the route handler via dependency injection.
2. The endpoint executes the transactional database operations (e.g. creating the unverified user, generating the OTP record in MySQL, committing the database session).
3. The email sending function is scheduled via `background_tasks.add_task(send_email_func, ...)`.
4. FastAPI immediately writes the HTTP response headers and body to the client.
5. Immediately after response delivery, Starlette/FastAPI executes the scheduled tasks.

```python
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    user_in: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    ...
    db_user = crud_user.create_user(db, user_in=user_in)
    _, plain_otp = crud_otp.create_user_otp(
        db, user_id=db_user.id, purpose=OTPPurpose.EMAIL_VERIFICATION
    )
    
    # Asynchronous dispatch via BackgroundTasks
    background_tasks.add_task(
        send_verification_email,
        to_email=db_user.email,
        full_name=db_user.full_name,
        otp=plain_otp,
    )
    return db_user
```

---

## 3. Resilience and Error Handling
- In `services/email.py`, `send_email` wraps network operations inside a comprehensive `try/except` block.
- If an SMTP server is unreachable or credentials are misconfigured, the error is logged via `logger.error(...)` and does not crash the server or interrupt subsequent background tasks.
- The client receives an immediate response regardless of external email server latencies.

---

## 4. Verification and Automated Testing
- Updated `tests/test_email_verification.py` with `test_registration_and_resend_trigger_background_email` to assert that background tasks trigger email delivery for registration and resend requests.
- Updated `tests/test_password_reset.py` with `test_forgot_password_triggers_background_email` to assert that background tasks trigger password reset emails.
- Verified all 13 automated tests run and pass cleanly.
