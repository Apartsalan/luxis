"""S231 — WACHTER: elke getoonde bijlage moet te openen zijn.

Aanleiding (Arsalan, 20-7): in de eerste-sommatie-dialoog stond een bijlage
vermeld die niet te openen was. Bij het uitzoeken bleek het een kruispunt-
probleem: vijf plekken toonden bijlagen, drie ervan konden ze niet openen —
een chip die stilletjes niets deed, doodlopende "gaat automatisch mee"-etiketten,
en een kale link zonder inlogbewijs (401).

De SOORT-fout is: *een bijlage tonen zonder adres om hem op te halen.* Deze
wachter loopt de voorvertoning-routes af en eist dat elk item vertelt waar het
bestand vandaan komt — `template_type` (server rendert vers) of `case_file_id`
(bestaand dossierbestand). Een toekomstige bijlagesoort die dat vergeet, valt
hier om in plaats van als dode knop bij Lisanne te eindigen.
"""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.auth.service import create_access_token
from app.cases.models import Case, CaseFile
from app.collections.models import Claim
from app.documents.router import RENDERABLE_PDF_KEYS
from app.incasso.models import IncassoPipelineStep
from app.relations.models import Contact


async def _sommatie_case(
    db: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID
) -> Case:
    """Eerste-sommatie-zaak met privé aansprakelijke wederpartij (→ renteoverzicht)
    én een factuur-PDF op de vordering (→ factuurbijlage)."""
    client_c = Contact(
        id=uuid.uuid4(), tenant_id=tenant_id, contact_type="company",
        name="Opdrachtgever B.V.", is_btw_plichtig=True,
    )
    opp = Contact(
        id=uuid.uuid4(), tenant_id=tenant_id, contact_type="person",
        name="Debiteur", email="debiteur@example.nl", legal_form=None,
    )
    db.add_all([client_c, opp])
    await db.flush()

    step = IncassoPipelineStep(
        id=uuid.uuid4(), tenant_id=tenant_id, name="Eerste sommatie",
        sort_order=1, min_wait_days=0, max_wait_days=4, debtor_type="both",
        step_category="minnelijk", template_type="sommatie_drukte",
    )
    db.add(step)
    await db.flush()

    case = Case(
        id=uuid.uuid4(), tenant_id=tenant_id, case_number="2026-97001",
        case_type="incasso", status="nieuw", debtor_type="b2b",
        client_id=client_c.id, opposing_party_id=opp.id,
        date_opened=date.today(), incasso_step_id=step.id,
    )
    db.add(case)
    await db.flush()

    factuur = CaseFile(
        id=uuid.uuid4(), tenant_id=tenant_id, case_id=case.id,
        original_filename="factuur-2026-001.pdf", stored_filename="x.pdf",
        file_size=1234, content_type="application/pdf",
        uploaded_by=user_id,
    )
    db.add(factuur)
    await db.flush()

    db.add(
        Claim(
            id=uuid.uuid4(), tenant_id=tenant_id, case_id=case.id,
            description="Factuur", principal_amount=Decimal("1000.00"),
            invoice_date=date.today(), default_date=date.today(),
            invoice_file_id=factuur.id,
        )
    )
    await db.commit()
    return case


@pytest.mark.asyncio
async def test_elke_auto_bijlage_heeft_een_bron(
    client, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Compose-route: elk 'gaat automatisch mee'-item moet openbaar te maken zijn."""
    case = await _sommatie_case(db, test_tenant.id, test_user.id)
    token = create_access_token(str(test_user.id), str(test_tenant.id))

    resp = await client.post(
        f"/api/email/compose/cases/{case.id}/auto-attachments",
        headers={"Authorization": f"Bearer {token}"},
        json={"template_type": "sommatie_drukte", "recipient_email": "debiteur@example.nl"},
    )
    assert resp.status_code == 200, resp.text
    items = resp.json()["items"]

    # De opzet moet écht bijlagen opleveren, anders bewijst de wachter niets.
    assert items, "verwacht renteoverzicht + factuur bij een eerste sommatie"
    for item in items:
        assert item["template_type"] or item["case_file_id"], (
            f"bijlage '{item['label']}' heeft geen bron om te openen — "
            "dode knop bij de gebruiker"
        )
        if item["template_type"]:
            assert item["template_type"] in RENDERABLE_PDF_KEYS, (
                f"'{item['template_type']}' staat niet in RENDERABLE_PDF_KEYS; "
                "de render-route zou hem weigeren"
            )


@pytest.mark.asyncio
async def test_facturen_per_stuk_niet_als_telling(
    client, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Eén regel per factuur — een telling ('2 factuur-PDF's') is niet te openen."""
    case = await _sommatie_case(db, test_tenant.id, test_user.id)
    token = create_access_token(str(test_user.id), str(test_tenant.id))

    resp = await client.post(
        f"/api/email/compose/cases/{case.id}/auto-attachments",
        headers={"Authorization": f"Bearer {token}"},
        json={"template_type": "sommatie_drukte", "recipient_email": "debiteur@example.nl"},
    )
    facturen = [i for i in resp.json()["items"] if i["kind"] == "factuur"]
    assert len(facturen) == 1
    assert facturen[0]["label"] == "factuur-2026-001.pdf"
    assert facturen[0]["case_file_id"]


@pytest.mark.asyncio
async def test_renteoverzicht_mag_als_pdf_gerenderd_worden():
    """De bijlage die de compose-route aanwijst, moet de render-route ook accepteren.

    Dit is de koppeling die eerder ontbrak: het etiket verwees nergens heen.
    """
    assert "renteoverzicht" in RENDERABLE_PDF_KEYS
    assert "verzoekschrift_faillissement" in RENDERABLE_PDF_KEYS


@pytest.mark.asyncio
async def test_render_pdf_weigert_onbekend_sjabloon(
    client, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """De render-route blijft dicht voor alles buiten de vaste lijst."""
    case = await _sommatie_case(db, test_tenant.id, test_user.id)
    token = create_access_token(str(test_user.id), str(test_tenant.id))

    resp = await client.post(
        f"/api/documents/docx/cases/{case.id}/render-pdf",
        headers={"Authorization": f"Bearer {token}"},
        json={"template_type": "sommatie_drukte"},
    )
    assert resp.status_code == 400
