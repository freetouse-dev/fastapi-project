# Step 10: Password Hashing & Security Utilities

## 1. Overview
In this step, we implemented secure password hashing using `pwdlib` with the `bcrypt` backend. We built reusable security functions for hashing plaintext passwords during registration and verifying passwords during authentication.

---

## 2. Concepts Learned

### 2.1 One-Way Cryptographic Hashing vs Encryption
- **Encryption:** Two-way; can be decrypted if the secret key is obtained. Storing passwords with reversible encryption is unsafe.
- **Hashing:** One-way; mathematical transformation that cannot be reversed. During login, the candidate password is run through the same hashing algorithm and compared against the stored hash.

### 2.2 Salting & Work Factors (Bcrypt)
- **Salting:** Generates a random cryptographic salt per hash to prevent precomputed dictionary and Rainbow Table attacks.
- **Work Factor (Cost):** Tunable iteration cost that makes brute-force attempts computationally expensive.

### 2.3 Tooling: `pwdlib`
- Modern Python 3.12+ / 3.13 standard for FastAPI password handling, superseding unmaintained legacy tools like `passlib`.

---

## 3. Implementation Details

File: `src/project_management_api/core/security.py`
```python
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

password_hash = PasswordHash((BcryptHasher(),))


def hash_password(password: str) -> str:
    """Hashes a plaintext password using bcrypt."""
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a stored hash."""
    return password_hash.verify(plain_password, hashed_password)
```

---

## 4. Verification & Testing
Executed smoke test via Python CLI:
- Hashed test password `"secret123"` -> yielded `$2b$12$...` bcrypt digest.
- `verify_password("secret123", hash)` -> `True`
- `verify_password("wrong", hash)` -> `False`
