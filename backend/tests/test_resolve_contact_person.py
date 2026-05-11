"""Tests voor _resolve_contact_person helper in automation_service.

Bij bedrijf-debiteur moet contactpersoon-naam via ContactLink async query
opgehaald worden (lazy loading werkt niet in async context). Bij persoon
gewoon eigen achternaam.
"""

import uuid
from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant
from app.incasso.automation_service import (
    _capitalize_name,
    _resolve_contact_person,
)
from app.relations.models import Contact, ContactLink


def test_capitalize_name_lowercase_becomes_proper():
    assert _capitalize_name("peterson") == "Peterson"


def test_capitalize_name_mixed_unchanged():
    """Naam met al een hoofdletter ergens → onveranderd."""
    assert _capitalize_name("Peterson") == "Peterson"
    assert _capitalize_name("de Vries") == "de Vries"  # V is upper, dus unchanged


def test_capitalize_name_empty_returns_empty():
    assert _capitalize_name("") == ""


@pytest.mark.asyncio
async def test_resolve_empty_when_contact_is_none(
    db: AsyncSession, test_tenant: Tenant
):
    result = await _resolve_contact_person(db, test_tenant.id, None)
    assert result == ""


@pytest.mark.asyncio
async def test_resolve_persoon_returns_last_name(
    db: AsyncSession, test_tenant: Tenant
):
    persoon = Contact(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        contact_type="person",
        name="Jan de Vries",
        first_name="Jan",
        last_name="de Vries",
    )
    db.add(persoon)
    await db.commit()
    result = await _resolve_contact_person(db, test_tenant.id, persoon)
    assert result == "de Vries"


@pytest.mark.asyncio
async def test_resolve_bedrijf_zonder_link_returns_empty(
    db: AsyncSession, test_tenant: Tenant
):
    bedrijf = Contact(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        contact_type="company",
        name="Acme BV",
    )
    db.add(bedrijf)
    await db.commit()
    result = await _resolve_contact_person(db, test_tenant.id, bedrijf)
    assert result == ""


@pytest.mark.asyncio
async def test_resolve_bedrijf_met_link_returns_persoon_naam(
    db: AsyncSession, test_tenant: Tenant
):
    bedrijf = Contact(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        contact_type="company",
        name="Acme BV",
    )
    persoon = Contact(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        contact_type="person",
        name="Piet pietersen",
        first_name="Piet",
        last_name="pietersen",
    )
    db.add_all([bedrijf, persoon])
    await db.flush()
    link = ContactLink(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        person_id=persoon.id,
        company_id=bedrijf.id,
        role_at_company="Directeur",
        is_active=True,
    )
    db.add(link)
    await db.commit()
    result = await _resolve_contact_person(db, test_tenant.id, bedrijf)
    assert result == "Pietersen"


@pytest.mark.asyncio
async def test_resolve_bedrijf_inactive_link_skipped(
    db: AsyncSession, test_tenant: Tenant
):
    bedrijf = Contact(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        contact_type="company",
        name="Acme BV",
    )
    persoon = Contact(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        contact_type="person",
        name="Inactief Persoon",
        last_name="InactiefPersoon",
    )
    db.add_all([bedrijf, persoon])
    await db.flush()
    link = ContactLink(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        person_id=persoon.id,
        company_id=bedrijf.id,
        is_active=False,
    )
    db.add(link)
    await db.commit()
    result = await _resolve_contact_person(db, test_tenant.id, bedrijf)
    assert result == ""


@pytest.mark.asyncio
async def test_resolve_bedrijf_voorkeur_rol_contactpersoon(
    db: AsyncSession, test_tenant: Tenant
):
    """Bij meerdere links: voorkeur voor rol 'Contactpersoon'."""
    bedrijf = Contact(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        contact_type="company",
        name="Acme BV",
    )
    directeur = Contact(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        contact_type="person",
        name="Dir Direkteur",
        last_name="Direkteur",
    )
    cp = Contact(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        contact_type="person",
        name="CP Contactpersoon",
        last_name="Contactnaam",
    )
    db.add_all([bedrijf, directeur, cp])
    await db.flush()
    db.add_all([
        ContactLink(
            id=uuid.uuid4(), tenant_id=test_tenant.id,
            person_id=directeur.id, company_id=bedrijf.id,
            role_at_company="Directeur", is_active=True,
        ),
        ContactLink(
            id=uuid.uuid4(), tenant_id=test_tenant.id,
            person_id=cp.id, company_id=bedrijf.id,
            role_at_company="Contactpersoon", is_active=True,
        ),
    ])
    await db.commit()
    result = await _resolve_contact_person(db, test_tenant.id, bedrijf)
    assert result == "Contactnaam"
