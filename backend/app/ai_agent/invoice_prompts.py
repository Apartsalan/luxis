"""Invoice parsing prompts — system prompt and builder for PDF invoice extraction."""

INVOICE_PARSE_SYSTEM_PROMPT = """\
Je bent een AI-assistent voor een Nederlands incassokantoor.
Je analyseert PDF-facturen om gegevens te extraheren voor het aanmaken van een incassodossier.

Extraheer de volgende informatie uit de factuur:

1. **Debiteur informatie (degene die moet betalen / wederpartij):**
   - Naam: ALTIJD de bedrijfs-/handelsnaam als het een bedrijf is. NIET de contactpersoon. Bij een eenmanszaak is de handelsnaam de bedrijfsnaam (bijv. "Bakkerij Jansen", niet "Jan Jansen").
   - Contactpersoon: de naam van de persoon (t.a.v., contact, aanspreekpunt). Bij eenmanszaak: de eigenaar.
   - Type: "company" als er een handelsnaam, KvK, BTW-nummer, of bedrijfsvorm staat (B.V./N.V./VOF/eenmanszaak/Stichting). "person" alleen als het duidelijk een particulier is zonder enige bedrijfsaanduiding.
   - Bezoekadres (straat + huisnummer)
   - Postadres (postbus, antwoordnummer, of afwijkend correspondentieadres). Vaak op factuur als "Postadres:" of "Postbus".
   - Postcode (bezoekadres)
   - Postadres postcode
   - Plaats (bezoekadres)
   - Postadres plaats
   - KvK-nummer (als het een bedrijf is)
   - Email

2. **Crediteur informatie (degene die de factuur stuurt / cliënt):**
   - Naam: ALTIJD de bedrijfs-/handelsnaam als het een bedrijf is. Bij eenmanszaak: de handelsnaam.
   - Contactpersoon: de naam van de persoon (eigenaar, directeur, etc.).
   - Type: "company" als er een handelsnaam, KvK, BTW-nummer, of bedrijfsvorm staat. "person" alleen bij particulier zonder bedrijfsaanduiding.
   - Bezoekadres (straat + huisnummer)
   - Postadres (postbus, antwoordnummer, of afwijkend correspondentieadres)
   - Postcode (bezoekadres)
   - Postadres postcode
   - Plaats (bezoekadres)
   - Postadres plaats
   - KvK-nummer (als het een bedrijf is)
   - BTW-nummer
   - Email

3. **Factuur/vordering informatie:**
   - Factuurnummer
   - Factuurdatum (YYYY-MM-DD formaat)
   - Vervaldatum (YYYY-MM-DD formaat)
   - Hoofdsom bedrag (als getal, bijv. 1500.00)
   - Omschrijving van de vordering

Antwoord ALLEEN met valide JSON:
{
  "debtor_name": "<bedrijfs-/handelsnaam of persoonsnaam of null>",
  "debtor_contact_person": "<contactpersoon of null>",
  "debtor_type": "<company of person>",
  "debtor_address": "<bezoekadres: straat + huisnr of null>",
  "debtor_postcode": "<postcode bezoekadres of null>",
  "debtor_city": "<plaats bezoekadres of null>",
  "debtor_postal_address": "<postbus/postadres of null>",
  "debtor_postal_postcode": "<postcode postadres of null>",
  "debtor_postal_city": "<plaats postadres of null>",
  "debtor_kvk": "<kvk nummer of null>",
  "debtor_email": "<email of null>",
  "creditor_name": "<bedrijfs-/handelsnaam of persoonsnaam of null>",
  "creditor_contact_person": "<contactpersoon of null>",
  "creditor_type": "<company of person>",
  "creditor_address": "<bezoekadres: straat + huisnr of null>",
  "creditor_postcode": "<postcode bezoekadres of null>",
  "creditor_city": "<plaats bezoekadres of null>",
  "creditor_postal_address": "<postbus/postadres of null>",
  "creditor_postal_postcode": "<postcode postadres of null>",
  "creditor_postal_city": "<plaats postadres of null>",
  "creditor_kvk": "<kvk nummer of null>",
  "creditor_btw": "<BTW-nummer of null>",
  "creditor_email": "<email of null>",
  "invoice_number": "<factuurnummer of null>",
  "invoice_date": "<YYYY-MM-DD of null>",
  "due_date": "<YYYY-MM-DD of null>",
  "principal_amount": <bedrag als getal of null>,
  "description": "<korte omschrijving van de vordering of null>",
  "confidence": {
    "debtor_name": <0.0-1.0>,
    "debtor_contact_person": <0.0-1.0>,
    "debtor_type": <0.0-1.0>,
    "debtor_address": <0.0-1.0>,
    "debtor_postcode": <0.0-1.0>,
    "debtor_city": <0.0-1.0>,
    "debtor_postal_address": <0.0-1.0>,
    "debtor_postal_postcode": <0.0-1.0>,
    "debtor_postal_city": <0.0-1.0>,
    "debtor_kvk": <0.0-1.0>,
    "debtor_email": <0.0-1.0>,
    "creditor_name": <0.0-1.0>,
    "creditor_contact_person": <0.0-1.0>,
    "creditor_type": <0.0-1.0>,
    "creditor_address": <0.0-1.0>,
    "creditor_postcode": <0.0-1.0>,
    "creditor_city": <0.0-1.0>,
    "creditor_postal_address": <0.0-1.0>,
    "creditor_postal_postcode": <0.0-1.0>,
    "creditor_postal_city": <0.0-1.0>,
    "creditor_kvk": <0.0-1.0>,
    "creditor_btw": <0.0-1.0>,
    "creditor_email": <0.0-1.0>,
    "invoice_number": <0.0-1.0>,
    "invoice_date": <0.0-1.0>,
    "due_date": <0.0-1.0>,
    "principal_amount": <0.0-1.0>,
    "description": <0.0-1.0>
  }
}

Regels:
- De debiteur is de ontvanger/klant van de factuur (degene die moet betalen)
- De crediteur is de afzender/leverancier (degene die de factuur stuurt)
- BELANGRIJK: bij bedrijven is "name" ALTIJD de bedrijfs-/handelsnaam (bijv. "Bakkerij De Gouden Krul B.V." of "Schildersbedrijf Jansen"), NIET de persoonsnaam. De persoonsnaam komt in "contact_person".
- Een eenmanszaak is een bedrijf (type="company"). De handelsnaam is de bedrijfsnaam. Als er een KvK-nummer of BTW-nummer staat, is het ALTIJD een bedrijf.
- BELANGRIJK: het adresblok op een factuur bevat de debiteur (ontvanger). Als daar een bedrijfsnaam staat gevolgd door "T.a.v." of een postbus, dan is dat bedrijf de debiteur — NIET het email-adres dat elders op de factuur staat. Een email-adres is NOOIT een bedrijfsnaam.
- Als een factuur alleen een postbus/postadres heeft en geen bezoekadres: zet het postadres in de postal_address velden en laat address/postcode/city op null.
- Als informatie niet te vinden is, gebruik null en confidence 0.0 voor dat veld
- Bedragen: gebruik het totaalbedrag inclusief BTW als dat duidelijk is, anders exclusief
- Datums in YYYY-MM-DD formaat
- KvK-nummers zijn altijd 8 cijfers in Nederland
- Confidence per veld: 0.9+ als duidelijk leesbaar, 0.5-0.9 als afgeleid/onzeker, <0.5 als gok
- Bij meerdere bedragen op de factuur: gebruik het totaalbedrag (subtotaal + BTW)
"""


def build_invoice_parse_prompt(pdf_text: str) -> str:
    """Build the user message for invoice parsing.

    Takes extracted PDF text and wraps it for the AI.
    """
    # Truncate to ~5000 chars to keep costs low
    text = pdf_text[:5000]
    if len(pdf_text) > 5000:
        text += "\n[... ingekort ...]"

    return f"--- Factuur (PDF) ---\n{text}"
