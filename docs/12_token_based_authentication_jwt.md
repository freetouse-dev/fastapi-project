# Step 12: Token-Based Authentication with JWT & OAuth2 Password Flow

## 1. Overview
In this step, we implemented stateless token-based authentication using JSON Web Tokens (JWT) and the standard OAuth2 Password Flow. Users authenticate with their email and password, receiving a cryptographically signed Bearer token to authorize subsequent API requests.

---

## 2. Concepts Learned

### 2.1 Stateless Authentication with JWT
- **Traditional Session Auth:** Requires server-side storage (Redis/DB) to validate session cookies on every request.
- **JWT (JSON Web Token):** Encodes the user's identity (`sub`) and expiration (`exp`) into a signed base64 payload. The backend validates authenticity mathematically using `SECRET_KEY` without querying the database for token state.
- **Structure:** `header.payload.signature`
  - Signed via `HS256` HMAC-SHA256 algorithm.

### 2.2 OAuth2 Specification & Form Data (`OAuth2PasswordRequestForm`)
- Under the OAuth2 standard (`RFC 6749`), login endpoints accept credentials via `application/x-www-form-urlencoded` fields (`username` and `password`).
- FastAPI integrates with this standard, enabling Swagger UI (`/docs`) to display an interactive **Authorize** modal for testing secured routes.

### 2.3 Troubleshooting: `python-multipart` Dependency
- **Error Encountered:** `RuntimeError: Form data requires "python-multipart" to be installed.`
- **Cause:** FastAPI delegates form parsing to `python-multipart`. When declaring `OAuth2PasswordRequestForm = Depends()`, the parser must be present in the environment.
- **Resolution:** Added `python-multipart` to the project via `uv add "python-multipart"`.

---

## 3. Implementation Details

- **Config:** Added `secret_key`, `algorithm`, and `access_token_expire_minutes` to `src/project_management_api/config.py`.
- **Token Schemas:** Created `src/project_management_api/schemas/token.py` defining `Token` and `TokenPayload`.
- **Token Utility:** Implemented `create_access_token` in `src/project_management_api/core/security.py`.
- **Login Endpoint:** Created `POST /api/v1/auth/login` in `src/project_management_api/api/v1/endpoints/auth.py`.

---

## 4. Verification & Testing
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=ajay@gmail.com&password=ajay123"
```
Output:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```
Token was signed, returned with `token_type: bearer`, and verified ready for request authorization.
