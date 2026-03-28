# Monorepo & Local Dependency Guide

Welcome to the **Job Wizard** monorepo! This guide explains how we structure our code and manage dependencies between different services.

---

## 🏗 What is a Monorepo?

A **Monorepo** (Monolithic Repository) is a strategy where we keep multiple related projects or services in a single repository. 

In this project, we have:
- **`services/backend`**: Our FastAPI web server.
- **`services/frontend`**: Our SvelteKit user interface.
- **`services/database`**: A shared Python package for database models and connection logic.

---

## 📦 Local Package Management

One of the most powerful features of our monorepo is the ability to share code between services without publishing to an external registry like PyPI.

### 1. The `job-wizard-db` Package
We have a dedicated package for all database-related code in `services/database`. This package is defined in its own `pyproject.toml` file:

```toml
# services/database/pyproject.toml
[project]
name = "job-wizard-db"
version = "0.1.0"

[tool.hatch.build.targets.wheel]
packages = ["database_pkg"]  # This tells Python that 'database_pkg' is the main code folder
```

### 2. Installing it in the Backend
Our backend service needs to use those database models. Instead of copying files, we "install" the database package as a local dependency:

```toml
# services/backend/pyproject.toml
dependencies = [
    "fastapi>=0.109.0",
    "job-wizard-db @ file:///root/job_wizard/services/database", # Local file reference!
]
```

This allows us to write code like this in the backend:
```python
from database_pkg.models.user import User  # This comes from services/database/database_pkg/models/user.py
```

---

## 🔄 Development Workflow

When you're working in a monorepo, you need to sync your environment whenever dependencies change.

### 1. Use `uv sync`
We use the **`uv`** package manager because it's extremely fast and handles local file dependencies perfectly.

If you add a new model to the database package:
1.  **Update the database code** in `services/database/database_pkg/`.
2.  **Sync the database package**:
    ```bash
    cd services/database && uv sync
    ```
3.  **Sync the backend** so it sees the changes:
    ```bash
    cd services/backend && uv sync
    ```

### 2. Common Gotchas
- **Renaming Packages**: If you rename the folder inside `services/database`, you must update the `packages` list in its `pyproject.toml` and then run `uv sync` in the backend to re-link it.
- **Import Paths**: Always use the package name (e.g., `database_pkg`) instead of the folder name (`services/database`) when importing in Python.

---

## 🎓 Summary for New Developers

1.  **Don't Duplicate Code**: If you need a database model in the backend, define it once in `services/database`.
2.  **Local Imports**: The backend sees the database code as an installed library named `database_pkg`.
3.  **Keep it Sync'd**: If something isn't importing correctly after a change, try running `uv sync` in both the backend and database directories.

---

## ⚡️ Database Performance: Shared Engine & Session Pooling

In our backend (`services/backend/app/core/db.py`), we use a **Shared Engine** approach. This is why it matters for performance and scalability:

### 1. What is the "Engine"?
The `engine` (defined in `database_pkg`) is the "connector" to your database. In a professional application, you don't create a new engine for every request. Instead, you create it once and share it across the entire application.

### 2. Advantages of Sharing the Engine
- **Connection Pooling**: The engine maintains a "pool" of active connections to the database. When a request comes in, it "borrows" a connection from the pool and returns it when finished.
- **Lower Latency**: Creating a new database connection (especially over a network) is expensive and slow. Reusing an existing connection from the pool is nearly instantaneous.
- **Resource Management**: By sharing the engine, we can limit the maximum number of simultaneous connections to the database (e.g., 20 connections), preventing our application from overwhelming the database during high-traffic spikes.

### 3. How we use it (Sessions)
Our `get_session()` generator in the backend uses the shared engine to provide clean, isolated **Sessions** to our API routes:

```python
# services/backend/app/core/db.py
def get_session():
    # Use the shared engine to create a session
    with Session(engine) as session:
        yield session
```

By following this pattern, we ensure that every database interaction in the **Job Wizard** is efficient, safe, and scalable.
