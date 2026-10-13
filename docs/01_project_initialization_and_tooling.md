# Step 1: Project Initialization & Tooling

## 1. Overview
In this step, we initialized our project management and collaboration API workspace using `uv`. We also compared traditional Python environment tooling (`pip` and `venv`) with `uv`.

---

## 2. Concepts Learned

### 2.1 Package & Environment Management: `pip`, `venv`, and `uv`
- **`pip`**: The package installer for Python. It downloads packages from PyPI and places them into an environment. It does not create isolated environments or manage Python versions by itself.
- **`venv`**: The built-in module for creating isolated virtual environments to prevent dependency conflicts between projects.
- **`uv`**: An extremely fast, modern Python package and project manager written in Rust. It unifies project initialization, virtual environment management, dependency resolution, lockfiles, and execution into a single CLI.

### Why `uv` for our project?
1. **Speed**: Resolves and installs packages significantly faster (up to 10-100x) than `pip`.
2. **Unified workflow**: Replaces separate invocations of `python -m venv`, `pip install`, and manual requirements file maintenance with commands like `uv add` and `uv run`.
3. **Deterministic builds**: Automatically generates and maintains `uv.lock` to ensure all collaborators run identical dependency versions.

---

## 3. Project Structure Created
Running `uv init project-management-api` created a standard Python package layout:

```
project-management-api/
├── .git/                 # Git repository initialized automatically
├── .gitignore            # Standard gitignore configured by uv
├── .python-version       # Specifies the pinned Python version
├── pyproject.toml        # Standard packaging and project configuration
├── README.md             # Project readme
└── src/
    └── project_management_api/
        └── __init__.py   # Root package entry point
```

### Important Files:
- **`pyproject.toml`**: The standardized configuration file (PEP 518/621) defining project metadata, build backend, Python requirements (`requires-python`), and project dependencies.
- **`src/` layout**: Keeps the application code isolated from the root configuration files, preventing accidental import conflicts.

---

## 4. Commands Executed
```bash
# Verify uv installation
uv --version

# Initialize the project
uv init project-management-api

# Navigate to project root
cd project-management-api
```
