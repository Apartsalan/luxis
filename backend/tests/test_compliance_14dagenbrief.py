"""S203 #5 — 14-dagenbrief-waarborg (art. 6:96 lid 6 BW).

De compliance-check las de altijd-lege generated_documents-tabel en had nul
callers. Nu leest hij het echte pijplijn-spoor (CaseStepHistory op de
14-dagenbrief-stap) én gate't de batch-verzending voor consumenten.
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.cases.models import Case
from app.collections.compliance import get_dagenbrief_entered_at
from app.incasso.models import IncassoPipelineStep
from app.incasso.service import batch_execute, move_case_to_step
from app.relations.models import Contact


async def _b2c_case_with_steps(db, tenant_id, user_id):
    """B2C-zaak + een 14-dagenbrief-stap en een sommatie-stap (met sjabloon)."""
    contact = Contact(
        id=uuid.uuid4(), tenant_id=tenant_id, contact_type="person",
        name="Jan Consument", email="jan@example.nl",
    )
    debtor = Contact(
        id=uuid.uuid4(), tenant_id=tenant_id, contact_type="person",
        name="Debiteur Consument", email="debiteur@example.nl",
    )
    db.add_all([contact, debtor])
    await db.flush()
    dagenbrief = IncassoPipelineStep(
        id=uuid.uuid4(), tenant_id=tenant_id, name="14-dagenbrief",
        sort_order=0, min_wait_days=0, max_wait_days=15, debtor_type="b2c",
    )
    sommatie = IncassoPipelineStep(
        id=uuid.uuid4(), tenant_id=tenant_id, name="Eerste sommatie",
        sort_order=1, min_wait_days=0, max_wait_days=7, debtor_type="both",
        template_type="sommatie_drukte",
        email_subject_template="Sommatie {{ zaak.zaaknummer }}",
        email_body_template="Betreft {{ zaak.zaaknummer }}. Gelieve te betalen.",
    )
    db.add_all([dagenbrief, sommatie])
    await db.flush()
    case = Case(
        id=uuid.uuid4(), tenant_id=tenant_id, case_number="2026-95001",
        case_type="incasso", status="nieuw", debtor_type="b2c",
        client_id=contact.id, opposing_party_id=debtor.id, date_opened=date.today(),
        incasso_step_id=sommatie.id,
    )
    db.add(case)
    await db.flush()
    return case, dagenbrief, sommatie


@pytest.mark.asyncio
async def test_dagenbrief_detection_reads_step_history(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    case, dagenbrief, _sommatie = await _b2c_case_with_steps(db, test_tenant.id, test_user.id)

    # Nog geen 14-dagenbrief-stap doorlopen → None.
    assert await get_dagenbrief_entered_at(db, test_tenant.id, case.id) is None

    # Zaak door de 14-dagenbrief-stap halen → detectie vindt de datum.
    await move_case_to_step(db, test_tenant.id, case, dagenbrief, user_id=test_user.id)
    await db.flush()
    entered = await get_dagenbrief_entered_at(db, test_tenant.id, case.id)
    assert entered == date.today()


@pytest.mark.asyncio
async def test_batch_blocks_b2c_sommatie_without_dagenbrief(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """B2C-zaak op de sommatie-stap zónder 14-dagenbrief in de historie → batch slaat
    'm over mét reden (art. 6:96 lid 6)."""
    case, _db_step, _sommatie = await _b2c_case_with_steps(db, test_tenant.id, test_user.id)
    await db.commit()

    result = await batch_execute(
        db, test_tenant.id, test_user.id,
        case_ids=[case.id], action="generate_document", send_email=False,
    )
    assert result.processed == 0
    assert result.skipped == 1
    assert any("14-dagenbrief" in e for e in result.errors)


@pytest.mark.asyncio
async def test_batch_allows_b2c_sommatie_after_dagenbrief(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Ná het doorlopen van de 14-dagenbrief-stap mag de sommatie wel gegenereerd worden."""
    from app.collections.models import InterestRate
    db.add(InterestRate(
        id=uuid.uuid4(), rate_type="statutory", rate=Decimal("8.00"),
        effective_from=date(2023, 1, 1),
    ))
    case, dagenbrief, sommatie = await _b2c_case_with_steps(db, test_tenant.id, test_user.id)
    # Historie-rij voor de 14-dagenbrief, 20 dagen geleden (termijn ruim verstreken),
    # daarna terug op de sommatie-stap.
    await move_case_to_step(db, test_tenant.id, case, dagenbrief, user_id=test_user.id)
    case.incasso_step_id = sommatie.id
    await db.flush()
    # Backdate de historie zodat de gate 'verstuurd' herkent.
    from sqlalchemy import update

    from app.incasso.models import CaseStepHistory
    await db.execute(
        update(CaseStepHistory)
        .where(CaseStepHistory.case_id == case.id, CaseStepHistory.step_id == dagenbrief.id)
        .values(entered_at=date.today() - timedelta(days=20))
    )
    await db.commit()

    result = await batch_execute(
        db, test_tenant.id, test_user.id,
        case_ids=[case.id], action="generate_document", send_email=False,
    )
    assert result.processed == 1
    assert not any("14-dagenbrief" in e for e in result.errors)
