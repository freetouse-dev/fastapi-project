# Project Management & Collaboration REST API

A high-performance, multi-tenant project management REST API built with **FastAPI**, **SQLAlchemy 2.0**, **MySQL**, and **uv**, inspired by tools like **Jira** and **Asana**.

---

## 1. Overview & Purpose
This application provides the backend foundation for modern collaborative project tracking. It features:
- **Stateless Authentication with Email Verification:** Cryptographic password hashing with `bcrypt` and JWT (JSON Web Tokens) via the OAuth2 Password Flow. New accounts require OTP email verification before login.
- **Secure Password Reset:** 3-step OTP recovery flow with account enumeration protection, attempt locking, and single-use signed authorization tokens.
- **Decoupled Email Service:** Reusable HTML & plain-text email dispatch service over SMTP with graceful development/test fallback logging.
- **True Multi-Tenancy:** Workspaces isolate organization data. Users hold distinct roles (`OWNER`, `ADMIN`, `MEMBER`) per workspace.
- **Projects & Team Membership:** Project-level access control (`PROJECT_LEAD`, `CONTRIBUTOR`, `VIEWER`) and Jira-style issue keys (e.g. `MOB-1`).
- **Concurrency-Safe Task Engine:** Row-level locking (`with_for_update()`) for race-condition-free ticket numbering, status workflows (`TODO` -> `IN_PROGRESS` -> `DONE`), and deadline tracking.
- **Collaboration & Auditing:** Threaded task comments with moderation rules and an automated audit trail (`task_activities`) recording field changes.
- **Search, Filtering & Pagination:** Generic pagination metadata, full-text search, and multi-criteria sorting.
- **Real-Time Analytics:** Database-level aggregations computing project completion rates, status distributions, and overdue ticket counts.
- **Production Architecture:** Alembic migrations, 12-factor configuration, CORS support, request timing middleware (`X-Process-Time`), and an automated Pytest suite with in-memory database isolation.

---

## 2. Technology Stack

- **Language:** Python 3.13+
- **Web Framework:** FastAPI (ASGI based on Starlette & Pydantic V2)
- **ASGI Web Server:** Uvicorn
- **Package & Project Manager:** `uv`
- **Database:** MySQL
- **ORM & Dialect:** SQLAlchemy 2.0 with PyMySQL & Cryptography
- **Database Migrations:** Alembic
- **Security & Passwords:** `pwdlib[bcrypt]`, `PyJWT`, `secrets`, `hmac`
- **Email Service:** Python Standard Library (`smtplib`, `email.mime`)
- **Testing:** `pytest`, `httpx` (FastAPI `TestClient`)

---

## 3. Project Architecture & Directory Layout

