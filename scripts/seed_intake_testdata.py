"""Seed script — populates the database with diverse IntakeRequest test data.

Creates 18 IntakeRequest records with varied statuses, confidence scores,
and scenarios for testing the intake review UI and pipeline.

Usage:
    python scripts/seed_intake_testdata.py              # Seed 18 records
    python scripts/seed_intake_testdata.py --dry-run     # Print without inserting
    python scripts/seed_intake_testdata.py --cleanup     # Remove all [TEST-SEED] data
"""

import argparse
import asyncio
import json
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import text

from app.database import async_session

# =============================================================================
# Constants — match seed_interest_rates.py
# =============================================================================
TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")

# Fixed namespace for deterministic UUIDs (idempotent re-runs)
NS = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")

# Deterministic UUID generator
def _uid(name: str) -> str:
    return str(uuid.uuid5(NS, name))


# Fixed email account for test emails
EMAIL_ACCOUNT_ID = _uid("test-email-account")

MARKER = "[TEST-SEED]"

# =============================================================================
# Test data definitions
# =============================================================================
TODAY = date.today()


def _days_ago(n: int) -> date:
    return TODAY - timedelta(days=n)


def _dt_ago(n: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=n)


INTAKE_RECORDS = [
    # --- PENDING_REVIEW: diverse scenarios ---
    {
        "key": "intake-01",
        "status": "pending_review",
        "confidence": "0.95",
        "debtor_type": "company",
        "debtor_name": "Van Dijk Installatietechniek B.V.",
        "debtor_email": "info@vandijkinstallatie.nl",
        "debtor_kvk": "67234891",
        "debtor_address": "Industrieweg 42",
        "debtor_city": "Rotterdam",
        "debtor_postcode": "3045 AE",
        "invoice_number": "F-2026-0147",
        "invoice_date": _days_ago(45),
        "due_date": _days_ago(15),
        "principal_amount": "15000.00",
        "description": "Onbetaalde factuur voor renovatie badkamer kantoorpand",
        "has_pdf_data": True,
        "ai_model": "claude-sonnet-4-20250514",
        "email_subject": "Incasso-opdracht Van Dijk Installatietechniek",
        "email_from": "jan@opdrachtgever-bouw.nl",
        "email_body": "Beste Lisanne, bijgaand de factuur van Van Dijk. Al 2x aangemaand, geen reactie.",
        "email_days_ago": 2,
    },
    {
        "key": "intake-02",
        "status": "pending_review",
        "confidence": "0.88",
        "debtor_type": "company",
        "debtor_name": "TechVision B.V.",
        "debtor_email": "administratie@techvision.nl",
        "debtor_kvk": "71456823",
        "debtor_address": "Singel 200",
        "debtor_city": "Amsterdam",
        "debtor_postcode": "1012 LJ",
        "invoice_number": "2026-003-TV",
        "invoice_date": _days_ago(60),
        "due_date": _days_ago(30),
        "principal_amount": "3200.00",
        "description": "Consultancy ICT-advies Q4 2025",
        "has_pdf_data": True,
        "ai_model": "claude-sonnet-4-20250514",
        "email_subject": "Vordering TechVision - factuurnr 2026-003-TV",
        "email_from": "petra@ict-adviesbureau.nl",
        "email_body": "Hierbij de factuur die TechVision weigert te betalen. Bedrag EUR 3.200.",
        "email_days_ago": 3,
    },
    {
        "key": "intake-03",
        "status": "pending_review",
        "confidence": "0.72",
        "debtor_type": "person",
        "debtor_name": "K. Janssen",
        "debtor_email": "k.janssen82@gmail.com",
        "debtor_kvk": None,
        "debtor_address": "Dorpsstraat 7",
        "debtor_city": "Haarlem",
        "debtor_postcode": "2011 AB",
        "invoice_number": "RK-2025-089",
        "invoice_date": _days_ago(90),
        "due_date": _days_ago(60),
        "principal_amount": "450.00",
        "description": "Onbetaalde rekening tandheelkunde",
        "has_pdf_data": True,
        "ai_model": "claude-sonnet-4-20250514",
        "email_subject": "Incasso particulier - Janssen",
        "email_from": "info@tandartspraktijk-haarlem.nl",
        "email_body": "Patient K. Janssen betaalt rekening van EUR 450 niet ondanks herhaalde herinneringen.",
        "email_days_ago": 1,
    },
    {
        "key": "intake-04",
        "status": "pending_review",
        "confidence": "0.55",
        "debtor_type": "company",
        "debtor_name": "Bakkerij De Molen",
        "debtor_email": None,
        "debtor_kvk": None,
        "debtor_address": None,
        "debtor_city": "Utrecht",
        "debtor_postcode": None,
        "invoice_number": "F2025-412",
        "invoice_date": _days_ago(120),
        "due_date": _days_ago(90),
        "principal_amount": "1875.50",
        "description": "Levering bloem en grondstoffen",
        "has_pdf_data": False,
        "ai_model": "claude-sonnet-4-20250514",
        "email_subject": "Openstaande factuur bakkerij",
        "email_from": "verkoop@meelgroothandel.nl",
        "email_body": "Een bakkerij in Utrecht, De Molen, betaalt factuur F2025-412 niet. Helaas weet ik het adres niet.",
        "email_days_ago": 5,
    },
    {
        "key": "intake-05",
        "status": "pending_review",
        "confidence": "0.42",
        "debtor_type": "person",
        "debtor_name": "Pietersen",
        "debtor_email": None,
        "debtor_kvk": None,
        "debtor_address": None,
        "debtor_city": None,
        "debtor_postcode": None,
        "invoice_number": None,
        "invoice_date": None,
        "due_date": None,
        "principal_amount": "320.00",
        "description": None,
        "has_pdf_data": False,
        "ai_model": "claude-sonnet-4-20250514",
        "email_subject": "Help nodig met wanbetaler",
        "email_from": "info@schoonmaakbedrijf-clean.nl",
        "email_body": "Ene Pietersen betaalt niet, het gaat om 320 euro. Kan u helpen?",
        "email_days_ago": 1,
    },
    {
        "key": "intake-06",
        "status": "pending_review",
        "confidence": "0.91",
        "debtor_type": "company",
        "debtor_name": "Groothandel Nederland B.V.",
        "debtor_email": "debiteuren@groothandelnl.nl",
        "debtor_kvk": "82345671",
        "debtor_address": "Havenweg 15-17",
        "debtor_city": "Breda",
        "debtor_postcode": "4825 BA",
        "invoice_number": "GHN-2026-0023",
        "invoice_date": _days_ago(35),
        "due_date": _days_ago(5),
        "principal_amount": "25000.00",
        "description": "Levering kantoormeubelen incl. 21% BTW (€20.661,16 excl.)",
        "has_pdf_data": True,
        "ai_model": "claude-sonnet-4-20250514",
        "email_subject": "Grote vordering Groothandel Nederland - EUR 25.000",
        "email_from": "cfo@kantoormeubelen-direct.nl",
        "email_body": "Factuur GHN-2026-0023 ad EUR 25.000 incl. BTW staat al 5 weken open.",
        "email_days_ago": 4,
    },
    # --- APPROVED: diverse scenarios ---
    {
        "key": "intake-07",
        "status": "approved",
        "confidence": "0.96",
        "debtor_type": "company",
        "debtor_name": "Bouwbedrijf Horizon B.V.",
        "debtor_email": "admin@bouwbedrijfhorizon.nl",
        "debtor_kvk": "56789012",
        "debtor_address": "Bouwlaan 88",
        "debtor_city": "Den Haag",
        "debtor_postcode": "2517 KL",
        "invoice_number": "BH-2025-199",
        "invoice_date": _days_ago(75),
        "due_date": _days_ago(45),
        "principal_amount": "8750.00",
        "description": "Architectuurdiensten verbouwing bedrijfspand",
        "has_pdf_data": True,
        "ai_model": "claude-sonnet-4-20250514",
        "review_note": "Dossier aangemaakt, 14-dagenbrief verzenden",
        "email_subject": "Nieuwe incasso Bouwbedrijf Horizon",
        "email_from": "info@architectenbureau-vdl.nl",
        "email_body": "Bouwbedrijf Horizon weigert onze factuur te betalen. Alle documenten bijgevoegd.",
        "email_days_ago": 10,
    },
    {
        "key": "intake-08",
        "status": "approved",
        "confidence": "0.85",
        "debtor_type": "person",
        "debtor_name": "M.A. de Vries",
        "debtor_email": "mdevries@hotmail.com",
        "debtor_kvk": None,
        "debtor_address": "Laan van Meerdervoort 150",
        "debtor_city": "Den Haag",
        "debtor_postcode": "2517 BD",
        "invoice_number": "FYS-2025-067",
        "invoice_date": _days_ago(100),
        "due_date": _days_ago(70),
        "principal_amount": "650.00",
        "description": "Fysiotherapie behandelingen sept-okt 2025",
        "has_pdf_data": True,
        "ai_model": "claude-sonnet-4-20250514",
        "review_note": "Particulier, 14-dagenbrief vereist (B2C)",
        "email_subject": "Wanbetaler fysiotherapie",
        "email_from": "administratie@fysio-denhaag.nl",
        "email_body": "Patient De Vries reageert niet meer op onze aanmaningen. Bedrag EUR 650.",
        "email_days_ago": 14,
    },
    {
        "key": "intake-09",
        "status": "approved",
        "confidence": "0.78",
        "debtor_type": "company",
        "debtor_name": "FlexStaf Uitzendbureau B.V.",
        "debtor_email": "finance@flexstaf.nl",
        "debtor_kvk": "34567890",
        "debtor_address": "Stationsplein 3",
        "debtor_city": "Eindhoven",
        "debtor_postcode": "5611 AB",
        "invoice_number": "FS-2026-011",
        "invoice_date": _days_ago(50),
        "due_date": _days_ago(20),
        "principal_amount": "4200.00",
        "description": "Detachering ICT-medewerker januari 2026",
        "has_pdf_data": True,
        "ai_model": "claude-sonnet-4-20250514",
        "review_note": "Data handmatig gecorrigeerd (adres was incompleet in extractie)",
        "email_subject": "Incasso FlexStaf - factuur FS-2026-011",
        "email_from": "hr@detacheringsbureau-pro.nl",
        "email_body": "FlexStaf betaalt de factuur voor de detachering niet. Bijgaand de factuur.",
        "email_days_ago": 8,
    },
    # --- REJECTED: diverse scenarios ---
    {
        "key": "intake-10",
        "status": "rejected",
        "confidence": "0.30",
        "debtor_type": "company",
        "debtor_name": None,
        "debtor_email": None,
        "debtor_kvk": None,
        "debtor_address": None,
        "debtor_city": None,
        "debtor_postcode": None,
        "invoice_number": None,
        "invoice_date": None,
        "due_date": None,
        "principal_amount": None,
        "description": None,
        "has_pdf_data": False,
        "ai_model": "claude-sonnet-4-20250514",
        "review_note": "Marketing email, geen factuur of vordering",
        "email_subject": "Nieuwe zakelijke kansen voor uw kantoor!",
        "email_from": "sales@marketingpartner.nl",
        "email_body": "Vergroot uw klantenbestand met onze lead generation service!",
        "email_days_ago": 6,
    },
    {
        "key": "intake-11",
        "status": "rejected",
        "confidence": "0.45",
        "debtor_type": "person",
        "debtor_name": "R. Bakker",
        "debtor_email": "r.bakker@ziggo.nl",
        "debtor_kvk": None,
        "debtor_address": "Kerkstraat 22",
        "debtor_city": "Leiden",
        "debtor_postcode": "2312 GH",
        "invoice_number": "INV-2025-445",
        "invoice_date": _days_ago(80),
        "due_date": _days_ago(50),
        "principal_amount": "890.00",
        "description": "Schilderwerkzaamheden woning",
        "has_pdf_data": True,
        "ai_model": "claude-sonnet-4-20250514",
        "review_note": "Dubbel dossier — al eerder aangemeld via ander kanaal",
        "email_subject": "Vordering R. Bakker - schilderwerk",
        "email_from": "info@schildersbedrijf-kleur.nl",
        "email_body": "Bakker betaalt niet voor het schilderwerk. Factuur bijgevoegd.",
        "email_days_ago": 7,
    },
    # --- PROCESSING: AI bezig ---
    {
        "key": "intake-12",
        "status": "processing",
        "confidence": None,
        "debtor_type": "company",
        "debtor_name": None,
        "debtor_email": None,
        "debtor_kvk": None,
        "debtor_address": None,
        "debtor_city": None,
        "debtor_postcode": None,
        "invoice_number": None,
        "invoice_date": None,
        "due_date": None,
        "principal_amount": None,
        "description": None,
        "has_pdf_data": False,
        "ai_model": "claude-sonnet-4-20250514",
        "email_subject": "Nieuwe vordering - Transport B.V.",
        "email_from": "logistiek@transportbedrijf-nl.nl",
        "email_body": "Bijgaand factuur en leveringsbewijs voor onze vordering op Transport B.V.",
        "email_days_ago": 0,
    },
    # --- DETECTED: net binnengekomen ---
    {
        "key": "intake-13",
        "status": "detected",
        "confidence": None,
        "debtor_type": "company",
        "debtor_name": None,
        "debtor_email": None,
        "debtor_kvk": None,
        "debtor_address": None,
        "debtor_city": None,
        "debtor_postcode": None,
        "invoice_number": None,
        "invoice_date": None,
        "due_date": None,
        "principal_amount": None,
        "description": None,
        "has_pdf_data": False,
        "ai_model": "",
        "email_subject": "Fwd: Onbetaalde factuur - dringend",
        "email_from": "directie@vastgoed-partners.nl",
        "email_body": "Doorgestuurd vanuit onze boekhouding. Graag uw hulp bij incasso.",
        "email_days_ago": 0,
    },
    # --- FAILED: extractie mislukt ---
    {
        "key": "intake-14",
        "status": "failed",
        "confidence": "0.15",
        "debtor_type": "company",
        "debtor_name": "???",
        "debtor_email": None,
        "debtor_kvk": None,
        "debtor_address": None,
        "debtor_city": None,
        "debtor_postcode": None,
        "invoice_number": None,
        "invoice_date": None,
        "due_date": None,
        "principal_amount": None,
        "description": None,
        "has_pdf_data": True,
        "ai_model": "claude-sonnet-4-20250514",
        "error_message": "PDF scan onleesbaar — resolutie te laag voor OCR",
        "email_subject": "Scan factuur bijgevoegd",
        "email_from": "secretariaat@advocaten-west.nl",
        "email_body": "Hierbij de gescande factuur. Het is een oude kopie maar hopelijk leesbaar.",
        "email_days_ago": 3,
    },
    {
        "key": "intake-15",
        "status": "failed",
        "confidence": None,
        "debtor_type": "company",
        "debtor_name": None,
        "debtor_email": None,
        "debtor_kvk": None,
        "debtor_address": None,
        "debtor_city": None,
        "debtor_postcode": None,
        "invoice_number": None,
        "invoice_date": None,
        "due_date": None,
        "principal_amount": None,
        "description": None,
        "has_pdf_data": False,
        "ai_model": "claude-sonnet-4-20250514",
        "error_message": "Geen PDF-bijlage gevonden in email",
        "email_subject": "Incasso aanvraag",
        "email_from": "boekhouding@retail-shop.nl",
        "email_body": "Kunt u deze vordering voor ons incasseren? Ik stuur de factuur later.",
        "email_days_ago": 2,
    },
    # --- PENDING_REVIEW: special scenarios ---
    {
        "key": "intake-16",
        "status": "pending_review",
        "confidence": "0.82",
        "debtor_type": "company",
        "debtor_name": "Van der Berg Transport B.V.",
        "debtor_email": "vdberg@transport-vdb.nl",
        "debtor_kvk": "45678901",
        "debtor_address": "Transportweg 5",
        "debtor_city": "Venlo",
        "debtor_postcode": "5928 NX",
        "invoice_number": "LOG-2026-001, LOG-2026-002",
        "invoice_date": _days_ago(40),
        "due_date": _days_ago(10),
        "principal_amount": "7650.00",
        "description": "2 facturen: LOG-2026-001 (€4.200) + LOG-2026-002 (€3.450) — transportdiensten",
        "has_pdf_data": True,
        "ai_model": "claude-sonnet-4-20250514",
        "email_subject": "Twee openstaande facturen Van der Berg Transport",
        "email_from": "operations@logistiek-centrum.nl",
        "email_body": "Van der Berg Transport betaalt 2 facturen niet. Totaal EUR 7.650. PDFs bijgevoegd.",
        "email_days_ago": 3,
    },
    {
        "key": "intake-17",
        "status": "pending_review",
        "confidence": "0.68",
        "debtor_type": "company",
        "debtor_name": "Müller GmbH",
        "debtor_email": "buchhaltung@mueller-gmbh.de",
        "debtor_kvk": None,
        "debtor_address": "Industriestraße 45",
        "debtor_city": "Düsseldorf",
        "debtor_postcode": "40210",
        "invoice_number": "EU-2025-088",
        "invoice_date": _days_ago(70),
        "due_date": _days_ago(40),
        "principal_amount": "12500.00",
        "description": "Export machinery parts — international B2B",
        "has_pdf_data": True,
        "ai_model": "claude-sonnet-4-20250514",
        "email_subject": "Buitenlandse debiteur - Müller GmbH Düsseldorf",
        "email_from": "export@machinefabriek-nl.nl",
        "email_body": "Duitse klant Müller GmbH betaalt factuur EUR 12.500 niet. Handelsrente van toepassing.",
        "email_days_ago": 5,
    },
    {
        "key": "intake-18",
        "status": "pending_review",
        "confidence": "0.90",
        "debtor_type": "company",
        "debtor_name": "Sigma Solutions B.V.",
        "debtor_email": "finance@sigmasolutions.nl",
        "debtor_kvk": "78901234",
        "debtor_address": "Zuidas 100",
        "debtor_city": "Amsterdam",
        "debtor_postcode": "1082 MD",
        "invoice_number": "SS-2026-045",
        "invoice_date": _days_ago(30),
        "due_date": _days_ago(0),
        "principal_amount": "5500.00",
        "description": "SaaS licentie Q1 2026",
        "has_pdf_data": True,
        "ai_model": "claude-sonnet-4-20250514",
        "email_subject": "Vordering Sigma Solutions - bekende klant",
        "email_from": "jan@opdrachtgever-bouw.nl",
        "email_body": "Sigma Solutions betaalt onze SaaS licentie niet. Factuur bijgevoegd. U kent ons al.",
        "email_days_ago": 1,
    },
]


