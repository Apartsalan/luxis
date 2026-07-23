"""S243 — BaseNet-fase vindbaar op de dossierlijst.

Wachters voor de demo-vondst: 11 "Akkoord dagvaarden"-dossiers stonden wél in
Luxis (alle 607 export-dossiers 1-op-1 aanwezig) maar waren onvindbaar — de
zoekbalk zocht niet op `basenet_origin_phase` en het stap-filter kijkt naar de
Luxis-stap, die bij geïmporteerde dossiers leeg is.
"""

import uuid
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.cases.models import Case
from app.relations.models import Contact


async def _make_case(db: AsyncSession, tenant_id, client_id, phase: str | None) -> Case:
    case = Case(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        case_number=f"TST-{uuid.uuid4().hex[:8]}",
        case_type="incasso",
        status="afgesloten",
        client_id=client_id,
        date_opened=date.today(),
        basenet_origin_phase=phase,
    )
    db.add(case)
    await db.commit()
    return case


@pytest.mark.asyncio
async def test_search_finds_case_by_basenet_phase(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_company: Contact
):
    """Zoeken op de fase-tekst ("Akkoord dagvaarden") vindt het dossier."""
    case = await _make_case(
        db, test_company.tenant_id, test_company.id, "Akkoord dagvaarden"
    )
    resp = await client.get(
        "/api/cases",
        params={"search": "akkoord dagvaard", "is_active": True},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    numbers = [c["case_number"] for c in resp.json()["items"]]
    assert case.case_number in numbers


@pytest.mark.asyncio
async def test_basenet_phase_filter_exact(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_company: Contact
):
    """Het fase-filter geeft alléén dossiers met exact die fase."""
    hit = await _make_case(
        db, test_company.tenant_id, test_company.id, "Akkoord dagvaarden"
    )
    miss = await _make_case(
        db, test_company.tenant_id, test_company.id, "Voorstel dagvaarden"
    )
    resp = await client.get(
        "/api/cases",
        params={"basenet_phase": "Akkoord dagvaarden"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    numbers = [c["case_number"] for c in resp.json()["items"]]
    assert hit.case_number in numbers
    assert miss.case_number not in numbers


@pytest.mark.asyncio
async def test_basenet_phases_endpoint_lists_distinct(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_company: Contact
):
    """Het opties-endpoint geeft de distinct fases (zonder NULL, zonder dubbelen)."""
    await _make_case(db, test_company.tenant_id, test_company.id, "Akkoord dagvaarden")
    await _make_case(db, test_company.tenant_id, test_company.id, "Akkoord dagvaarden")
    await _make_case(db, test_company.tenant_id, test_company.id, "Procederen?")
    await _make_case(db, test_company.tenant_id, test_company.id, None)

    resp = await client.get("/api/cases/basenet-phases", headers=auth_headers)
    assert resp.status_code == 200
    phases = resp.json()["phases"]
    assert phases.count("Akkoord dagvaarden") == 1
    assert "Procederen?" in phases
    assert None not in phases