```
project-management-api/
├── alembic/                      # Database migration scripts & environment
│   └── versions/                 # Versioned migration revisions
├── docs/                         # Step-by-step learning & architecture notes
│   ├── 01_project_initialization_and_tooling.md
│   ├── ...
│   ├── 30_email_verification_and_otp_schema_design.md
│   ├── 31_otp_security_utilities_and_email_service.md
│   ├── 32_email_verification_workflow.md
│   └── 33_otp_based_password_reset_workflow.md
├── src/
│   └── project_management_api/
│       ├── main.py               # FastAPI application factory, middleware & exception handlers
│       ├── config.py             # Typed 12-factor settings (pydantic-settings)
│       ├── api/
│       │   ├── deps.py           # Authentication & database dependency injection
│       │   └── v1/
│       │       ├── api.py        # V1 aggregator router
│       │       └── endpoints/    # Domain route handlers
│       │           ├── auth.py       # Registration, Email Verification, Password Reset & Login
│       │           ├── users.py      # User profiles (/users)
│       │           ├── workspaces.py # Workspaces & members (/workspaces)
│       │           ├── projects.py   # Projects, project members & dashboards
│       │           ├── tasks.py      # Tasks & activities
│       │           ├── comments.py   # Task comments & moderation
│       │           └── health.py     # System health & liveness checks
│       ├── core/
│       │   └── security.py       # Passwords, JWTs, cryptographically secure OTP generation & HMAC hashing
│       ├── services/
│       │   └── email.py          # Decoupled email templates & SMTP dispatch
│       ├── crud/                 # Database queries & mutation layer
│       │   ├── user.py
│       │   ├── otp.py            # OTP lifecycle, validation & attempt tracking
│       │   ├── workspace.py
│       │   ├── project.py
│       │   ├── task.py
│       │   ├── comment.py
│       │   ├── activity.py
│       │   └── report.py
│       ├── db/
│       │   └── session.py        # SQLAlchemy engine, connection pool & sessionmaker
│       ├── models/               # SQLAlchemy ORM database models
│       │   ├── user.py           # User entity (with is_verified)
│       │   ├── otp.py            # UserOTP entity (hashed_otp, purpose, attempts)
│       │   ├── workspace.py
│       │   ├── project.py
│       │   ├── task.py
│       │   ├── comment.py
│       │   └── activity.py
│       └── schemas/              # Pydantic V2 validation & DTO serialization
│           ├── common.py         # PaginatedResponse[T]
│           ├── auth.py           # Verification & Password Reset requests/responses
│           ├── user.py
│           ├── token.py
│           ├── workspace.py
│           ├── project.py
│           ├── task.py
│           ├── comment.py
│           ├── activity.py
│           └── report.py
├── tests/                        # Automated Pytest suite with SQLite in-memory isolation
│   ├── conftest.py               # Shared test fixtures & database overrides
│   ├── test_health.py
│   ├── test_auth.py
│   ├── test_email_verification.py
│   ├── test_password_reset.py
│   └── test_workspaces.py
├── pyproject.toml                # Project metadata & pinned dependencies
└── uv.lock                       # Cryptographically locked dependency graph
```

---

## 4. Authentication & Security Workflows

### 4.1 Email Verification Flow
1. **Registration:** `POST /api/v1/auth/register` creates an account with `is_verified = False`. A 6-digit OTP is generated, hashed with HMAC-SHA256, saved in `user_otps` (10-minute expiry), and emailed to the user.
2. **Login Block:** Any attempt to call `POST /api/v1/auth/login` before verification returns `403 Forbidden` (`"Email address not verified."`).
3. **Verification:** `POST /api/v1/auth/verify-email` checks the OTP, enforces maximum attempts (default 5), marks `is_verified = True`, and invalidates the OTP.
4. **Resend Code:** `POST /api/v1/auth/resend-verification-otp` invalidates previous active OTPs and sends a fresh code.

### 4.2 OTP-Based Password Reset Flow
1. **Forgot Password:** `POST /api/v1/auth/forgot-password` accepts an email. To prevent account enumeration, it returns a generic `200 OK` whether the email exists or not. If registered, a reset OTP is generated and emailed.
2. **Verify Code:** `POST /api/v1/auth/verify-reset-otp` validates the 6-digit code. Upon success, the OTP is invalidated and the server returns a signed, short-lived JWT `reset_token` (valid 15 minutes).
3. **Set Password:** `POST /api/v1/auth/reset-password` accepts `reset_token` and `new_password`. It hashes the new password with bcrypt, updates MySQL, and invalidates any outstanding reset challenges.

---

## 5. Complete API Endpoints Reference

### 5.1 System & Health
- `GET /`: API welcome and documentation link.
- `GET /api/v1/health`: Operational status, database ping (`SELECT 1`), and `X-Process-Time`.

### 5.2 Authentication & User Profiles
- `POST /api/v1/auth/register`: Register new account and send verification OTP.
- `POST /api/v1/auth/verify-email`: Verify email with 6-digit code.
- `POST /api/v1/auth/resend-verification-otp`: Invalidate prior codes and send fresh verification OTP.
- `POST /api/v1/auth/forgot-password`: Request password reset OTP (enumeration protected).
- `POST /api/v1/auth/verify-reset-otp`: Validate reset OTP and obtain `reset_token`.
- `POST /api/v1/auth/reset-password`: Set new password using `reset_token`.
- `POST /api/v1/auth/login`: Authenticate verified credentials and obtain Bearer JWT.
- `GET /api/v1/users/me`: View authenticated user profile.

