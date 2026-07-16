cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 221 — Bouwsprint demolijst DEEL 2 (Opus) — restant na S220

## Start
Draai eerst `/sessie-start`. Context: S220 heeft Blok 1 (verzendpad-fundament),
Blok 2 (stap-teksten & sjablonen) en Blok 3.1 (zombie-opruiming) + Blok 5-fasebalk
LIVE gezet en op prod geverifieerd — zie SESSION-NOTES S220 en `docs/sessions/
S219-onderzoek.md` (alle vindplaatsen). NIET opnieuw uitzoeken wat daar staat.

## ⚠️ Voorrang-check EERST
KvK-productiesleutel binnen? JA → eerst de rechtsvorm-backfill
(`docs/archief/prompts/PROMPT-S217.md`), daarna dit. NEE → direct door.

## Beslissingen (Arsalan, 15-07 einde S220)
1. ✅ **Timeout Eerste→Tweede 7→4: GEDAAN in S220** (step_transitions id
   44c31bf7-4e17-44f9-b47c-38442bf8aafd, condition `{"days": 4}`, geverifieerd). Niets meer doen.
2. **Auto-concept per categorie (Blok 4.2):** AAN voor **Verweer** (staat al) +
   **Algemene vraag/overig**. Arsalan's kanttekening: nut hangt af van de antwoord-
   KWALITEIT → doe dit PAS ná de begrip-eerst-antwoord-route (Blok 4.3) goed werkt en
   getoetst is; niet daarvoor aanzetten.
3. **Backfills (Blok 3.3): NIET zelf uitvoeren.** Arsalan wil eerst dat Fable uitzoekt
   wát die items precies zijn (3 adviezen / 470 classificaties / 14 intake / 8 concepten)
   vóór er iets gesloten wordt. → Fable-taak (S222), niet in de Opus-bouw.
4. **Sjabloon-herzaaiingen:** nog GO vragen — Courier→Calibri (DOCX-default) +
   verzoekschrift-bijlage vervangen door "CONCEPT VERZOEKSCHRIFT FAILLISSEMENT
   (aangepast 1612).pdf" uit de projectmap (S210-reseed-flow: backup DB-sjablonen →
   gerichte reseed).

## Blokken (aflopend risico/waarde)

### Blok 3 (rest)
- **3.2 Dedupe concepten:** nieuwe conceptgeneratie voor dezelfde zaak+stap toont het
  bestaande concept i.p.v. een tweede te maken (`ai_drafts` mist stap-koppeling —
  kolom toevoegen of matchen op case+subject). IN100521 had er 2 identiek.
- **3.4 Skipped-taken:** weergave voor overgeslagen taken (18 onzichtbaar) +
  herstel-knop (skipped/completed → pending) + undo-toast direct na de pijltjes-klik.
- **3.3 Backfills:** NIET in de Opus-bouw — Fable zoekt eerst uit wát de items zijn
  (beslissing Arsalan). Pas daarna eventueel opruimen.

### Blok 4 — AI-keten
- Classificatie direct ná mailsync triggeren (race weg; latency → ~5 min).
- Auto-concept per categorie AAN voor Verweer + Algemene/overig — PAS ná de
  antwoord-route hieronder goed werkt (beslissing Arsalan).
- **Antwoord-route begrip-eerst (punt 21):** AI leest inkomende mail + volledige
  dossiercontext en schrijft zélf het antwoord met spelregels (niets verzinnen, geen
  toezeggingen, bedragen alleen uit dossier, bij twijfel escaleren). Typen/bibliotheek =
  referentie, geen dwang. Test met de echte IN100607-mail. **Sluitstuk: testronde-script
  uit `docs/plans/PLAN-ai-antwoord-testronde.md`** (goud-set + genereer-script + checklist;
  niets versturen/op echte dossiers). Bouw het script; analyse-iteraties = Fable (S222).
- Voortgangsindicator bij genereren + bestaand-concept-check (3.2).
- (Timeout 7→4 is al gedaan in S220.) Eén review-scherm classificatie+concept naast elkaar.
- **AI-concept-HTML-tabellen (punt 11):** prompt laten HTML-tabellen maken i.p.v.
  spatie-uitlijning (SYSTEM_PROMPT in `ai_agent/incasso_email_prompts.py`).

### Blok 5 — UX-rest
- Zaaknummer klikbaar in de mail-LIJSTrij (detailpaneel heeft de link al, punt 18).
- Tijdlijn-mailregel klikbaar → preview (kan nu, logging staat live, punt 17).
- S218-restanten: menu-item Intake weg (Mail-tab "Aanvragen" is de ingang) +
  intake-detectie dempen; menu "Bankimport" → "Betalingen"; rapportage-label
  "Incassoratio" → "Geïnd op lopende zaken" + tooltip; agenda-blok lege staat;
  soft-delete-banner op verwijderd dossier; follow-up dossiernummer-link in de tabel +
  echte dagen-kolom + sorteerbare koppen.

### Blok 6 — Beslismemo b2b/b2c (geen code)
Memo voor Lisanne: 105 BaseNet-B2C-spoor-dossiers (lijst per dossier uit
`Xml_02-07-2026_2400.zip`), wat verandert bij omzetten (14-dagenbrief-plicht, BIK+BTW,
consumentenrente, WIK-bijlage), advies + vraag. Koppel aan de KvK-backfill.

## Verificatie
Per blok: backend `pytest -k "..."` (vol alleen bij refactors), `uvx ruff check app/`;
frontend `npx tsc --noEmit`. Per blok visueel/functioneel op prod. Verzend-tests ALLEEN
naar eigen adressen (testdossier 2026-00006 = Arsalans gmail).

## Constraints
Geen echte debiteuren mailen. Prod-data-mutaties: dry-run/telling + GO. Geen nieuwe
deps. Geen `git add -A` (expliciete paden). Beslispunten niet zelf beslissen — vragen.

## Commit / afsluiten
Per blok commit + push + deploy via SSH. Sluit af met `/sessie-einde`; daarna
Fable-review van S220+S221 (VERPLICHT vóór echte inzet).
