# Step 5: Clean Architecture & Modular Routing with APIRouter

## 1. Overview
In this step, we introduced `APIRouter` to break monolithic routing into modular domain endpoints. We established an API versioning strategy (`/api/v1`) and structured the project layout following real-world clean architecture principles.

---

## 2. Concepts Learned

### 2.1 The Need for Modular Routing
- Placing all endpoints in `main.py` causes merge conflicts, decreases readability, and violates separation of concerns.
- `APIRouter` operates as an isolated sub-application grouping related routes (e.g., users, tasks, projects) before mounting them onto the core FastAPI app.

### 2.2 API Versioning (`/api/v1`)
- Production APIs serve multiple client types (web, mobile, external consumers).
- Breaking changes in schemas or endpoints can disrupt existing clients.
- Version prefixing (`/api/v1`) allows running and maintaining older and newer API contracts simultaneously.

### 2.3 Router Composition Pattern
- **Domain Router (`endpoints/health.py`)**: Declares routes specific to the domain.
- **Aggregator Router (`api/v1/api.py`)**: Merges multiple domain routers into a single `api_router`.
- **Application Root (`main.py`)**: Mounts `api_router` with the version prefix `/api/v1`.

---

## 3. Directory Layout Established

```
src/project_management_api/
├── main.py              # Application factory & mounts
├── config.py            # Environment configuration
└── api/
    └── v1/
        ├── api.py       # Aggregator router
        └── endpoints/
            └── health.py # Health check endpoint
```

---

## 4. Verification & Testing
```bash
curl http://127.0.0.1:8000/api/v1/health
```
Output:
```json
{
  "status": "healthy",
  "service": "Project Management API",
  "environment": "development",
  "version": "0.1.0"
}
```
Swagger UI at `http://127.0.0.1:8000/docs` now reflects the `/api/v1/health` route grouped under the `Health` tag.
