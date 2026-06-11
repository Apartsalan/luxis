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
COPY pyproject.toml uv.lock ./

# Install pinned, hashed dependencies from the lockfile (reproducible builds).
# Export the locked runtime closure to a fully-pinned + hashed requirements file,
# then install exactly that set. The project itself is NOT installed here — it's
# copied below and imported via PYTHONPATH=/app, so --no-emit-project is correct.
RUN uv export --frozen --no-dev --no-emit-project -o requirements.txt \
    && uv pip install --system --no-deps -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN adduser --disabled-password --gecos '' --uid 1001 appuser \
    && mkdir -p /app/uploads && chown -R appuser:appuser /app/uploads
USER appuser

# Run migrations and start server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
