# Step 2: FastAPI & ASGI Fundamentals

## 1. Overview
In this step, we introduced FastAPI and the ASGI server Uvicorn, and installed our core web dependencies using `uv`.

---

## 2. Concepts Learned

### 2.1 FastAPI
- **What is it?** A modern, high-performance web framework for Python based on standard type hints.
- **Why do we need it?** 
  - Automatically validates request data using Pydantic.
  - Generates interactive API documentation out of the box (`/docs` using Swagger UI, `/redoc` using ReDoc).
  - High performance natively supporting asynchronous programming (`async`/`await`).

### 2.2 ASGI & Uvicorn
- **What is ASGI?** Asynchronous Server Gateway Interface. It is the modern standard specification for asynchronous Python web servers to communicate with web frameworks.
- **What is Uvicorn?** A lightning-fast ASGI server implementation that listens for HTTP/WebSocket traffic and hands requests over to FastAPI.
- **Architecture Flow:**
  ```
  Client (Browser / Postman / curl)
                 │ HTTP Request
                 ▼
          Uvicorn (ASGI Server)
                 │ Converts HTTP bytes into ASGI event dictionary
                 ▼
          FastAPI (Application)
                 │ Routes request, validates inputs, executes business logic
                 ▼
          Uvicorn (Formats HTTP Response)
                 │ HTTP Response
                 ▼
               Client
  ```

---

## 3. Dependency Management with `uv`
Running `uv add "fastapi" "uvicorn[standard]"` performed the following actions automatically:
1. Created an isolated virtual environment at `.venv/`.
2. Resolved and pinned all transitive dependencies in `uv.lock`.
3. Updated `pyproject.toml` under `[project.dependencies]`.

---

## 4. Commands Executed
```bash
# Add FastAPI and Uvicorn to the project
uv add "fastapi" "uvicorn[standard]"
```
