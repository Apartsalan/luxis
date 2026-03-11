"""Tool definitions — JSON schemas and registration for all AI agent tools.

Each tool is defined with:
- name: tool identifier
- description: Dutch description for Claude (explains what the tool does)
- input_schema: JSON Schema for parameters
- handler: async function from handlers/

Call `register_all_tools(registry)` to populate a ToolRegistry instance.
"""

from __future__ import annotations

from app.ai_agent.tools.handlers.cases import (
    handle_case_add_activity,
    handle_case_create,
    handle_case_get,
    handle_case_list,
    handle_case_update,
)
from app.ai_agent.tools.handlers.collections import (
    handle_claim_create,
    handle_claim_list,
    handle_financial_summary,
    handle_payment_list,
    handle_payment_register,
)
from app.ai_agent.tools.handlers.contacts import (
    handle_contact_create,
    handle_contact_get,
    handle_contact_lookup,
)
from app.ai_agent.tools.handlers.documents import (
    handle_document_generate,
    handle_document_list,
    handle_template_list,
)
from app.ai_agent.tools.handlers.email import (
    handle_email_compose,
    handle_email_unlinked,
)
from app.ai_agent.tools.handlers.general import (
    handle_dashboard_summary,
    handle_global_search,
    handle_trust_fund_balance,
)
from app.ai_agent.tools.handlers.invoices import (
    handle_invoice_add_line,
    handle_invoice_approve,
    handle_invoice_create,
    handle_invoice_send,
    handle_receivables_list,
)
from app.ai_agent.tools.handlers.pipeline import (
    handle_pipeline_batch,
    handle_pipeline_overview,
    handle_pipeline_queue_counts,
)
from app.ai_agent.tools.handlers.time_entries import (
    handle_time_entry_create,
    handle_unbilled_hours,
)
from app.ai_agent.tools.handlers.workflow import (
    handle_task_create,
    handle_task_list,
    handle_verjaring_check,
)
from app.ai_agent.tools.registry import ToolRegistry

# ── Tool Definitions ──────────────────────────────────────────────────────────

