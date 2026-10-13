# Step 6: Database Architecture — Connecting MySQL with SQLAlchemy

## 1. Overview
In this step, we integrated MySQL with our FastAPI application using SQLAlchemy 2.0 and PyMySQL. We introduced connection pooling, session lifecycle management with FastAPI dependency injection (`Depends`), and upgraded our health check endpoint to verify database connectivity.

---

## 2. Concepts Learned

### 2.1 Object-Relational Mapping (ORM) & SQLAlchemy
- **What is it?** A layer that maps database tables to Python classes and rows to Python objects.
- **Why do we need it?** Eliminates manual SQL string concatenation, parameterizes queries to avoid SQL injection vulnerabilities, and provides IDE autocompletion and type checking.

### 2.2 Connection Pooling & Engine Configuration
- **Engine (`create_engine`)**: Maintains a persistent pool of database connections, avoiding the high overhead of establishing a new TCP connection on every HTTP request.
- **`pool_pre_ping=True`**: Tests whether a connection is still alive before issuing a query, recovering automatically if MySQL dropped the connection.
- **`pool_recycle=3600`**: Proactively refreshes idle connections before MySQL's default timeout causes connection drops.

### 2.3 Session Lifecycle & Dependency Injection (`Depends(get_db)`)
- **What is `SessionLocal`?** A session factory that produces database sessions.
- **Why use a generator function with `yield`?**
  ```python
  def get_db():
      db = SessionLocal()
      try:
          yield db
      finally:
          db.close()
  ```
  - Isolates transactions per request.
  - Ensures every connection is safely returned to the pool even if an unhandled exception occurs in the endpoint handler.

---

## 3. Implementation Details

- **Configuration:** Updated `Settings` in `src/project_management_api/config.py` with MySQL credentials and dynamic `database_url` property.
- **Database Module:** Created `src/project_management_api/db/session.py` defining the engine, `SessionLocal`, `Base`, and `get_db` dependency.
- **Health Check Integration:** Updated `src/project_management_api/api/v1/endpoints/health.py` to run `SELECT 1` using `Depends(get_db)`.

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
  "version": "0.1.0",
  "database": "connected"
}
```
The database session dependency ran, executed the test query, and confirmed MySQL connectivity with status `connected`.
