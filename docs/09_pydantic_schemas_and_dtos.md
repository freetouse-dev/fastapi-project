# Step 9: Pydantic Schemas & Data Transfer Objects (DTOs)

## 1. Overview
In this step, we introduced Pydantic schemas to validate incoming request payloads and serialize outgoing response data. We separated database persistence models (`SQLAlchemy`) from network transport models (`Pydantic`).

---

## 2. Concepts Learned

### 2.1 ORM Models vs Pydantic Schemas
- **SQLAlchemy ORM Model (`models/user.py`)**: Represents the physical table in MySQL. Stores internal columns like `hashed_password`.
- **Pydantic Schemas (`schemas/user.py`)**: Defines the HTTP API contract. Validates inputs and strictly filters what the API sends back.
- **Security Rule**: The API output contract (`UserResponse`) must NEVER expose `hashed_password` or raw credentials.

### 2.2 Schema Inheritance Pattern
- `UserBase`: Common properties shared across requests/responses (`email`, `full_name`, `is_active`).
- `UserCreate`: Accepts user registration input including the plaintext `password`.
- `UserUpdate`: Optional fields for updating user profiles.
- `UserResponse`: Outgoing response containing public identifiers (`id`, `created_at`, `updated_at`, `is_superuser`) while omitting password fields.

### 2.3 Object Mapping with `from_attributes=True`
- In Pydantic V2, `model_config = ConfigDict(from_attributes=True)` instructs Pydantic to read fields directly from SQLAlchemy ORM instances (e.g. `user.id`, `user.email`) rather than requiring a plain dictionary.

### 2.4 Built-in Validation
- `EmailStr`: Rejects malformed email inputs automatically with HTTP `422 Unprocessable Entity`.
- `Field(min_length=..., max_length=...)`: Enforces string boundary constraints before touching database logic.

---

## 3. Implementation Details

- **Schemas:** Created `src/project_management_api/schemas/user.py`
- **Exports:** Created `src/project_management_api/schemas/__init__.py`

---

## 4. Verification
Schema files verified with valid type hints, `from_attributes=True` configuration, and exported in `__all__`.
