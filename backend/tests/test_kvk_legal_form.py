"""S211: rechtsvorm-koppeling (KvK) + renteoverzicht-bijlage-beslissing.

Dekt:
- de beslisregel should_attach_rente_bijlage per rechtsvorm (besluit A/B/C);
- de KvK-client get_rechtsvorm met een gemockte respons + zacht falen;
- auto-vullen van legal_form bij relatie-aanmaak (KvK gemockt);
- dat een KvK-storing de relatie-opslag NIET breekt.
"""

from types import SimpleNamespace

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant
from app.collections.compliance import (
    RENTE_BIJLAGE_TEMPLATE_TYPES,
    should_attach_rente_bijlage,
)
from app.relations import service as relations_service
from app.relations.schemas import ContactCreate

# ── Beslisregel (besluit A/B/C) ───────────────────────────────────────────────


def _party(legal_form):
    return SimpleNamespace(legal_form=legal_form)


@pytest.mark.parametrize(
    "legal_form",
    [
        "Eenmanszaak",
        "Vennootschap onder firma",
        "Commanditaire vennootschap",
        "Maatschap",
    ],
)
def test_prive_aansprakelijk_krijgt_bijlage(legal_form):
    """Besluit A: privé aansprakelijke vormen → wél bijlage."""
    assert should_attach_rente_bijlage(_party(legal_form)) is True


@pytest.mark.parametrize(
    "legal_form",
    [
        "Besloten Vennootschap",
        "Besloten Vennootschap met gewone structuur",
        "Naamloze Vennootschap",
        "Stichting",
        "Coöperatie",
        "Coöperatieve vereniging",
    ],
)
def test_beperkt_aansprakelijk_geen_bijlage(legal_form):
    """Besluit A: BV/NV/stichting/coöperatie → geen bijlage."""
    assert should_attach_rente_bijlage(_party(legal_form)) is False


def test_vof_bevat_vennootschap_maar_krijgt_wel_bijlage():
    """Valkuil (premortem 2): VOF/CV bevatten 'vennootschap' maar zijn privé
    aansprakelijk — mogen NIET als BV/NV worden uitgesloten."""
    assert should_attach_rente_bijlage(_party("Vennootschap onder firma")) is True
    assert should_attach_rente_bijlage(_party("Commanditaire vennootschap")) is True


def test_onbekende_rechtsvorm_krijgt_bijlage():
    """Besluit B: zakelijk met lege/onbekende rechtsvorm → veilige kant (wél)."""
    assert should_attach_rente_bijlage(_party(None)) is True
    assert should_attach_rente_bijlage(_party("")) is True
    assert should_attach_rente_bijlage(None) is True


def test_b2c_altijd_bijlage_ongeacht_rechtsvorm():
    """Besluit C: consument is altijd privé aansprakelijk → altijd bijlage,
    ook als er per ongeluk een BV-rechtsvorm op zou staan."""
    assert should_attach_rente_bijlage(_party("Besloten Vennootschap"), "b2c") is True
    assert should_attach_rente_bijlage(None, "b2c") is True


def test_bijlage_sjablonen_zijn_de_sommatie_brieven():
    """De bijlage hoort bij de 14-dagenbrief en de sommaties.

    S220 blok 1 punt 3 voegde 'sommatie' bewust toe (renteoverzicht ook op de
    documentenroute met dat brieftype) maar vergat deze pin-test — CI stond
    daardoor stil rood van 15 t/m 16 juli (S223-review). Wijzigt de set opnieuw
    bewust? Werk deze test dan in dezelfde commit bij."""
    assert RENTE_BIJLAGE_TEMPLATE_TYPES == frozenset(
        {"14_dagenbrief", "sommatie_drukte", "sommatie"}
    )


# ── KvK-client ────────────────────────────────────────────────────────────────


class _FakeResponse:
    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


class _FakeClient:
    """Vervangt httpx.AsyncClient: geeft een vooraf ingestelde respons terug."""

    def __init__(self, response):
        self._response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def get(self, url, headers=None):
        if isinstance(self._response, Exception):
            raise self._response
        return self._response


@pytest.mark.asyncio
async def test_get_rechtsvorm_leest_uitgebreide_rechtsvorm(monkeypatch):
    payload = {
        "_embedded": {
            "eigenaar": {
                "rechtsvorm": "Besloten vennootschap",
                "uitgebreideRechtsvorm": "Besloten Vennootschap met gewone structuur",
            }
        }
    }
    monkeypatch.setattr("app.integrations.kvk_service.settings.kvk_api_key", "testkey")
    monkeypatch.setattr(
        "app.integrations.kvk_service.httpx.AsyncClient",
        lambda *a, **k: _FakeClient(_FakeResponse(200, payload)),
    )
    from app.integrations.kvk_service import get_rechtsvorm

    assert await get_rechtsvorm("68750110") == "Besloten Vennootschap met gewone structuur"


