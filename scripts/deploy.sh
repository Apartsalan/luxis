#!/bin/bash
# Deployment script for Luxis on Hetzner VPS
# Usage: ./scripts/deploy.sh

set -e

echo "Pulling latest changes..."
git pull origin main

echo "Building and starting containers..."
docker compose build
docker compose up -d

echo "Running database migrations..."
docker compose exec -T backend alembic upgrade head

echo "Deployment complete!"
echo "  Backend: http://localhost:8000/docs"
echo "  Frontend: http://localhost:3000"
