"""Seed 28 Basenet products into the products table.

Idempotent: skips products that already exist by code.
"""

import logging
import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.products.models import Product
from app.products.service import get_product_by_code

logger = logging.getLogger(__name__)

D21 = Decimal("21.00")
D0 = Decimal("0.00")

# fmt: off
# All 30 products from Basenet Excel export (8 april 2026)
# (code, name, price, gl_code, gl_name, vat_type, vat_pct, sort)
BASENET_PRODUCTS = [
    ("100000", "Honorarium",
     None, "8000", "Omzet honorarium", "21", D21, 10),
    ("100001", "Kantoorkosten",
     None, "8050", "Omzet kantoorkosten", "21", D21, 20),
    ("100004", "Reiskosten",
     None, "8060", "Omzet reiskosten", "21", D21, 30),
    ("100012", "Aanvullende kosten Incasso",
     None, "8300", "Opbrengst incassokosten", "21", D21, 100),
    ("100013", "Verrekening incassodossiers",
     None, "2010", "Depotgelden verrekend", "0", D0, 200),
    ("100014", "Onbelaste verschotten",
     None, "8020", "Onbelaste verschotten", "0", D0, 40),
    ("100015", "Belaste verschotten",
     None, "8000", "Omzet honorarium", "21", D21, 50),
    ("100017", "Honorarium buitenland binnen EU",
     None, "8100", "Omzet buitenland binnen EU", "eu", D0, 60),
    ("100018", "Kantoorkosten buitenland binnen EU",
     None, "8150", "Kantoorkosten buitenland EU", "eu", D0, 70),
    ("100019", "Reiskosten buitenland binnen EU",
     None, "8160", "Reiskosten buitenland EU", "eu", D0, 80),
    ("100021", "Honorarium buitenland buiten EU",
     None, "8120", "Omzet buitenland buiten EU", "non_eu", D0, 90),
    ("100022", "Kantoorkosten buitenland buiten EU",
     None, "8130", "Kantoorkosten buiten EU", "non_eu", D0, 91),
    ("100023", "Reiskosten buitenland buiten EU",
     None, "8140", "Reiskosten buiten EU", "non_eu", D0, 92),
    ("100025", "Verschotten buitenland binnen EU",
     None, "8100", "Omzet buitenland binnen EU", "eu", D0, 93),
    ("100026", "Verschotten buitenland buiten EU",
     None, "8120", "Omzet buitenland buiten EU", "non_eu", D0, 94),
    ("100027", "Incassokosten",
     None, "8300", "Opbrengst incassokosten", "21", D21, 110),
    ("100028", "Provisie Incasso",
     None, "8300", "Opbrengst incassokosten", "21", D21, 120),
    ("100029", "Dossierkosten Incasso",
     None, "8300", "Opbrengst incassokosten", "21", D21, 130),
    ("100030", "Annuleringskosten",
     None, "8300", "Opbrengst incassokosten", "21", D21, 140),
    ("100031", "Extra dossierkosten Incasso",
     None, "8300", "Opbrengst incassokosten", "21", D21, 150),
    ("100032", "Overige opbrengsten Incasso",
     None, "8300", "Opbrengst incassokosten", "21", D21, 160),
    ("100033", "Proceskosten Incasso",
     None, "8360", "Opbrengst proceskosten", "21", D21, 170),
    ("100034", "Rente opbrengst",
     None, "8300", "Opbrengst incassokosten", "21", D21, 180),
    ("100037", "Verrekend naar klant",
     None, "2010", "Depotgelden verrekend", "0", D0, 210),
    ("100038", "Ontvangen derdengelden",
     None, "2020", "Nog te ontvangen derdengeldenrek", "0", D0, 220),
    ("100039", "Griffierecht handel",
     Decimal("3083.00"), "8020", "Onbelaste verschotten", "0", D0, 41),
    ("100040", "KvK uittreksels",
     Decimal("18.00"), "8020", "Onbelaste verschotten", "0", D0, 42),
    ("100041", "Waarneming zitting",
     Decimal("125.00"), "8000", "Omzet honorarium", "21", D21, 35),
    ("100042", "Voorschot",
     None, "1950", "Voorschotten", "21", D21, 230),
    ("100043", "Griffierecht verzoek",
     Decimal("735.00"), "8020", "Onbelaste verschotten", "0", D0, 43),
]
# fmt: on


async def seed_products(
    db: AsyncSession, tenant_id: uuid.UUID
) -> int:
    """Seed Basenet products. Returns count of new products."""
    created = 0
    for row in BASENET_PRODUCTS:
        code, name, price, gl_code, gl_name, vat_type, vat_pct, sort = row
        existing = await get_product_by_code(db, tenant_id, code)
        if existing:
            continue

        product = Product(
            tenant_id=tenant_id,
            code=code,
            name=name,
            default_price=price,
            gl_account_code=gl_code,
            gl_account_name=gl_name,
            vat_type=vat_type,
            vat_percentage=vat_pct,
            sort_order=sort,
        )
        db.add(product)
        created += 1

    await db.flush()
    total = len(BASENET_PRODUCTS)
    logger.info(f"Products seeded: {created} new, {total - created} existing")
    return created
