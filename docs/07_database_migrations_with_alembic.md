# Step 7: Database Migrations with Alembic

## 1. Overview
In this step, we integrated Alembic to manage database schema migrations. We configured Alembic to read database connection details dynamically from application settings and connected it to SQLAlchemy's `Base.metadata`.

---

## 2. Concepts Learned

### 2.1 Schema Migration vs `create_all()`
- `Base.metadata.create_all(engine)` only creates missing tables; it cannot detect altered columns, dropped columns, renamed fields, or new index definitions.
- Alembic treats database schema evolution like Git for databases: changes are written into reproducible, versioned migration scripts with `upgrade()` and `downgrade()` steps.
- The `alembic_version` table in MySQL tracks the active migration revision hash.

### 2.2 Dynamic Configuration in `alembic/env.py`
- Rather than hardcoding database connection strings in `alembic.ini`, `alembic/env.py` was configured to use `get_settings().database_url` directly.
- The `target_metadata` was pointed to `Base.metadata` to enable autogeneration of migration scripts by comparing declared ORM models against the live database schema.

---

## 3. Implementation Details

- Installed `alembic` via `uv add "alembic"`.
- Initialized migration structure via `uv run alembic init alembic`.
- Updated `alembic/env.py` to:
  - Import `get_settings` and `Base`.
  - Point `target_metadata = Base.metadata`.
  - Use `create_engine(settings.database_url, poolclass=pool.NullPool)` in `run_migrations_online()`.

---

## 4. Verification & Testing
```bash
uv run alembic current
```
Output:
```
INFO  [alembic.runtime.migration] Context impl MySQLImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
```
Alembic successfully connected to MySQL using `MySQLImpl`, verified connectivity, and is prepared to generate and apply migrations.
