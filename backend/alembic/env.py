import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import all models so Alembic can detect them
from app.auth.models import Tenant, User  # noqa: F401
from app.cases.models import Case, CaseActivity, CaseParty  # noqa: F401
from app.collections.models import (  # noqa: F401,E501
    Claim,
    Derdengelden,
    InterestRate,
    Payment,
    PaymentArrangement,
)
from app.config import settings
from app.database import Base
from app.documents.models import DocumentTemplate, GeneratedDocument  # noqa: F401
from app.email.attachment_models import EmailAttachment  # noqa: F401
from app.email.oauth_models import EmailAccount  # noqa: F401
from app.email.synced_email_models import SyncedEmail  # noqa: F401
from app.incasso.models import IncassoPipelineStep  # noqa: F401
from app.invoices.models import Expense, Invoice, InvoiceLine, InvoicePayment  # noqa: F401
from app.relations.kyc_models import KycVerification  # noqa: F401
from app.relations.models import Contact, ContactLink  # noqa: F401
from app.time_entries.models import TimeEntry  # noqa: F401
from app.trust_funds.models import TrustTransaction  # noqa: F401
from app.workflow.models import (  # noqa: F401,E501
    WorkflowRule,
    WorkflowStatus,
    WorkflowTask,
    WorkflowTransition,
)

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
