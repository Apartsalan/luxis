"""Luxis — Practice Management System for Dutch Law Firms."""

import logging
import sys
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ai_agent.followup_router import router as followup_router
from app.ai_agent.intake_router import router as intake_router
from app.ai_agent.payment_matching_router import router as payment_matching_router
from app.ai_agent.router import router as ai_agent_router
from app.auth.router import router as auth_router
from app.auth.router import users_router
from app.calendar.router import router as calendar_router
from app.cases.router import router as cases_router
from app.collections.router import rates_router
from app.collections.router import router as collections_router
from app.config import settings
from app.dashboard.router import router as dashboard_router
from app.documents.router import router as documents_router
from app.email.compose_router import router as email_compose_router
from app.email.oauth_router import router as email_oauth_router
from app.email.router import router as email_router
from app.email.sync_router import router as email_sync_router
from app.incasso.router import router as incasso_router
from app.invoices.router import cases_billing_router, expenses_router
from app.invoices.router import router as invoices_router
from app.middleware.logging import RequestLoggingMiddleware
from app.notifications.router import router as notifications_router
from app.relations.kyc_router import router as kyc_router
from app.relations.router import router as relations_router
from app.search.router import router as search_router
from app.settings.router import router as settings_router
from app.time_entries.router import router as time_entries_router
from app.trust_funds.router import router as trust_funds_router
from app.workflow.router import router as workflow_router
from app.workflow.scheduler import start_scheduler, stop_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.app_debug else logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

# SEC-4: Refuse to start in production with default SECRET_KEY
_default_key = "change-this-to-a-random-string-in-production"
if settings.app_env == "production" and settings.secret_key == _default_key:
    logging.critical(
        "FATAL: SECRET_KEY is the default placeholder. "
        "Set a strong random SECRET_KEY in production!"
    )
    sys.exit(1)

# Initialize Sentry if DSN is configured
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        traces_sample_rate=0.1,
        send_default_pii=False,  # Never send PII to Sentry
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup: start the workflow scheduler
    start_scheduler()
    yield
    # Shutdown: stop the scheduler
    stop_scheduler()


app = FastAPI(
    title="Luxis API",
    description="Praktijkmanagementsysteem voor de Nederlandse Advocatuur",
    version="0.1.0",
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url="/redoc" if settings.app_env != "production" else None,
    lifespan=lifespan,
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
app.include_router(users_router)
app.include_router(relations_router)
app.include_router(cases_router)
app.include_router(collections_router)
app.include_router(rates_router)
app.include_router(documents_router)
app.include_router(dashboard_router)
app.include_router(workflow_router)
app.include_router(time_entries_router)
app.include_router(invoices_router)
app.include_router(expenses_router)
app.include_router(cases_billing_router)
app.include_router(settings_router)
app.include_router(trust_funds_router)
app.include_router(kyc_router)
app.include_router(calendar_router)
app.include_router(email_router)
app.include_router(email_oauth_router)
app.include_router(email_sync_router)
app.include_router(email_compose_router)
app.include_router(search_router)
app.include_router(incasso_router)
app.include_router(ai_agent_router)
app.include_router(intake_router)
app.include_router(followup_router)
app.include_router(payment_matching_router)
app.include_router(notifications_router)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}
