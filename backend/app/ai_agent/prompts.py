"""AI Agent prompts — system prompt and prompt builder for email classification."""

import html
import re

CLASSIFICATION_SYSTEM_PROMPT = """\
Je bent een AI-assistent voor een Nederlands incassokantoor.
Je analyseert emails van debiteuren en classificeert ze.

Classificeer de email in PRECIES ÉÉN categorie:
1. belofte_tot_betaling — Debiteur belooft te betalen (noemt datum/intentie)
2. betwisting — Debiteur betwist de vordering (oneens met bedrag, ontkent schuld)
3. betalingsregeling_verzoek — Debiteur vraagt een betalingsregeling (in termijnen)
4. beweert_betaald — Debiteur zegt al betaald te hebben
5. onvermogen — Debiteur zegt niet te kunnen betalen (financiële problemen)
6. juridisch_verweer — Juridische reactie (advocaat betrokken, formele juridische taal)
7. ontvangstbevestiging — Simpele ontvangstbevestiging, neutraal
8. niet_gerelateerd — Spam, niet-gerelateerd, of automatisch antwoord

Antwoord ALLEEN met valide JSON:
{
  "category": "<een van de 8 categorieën>",
  "confidence": <0.0-1.0>,
  "reasoning": "<1-2 zinnen uitleg in het Nederlands>",
  "suggested_action": "<wait_and_remind|escalate|send_template|dismiss|request_proof|no_action>",
  "suggested_template_key": "<template key of null>",
  "suggested_reminder_days": <getal of null>
}

Regels voor suggested_action:
- belofte_tot_betaling → wait_and_remind, reminder_days op basis van genoemde termijn (standaard 7)
- betwisting → escalate (altijd menselijke beoordeling nodig)
- betalingsregeling_verzoek → escalate (advocaat moet voorwaarden bepalen)
- beweert_betaald → send_template (key: "verzoek_betalingsbewijs")
- onvermogen → escalate (advocaat moet situatie beoordelen)
- juridisch_verweer → escalate (altijd advocaat nodig)
- ontvangstbevestiging → no_action
- niet_gerelateerd → dismiss
"""


def build_classification_prompt(
    *,
    case_number: str,
    pipeline_step_name: str | None,
    outstanding_amount: str,
    opposing_party_name: str,
    last_outbound_subject: str | None,
    last_outbound_date: str | None,
    email_subject: str,
    email_from_name: str,
    email_from_email: str,
    email_date: str,
    email_body: str,
) -> str:
    """Build the user message for the classification AI call.

    Includes case context and the email to classify.
    """
    last_outbound_section = ""
    if last_outbound_subject:
        last_outbound_section = (
            f"\n--- Laatste uitgaande email ---\n"
            f"Onderwerp: {last_outbound_subject}\n"
            f"Verzonden: {last_outbound_date or 'onbekend'}\n"
        )

    # Truncate body to ~3000 chars to keep costs low
    body = email_body[:3000]
    if len(email_body) > 3000:
        body += "\n[... ingekort ...]"

    return (
        f"Dossier: {case_number}\n"
        f"Huidige stap: {pipeline_step_name or 'geen'}\n"
        f"Openstaand bedrag: EUR {outstanding_amount}\n"
        f"Debiteur: {opposing_party_name}\n"
        f"{last_outbound_section}"
        f"\n--- Inkomende email van debiteur ---\n"
        f"Onderwerp: {email_subject}\n"
        f"Van: {email_from_name} <{email_from_email}>\n"
        f"Datum: {email_date}\n\n"
        f"{body}"
    )


def strip_html(raw_html: str) -> str:
    """Strip HTML tags and decode entities to get plain text.

    Handles Microsoft Outlook HTML which contains large <style> blocks,
    conditional comments, and heavy entity encoding.
    """
    if not raw_html:
        return ""
    text = raw_html
    # Remove <style> and <script> blocks entirely (including content)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    # Remove HTML comments (including IE conditional comments <!--[if ...]>)
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)
    # Replace <br>, <p>, <div>, <tr> with newlines for readability
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</(p|div|tr|li|h[1-6])>", "\n", text, flags=re.IGNORECASE)
    # Remove remaining HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Decode HTML entities (&amp; &nbsp; &#160; etc.)
    text = html.unescape(text)
    # Replace non-breaking spaces with regular spaces
    text = text.replace("\u00a0", " ")
    # Collapse multiple whitespace (but keep single newlines)
    text = re.sub(r"[^\S\n]+", " ", text)  # collapse spaces/tabs but not newlines
    text = re.sub(r"\n\s*\n+", "\n\n", text)  # collapse multiple blank lines
    text = text.strip()
    return text
