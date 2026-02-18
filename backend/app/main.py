"""Luxis — Practice Management System for Dutch Law Firms."""

import logging

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.cases.router import router as cases_router
from app.collections.router import rates_router
from app.collections.router import router as collections_router
from app.config import settings
from app.dashboard.router import router as dashboard_router
from app.documents.router import router as documents_router
from app.middleware.logging import RequestLoggingMiddleware
from app.relations.router import router as relations_router

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.app_debug else logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

# Initialize Sentry if DSN is configured
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        traces_sample_rate=0.1,
        send_default_pii=False,  # Never send PII to Sentry
    )

app = FastAPI(
    title="Luxis API",
    description="Praktijkmanagementsysteem voor de Nederlandse Advocatuur",
    version="0.1.0",
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url="/redoc" if settings.app_env != "production" else None,
)

# CORS — allow frontend to talk to the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging
app.add_middleware(RequestLoggingMiddleware)

# Routers
app.include_router(auth_router)
app.include_router(relations_router)
app.include_router(cases_router)
app.include_router(collections_router)
app.include_router(rates_router)
app.include_router(documents_router)
app.include_router(dashboard_router)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}