# =============================================================================
# Seed functions
# =============================================================================

async def seed(dry_run: bool = False) -> None:
    """Insert test email account, synced emails, and intake requests."""
    if dry_run:
        print("=" * 60)
        print("DRY RUN — geen data wordt geschreven")
        print("=" * 60)
        print()
        for i, rec in enumerate(INTAKE_RECORDS, 1):
            amt = rec.get("principal_amount") or "—"
            conf = rec.get("confidence") or "—"
            print(
                f"  {i:2d}. [{rec['status']:<15s}] "
                f"conf={conf!s:<5s} "
                f"type={rec['debtor_type']:<7s} "
                f"bedrag=€{amt:<12s} "
                f"{rec.get('debtor_name') or '(onbekend)'}"
            )
        print()
        print(f"Totaal: {len(INTAKE_RECORDS)} records zouden worden aangemaakt")
        return

    async with async_session() as db:
        # 1. Create test email account (idempotent)
        await db.execute(
            text("""
                INSERT INTO email_accounts
                    (id, tenant_id, user_id, provider, email_address,
                     access_token_enc, refresh_token_enc, connected_at,
                     created_at, updated_at)
                VALUES
                    (:id, :tenant_id, :user_id, :provider, :email,
                     :access_token, :refresh_token, now(),
                     now(), now())
                ON CONFLICT (id) DO NOTHING
            """),
            {
                "id": EMAIL_ACCOUNT_ID,
                "tenant_id": str(TENANT_ID),
                "user_id": str(USER_ID),
                "provider": "outlook",
                "email": "test-intake@kestinglegal.nl",
                "access_token": b"dummy_test_seed_token",
                "refresh_token": b"dummy_test_seed_refresh",
            },
        )

        # 2. Insert synced emails + intake requests
        email_count = 0
        intake_count = 0

        for rec in INTAKE_RECORDS:
            email_id = _uid(f"email-{rec['key']}")
            intake_id = _uid(f"intake-{rec['key']}")

            # SyncedEmail
            await db.execute(
                text("""
                    INSERT INTO synced_emails
                        (id, tenant_id, email_account_id, provider_message_id,
                         subject, from_email, from_name, to_emails, cc_emails,
                         body_text, body_html, direction, is_read, has_attachments,
                         email_date, synced_at, created_at, updated_at)
                    VALUES
                        (:id, :tenant_id, :email_account_id, :provider_message_id,
                         :subject, :from_email, :from_name, :to_emails, :cc_emails,
                         :body_text, '', 'inbound', true, :has_attachments,
                         :email_date, now(), now(), now())
                    ON CONFLICT (id) DO NOTHING
                """),
                {
                    "id": email_id,
                    "tenant_id": str(TENANT_ID),
                    "email_account_id": EMAIL_ACCOUNT_ID,
                    "provider_message_id": f"test-seed-{rec['key']}",
                    "subject": rec["email_subject"],
                    "from_email": rec["email_from"],
                    "from_name": rec["email_from"].split("@")[0].replace(".", " ").title(),
                    "to_emails": json.dumps(["seidony@kestinglegal.nl"]),
                    "cc_emails": "[]",
                    "body_text": rec["email_body"],
                    "has_attachments": rec.get("has_pdf_data", False),
                    "email_date": _dt_ago(rec["email_days_ago"]),
                },
            )
            email_count += 1

            # Build AI reasoning with marker
            base_reasoning = _build_reasoning(rec)
            ai_reasoning = f"{MARKER} {base_reasoning}"

            # Build raw extraction JSON
            raw = {
                k: str(v) if isinstance(v, (Decimal, date)) else v
                for k, v in rec.items()
                if k.startswith("debtor_") or k in (
                    "invoice_number", "invoice_date", "due_date",
                    "principal_amount", "description",
                )
            }
            raw_json = json.dumps(raw, default=str)

            # Reviewed fields (for approved/rejected)
            reviewed_by_id = None
            reviewed_at = None
            if rec["status"] in ("approved", "rejected"):
                reviewed_by_id = str(USER_ID)
                reviewed_at = _dt_ago(max(0, rec["email_days_ago"] - 1))

            # IntakeRequest
            await db.execute(
                text("""
                    INSERT INTO intake_requests
                        (id, tenant_id, synced_email_id,
                         debtor_name, debtor_email, debtor_kvk,
                         debtor_address, debtor_city, debtor_postcode, debtor_type,
                         invoice_number, invoice_date, due_date,
                         principal_amount, description,
                         ai_model, ai_confidence, ai_reasoning, raw_extraction,
                         has_pdf_data, status, error_message,
                         reviewed_by_id, reviewed_at, review_note,
                         created_at, updated_at)
                    VALUES
                        (:id, :tenant_id, :synced_email_id,
                         :debtor_name, :debtor_email, :debtor_kvk,
                         :debtor_address, :debtor_city, :debtor_postcode, :debtor_type,
                         :invoice_number, :invoice_date, :due_date,
                         :principal_amount, :description,
                         :ai_model, :ai_confidence, :ai_reasoning, :raw_extraction,
                         :has_pdf_data, :status, :error_message,
                         :reviewed_by_id, :reviewed_at, :review_note,
                         now(), now())
                    ON CONFLICT (id) DO NOTHING
                """),
                {
                    "id": intake_id,
                    "tenant_id": str(TENANT_ID),
                    "synced_email_id": email_id,
                    "debtor_name": rec.get("debtor_name"),
                    "debtor_email": rec.get("debtor_email"),
                    "debtor_kvk": rec.get("debtor_kvk"),
                    "debtor_address": rec.get("debtor_address"),
                    "debtor_city": rec.get("debtor_city"),
                    "debtor_postcode": rec.get("debtor_postcode"),
                    "debtor_type": rec["debtor_type"],
                    "invoice_number": rec.get("invoice_number"),
                    "invoice_date": rec.get("invoice_date"),
                    "due_date": rec.get("due_date"),
                    "principal_amount": rec.get("principal_amount"),
                    "description": rec.get("description"),
                    "ai_model": rec.get("ai_model", ""),
                    "ai_confidence": rec.get("confidence"),
                    "ai_reasoning": ai_reasoning,
                    "raw_extraction": raw_json,
                    "has_pdf_data": rec.get("has_pdf_data", False),
                    "status": rec["status"],
                    "error_message": rec.get("error_message"),
                    "reviewed_by_id": reviewed_by_id,
                    "reviewed_at": reviewed_at,
                    "review_note": rec.get("review_note"),
                },
            )
            intake_count += 1

        await db.commit()

        # Report
        print("=" * 60)
        print("Intake Test Data — Seed Report")
        print("=" * 60)
        print()
        print(f"  Email account:    1 (test-intake@kestinglegal.nl)")
        print(f"  Synced emails:    {email_count}")
        print(f"  Intake requests:  {intake_count}")
        print()
        # Status breakdown
        from collections import Counter
        statuses = Counter(r["status"] for r in INTAKE_RECORDS)
        print("  Status breakdown:")
        for status, count in sorted(statuses.items()):
            print(f"    {status:<15s}  {count}")
        print()
        print(f"  Marker: ai_reasoning starts with '{MARKER}'")
        print(f"  Cleanup: python scripts/seed_intake_testdata.py --cleanup")


