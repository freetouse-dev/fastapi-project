# Project Management & Collaboration REST API

A high-performance, multi-tenant project management REST API built with **FastAPI**, **SQLAlchemy 2.0**, **MySQL**, and **uv**, inspired by tools like **Jira** and **Asana**.

---

## 1. Overview & Purpose
This application provides the backend foundation for modern collaborative project tracking. It features:
- **Stateless Authentication:** Cryptographic password hashing with `bcrypt` and JWT (JSON Web Tokens) via the OAuth2 Password Flow.
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
- **Security & Passwords:** `pwdlib[bcrypt]`, `PyJWT`
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
│   └── 29_automated_testing_with_pytest.md
├── src/
│   └── project_management_api/
│       ├── main.py               # FastAPI application factory, middleware & exception handlers
│       ├── config.py             # Typed 12-factor settings (pydantic-settings)
│       ├── api/
│       │   ├── deps.py           # Authentication & database dependency injection
│       │   └── v1/
│       │       ├── api.py        # V1 aggregator router
│       │       └── endpoints/    # Domain route handlers
│       │           ├── auth.py       # Registration & Login (/auth)
│       │           ├── users.py      # User profiles (/users)
│       │           ├── workspaces.py # Workspaces & members (/workspaces)
│       │           ├── projects.py   # Projects & project members
│       │           ├── tasks.py      # Tasks & activities
│       │           ├── comments.py   # Task comments & moderation
│       │           └── health.py     # System health & liveness checks
│       ├── core/
│       │   └── security.py       # Password hashing & JWT token encoding/decoding
│       ├── crud/                 # Database queries & mutation layer
│       │   ├── user.py
│       │   ├── workspace.py
│       │   ├── project.py
│       │   ├── task.py
│       │   ├── comment.py
│       │   ├── activity.py
│       │   └── report.py
│       ├── db/
│       │   └── session.py        # SQLAlchemy engine, connection pool & sessionmaker
│       ├── models/               # SQLAlchemy ORM database models
│       │   ├── user.py
│       │   ├── workspace.py
│       │   ├── project.py
│       │   ├── task.py
│       │   ├── comment.py
│       │   └── activity.py
│       └── schemas/              # Pydantic V2 validation & DTO serialization
│           ├── common.py         # PaginatedResponse[T]
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
│   └── test_workspaces.py
├── pyproject.toml                # Project metadata & pinned dependencies
└── uv.lock                       # Cryptographically locked dependency graph
```

---

## 4. Database Schema & Entity Relationships

```
┌──────────────┐         ┌────────────────────────┐         ┌──────────────┐
│    User      │ 1     * │    WorkspaceMember     │ *     1 │  Workspace   │
├──────────────┤─────────├────────────────────────┤─────────├──────────────┤
│ id (PK)      │         │ id (PK)                │         │ id (PK)      │
│ email        │         │ workspace_id (FK)      │         │ name         │
│ hashed_pw    │         │ user_id (FK)           │         │ slug (unique)│
│ full_name    │         │ role (OWNER/ADMIN/MEM) │         │ owner_id (FK)│
└──────┬───────┘         └────────────────────────┘         └──────┬───────┘
       │                                                           │ 1
       │                                                           ▼ *
       │ 1               ┌────────────────────────┐         ┌──────────────┐
       │                 │     ProjectMember      │ *     1 │   Project    │
       ├─────────────────├────────────────────────┤─────────├──────────────┤
       │                 │ id (PK)                │         │ id (PK)      │
       │                 │ project_id (FK)        │         │ workspace_id │
       │                 │ user_id (FK)           │         │ key (e.g MOB)│
       │                 │ role (LEAD/CONTRIB/VW) │         │ status       │
       │                 └────────────────────────┘         └──────┬───────┘
       │                                                           │ 1
       │                                                           ▼ *
       │                 ┌─────────────────────────────────────────────────┐
       │ 1             * │                      Task                       │
       ├─────────────────├─────────────────────────────────────────────────┤
       │                 │ id (PK), project_id (FK), task_number (1, 2...) │
       │                 │ ticket_key (e.g. MOB-1), title, description     │
       │                 │ status (TODO/IN_PROGRESS/DONE), priority        │
       │                 │ creator_id (FK), assignee_id (FK), due_date     │
       │                 └───────┬─────────────────────────────────┬───────┘
       │                         │ 1                               │ 1
       │                         ▼ *                               ▼ *
       │                 ┌──────────────────────┐         ┌──────────────────────┐
       │                 │     TaskComment      │         │     TaskActivity     │
       │                 ├──────────────────────┤         ├──────────────────────┤
       │                 │ id (PK)              │         │ id (PK)              │
       └─────────────────│ task_id (FK)         │         │ task_id (FK)         │
                         │ author_id (FK)       │         │ actor_id (FK)        │
                         │ content, timestamps  │         │ action, field_name   │
                         └──────────────────────┘         │ old_value, new_value │
                                                          └──────────────────────┘
