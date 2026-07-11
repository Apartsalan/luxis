"""Luxis — Practice Management System for Dutch Law Firms."""

import logging
import sys
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.ai_agent.followup_router import router as followup_router
from app.ai_agent.intake_router import router as intake_router
from app.ai_agent.payment_matching_router import router as payment_matching_router
from app.ai_agent.router import router as ai_agent_router
from app.ai_agent.unified_router import router as ai_unified_router
from app.auth.router import router as auth_router
from app.auth.router import users_router
from app.calendar.router import router as calendar_router
from app.cases.router import router as cases_router
from app.collections.router import rates_router
from app.collections.router import router as collections_router
from app.config import secret_key_status, settings
from app.dashboard.router import reports_router
from app.dashboard.router import router as dashboard_router
from app.documents.router import router as documents_router
from app.email.compose_router import router as email_compose_router
from app.email.oauth_router import router as email_oauth_router
from app.email.router import router as email_router
from app.email.sync_router import router as email_sync_router
from app.exact_online.router import router as exact_online_router
from app.incasso.router import router as incasso_router
from app.invoices.router import cases_billing_router, expenses_router
from app.invoices.router import router as invoices_router
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.rate_limit import limiter
from app.notifications.router import router as notifications_router
from app.products.router import router as products_router
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

# SECRET_KEY hardening (AUDIT-B1). A placeholder/short key lets an attacker
# forge valid JWTs. Default-secure: any environment that is NOT an explicit
# dev/test env is enforced — so an unset or misspelled APP_ENV in production
# still refuses to start instead of silently running with a weak key.
_secret_weak, _secret_enforced = secret_key_status(settings.secret_key, settings.app_env)
if _secret_weak and _secret_enforced:
    logging.critical(
        "FATAL: SECRET_KEY is a default placeholder or too short (min 32 chars) "
        "and APP_ENV=%r is not a development environment. Set a strong random "
        "SECRET_KEY. Refusing to start.",
        settings.app_env,
    )
    sys.exit(1)
elif _secret_weak:
    logging.critical(
        "SECURITY WARNING: SECRET_KEY is a default placeholder or too short "
        "(min 32 chars). Tolerated only because APP_ENV=%r is a development "
        "environment — NEVER deploy with this key.",
        settings.app_env,
    )

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
    # S183-1 drift-guard: in production, refuse to serve if any tenant table lacks
    # RLS. A silent tenant-isolation gap is a client-PII leak risk, so we fail
    # closed — same posture as the luxis_app-role check in app.middleware.tenant.
    # Skipped outside production: the create_all dev/test schema legitimately has
    # no RLS applied (only the migration/isolation-test applies it).
    if settings.app_env == "production":
        from app.database import engine
        from app.security.rls import find_unprotected_tenant_tables

        async with engine.connect() as conn:
            unprotected = await conn.run_sync(find_unprotected_tenant_tables)
        if unprotected:
            raise RuntimeError(
                "CRITICAL: tenant-isolatie-gat — deze tabellen missen RLS in "
                f"productie: {unprotected}. Draai de migraties (apply_rls)."
            )
    # Laad de persistente mailslot-stand in het geheugen (S197), vóórdat er ook
    # maar één request wordt bediend. Fail-safe: lukt het laden niet, dan blijft
    # de stand ongewijzigd en dekt het env-noodslot productie.
    from app.database import async_session
    from app.email.service import load_mail_lock

    try:
        async with async_session() as _lock_db:
            await load_mail_lock(_lock_db)
    except Exception:
        logging.exception("Kon mailslot-stand niet laden bij opstart (fail-safe: blijft dicht).")

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

# Rate limiting on auth endpoints
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
app.include_router(reports_router)
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
app.include_router(ai_unified_router)
app.include_router(intake_router)
app.include_router(followup_router)
app.include_router(payment_matching_router)
app.include_router(notifications_router)
app.include_router(exact_online_router)
app.include_router(products_router)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}
