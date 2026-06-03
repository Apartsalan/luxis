"""Tests for griffierecht calculation — official 2026 tariffs (Stcrt. 2025, 39855).

Guards AUDIT-H5 (the staffel was fully outdated — every tariff wrong) and
AUDIT-H6 (tariff was based on the debtor instead of the eiser/client).
"""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.collections.griffierechten import calculate_griffierecht
from app.collections.models import Claim
from app.relations.models import Contact

# ── Unit tests: official 2026 kanton tariffs ──────────────────────────────────


def test_kanton_onbepaald_and_tot_500():
    # ≤ €500: rechtspersoon €139, natuurlijk €93
    assert calculate_griffierecht(Decimal("400"), is_rechtspersoon=True)["griffierecht"] == Decimal("139")
    assert calculate_griffierecht(Decimal("400"), is_rechtspersoon=False)["griffierecht"] == Decimal("93")


def test_kanton_500_to_1500():
    assert calculate_griffierecht(Decimal("1000"), is_rechtspersoon=True)["griffierecht"] == Decimal("350")
    assert calculate_griffierecht(Decimal("1000"), is_rechtspersoon=False)["griffierecht"] == Decimal("233")


def test_kanton_2500_to_5000():
    # The audit's headline number: €5.000 rechtspersoon must be €529 (was 530).
    assert calculate_griffierecht(Decimal("5000"), is_rechtspersoon=True)["griffierecht"] == Decimal("529")
    assert calculate_griffierecht(Decimal("5000"), is_rechtspersoon=False)["griffierecht"] == Decimal("265")


def test_kanton_5000_to_12500():
    assert calculate_griffierecht(Decimal("10000"), is_rechtspersoon=True)["griffierecht"] == Decimal("559")
    assert calculate_griffierecht(Decimal("10000"), is_rechtspersoon=False)["griffierecht"] == Decimal("265")


def test_kanton_top_band():
    # > €12.500 (t/m kantongrens €25.000): rechtspersoon €1.504, natuurlijk €753.
    assert calculate_griffierecht(Decimal("25000"), is_rechtspersoon=True)["griffierecht"] == Decimal("1504")
    assert calculate_griffierecht(Decimal("25000"), is_rechtspersoon=False)["griffierecht"] == Decimal("753")


def test_kanton_band_boundaries():
    # Exactly €500 → ≤500 band; €500.01 → next band.
    assert calculate_griffierecht(Decimal("500"), is_rechtspersoon=False)["griffierecht"] == Decimal("93")
    assert calculate_griffierecht(Decimal("500.01"), is_rechtspersoon=False)["griffierecht"] == Decimal("233")


def test_kanton_vs_rechtbank_court_label():
    assert calculate_griffierecht(Decimal("25000"))["rechter"] == "kantonrechter"
    assert calculate_griffierecht(Decimal("25000.01"))["rechter"] == "rechtbank"


# ── Unit tests: official 2026 civiel (rechtbank) tariffs ──────────────────────


def test_civiel_tot_100k():
    assert calculate_griffierecht(Decimal("60000"), is_rechtspersoon=True)["griffierecht"] == Decimal("3083")
    assert calculate_griffierecht(Decimal("60000"), is_rechtspersoon=False)["griffierecht"] == Decimal("1414")


def test_civiel_100k_to_1m():
    assert calculate_griffierecht(Decimal("500000"), is_rechtspersoon=True)["griffierecht"] == Decimal("7062")
    assert calculate_griffierecht(Decimal("500000"), is_rechtspersoon=False)["griffierecht"] == Decimal("2803")


def test_civiel_boven_1m():
    assert calculate_griffierecht(Decimal("2000000"), is_rechtspersoon=True)["griffierecht"] == Decimal("10487")
    assert calculate_griffierecht(Decimal("2000000"), is_rechtspersoon=False)["griffierecht"] == Decimal("2803")


# ── Unit tests: onvermogenden + edge cases ────────────────────────────────────


def test_onvermogend_is_flat_93_everywhere():
    # The reduced tariff is €93 regardless of band or court, and overrides the
    # rechtspersoon/natuurlijk distinction.
    for vordering in (Decimal("400"), Decimal("5000"), Decimal("25000"), Decimal("60000"), Decimal("2000000")):
        for is_rp in (True, False):
            res = calculate_griffierecht(vordering, is_rechtspersoon=is_rp, is_onvermogend=True)
            assert res["griffierecht"] == Decimal("93"), vordering


def test_zero_or_negative_claim():
    assert calculate_griffierecht(Decimal("0"))["griffierecht"] == Decimal("0")
    assert calculate_griffierecht(Decimal("-100"))["griffierecht"] == Decimal("0")


# ── Endpoint tests: tariff follows the eiser/client (AUDIT-H6) ─────────────────


async def _create_case_with_claim(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, *, client_id, debtor_type: str
):
    resp = await client.post(
        "/api/cases",
        json={
            "case_type": "incasso",
            "client_id": str(client_id),
            "debtor_type": debtor_type,
            "date_opened": date.today().isoformat(),
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    case_id = resp.json()["id"]
    contact = await db.get(Contact, client_id)
    db.add(
        Claim(
            id=uuid.uuid4(),
            tenant_id=contact.tenant_id,
            case_id=uuid.UUID(case_id),
            description="Factuur griffie-test",
            principal_amount=Decimal("5000.00"),
            default_date=date.today(),
        )
    )
    await db.commit()
    return case_id


@pytest.mark.asyncio
async def test_griffierecht_endpoint_follows_client_not_debtor(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_company: Contact, test_person: Contact
):
    """Eiser = company (rechtspersoon), debtor = b2c. The tariff must follow the
    client (€529), not the debtor (which would give €265) (AUDIT-H6)."""
    case_id = await _create_case_with_claim(
        client, auth_headers, db, client_id=test_company.id, debtor_type="b2c"
    )
    resp = await client.get(f"/api/cases/{case_id}/griffierecht", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert Decimal(str(data["griffierecht"])) == Decimal("529")
    assert data["tarief_categorie"] == "rechtspersoon"


@pytest.mark.asyncio
async def test_griffierecht_endpoint_natural_person_client(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_person: Contact
):
    """Eiser = natural person → natuurlijk-persoon tariff (€265 at €5.000)."""
    case_id = await _create_case_with_claim(
        client, auth_headers, db, client_id=test_person.id, debtor_type="b2b"
    )
    resp = await client.get(f"/api/cases/{case_id}/griffierecht", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    assert Decimal(str(resp.json()["griffierecht"])) == Decimal("265")


@pytest.mark.asyncio
async def test_griffierecht_endpoint_onvermogend_toggle(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_company: Contact
):
    """The optional ?onvermogend=true flag yields the reduced €93 tariff."""
    case_id = await _create_case_with_claim(
        client, auth_headers, db, client_id=test_company.id, debtor_type="b2b"
    )
    resp = await client.get(
        f"/api/cases/{case_id}/griffierecht?onvermogend=true", headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    assert Decimal(str(resp.json()["griffierecht"])) == Decimal("93")
