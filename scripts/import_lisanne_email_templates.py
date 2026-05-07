"""Importeer Lisanne's .eml sjablonen naar IncassoPipelineStep.email_*_template velden.

Bron: `templates incasso/` (repo root) — 5 .eml bestanden.
Doel: bij elke matching pipeline-stap de subject + body opslaan zodat de email-engine
en AI deze kan gebruiken als basis-template.

Mapping (zie docs/lisanne-incasso-workflow.md):
    SOMMATIE TOT BETALING _  _.eml                              → Eerste sommatie
    TWEEDE SOMMATIE (GEEN VERWEER).eml                          → Tweede sommatie, Derde sommatie
    SOMMATIE AANKONDIGING FAILLISSEMENT.eml                     → Sommatie laatste mogelijkheid
    VERZOEKSCHRIFT FAILLISSEMENT (LAATSTE MOGELIJKHEID) _  _.eml → Verzoekschrift faillissement
    TWEEDE SOMMATIE INDIEN WEL VERWEER.eml                      → Verweer beantwoorden

Run: docker compose exec backend python scripts/import_lisanne_email_templates.py
"""

import asyncio
import email
import re
import sys
from email import policy
from pathlib import Path

from sqlalchemy import select, text

# Importeer main om alle SQLAlchemy modellen te registreren (FastAPI app laad-volgorde)
import app.main  # noqa: F401
from app.auth.models import Tenant
from app.database import async_session
from app.incasso.models import IncassoPipelineStep

# Container mount: /app/templates/lisanne (host: templates/lisanne/)
TEMPLATE_DIR = Path("/app/templates/lisanne")
if not TEMPLATE_DIR.exists():
    # fallback voor lokale runs (host pad)
    TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates" / "lisanne"

# Mapping: bestandsnaam → lijst van stap-namen die deze sjabloon krijgen
EMAIL_MAPPING: dict[str, list[str]] = {
    "SOMMATIE TOT BETALING _  _.eml": ["Eerste sommatie"],
    "TWEEDE SOMMATIE (GEEN VERWEER).eml": ["Tweede sommatie", "Derde sommatie"],
    "SOMMATIE AANKONDIGING FAILLISSEMENT.eml": ["Sommatie laatste mogelijkheid"],
    "VERZOEKSCHRIFT FAILLISSEMENT (LAATSTE MOGELIJKHEID) _  _.eml": ["Verzoekschrift faillissement"],
    "TWEEDE SOMMATIE INDIEN WEL VERWEER.eml": ["Verweer beantwoorden"],
}


_LOGO_B64_CANDIDATES = [
    Path("/app/templates/lisanne/_kesting_logo.b64"),  # container mount
    Path(__file__).resolve().parents[1] / "templates" / "lisanne" / "_kesting_logo.b64",  # host
]


def _load_logo_data_url() -> str | None:
    """Return data:image/png;base64,XXX or None if logo file missing."""
    for path in _LOGO_B64_CANDIDATES:
        if path.exists():
            b64 = path.read_text().strip()
            return f"data:image/png;base64,{b64}"
    return None


def _decode_part(part) -> str:
    try:
        return part.get_content()
    except (LookupError, UnicodeDecodeError):
        raw = part.get_payload(decode=True)
        if isinstance(raw, bytes):
            for enc in ("utf-8", "cp1252", "iso-8859-1"):
                try:
                    return raw.decode(enc)
                except UnicodeDecodeError:
                    continue
            return raw.decode("utf-8", errors="replace")
        return str(raw)


_BASENET_LOGO_RE = re.compile(
    r'(?P<full><img[^>]*src=")https?://static\.basenet\.nl/cms/[^"]*("[^>]*>)',
    re.IGNORECASE,
)


def _swap_basenet_logo(html: str, data_url: str | None) -> str:
    """Vervang BaseNet logo-URLs door inline data-URL of verwijder ze."""
    if not data_url:
        return _BASENET_LOGO_RE.sub("", html)
    return _BASENET_LOGO_RE.sub(rf'\g<full>{data_url}\2', html)


def parse_eml(path: Path) -> tuple[str, str, str]:
    """Parse .eml file, return (subject, body_text, body_html). Probeert utf-8, valt terug op cp1252."""
    with open(path, "rb") as fp:
        msg = email.message_from_binary_file(fp, policy=policy.default)

    subject = msg["subject"] or ""

    plain_part = msg.get_body(preferencelist=("plain",))
    html_part = msg.get_body(preferencelist=("html",))

    body = _decode_part(plain_part) if plain_part else ""
    body_html = _decode_part(html_part) if html_part else ""

    # Fix common cp1252 mojibake → utf-8 chars
    body = body.replace("�", "ë")
    body_html = body_html.replace("�", "ë")

    # Swap externe BaseNet logo door embedded data-URL
    if body_html:
        body_html = _swap_basenet_logo(body_html, _load_logo_data_url())

    return subject, body, body_html


async def main() -> int:
    if not TEMPLATE_DIR.exists():
        print(f"FOUT: template-folder niet gevonden: {TEMPLATE_DIR}")
        return 1

    parsed: dict[str, tuple[str, str, str]] = {}
    for filename in EMAIL_MAPPING:
        path = TEMPLATE_DIR / filename
        if not path.exists():
            print(f"WAARSCHUWING: bestand ontbreekt: {filename}")
            continue
        subject, body, body_html = parse_eml(path)
        parsed[filename] = (subject, body, body_html)
        print(
            f"  geparsed {filename}: subject={subject!r}, "
            f"plain={len(body)} chars, html={len(body_html)} chars"
        )

    if not parsed:
        print("FOUT: geen sjablonen geparsed")
        return 1

    async with async_session() as session:
        tenants = (await session.execute(
            select(Tenant).where(Tenant.is_active.is_(True))
        )).scalars().all()

        for tenant in tenants:
            await session.execute(text(f"SET app.current_tenant = '{tenant.id}'"))
            steps = (await session.execute(
                select(IncassoPipelineStep).where(
                    IncassoPipelineStep.tenant_id == tenant.id,
                    IncassoPipelineStep.is_active.is_(True),
                )
            )).scalars().all()

            updated = 0
            for filename, step_names in EMAIL_MAPPING.items():
                if filename not in parsed:
                    continue
                subject, body, body_html = parsed[filename]
                for step in steps:
                    if step.name in step_names:
                        step.email_subject_template = subject
                        step.email_body_template = body
                        step.email_body_template_html = body_html or None
                        updated += 1

            await session.commit()
            print(f"{tenant.name}: {updated} stappen voorzien van sjabloon")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
