# Step 3: First FastAPI Endpoint & Server Execution

## 1. Overview
In this step, we built our FastAPI application entry point, added metadata, exposed root (`/`) and health check (`/health`) endpoints, and ran the ASGI server using Uvicorn with automatic reload.

---

## 2. Concepts Learned

### 2.1 FastAPI App Instance
- **What is it?** The main application object created via `FastAPI(...)`.
- **Purpose:** Acts as the registry for all route definitions, middleware, exception handlers, and API metadata (`title`, `version`, `description`).
- **OpenAPI Schema Generation:** FastAPI inspects this object and automatically builds an OpenAPI schema served at `/openapi.json`.

### 2.2 Path Operation Decorators & Handlers
- **Decorators (`@app.get(...)`):** Associates an HTTP method and URL path with a Python function.
- **Serialization:** Returning a Python dictionary automatically sets the response header to `Content-Type: application/json` and serializes the dictionary into a JSON string.

### 2.3 Interactive Documentation
- **`/docs` (Swagger UI):** Interactive API documentation allowing live testing directly from the browser.
- **`/redoc` (ReDoc):** Clean, structured alternative view for API reference.

### 2.4 Running with `uv run` & Hot Reload
- `uv run uvicorn project_management_api.main:app --reload`
  - `uv run`: Executes commands inside the virtual environment without manual activation (`source .venv/bin/activate`).
  - `--reload`: Uses `watchfiles` to detect filesystem changes and restart the worker process automatically.

---

## 3. Implementation Details

File: `src/project_management_api/main.py`
```python
from fastapi import FastAPI

app = FastAPI(
    title="Project Management API",
    version="0.1.0",
    description="A collaborative project management REST API built with FastAPI.",
)


@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Project Management & Collaboration API",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "project-management-api",
    }
```

---

## 4. Verification & Testing
- Accessed `http://127.0.0.1:8000/` -> Returned status code `200 OK` with JSON greeting.
- Accessed `http://127.0.0.1:8000/docs` -> Swagger UI rendered successfully with `/` and `/health` documented.
- Accessed `http://127.0.0.1:8000/openapi.json` -> OpenAPI schema returned.
