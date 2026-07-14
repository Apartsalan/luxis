"""KvK-koppeling — rechtsvorm ophalen uit het Basisprofiel (S211).

Wordt ALLEEN aangeroepen bij het aanmaken/bijwerken van een relatie en in het
backfill-script — NOOIT in het verzendpad. Faalt altijd zacht: bij een storing,
timeout of onbekend nummer komt er `None` terug (+ een logregel), zodat een
KvK-probleem nooit een relatie-opslag of een verzending kan blokkeren.
"""

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# KvK-nummers zijn 8 cijfers. Alles daarbuiten bevragen we niet.
_KVK_TIMEOUT_SECONDS = 8.0


def _clean_kvk(kvk_number: str | None) -> str | None:
    """Normaliseer naar 8 cijfers, of None als het geen geldig nummer is."""
    if not kvk_number:
        return None
    digits = "".join(ch for ch in kvk_number if ch.isdigit())
    return digits if len(digits) == 8 else None


async def get_rechtsvorm(kvk_number: str | None) -> str | None:
    """Haal de rechtsvorm op uit het KvK-basisprofiel.

    Retourneert de uitgebreide rechtsvorm (bv. "Besloten Vennootschap",
    "Eenmanszaak") of None bij een ongeldig nummer, storing of onbekend bedrijf.
    Prefereert `uitgebreideRechtsvorm` (fijnmaziger); valt terug op `rechtsvorm`.
    """
    kvk = _clean_kvk(kvk_number)
    if kvk is None:
        return None

    url = f"{settings.kvk_api_base.rstrip('/')}/v1/basisprofielen/{kvk}"
    headers = {"apikey": settings.kvk_api_key}

    try:
        async with httpx.AsyncClient(timeout=_KVK_TIMEOUT_SECONDS) as client:
            resp = await client.get(url, headers=headers)
        if resp.status_code == 404:
            logger.info("KvK %s: geen basisprofiel gevonden", kvk)
            return None
        resp.raise_for_status()
        data = resp.json()
    except Exception:  # noqa: BLE001 — elke fout = zacht falen (None), nooit blokkeren
        logger.warning("KvK-bevraging mislukt voor %s", kvk, exc_info=True)
        return None

    eigenaar = (data.get("_embedded") or {}).get("eigenaar") or {}
    rechtsvorm = eigenaar.get("uitgebreideRechtsvorm") or eigenaar.get("rechtsvorm")
    if not rechtsvorm:
        logger.info("KvK %s: profiel zonder rechtsvorm-veld", kvk)
        return None
    return str(rechtsvorm).strip()
