# Step 28: Global Error Handling, CORS & Middleware

## 1. Overview
In this step, we introduced cross-cutting middleware and centralized exception handlers. We configured Cross-Origin Resource Sharing (CORS) for web frontend compatibility, added request timing middleware to monitor endpoint latency (`X-Process-Time`), and standardized error response contracts across the API.

---

## 2. Concepts Learned

### 2.1 Cross-Origin Resource Sharing (CORS)
- **The Problem:** Modern frontend single-page apps (React, Vue, Next.js) run on different ports/domains (e.g. `http://localhost:3000`) and are blocked by browser Same-Origin Policies from calling `http://127.0.0.1:8000`.
- **The Solution:** `CORSMiddleware` handles pre-flight `OPTIONS` requests and returns headers (`Access-Control-Allow-Origin`, `Access-Control-Allow-Headers`) allowing trusted origins to consume the API.

### 2.2 Request Timing Middleware (`@app.middleware("http")`)
- Captures start time using high-resolution monotonic timer `time.perf_counter()`.
- Executes downstream routing and database queries via `await call_next(request)`.
- Attaches `X-Process-Time` (e.g. `14.21ms`) to all response headers for real-time observability.

### 2.3 Structured Error Contract
- Instead of returning inconsistent or raw errors, all exceptions return a standardized schema:
  ```json
  {
    "error": true,
    "status_code": 401,
    "detail": "Not authenticated",
    "path": "/api/v1/workspaces/..."
  }
  ```
- Uncaught Python crashes are intercepted by `global_exception_handler`, preventing stack trace leaks while logging errors safely.

---

## 3. Implementation Details

- **Config:** Added `cors_origins: list[str] = ["*"]` to `src/project_management_api/config.py`.
- **Middleware & Error Handlers:** Updated `src/project_management_api/main.py`:
  - `CORSMiddleware`
  - `add_process_time_header` HTTP middleware
  - `custom_http_exception_handler` (`HTTPException`)
  - `validation_exception_handler` (`RequestValidationError`)
  - `global_exception_handler` (`Exception`)

---

## 4. Verification & Testing
1. **Response Headers Test (`GET /api/v1/health`):**
   ```http
   HTTP/1.1 200 OK
   x-process-time: 14.21ms
   vary: Origin
   ```
2. **Standardized Error Test (`GET /api/v1/workspaces/non-existent...`):**
   ```json
   {
     "error": true,
     "status_code": 401,
     "detail": "Not authenticated",
     "path": "/api/v1/workspaces/non-existent-workspace-12345"
   }
   ```
