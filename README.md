# Luxis

Praktijkmanagementsysteem voor de Nederlandse advocatuur.

## Quick Start

```bash
# Copy environment file
cp .env.example .env

# Start all services
docker compose up

# Backend API docs: http://localhost:8000/docs
# Frontend: http://localhost:3000
```

## Development

```bash
# Start with hot reload
docker compose -f docker-compose.yml -f docker-compose.dev.yml up

# Run tests
docker compose exec backend pytest tests/ -v

# Create migration
docker compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker compose exec backend alembic upgrade head
```

## Stack

- **Backend:** FastAPI (Python 3.12) + PostgreSQL 16
- **Frontend:** Next.js 15 + shadcn/ui
- **Deployment:** Docker Compose