def _build_reasoning(rec: dict) -> str:
    """Generate realistic AI reasoning text based on the scenario."""
    status = rec["status"]
    conf = rec.get("confidence")

    if status in ("detected", "processing"):
        return "Email gedetecteerd als mogelijke incasso-opdracht. Verwerking gestart."

    if status == "failed":
        return f"Extractie mislukt: {rec.get('error_message', 'onbekende fout')}"

    if conf and float(conf) >= 0.85:
        return (
            "Alle relevante gegevens succesvol geëxtraheerd uit email en bijlage. "
            "Debiteur, factuurnummer, bedrag en vervaldatum duidelijk aanwezig."
        )
    if conf and float(conf) >= 0.60:
        return (
            "Gedeeltelijke extractie. Hoofdgegevens gevonden maar sommige velden "
            "ontbreken of zijn onzeker. Handmatige controle aanbevolen."
        )
    return (
        "Beperkte gegevens gevonden. Veel velden ontbreken. "
        "Handmatige invoer waarschijnlijk nodig."
    )


async def cleanup() -> None:
    """Remove all test-seeded intake data (identified by [TEST-SEED] marker)."""
    async with async_session() as db:
        # Delete intake requests with marker
        result_intake = await db.execute(
            text("""
                DELETE FROM intake_requests
                WHERE ai_reasoning LIKE :marker
                RETURNING id
            """),
            {"marker": f"{MARKER}%"},
        )
        intake_deleted = len(result_intake.fetchall())

        # Delete synced emails linked to test email account
        result_emails = await db.execute(
            text("""
                DELETE FROM synced_emails
                WHERE email_account_id = :account_id
                AND provider_message_id LIKE 'test-seed-%'
                RETURNING id
            """),
            {"account_id": EMAIL_ACCOUNT_ID},
        )
        emails_deleted = len(result_emails.fetchall())

        # Delete test email account
        await db.execute(
            text("""
                DELETE FROM email_accounts WHERE id = :id
            """),
            {"id": EMAIL_ACCOUNT_ID},
        )

        await db.commit()

        print("=" * 60)
        print("Intake Test Data — Cleanup Report")
        print("=" * 60)
        print()
        print(f"  Intake requests deleted:  {intake_deleted}")
        print(f"  Synced emails deleted:    {emails_deleted}")
        print(f"  Email account deleted:    1")
        print()
        print("  Cleanup complete.")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Seed intake test data")
    parser.add_argument("--dry-run", action="store_true", help="Print without inserting")
    parser.add_argument("--cleanup", action="store_true", help="Remove all test data")
    args = parser.parse_args()

    if args.cleanup:
        await cleanup()
    else:
        await seed(dry_run=args.dry_run)


if __name__ == "__main__":
    asyncio.run(main())
