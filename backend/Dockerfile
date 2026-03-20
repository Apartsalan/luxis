FROM python:3.12-slim

WORKDIR /app

# Ensure Python can always find the app module
ENV PYTHONPATH=/app

# Install system dependencies for WeasyPrint, LibreOffice (PDF), and PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    libcairo2 \
    libreoffice-writer \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first (Docker layer caching)
COPY pyproject.toml ./

# Install dependencies only (not the package itself — code isn't copied yet)
RUN uv pip install --system ".[dev]"

# Copy application code
COPY . .

# Create non-root user for security
RUN adduser --disabled-password --gecos '' --uid 1001 appuser \
    && mkdir -p /app/uploads && chown -R appuser:appuser /app/uploads
USER appuser

# Run migrations and start server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
