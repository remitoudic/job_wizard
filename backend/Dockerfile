FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY backend/pyproject.toml ./

# Copy database package
COPY database /database_pkg

# Install dependencies
RUN uv sync --no-dev

# Install Playwright browser binaries
# We set the path to be inside the project so it's easier to manage
ENV PLAYWRIGHT_BROWSERS_PATH=/app/.venv/ms-playwright
RUN uv run playwright install --with-deps chromium

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Copy uv and dependencies from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv
COPY --from=builder /database_pkg /database_pkg

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p /app/uploads

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/app/.venv/ms-playwright

# Install system dependencies required to run Chromium at runtime
RUN apt-get update && \
	apt-get install -y --no-install-recommends \
	ca-certificates \
	fonts-liberation \
	libasound2 \
	libatk1.0-0 \
	libatk-bridge2.0-0 \
	libcups2 \
	libdbus-1-3 \
	libdrm2 \
	libexpat1 \
	libfontconfig1 \
	libgbm1 \
	libgcc1 \
	libglib2.0-0 \
	libgtk-3-0 \
	libnspr4 \
	libnss3 \
	libpango-1.0-0 \
	libx11-6 \
	libx11-xcb1 \
	libxcb1 \
	libxcomposite1 \
	libxdamage1 \
	libxext6 \
	libxfixes3 \
	libxrandr2 \
	libxrender1 \
	libxss1 \
	libxtst6 \
	lsb-release \
	wget \
	xdg-utils && \
	rm -rf /var/lib/apt/lists/*

# Note: Playwright and browser binaries are installed in the builder stage
# so the virtualenv is populated before being copied into the final image.

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
