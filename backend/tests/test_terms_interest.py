"""S177: rente uit de AV lezen + de laag 'uit-AV-gelezen' in de rentekeuze-keten.

Hiërarchie: dossier > klantkaart (default_*) > uit-AV (terms_*) > wettelijk.
"""

import uuid
from datetime import date
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant
from app.relations.models import Contact
from app.relations.terms_interest import parse_interest_from_text

# ── De pure lezer (regex) ────────────────────────────────────────────────────

def test_parse_reads_two_percent_per_month():
    txt = (
        "13.3. Indien Cliënt in verzuim is, heeft Invorderingsbedrijf het recht een "
        "rente in rekening te brengen gelijk aan 2% per maand vanaf de vervaldag van de factuur."
    )
    r = parse_interest_from_text(txt)
    assert r is not None
    assert r.rate == Decimal("2")
    assert r.basis == "monthly"
    assert r.compound is False
    assert "13.3" in r.source
    assert r.method == "regex"


def test_parse_ignores_incassokosten_percentage():
    # 15% incassokosten is GEEN rente — er staat geen 'per maand/jaar' bij.
    txt = "De buitengerechtelijke incassokosten bedragen 15% van de openstaande vordering."
    assert parse_interest_from_text(txt) is None


def test_parse_handles_comma_decimal_and_year():
    r = parse_interest_from_text("een vertragingsrente van 1,5 % per jaar is verschuldigd")
    assert r is not None
    assert r.rate == Decimal("1.5")
    assert r.basis == "yearly"


# ── De keten: uit-AV-gelezen als default op een nieuw dossier ────────────────

@pytest_asyncio.fixture
async def av_client(db: AsyncSession, test_tenant: Tenant) -> Contact:
    """Cliënt zonder handmatige rente, mét een uit-AV-gelezen 2%/maand."""
    contact = Contact(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        contact_type="company",
        name="AV Leest B.V.",
        email="info@avleest.nl",
        terms_interest_rate=Decimal("2.00"),
        terms_interest_basis="monthly",
        terms_interest_compound=False,
        terms_interest_source="artikel 13.3: 2% per maand",
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


@pytest_asyncio.fixture
async def av_client_but_manual(db: AsyncSession, test_tenant: Tenant) -> Contact:
    """Cliënt met ZOWEL een handmatige klantkaart-keuze als een uit-AV-waarde."""
    contact = Contact(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        contact_type="company",
        name="Handmatig Wint B.V.",
        email="info@handmatig.nl",
        default_interest_type="commercial",       # klantkaart (override)
        terms_interest_rate=Decimal("2.00"),       # uit AV
        terms_interest_basis="monthly",
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


@pytest.mark.asyncio
async def test_case_inherits_rate_from_av(client: AsyncClient, auth_headers: dict, av_client: Contact):
    """Geen handmatige keuze → dossier neemt de uit-AV-rente over (contractueel 2%)."""
    payload = {
        "case_type": "incasso",
        "client_id": str(av_client.id),
        "date_opened": date.today().isoformat(),
    }
    resp = await client.post("/api/cases", json=payload, headers=auth_headers)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["interest_type"] == "contractual"
    assert float(data["contractual_rate"]) == 2.0
    assert data["contractual_compound"] is False


@pytest.mark.asyncio
async def test_manual_klantkaart_wins_over_av(
    client: AsyncClient, auth_headers: dict, av_client_but_manual: Contact
):
    """Handmatige klantkaart-keuze (commercial) wint van de uit-AV-waarde."""
    payload = {
        "case_type": "incasso",
        "client_id": str(av_client_but_manual.id),
        "date_opened": date.today().isoformat(),
    }
    resp = await client.post("/api/cases", json=payload, headers=auth_headers)
    assert resp.status_code == 201, resp.text
    assert resp.json()["interest_type"] == "commercial"