### 5.3 Workspaces (Multi-Tenancy)
- `POST /api/v1/workspaces/`: Create workspace (creator assigned as `OWNER`).
- `GET /api/v1/workspaces/`: List workspaces where the current user is a member.
- `GET /api/v1/workspaces/{slug}`: Retrieve workspace details.
- `GET /api/v1/workspaces/{slug}/members`: List workspace collaborators.
- `POST /api/v1/workspaces/{slug}/members`: Invite member (`OWNER` or `ADMIN` only).

### 5.4 Projects
- `POST /api/v1/workspaces/{slug}/projects/`: Create project (creator assigned as `PROJECT_LEAD`).
- `GET /api/v1/workspaces/{slug}/projects/`: List projects visible to user.
- `GET /api/v1/workspaces/{slug}/projects/{key}`: Retrieve project details.
- `GET /api/v1/workspaces/{slug}/projects/{key}/members`: List project members.
- `POST /api/v1/workspaces/{slug}/projects/{key}/members`: Add workspace member to project.
- `GET /api/v1/workspaces/{slug}/projects/{key}/dashboard`: Real-time project metrics & analytics.

### 5.5 Tasks & Lifecycle State Machine
- `POST /api/v1/workspaces/{slug}/projects/{key}/tasks/`: Create task with sequential key (`MOB-1`).
- `GET /api/v1/workspaces/{slug}/projects/{key}/tasks/`: Paginated list with `search`, `status`, `priority`, `sort_by`, `sort_order`, `page`, and `size`.
- `GET /api/v1/workspaces/{slug}/projects/{key}/tasks/{task_number}`: Get task details.
- `PATCH /api/v1/workspaces/{slug}/projects/{key}/tasks/{task_number}`: Update task attributes & status transitions.
- `GET /api/v1/workspaces/{slug}/projects/{key}/tasks/{task_number}/activities/`: Full audit trail of task changes.

### 5.6 Task Comments
- `POST /api/v1/workspaces/{slug}/projects/{key}/tasks/{task_number}/comments/`: Post comment.
- `GET /api/v1/workspaces/{slug}/projects/{key}/tasks/{task_number}/comments/`: List comments chronologically.
- `DELETE /api/v1/workspaces/{slug}/projects/{key}/tasks/{task_number}/comments/{comment_id}`: Delete comment (Author or Admin/Lead).

---

## 6. Setup & Execution Instructions

### Prerequisites
- Python 3.13+ installed
- MySQL running locally or remotely
- `uv` installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)

### Step 1: Configure Environment (`.env`)
```env
ENVIRONMENT=development
DEBUG=True

# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=project_management_db

# Security & Tokens
SECRET_KEY=generate_a_secure_random_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
OTP_EXPIRE_MINUTES=10
OTP_MAX_ATTEMPTS=5
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES=15

# SMTP / Email Configuration (Falls back to console logs in development/testing)
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USER=
SMTP_PASSWORD=
SMTP_TLS=False
EMAILS_FROM_EMAIL=noreply@projectapi.com
EMAILS_FROM_NAME="Project Management API"
```

### Step 2: Install Dependencies with `uv`
```bash
uv sync
```

### Step 3: Run Database Migrations
```bash
uv run alembic upgrade head
```

### Step 4: Start the Development Server
```bash
uv run uvicorn project_management_api.main:app --reload
```
The API is live at `http://127.0.0.1:8000`.
- Interactive Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc Reference: `http://127.0.0.1:8000/redoc`

---

## 7. Automated Testing

Run the automated Pytest test suite:
```bash
uv run pytest -v
```
All tests run against an isolated in-memory SQLite database (`sqlite:///:memory:`), keeping local development and production databases completely clean.