@pytest.mark.asyncio
async def test_get_rechtsvorm_zonder_sleutel_slaapt(monkeypatch):
    """Lege sleutel → geen HTTP-call, gewoon None (nooit stil verkeerde omgeving)."""

    def _boom(*a, **k):
        raise AssertionError("KvK mag niet bevraagd worden zonder sleutel")

    monkeypatch.setattr("app.integrations.kvk_service.settings.kvk_api_key", "")
    monkeypatch.setattr("app.integrations.kvk_service.httpx.AsyncClient", _boom)
    from app.integrations.kvk_service import get_rechtsvorm

    assert await get_rechtsvorm("68750110") is None


@pytest.mark.asyncio
async def test_get_rechtsvorm_kapt_lange_waarde_af(monkeypatch):
    """Onverwacht lange KvK-rechtsvorm → afgekapt op 100 (kolomlengte)."""
    payload = {"_embedded": {"eigenaar": {"uitgebreideRechtsvorm": "X" * 250}}}
    monkeypatch.setattr("app.integrations.kvk_service.settings.kvk_api_key", "testkey")
    monkeypatch.setattr(
        "app.integrations.kvk_service.httpx.AsyncClient",
        lambda *a, **k: _FakeClient(_FakeResponse(200, payload)),
    )
    from app.integrations.kvk_service import get_rechtsvorm

    assert len(await get_rechtsvorm("68750110")) == 100


@pytest.mark.asyncio
async def test_get_rechtsvorm_ongeldig_nummer_niet_bevraagd(monkeypatch):
    """Geen 8 cijfers → geen HTTP-call, gewoon None."""
    called = {"hit": False}

    def _boom(*a, **k):
        called["hit"] = True
        raise AssertionError("KvK mag niet bevraagd worden bij ongeldig nummer")

    monkeypatch.setattr("app.integrations.kvk_service.httpx.AsyncClient", _boom)
    from app.integrations.kvk_service import get_rechtsvorm

    assert await get_rechtsvorm("123") is None
    assert await get_rechtsvorm(None) is None
    assert called["hit"] is False


@pytest.mark.asyncio
async def test_get_rechtsvorm_storing_geeft_none(monkeypatch):
    """Netwerkfout / timeout → zacht falen (None), nooit een exception."""
    monkeypatch.setattr("app.integrations.kvk_service.settings.kvk_api_key", "testkey")
    monkeypatch.setattr(
        "app.integrations.kvk_service.httpx.AsyncClient",
        lambda *a, **k: _FakeClient(TimeoutError("kvk traag")),
    )
    from app.integrations.kvk_service import get_rechtsvorm

    assert await get_rechtsvorm("68750110") is None


@pytest.mark.asyncio
async def test_get_rechtsvorm_404_geeft_none(monkeypatch):
    monkeypatch.setattr("app.integrations.kvk_service.settings.kvk_api_key", "testkey")
    monkeypatch.setattr(
        "app.integrations.kvk_service.httpx.AsyncClient",
        lambda *a, **k: _FakeClient(_FakeResponse(404)),
    )
    from app.integrations.kvk_service import get_rechtsvorm

    assert await get_rechtsvorm("68750110") is None


# ── Auto-vullen bij aanmaak ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_contact_vult_legal_form_uit_kvk(
    db: AsyncSession, test_tenant: Tenant, monkeypatch
):
    async def _fake_rechtsvorm(kvk_number):
        return "Eenmanszaak"

    monkeypatch.setattr(
        "app.integrations.kvk_service.get_rechtsvorm", _fake_rechtsvorm
    )

    contact = await relations_service.create_contact(
        db,
        test_tenant.id,
        ContactCreate(contact_type="company", name="Test VOF", kvk_number="68750110"),
    )
    assert contact.legal_form == "Eenmanszaak"
    assert contact.legal_form_source == "kvk"
    assert contact.legal_form_checked_at is not None


@pytest.mark.asyncio
async def test_create_contact_kvk_storing_breekt_niet(
    db: AsyncSession, test_tenant: Tenant, monkeypatch
):
    """KvK onbereikbaar → relatie wordt gewoon aangemaakt, rechtsvorm blijft leeg."""

    async def _fake_none(kvk_number):
        return None

    monkeypatch.setattr("app.integrations.kvk_service.get_rechtsvorm", _fake_none)

    contact = await relations_service.create_contact(
        db,
        test_tenant.id,
        ContactCreate(contact_type="company", name="Onbekend BV", kvk_number="68750110"),
    )
    assert contact.legal_form is None
    assert contact.legal_form_source is None


