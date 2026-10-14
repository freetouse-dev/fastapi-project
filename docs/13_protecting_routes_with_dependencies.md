# Step 13: Protecting Routes — The `get_current_user` Dependency

## 1. Overview
In this step, we built an authentication guard using FastAPI's dependency injection system. We implemented the `get_current_user` dependency to extract Bearer tokens from incoming HTTP headers, verify their cryptographic signatures, fetch the matching user from MySQL, and inject the authenticated user entity into protected route handlers like `GET /api/v1/users/me`.

---

## 2. Concepts Learned

### 2.1 Dependency Chaining in FastAPI
Dependencies can depend on other dependencies:
1. **`oauth2_scheme = OAuth2PasswordBearer(...)`**:
   - Parses the HTTP `Authorization: Bearer <token>` header.
   - Rejects unauthenticated requests with HTTP `401 Unauthorized`.
   - Signals Swagger UI to attach security tokens to documented endpoints.
2. **`get_current_user(db = Depends(get_db), token = Depends(oauth2_scheme))`**:
   - Decodes the JWT using the configured `SECRET_KEY` and algorithm.
   - Extracts subject (`sub` / `user_id`).
   - Queries the database for the active user.
   - Rejects expired, tampered, or inactive credentials with HTTP 401/400.
3. **Route Handler**: Receives a validated `User` ORM instance with no manual token parsing required.

---

## 3. Implementation Details

- **Dependency Module:** Created `src/project_management_api/api/deps.py` with `oauth2_scheme` and `get_current_user`.
- **Users Router:** Created `src/project_management_api/api/v1/endpoints/users.py` exposing `GET /api/v1/users/me`.
- **Router Aggregation:** Mounted `/users` onto `api_router` in `src/project_management_api/api/v1/api.py`.

---

## 4. Verification & Testing
1. **Unauthenticated access (`curl http://127.0.0.1:8000/api/v1/users/me`):**
   - Result: HTTP `401 Unauthorized: Not authenticated`.
2. **Authenticated access (`curl -H "Authorization: Bearer <token>" ...`):**
   - Result: HTTP `200 OK`
   ```json
   {
     "email": "admin@gmail.com",
     "full_name": "Admin",
     "is_active": true,
     "id": 1,
     "is_superuser": false,
     "created_at": "2026-10-14T12:26:13",
     "updated_at": "2026-10-14T12:26:13"
   }
   ```