TOOL_DEFINITIONS: list[dict] = [
    # ── Cases (Dossiers) ──────────────────────────────────────────────────────
    {
        "name": "case_list",
        "description": (
            "Zoek en filter dossiers. Kan filteren op type (incasso/insolventie/advies), "
            "status, cliënt, en vrije tekst. Geeft een gepagineerde lijst terug."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "search": {"type": "string", "description": "Zoektekst (zaaknummer, beschrijving, referentie)"},
                "case_type": {"type": "string", "enum": ["incasso", "insolventie", "advies", "overig"]},
                "status": {"type": "string", "description": "Status filter (nieuw, sommatie, betaald, etc.)"},
                "client_id": {"type": "string", "description": "UUID van de cliënt"},
                "is_active": {"type": "boolean", "default": True},
                "page": {"type": "integer", "default": 1, "minimum": 1},
                "per_page": {"type": "integer", "default": 20, "minimum": 1, "maximum": 100},
            },
            "required": [],
        },
        "handler": handle_case_list,
    },
    {
        "name": "case_get",
        "description": (
            "Haal alle details van één dossier op: type, status, cliënt, wederpartij, "
            "rentesoort, openstaand bedrag, etc."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "description": "UUID van het dossier"},
            },
            "required": ["case_id"],
        },
        "handler": handle_case_get,
    },
    {
        "name": "case_create",
        "description": (
            "Maak een nieuw dossier aan. Vereist minimaal een cliënt-ID en openingsdatum. "
            "Genereert automatisch een zaaknummer."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "client_id": {"type": "string", "description": "UUID van de cliënt (verplicht)"},
                "date_opened": {"type": "string", "format": "date", "description": "Openingsdatum (YYYY-MM-DD)"},
                "case_type": {"type": "string", "enum": ["incasso", "insolventie", "advies", "overig"], "default": "incasso"},
                "debtor_type": {"type": "string", "enum": ["b2b", "b2c"], "default": "b2b"},
                "description": {"type": "string", "description": "Korte beschrijving van de zaak"},
                "reference": {"type": "string", "description": "Externe referentie (bijv. klantreferentie)"},
                "opposing_party_id": {"type": "string", "description": "UUID van de wederpartij"},
                "interest_type": {"type": "string", "enum": ["statutory", "commercial", "government", "contractual"], "default": "statutory"},
            },
            "required": ["client_id", "date_opened"],
        },
        "handler": handle_case_create,
    },
    {
        "name": "case_update",
        "description": "Wijzig velden van een bestaand dossier (beschrijving, referentie, wederpartij, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "description": "UUID van het dossier"},
                "description": {"type": "string"},
                "reference": {"type": "string"},
                "opposing_party_id": {"type": "string", "description": "UUID van de wederpartij"},
                "interest_type": {"type": "string", "enum": ["statutory", "commercial", "government", "contractual"]},
                "debtor_type": {"type": "string", "enum": ["b2b", "b2c"]},
            },
            "required": ["case_id"],
        },
        "handler": handle_case_update,
    },
    {
        "name": "case_add_activity",
        "description": "Voeg een notitie of activiteit toe aan een dossier (bijv. telefoongesprek, email, notitie).",
        "input_schema": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "description": "UUID van het dossier"},
                "activity_type": {
                    "type": "string",
                    "enum": ["note", "phone_call", "email", "document", "payment", "status_change"],
                    "description": "Type activiteit",
                },
                "title": {"type": "string", "description": "Titel van de activiteit"},
                "description": {"type": "string", "description": "Optionele beschrijving"},
            },
            "required": ["case_id", "activity_type", "title"],
        },
        "handler": handle_case_add_activity,
    },

    # ── Contacts (Relaties) ───────────────────────────────────────────────────
    {
        "name": "contact_lookup",
        "description": (
            "Zoek bestaande relaties (personen of bedrijven) op naam, email, of KvK-nummer. "
            "Gebruik dit voordat je een nieuwe relatie aanmaakt om duplicaten te voorkomen."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "search": {"type": "string", "description": "Zoektekst (naam, email, KvK-nummer)"},
                "contact_type": {"type": "string", "enum": ["company", "person"]},
                "page": {"type": "integer", "default": 1},
                "per_page": {"type": "integer", "default": 10},
            },
            "required": ["search"],
        },
        "handler": handle_contact_lookup,
    },
    {
        "name": "contact_get",
        "description": "Haal alle details van één relatie op: adres, KvK, BTW, IBAN, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "contact_id": {"type": "string", "description": "UUID van de relatie"},
            },
            "required": ["contact_id"],
        },
        "handler": handle_contact_get,
    },
    {
        "name": "contact_create",
        "description": "Maak een nieuwe relatie aan (persoon of bedrijf).",
        "input_schema": {
            "type": "object",
            "properties": {
                "contact_type": {"type": "string", "enum": ["company", "person"], "description": "Type: bedrijf of persoon"},
                "name": {"type": "string", "description": "Naam (verplicht)"},
                "email": {"type": "string", "description": "E-mailadres"},
                "phone": {"type": "string", "description": "Telefoonnummer"},
                "kvk_number": {"type": "string", "description": "KvK-nummer"},
                "btw_number": {"type": "string", "description": "BTW-nummer"},
                "visit_address": {"type": "string", "description": "Bezoekadres"},
                "visit_postcode": {"type": "string", "description": "Postcode"},
                "visit_city": {"type": "string", "description": "Plaats"},
            },
            "required": ["contact_type", "name"],
        },
        "handler": handle_contact_create,
    },

    # ── Collections (Incasso) ─────────────────────────────────────────────────
    {
        "name": "claim_list",
        "description": "Lijst alle vorderingen op een dossier (bedrag, vervaldatum, factuurnummer).",
        "input_schema": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "description": "UUID van het dossier"},
            },
            "required": ["case_id"],
        },
        "handler": handle_claim_list,
    },
    {
        "name": "claim_create",
        "description": (
            "Voeg een vordering toe aan een dossier. De verzuimdatum (default_date) is "
            "essentieel voor renteberekening."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "description": "UUID van het dossier"},
                "description": {"type": "string", "description": "Omschrijving van de vordering"},
                "principal_amount": {"type": "string", "description": "Hoofdsom als decimaal getal (bijv. '1500.00')"},
                "default_date": {"type": "string", "format": "date", "description": "Verzuimdatum (YYYY-MM-DD)"},
                "invoice_number": {"type": "string", "description": "Factuurnummer"},
                "invoice_date": {"type": "string", "format": "date", "description": "Factuurdatum (YYYY-MM-DD)"},
            },
            "required": ["case_id", "description", "principal_amount", "default_date"],
        },
        "handler": handle_claim_create,
    },
    {
        "name": "payment_register",
        "description": (
            "Registreer een betaling op een dossier. De betaling wordt automatisch verdeeld "
            "volgens art. 6:44 BW: eerst kosten, dan rente, dan hoofdsom."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "description": "UUID van het dossier"},
                "amount": {"type": "string", "description": "Betaald bedrag als decimaal (bijv. '500.00')"},
                "payment_date": {"type": "string", "format": "date", "description": "Betalingsdatum (YYYY-MM-DD)"},
                "description": {"type": "string", "description": "Omschrijving (bijv. 'Bankoverschrijving')"},
                "payment_method": {"type": "string", "description": "Betaalwijze (bijv. 'bank', 'ideal', 'cash')"},
            },
            "required": ["case_id", "amount", "payment_date"],
        },
        "handler": handle_payment_register,
    },
    {
        "name": "payment_list",
        "description": "Lijst alle betalingen op een dossier met de art. 6:44 BW verdeling per betaling.",
        "input_schema": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "description": "UUID van het dossier"},
            },
            "required": ["case_id"],
        },
        "handler": handle_payment_list,
    },
    {
        "name": "financial_summary",
        "description": (
            "Volledig financieel overzicht van een dossier: hoofdsom, rente (berekend per art. 6:119/6:119a BW), "
            "BIK (art. 6:96 BW), betalingen, en openstaand saldo. Dit is de kernberekening voor incasso."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "description": "UUID van het dossier"},
                "calc_date": {"type": "string", "format": "date", "description": "Berekendate (default: vandaag)"},
            },
            "required": ["case_id"],
        },
        "handler": handle_financial_summary,
    },

    # ── Documents ─────────────────────────────────────────────────────────────
    {
        "name": "document_generate",
        "description": (
            "Genereer een document vanuit een template voor een dossier (bijv. 14-dagenbrief, "
            "sommatie, renteoverzicht). Geeft het gegenereerde document terug."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "description": "UUID van het dossier"},
                "template_id": {"type": "string", "description": "UUID van het template"},
                "title": {"type": "string", "description": "Optionele aangepaste titel"},
            },
            "required": ["case_id", "template_id"],
        },
        "handler": handle_document_generate,
    },
    {
        "name": "document_list",
        "description": "Lijst alle gegenereerde documenten voor een dossier.",
        "input_schema": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "description": "UUID van het dossier"},
            },
            "required": ["case_id"],
        },
        "handler": handle_document_list,
    },
    {
        "name": "template_list",
        "description": "Lijst beschikbare documenttemplates (14-dagenbrief, sommatie, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {
                "template_type": {"type": "string", "description": "Filter op type (bijv. '14_dagenbrief')"},
            },
            "required": [],
        },
        "handler": handle_template_list,
    },

    # ── Email ─────────────────────────────────────────────────────────────────
    {
        "name": "email_compose",
        "description": (
            "Verstuur een email via de geconfigureerde email provider (Gmail/Outlook). "
            "De email verschijnt in de Verzonden map en wordt gekoppeld aan het dossier."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "description": "UUID van het dossier"},
                "to": {"type": "string", "description": "Ontvanger email"},
                "subject": {"type": "string", "description": "Onderwerp"},
                "body": {"type": "string", "description": "Email inhoud (HTML)"},
                "cc": {"type": "string", "description": "CC adressen, komma-gescheiden"},
            },
            "required": ["case_id", "to", "subject", "body"],
        },
        "handler": handle_email_compose,
    },
    {
        "name": "email_unlinked",
        "description": "Haal emails op die niet automatisch aan een dossier gekoppeld konden worden.",
        "input_schema": {
            "type": "object",
            "properties": {
                "page": {"type": "integer", "default": 1},
                "per_page": {"type": "integer", "default": 20},
            },
            "required": [],
        },
        "handler": handle_email_unlinked,
    },

    # ── Invoices (Facturen) ───────────────────────────────────────────────────
    {
        "name": "invoice_create",
        "description": "Maak een nieuwe factuur aan (status: concept). Voeg daarna regels toe met invoice_add_line.",
        "input_schema": {
            "type": "object",
            "properties": {
                "contact_id": {"type": "string", "description": "UUID van de cliënt/debiteur"},
                "invoice_date": {"type": "string", "format": "date", "description": "Factuurdatum (YYYY-MM-DD)"},
                "due_date": {"type": "string", "format": "date", "description": "Vervaldatum (YYYY-MM-DD)"},
                "case_id": {"type": "string", "description": "UUID van het dossier (optioneel)"},
                "reference": {"type": "string", "description": "Referentie"},
                "notes": {"type": "string", "description": "Notities op de factuur"},
                "btw_percentage": {"type": "string", "default": "21.00", "description": "BTW-percentage"},
            },
            "required": ["contact_id", "invoice_date", "due_date"],
        },
        "handler": handle_invoice_create,
    },
    {
        "name": "invoice_add_line",
        "description": "Voeg een factuurregel toe aan een bestaande factuur.",
        "input_schema": {
            "type": "object",
            "properties": {
                "invoice_id": {"type": "string", "description": "UUID van de factuur"},
                "description": {"type": "string", "description": "Omschrijving van de regel"},
                "unit_price": {"type": "string", "description": "Prijs per eenheid als decimaal"},
                "quantity": {"type": "string", "default": "1", "description": "Aantal"},
                "time_entry_id": {"type": "string", "description": "UUID van tijdregistratie (optioneel)"},
                "expense_id": {"type": "string", "description": "UUID van onkost (optioneel)"},
            },
            "required": ["invoice_id", "description", "unit_price"],
        },
        "handler": handle_invoice_add_line,
    },
    {
        "name": "invoice_approve",
        "description": "Keur een concept-factuur goed. Na goedkeuring kan de factuur verzonden worden.",
        "input_schema": {
            "type": "object",
            "properties": {
                "invoice_id": {"type": "string", "description": "UUID van de factuur"},
            },
            "required": ["invoice_id"],
        },
        "handler": handle_invoice_approve,
    },
    {
        "name": "invoice_send",
        "description": "Markeer een goedgekeurde factuur als verzonden.",
        "input_schema": {
            "type": "object",
            "properties": {
                "invoice_id": {"type": "string", "description": "UUID van de factuur"},
            },
            "required": ["invoice_id"],
        },
        "handler": handle_invoice_send,
    },
    {
        "name": "receivables_list",
        "description": (
            "Debiteurenoverzicht: openstaande facturen gegroepeerd per relatie met aging buckets "
            "(0-30 dagen, 31-60, 61-90, 90+)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
        "handler": handle_receivables_list,
    },

    # ── Pipeline (Incasso) ────────────────────────────────────────────────────
    {
        "name": "pipeline_overview",
        "description": "Overzicht van alle incasso-dossiers gegroepeerd per pipeline-stap (intake, herinnering, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
        "handler": handle_pipeline_overview,
    },
    {
        "name": "pipeline_batch",
        "description": (
            "Voer een batch-actie uit op meerdere dossiers tegelijk (bijv. verplaatsen naar "
            "volgende stap, documenten genereren, emails versturen)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "case_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Lijst van dossier-UUIDs",
                },
                "action": {"type": "string", "description": "Actie (bijv. 'advance', 'generate_document')"},
                "target_step_id": {"type": "string", "description": "UUID van de doelstap (bij 'move')"},
                "send_email": {"type": "boolean", "default": False, "description": "Verstuur email na actie"},
            },
            "required": ["case_ids", "action"],
        },
        "handler": handle_pipeline_batch,
    },
    {
        "name": "pipeline_queue_counts",
        "description": "Aantal dossiers per pipeline-stap (voor dashboard/overzicht).",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
        "handler": handle_pipeline_queue_counts,
    },

    # ── Workflow (Tasks) ──────────────────────────────────────────────────────
    {
        "name": "task_create",
        "description": "Maak een workflow-taak aan voor een dossier (bijv. check_payment, manual_review, send_letter).",
        "input_schema": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "description": "UUID van het dossier"},
                "task_type": {
                    "type": "string",
                    "enum": ["generate_document", "send_letter", "send_email", "check_payment", "escalate_status", "manual_review", "set_deadline", "custom"],
                    "description": "Type taak",
                },
                "title": {"type": "string", "description": "Titel van de taak"},
                "due_date": {"type": "string", "format": "date", "description": "Deadline (YYYY-MM-DD)"},
                "description": {"type": "string", "description": "Optionele beschrijving"},
                "assigned_to_id": {"type": "string", "description": "UUID van de toegewezen gebruiker"},
            },
            "required": ["case_id", "task_type", "title", "due_date"],
        },
        "handler": handle_task_create,
    },
    {
        "name": "task_list",
        "description": "Lijst openstaande workflow-taken. Kan filteren op dossier, status, of toegewezen gebruiker.",
        "input_schema": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "description": "Filter op dossier UUID"},
                "status": {"type": "string", "enum": ["pending", "due", "completed", "skipped", "overdue"]},
                "assigned_to_id": {"type": "string", "description": "Filter op toegewezen gebruiker UUID"},
            },
            "required": [],
        },
        "handler": handle_task_list,
    },
    {
        "name": "verjaring_check",
        "description": (
            "Controleer alle actieve dossiers op naderende verjaring (art. 3:307 BW: 5 jaar). "
            "Geeft een lijst van dossiers die aandacht nodig hebben."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
        "handler": handle_verjaring_check,
    },

    # ── Time Entries (Tijdregistratie) ────────────────────────────────────────
    {
        "name": "time_entry_create",
        "description": "Registreer gewerkte tijd op een dossier.",
        "input_schema": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "description": "UUID van het dossier"},
                "duration_minutes": {"type": "integer", "minimum": 1, "description": "Duur in minuten"},
                "entry_date": {"type": "string", "format": "date", "description": "Datum (default: vandaag)"},
                "description": {"type": "string", "description": "Beschrijving van het werk"},
                "activity_type": {
                    "type": "string",
                    "enum": ["correspondence", "meeting", "phone", "research", "court", "travel", "drafting", "other"],
                    "default": "other",
                },
                "billable": {"type": "boolean", "default": True},
                "hourly_rate": {"type": "string", "description": "Uurtarief als decimaal (bijv. '250.00')"},
            },
            "required": ["case_id", "duration_minutes"],
        },
        "handler": handle_time_entry_create,
    },
    {
        "name": "unbilled_hours",
        "description": "Lijst onbefactureerde uren. Optioneel filteren op dossier.",
        "input_schema": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "description": "Filter op dossier UUID"},
            },
            "required": [],
        },
        "handler": handle_unbilled_hours,
    },

    # ── General ───────────────────────────────────────────────────────────────
    {
        "name": "dashboard_summary",
        "description": (
            "Dashboard KPI's: totaal dossiers, openstaande vorderingen, komende deadlines, "
            "recente activiteit."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
        "handler": handle_dashboard_summary,
    },
    {
        "name": "global_search",
        "description": "Zoek in dossiers, relaties, en documenten tegelijk.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Zoektekst"},
                "limit": {"type": "integer", "default": 20, "maximum": 50},
            },
            "required": ["query"],
        },
        "handler": handle_global_search,
    },
    {
        "name": "trust_fund_balance",
        "description": "Saldo van de derdengeldrekening voor een dossier (stortingen, uitkeringen, saldo).",
        "input_schema": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "description": "UUID van het dossier"},
            },
            "required": ["case_id"],
        },
        "handler": handle_trust_fund_balance,
    },
]


def register_all_tools(registry: ToolRegistry) -> None:
    """Register all AI agent tools in the given registry."""
    for defn in TOOL_DEFINITIONS:
        registry.register(
            name=defn["name"],
            description=defn["description"],
            input_schema=defn["input_schema"],
            handler=defn["handler"],
        )


def create_default_registry() -> ToolRegistry:
    """Create and populate a ToolRegistry with all default tools."""
    registry = ToolRegistry()
    register_all_tools(registry)
    return registry