@pytest.mark.asyncio
async def test_create_contact_handmatige_rechtsvorm_blijft_handmatig(
    db: AsyncSession, test_tenant: Tenant, monkeypatch
):
    """Handmatig ingevulde rechtsvorm → herkomst 'handmatig', KvK niet geraadpleegd."""

    async def _boom(kvk_number):
        raise AssertionError("KvK mag niet bevraagd worden als rechtsvorm al ingevuld is")

    monkeypatch.setattr("app.integrations.kvk_service.get_rechtsvorm", _boom)

    contact = await relations_service.create_contact(
        db,
        test_tenant.id,
        ContactCreate(
            contact_type="company",
            name="Handmatig BV",
            kvk_number="68750110",
            legal_form="Besloten Vennootschap",
        ),
    )
    assert contact.legal_form == "Besloten Vennootschap"
    assert contact.legal_form_source == "handmatig"


# ── Update-flow ───────────────────────────────────────────────────────────────


async def _company_with_kvk(db, tenant_id, monkeypatch, legal_form=None):
    """Maak een bedrijf met KvK-nummer; auto-vullen uitgeschakeld tenzij gevraagd."""

    async def _none(kvk_number):
        return legal_form

    monkeypatch.setattr("app.integrations.kvk_service.get_rechtsvorm", _none)
    return await relations_service.create_contact(
        db,
        tenant_id,
        ContactCreate(contact_type="company", name="Bedrijf", kvk_number="68750110"),
    )


@pytest.mark.asyncio
async def test_update_leegmaken_blijft_leeg(
    db: AsyncSession, test_tenant: Tenant, monkeypatch
):
    """Rechtsvorm leegmaken → blijft leeg, KvK wordt NIET opnieuw bevraagd."""
    from app.relations.schemas import ContactUpdate

    contact = await _company_with_kvk(
        db, test_tenant.id, monkeypatch, legal_form="Eenmanszaak"
    )
    assert contact.legal_form == "Eenmanszaak"

    async def _boom(kvk_number):
        raise AssertionError("KvK mag niet opnieuw bevraagd worden bij leegmaken")

    monkeypatch.setattr("app.integrations.kvk_service.get_rechtsvorm", _boom)
    updated = await relations_service.update_contact(
        db, test_tenant.id, contact.id, ContactUpdate(legal_form="")
    )
    assert updated.legal_form in (None, "")
    assert updated.legal_form_source is None


@pytest.mark.asyncio
async def test_update_kvk_toegevoegd_vult_alsnog(
    db: AsyncSession, test_tenant: Tenant, monkeypatch
):
    """KvK-nummer later toegevoegd terwijl rechtsvorm leeg → alsnog ophalen."""
    from app.relations.schemas import ContactUpdate

    async def _none(kvk_number):
        return None

    monkeypatch.setattr("app.integrations.kvk_service.get_rechtsvorm", _none)
    contact = await relations_service.create_contact(
        db, test_tenant.id, ContactCreate(contact_type="company", name="Nog Geen KvK")
    )
    assert contact.legal_form is None

    async def _fill(kvk_number):
        return "Besloten Vennootschap"

    monkeypatch.setattr("app.integrations.kvk_service.get_rechtsvorm", _fill)
    updated = await relations_service.update_contact(
        db, test_tenant.id, contact.id, ContactUpdate(kvk_number="68750110")
    )
    assert updated.legal_form == "Besloten Vennootschap"
    assert updated.legal_form_source == "kvk"


@pytest.mark.asyncio
async def test_update_ongewijzigde_rechtsvorm_flipt_herkomst_niet(
    db: AsyncSession, test_tenant: Tenant, monkeypatch
):
    """UI stuurt legal_form bij elke bewerking mee; ongewijzigd → herkomst blijft 'kvk'."""
    from app.relations.schemas import ContactUpdate

    contact = await _company_with_kvk(
        db, test_tenant.id, monkeypatch, legal_form="Eenmanszaak"
    )
    contact.legal_form_source = "kvk"
    await db.flush()

    async def _boom(kvk_number):
        raise AssertionError("KvK niet bevragen bij ongewijzigde rechtsvorm")

    monkeypatch.setattr("app.integrations.kvk_service.get_rechtsvorm", _boom)
    updated = await relations_service.update_contact(
        db,
        test_tenant.id,
        contact.id,
        ContactUpdate(legal_form="Eenmanszaak", phone="0201234567"),
    )
    assert updated.legal_form == "Eenmanszaak"
    assert updated.legal_form_source == "kvk"
