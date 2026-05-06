# Lisanne's Incasso Workflow — Bron van Waarheid

**Status:** officieel vastgesteld door Lisanne via Arsalan (sessie 133, 2026-05-06).
**Doel:** dit document is leidend. Toekomstige sessies mogen NIET zelf nieuwe stappen verzinnen of bestaande herbenoemen zonder expliciete bevestiging.

## Concept

Een **stap = status van het dossier**. Aan een stap is meestal (niet altijd) een email/brief-sjabloon gekoppeld. Het dossier doorloopt het hoofdpad automatisch tenzij debiteur reageert of Lisanne handmatig naar tussenstap schakelt.

## Hoofdpad (lineair, debiteur reageert niet)

Sjabloonbestanden staan in `templates incasso/` (repo root).

| # | Status | Sjabloon-bestand | Bijlage | Auto-volgende stap na |
|---|--------|------------------|---------|----------------------|
| 1 | Eerste sommatie | `SOMMATIE TOT BETALING _  _.eml` | — | 4 dagen geen reactie |
| 2 | Tweede sommatie | `TWEEDE SOMMATIE (GEEN VERWEER).eml` | — | 4 dagen geen reactie |
| 3 | Derde sommatie | `TWEEDE SOMMATIE (GEEN VERWEER).eml` *(zelfde sjabloon, andere status)* | — | 4 dagen geen reactie |
| 4 | Sommatie laatste mogelijkheid | `SOMMATIE AANKONDIGING FAILLISSEMENT.eml` | — | 4 dagen geen reactie |
| 5 | Verzoekschrift faillissement | `VERZOEKSCHRIFT FAILLISSEMENT (LAATSTE MOGELIJKHEID) _  _.eml` | Verzoekschrift PDF *(uit DOCX-bron, AI-gevuld)* | — eindstap |

**Standaard wachttijd tussen stappen:** 4 dagen.

## Auto-trigger statussen

### Verweer beantwoorden
- **Trigger:** Luxis detecteert inkomende email van debiteur
- **Actie:** dossier wordt automatisch op status "Verweer beantwoorden" gezet, hoofdpad pauzeert
- **Sjabloon:** `TWEEDE SOMMATIE INDIEN WEL VERWEER.eml` — Lisanne reageert hiermee op verweer
- **AI vult in:** verweer-respons in alinea op basis van inhoud inkomende mail + dossiercontext
- **Na afhandeling:** Lisanne markeert verweer als afgehandeld → dossier hervat hoofdpad waar het was, telling 4-dagen begint opnieuw vanaf laatste actie

## Verzoekschrift PDF — speciale flow

- **Bron:** `templates incasso/Template Verzoekschrift Bijlage.docx`
- **Regel:** origineel DOCX NOOIT wijzigen of verwijderen
- **Per zaak:** kopie maken → AI vult naam, bedrag, zaakgegevens, AV-context, dossier-historie → render naar PDF → attach aan verzoekschrift-email
- **Concept-PDF** `CONCEPT VERZOEKSCHRIFT FAILLISSEMENT (aangepast 1612).pdf` is referentie/visueel voorbeeld, NIET gebruiken voor productie

## Tussenstappen (handmatig door Lisanne)

Niet elke tussenstap heeft een sjabloon. Tussenstap onderbreekt hoofdpad; Lisanne kan handmatig terug naar hoofdpad zetten waarna telling hervat.

| Status | Sjabloon? |
|--------|-----------|
| Opvragen stukken bij cliënt | Optioneel |
| Voorstel dagvaarding | Optioneel |
| Treffen van regeling | Optioneel |
| Bijhouden regeling | Geen |
| Akkoord dagvaarden | Geen |

## AI-gedrag bij brief/email-generatie

1. **Layout** = exact zoals voorbeeld-sjabloon. Logo, briefhoofd, footer, ondertekening, opmaak — nooit afwijken.
2. **Standaardzinnen** (juridische formuleringen, openings/afsluiting, BIK-tekst) = niet aanraken.
3. **Situatie-specifieke alinea's** = AI personaliseert op basis van:
   - Naam + adres debiteur
   - Bedrag + factuurnummer
   - Algemene voorwaarden van cliënt
   - Eerdere correspondentie (in/uit + notities)
   - Dossier-historie (welke stappen al gedaan, betalingen, betwistingen)

**AI mag GEEN nieuwe layout of nieuwe schrijfstijl maken.** Template = baseline structuur, AI = invuller.

## Datamodel-implicaties (voor ontwikkelaars)

- **Pipeline:** lineair, geen branching state machine. Stappen hebben `sequence_number`, geen `transitions` tabel met meerdere edges.
- **Automation rules:** apart, niet als pipeline-edges. Patroon B+C uit sessie-133 onderzoek.
  - Rule: `no_response_4d` → action: `advance_to_next_step`
  - Rule: `incoming_email_from_debtor` → action: `move_to_status:verweer_beantwoorden` (pauzeert hoofdpad)
  - Rule: `verweer_afgehandeld` → action: `resume_main_pipeline`
- **Variant-sjabloon logica:** dossier heeft flag `had_debtor_reaction: bool`. AI-prompt kiest sjabloon op basis van flag.
- **Verzend-teller:** stap "Tweede sommatie" heeft veld `send_count` voor herhalingen, niet voor naamswijziging.

## Wat ontbreekt

Lisanne levert nog aan:
- Voorbeeld-DOCX/email per stap (Eerste sommatie, Tweede sommatie, Aankondiging faillissement, Verzoekschrift, Verweer beantwoorden, etc.)
- Eventuele extra timings die afwijken van 4-dagen-default

Tot upload: niet bouwen, niet gokken.
