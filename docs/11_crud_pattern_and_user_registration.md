# Step 11: The CRUD Pattern & User Registration Endpoint

## 1. Overview
In this step, we introduced the Clean Architecture separation between HTTP route handlers and database persistence by creating a dedicated CRUD (Create, Read, Update, Delete) module. We implemented user registration (`POST /api/v1/auth/register`), verified validation rejection, successful creation, and duplicate email prevention.

---

## 2. Concepts Learned

### 2.1 The CRUD / Service Layer Pattern
- **Route Handlers (`api/v1/endpoints/auth.py`)**: Responsible solely for HTTP transport concerns (status codes, dependency injection, exception handling, schema contracts).
- **CRUD Operations (`crud/user.py`)**: Reusable database queries decoupled from HTTP context, making them testable and usable across APIs, background workers, or CLI scripts.

### 2.2 End-to-End Registration Flow & HTTP Status Codes
1. **HTTP 422 Unprocessable Content:** Triggered when the incoming payload violates Pydantic constraints (e.g. invalid email format or password shorter than requirements).
2. **HTTP 201 Created:** Returned upon successful user registration, returning the sanitized `UserResponse` DTO (password hash excluded).
3. **HTTP 400 Bad Request:** Returned when an email collision is detected (`get_user_by_email`).

---

## 3. Implementation Details

- **CRUD Layer:** Created `src/project_management_api/crud/user.py` with `get_user_by_email`, `get_user_by_id`, and `create_user`.
- **Auth Endpoint:** Created `src/project_management_api/api/v1/endpoints/auth.py` exposing `/register`.
- **Router Aggregation:** Mounted `/auth` onto `api_router` in `src/project_management_api/api/v1/api.py`.

---

## 4. Verification & Testing
Server logs confirmed all three validation branches:
```
POST /api/v1/auth/register -> 422 Unprocessable Content (Malformed payload rejected)
POST /api/v1/auth/register -> 201 Created (User persisted and hashed)
POST /api/v1/auth/register -> 400 Bad Request (Duplicate email rejected)
```
