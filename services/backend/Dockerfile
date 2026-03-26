FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY services/backend/pyproject.toml ./

# Copy database package
COPY services/database /database_pkg

# Install build dependencies for compiling Python packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Fix absolute path in pyproject.toml for Docker environment
RUN sed -i 's|file:///root/job_wizard/services/database|file:///database_pkg|g' pyproject.toml

# Install dependencies (including dev dependencies for testing)
ENV UV_HTTP_TIMEOUT=300
RUN uv sync --extra dev

# Production stage
FROM python:3.11-slim

WORKDIR /app

# WeasyPrint system dependencies (Pango, Cairo, GDK-Pixbuf, fonts)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 libffi-dev libcairo2 \
    fonts-liberation fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Copy uv and dependencies from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv
COPY --from=builder /database_pkg /database_pkg

# Copy application code from backend directory
COPY services/backend/app ./app
COPY services/backend/scripts/seed_user.py ./scripts/seed_user.py
COPY services/backend/pyproject.toml .

# Fix absolute path in pyproject.toml for Docker environment (same as builder)
RUN sed -i 's|file:///root/job_wizard/services/database|file:///database_pkg|g' pyproject.toml

# Create uploads directory
RUN mkdir -p /app/uploads

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1


# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
