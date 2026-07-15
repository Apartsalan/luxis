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

## Beslissingen vooraf ophalen bij Arsalan (bundelen)
1. **Auto-concept per categorie (Blok 4.2):** welke inkomende-mail-categorieën mogen
   automatisch een concept klaarzetten (nooit auto-versturen)? Nu staat alles UIT
   behalve verweer (`orchestrator.py:78`).
2. **Timeout Eerste→Tweede 7→4 dagen (Blok 4.5):** GO voor de ene UPDATE in
   step_transitions? (stap-wachttijd = 4, workflow Lisanne = 4).
3. **Backfills (Blok 3.3):** GO om te sluiten: 3 verouderde adviezen
   (IN100607/IN100613/IN100521) + 470 pending classificaties (import-ruis vóór 13-07)
   + 14 intake-ruiskandidaten + 8 verouderde AI-concepten (oud adres). Dry-run + telling eerst.
4. **Sjabloon-herzaaiingen:** GO voor Courier→Calibri (DOCX-default) + verzoekschrift-
   bijlage vervangen door "CONCEPT VERZOEKSCHRIFT FAILLISSEMENT (aangepast 1612).pdf"
   uit de projectmap (S210-reseed-flow: backup DB-sjablonen → gerichte reseed).

## Blokken (aflopend risico/waarde)

### Blok 3 (rest)
- **3.2 Dedupe concepten:** nieuwe conceptgeneratie voor dezelfde zaak+stap toont het
  bestaande concept i.p.v. een tweede te maken (`ai_drafts` mist stap-koppeling —
  kolom toevoegen of matchen op case+subject). IN100521 had er 2 identiek.
- **3.4 Skipped-taken:** weergave voor overgeslagen taken (18 onzichtbaar) +
  herstel-knop (skipped/completed → pending) + undo-toast direct na de pijltjes-klik.
- **3.3 Backfills:** uitvoeren na GO (zie boven).

### Blok 4 — AI-keten
- Classificatie direct ná mailsync triggeren (race weg; latency → ~5 min).
- Auto-concept per categorie AAN (na beslissing).
- **Antwoord-route begrip-eerst (punt 21):** AI leest inkomende mail + volledige
  dossiercontext en schrijft zélf het antwoord met spelregels (niets verzinnen, geen
  toezeggingen, bedragen alleen uit dossier, bij twijfel escaleren). Typen/bibliotheek =
  referentie, geen dwang. Test met de echte IN100607-mail. **Sluitstuk: testronde-script
  uit `docs/plans/PLAN-ai-antwoord-testronde.md`** (goud-set + genereer-script + checklist;
  niets versturen/op echte dossiers). Bouw het script; analyse-iteraties = Fable (S222).
- Voortgangsindicator bij genereren + bestaand-concept-check (3.2).
- Timeout 7→4 (na GO). Eén review-scherm classificatie+concept naast elkaar.
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
