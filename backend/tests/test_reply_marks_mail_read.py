"""S245 — kruispunt-wachter (breed-testen): een verstuurd ANTWOORD op het
gedeelde verzendpunt (compose/send) markeert de 'nieuwe mail'-meldingen van dát
dossier als gelezen. Wachters: een ander dossier en een ander meldingstype
blijven ongelezen; een verse mail (geen reply) raakt de meldingen niet.

De provider-send wordt gemockt (geen echte mail) — we toetsen de bedrading en
de afbakening, niet de verzending zelf.
"""

import uuid
from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.auth.service import create_access_token
from app.cases.models import Case
from app.email.oauth_models import EmailAccount
from app.notifications.models import Notification
from app.notifications.schemas import NotificationCreate
from app.notifications.service import (
    NOTIF_AI_DRAFT_READY,
    NOTIF_EMAIL_RECEIVED,
    create_notification,
)
from app.relations.models import Contact


async def _case(db, tenant_id, number):
    contact = Contact(
        id=uuid.uuid4(), tenant_id=tenant_id, contact_type="company", name="Cliënt",
    )
    db.add(contact)
    await db.flush()
    case = Case(
        id=uuid.uuid4(), tenant_id=tenant_id, case_number=number, case_type="incasso",
        status="nieuw", debtor_type="b2b", client_id=contact.id, date_opened=date.today(),
    )
    db.add(case)
    await db.flush()
    return case


async def _unread(db, tenant_id, case_id, type_):
    rows = await db.execute(
        select(Notification).where(
            Notification.tenant_id == tenant_id,
            Notification.case_id == case_id,
            Notification.type == type_,
            Notification.is_read == False,  # noqa: E712
        )
    )
    return len(list(rows.scalars().all()))


@pytest.mark.asyncio
async def test_reply_marks_case_mail_read_but_scopes(
    client, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    case = await _case(db, test_tenant.id, "2026-97001")
    other = await _case(db, test_tenant.id, "2026-97002")
    db.add(EmailAccount(
        id=uuid.uuid4(), tenant_id=test_tenant.id, user_id=test_user.id,
        provider="outlook", email_address="kantoor@test.nl",
        access_token_enc=b"x", refresh_token_enc=b"y",
    ))
    for c in (case, other):
        await create_notification(db, test_tenant.id, test_user.id, NotificationCreate(
            type=NOTIF_EMAIL_RECEIVED, title="Nieuwe email", message="x",
            case_id=c.id, case_number=c.case_number))
    await create_notification(db, test_tenant.id, test_user.id, NotificationCreate(
        type=NOTIF_AI_DRAFT_READY, title="AI-concept", message="x", case_id=case.id))
    await db.commit()

    token = create_access_token(str(test_user.id), str(test_tenant.id))
    provider = SimpleNamespace(send_message=AsyncMock(return_value="provider-msg-1"))
    with (
        patch("app.email.compose_router.resolve_office_channel",
              new_callable=AsyncMock) as mock_resolve,
        patch("app.email.compose_router.get_valid_access_token",
              new_callable=AsyncMock) as mock_token,
        patch("app.email.compose_router.get_provider", return_value=provider),
    ):
        mock_resolve.return_value = (None, None)  # geen kantoorkanaal → val terug op account
        mock_token.return_value = "fake-token"
        resp = await client.post(
            "/api/email/compose/send",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "to": ["debiteur@example.nl"],
                "subject": "Re: uw bericht",
                "body_html": "<p>Dank voor uw reactie.</p>",
                "case_id": str(case.id),
                "reply_to_message_id": "msg-abc",
                "already_branded": True,
            },
        )

    assert resp.status_code == 200, resp.text
    provider.send_message.assert_called_once()  # echt via provider verstuurd

    assert await _unread(db, test_tenant.id, case.id, NOTIF_EMAIL_RECEIVED) == 0   # gewist
    assert await _unread(db, test_tenant.id, other.id, NOTIF_EMAIL_RECEIVED) == 1  # ander dossier blijft
    assert await _unread(db, test_tenant.id, case.id, NOTIF_AI_DRAFT_READY) == 1   # ander type blijft


@pytest.mark.asyncio
async def test_fresh_mail_does_not_mark_read(
    client, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Een verse mail (geen reply_to_message_id) op hetzelfde dossier mag de
    mail-meldingen NIET wissen — alleen een echt antwoord doet dat."""
    case = await _case(db, test_tenant.id, "2026-97003")
    db.add(EmailAccount(
        id=uuid.uuid4(), tenant_id=test_tenant.id, user_id=test_user.id,
        provider="outlook", email_address="kantoor@test.nl",
        access_token_enc=b"x", refresh_token_enc=b"y",
    ))
    await create_notification(db, test_tenant.id, test_user.id, NotificationCreate(
        type=NOTIF_EMAIL_RECEIVED, title="Nieuwe email", message="x",
        case_id=case.id, case_number=case.case_number))
    await db.commit()

    token = create_access_token(str(test_user.id), str(test_tenant.id))
    provider = SimpleNamespace(send_message=AsyncMock(return_value="provider-msg-2"))
    with (
        patch("app.email.compose_router.resolve_office_channel",
              new_callable=AsyncMock) as mock_resolve,
        patch("app.email.compose_router.get_valid_access_token",
              new_callable=AsyncMock) as mock_token,
        patch("app.email.compose_router.get_provider", return_value=provider),
    ):
        mock_resolve.return_value = (None, None)
        mock_token.return_value = "fake-token"
        resp = await client.post(
            "/api/email/compose/send",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "to": ["debiteur@example.nl"],
                "subject": "Vrij bericht",
                "body_html": "<p>Ter info.</p>",
                "case_id": str(case.id),
                "already_branded": True,
            },
        )

    assert resp.status_code == 200, resp.text
    assert await _unread(db, test_tenant.id, case.id, NOTIF_EMAIL_RECEIVED) == 1  # blijft ongelezen