```

---

## 5. Available API Endpoints

### 5.1 Health & Root
- `GET /`: API welcome and documentation link.
- `GET /api/v1/health`: Operational status and live database ping (`SELECT 1`).

### 5.2 Authentication & Users
- `POST /api/v1/auth/register`: Register new user account.
- `POST /api/v1/auth/login`: OAuth2 password login, returns Bearer JWT.
- `GET /api/v1/users/me`: Authenticated profile details.

### 5.3 Workspaces (Multi-Tenancy)
- `POST /api/v1/workspaces/`: Create a workspace (creator automatically assigned as `OWNER`).
- `GET /api/v1/workspaces/`: List workspaces where the current user is a member.
- `GET /api/v1/workspaces/{slug}`: Retrieve workspace details.
- `GET /api/v1/workspaces/{slug}/members`: List workspace collaborators.
- `POST /api/v1/workspaces/{slug}/members`: Invite/add member (requires `OWNER` or `ADMIN`).

### 5.4 Projects
- `POST /api/v1/workspaces/{slug}/projects/`: Create project (creator assigned as `PROJECT_LEAD`).
- `GET /api/v1/workspaces/{slug}/projects/`: List projects in workspace.
- `GET /api/v1/workspaces/{slug}/projects/{key}`: Retrieve project details.
- `GET /api/v1/workspaces/{slug}/projects/{key}/members`: List project members.
- `POST /api/v1/workspaces/{slug}/projects/{key}/members`: Add workspace member to project.
- `GET /api/v1/workspaces/{slug}/projects/{key}/dashboard`: Real-time project metrics & completion analytics.

### 5.5 Tasks & Issue Lifecycle
- `POST /api/v1/workspaces/{slug}/projects/{key}/tasks/`: Create task with sequential key (`MOB-1`).
- `GET /api/v1/workspaces/{slug}/projects/{key}/tasks/`: Paginated list with `search`, `status`, `priority`, `sort_by`, `sort_order`, `page`, and `size`.
- `GET /api/v1/workspaces/{slug}/projects/{key}/tasks/{task_number}`: Get task details.
- `PATCH /api/v1/workspaces/{slug}/projects/{key}/tasks/{task_number}`: State transition & attribute updates.
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

### Step 1: Clone & Configure Environment
Create a `.env` file in the project root:
```env
ENVIRONMENT=development
DEBUG=True
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=project_management_db
SECRET_KEY=generate_a_secure_random_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
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
The API is now live at `http://127.0.0.1:8000`.
- Interactive Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc Reference: `http://127.0.0.1:8000/redoc`

---

## 7. Running the Automated Test Suite

Run the complete Pytest suite with:
```bash
uv run pytest -v
```
All tests run against an isolated in-memory SQLite database without modifying local MySQL data.
