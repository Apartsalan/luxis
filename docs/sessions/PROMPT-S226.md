cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 226 — Punten Arsalan + testvondsten S225 + S221b-restant

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant
modules, laadt de verbindingskaart). Ga daarna zonder te wachten door.
Model: **Opus** (bouwen). Extra context: `docs/sessions/S225-testronde.md`
(alle vondsten + testdata-overzicht).

## ⚠️ Voorrang-check EERST
KvK-productiesleutel binnen (~22 juli)? JA → eerst de rechtsvorm-backfill
(`docs/archief/prompts/PROMPT-S217.md` + STAND in `PROMPT-S215.md`), dán de rest.
NEE → direct door.

## Taak A — Punten Arsalan (17/7)
1. **AI-antwoord-knop op dossierniveau:** dezelfde knop + instructieveld +
   toon-keuze als op de Mail-pagina (S223), maar dan op het tabblad
   Correspondentie van het dossier, bij inkomende mails. Zelfde dialoog/
   spelregels (component delen, niet kopiëren). ⚠️ Nieuwe route voor het effect
   "concept maken" → kruispunt-matrix (skill `breed-testen`) + brede test
   verplicht: afzender, drieluik, onderwerp, P1 (antwoord schuift zaak niet
   door), zichtbaarheid op alle pagina's.
2. **Verweerreactie-aanhef:** gemeten S225 — de 103 bibliotheek-antwoorden
   hebben 0× een aanhef; de 6 beheerde reactiesjablonen zeggen "Geachte
   {{ wederpartij.naam }}," i.p.v. de S220-keuze "Geachte heer, mevrouw,".
   Eerst uitzoeken of de aanhef bij écht versturen wordt aangevuld (weergave-
   kwestie) of echt ontbreekt in de mail; dan gelijktrekken naar "Geachte
   heer, mevrouw," (S220-lijn).
3. **Betreft-regel ÍN de brieven:** draagt nog het BaseNet-formaat "SOMMATIE
   TOT BETALING / {nr} / {debiteur}" — 7 plekken in
   `email/incasso_templates.py` + de stap-teksten-vulling in
   `incasso/html_renderer.py`. Gewenst formaat Arsalan: "klant / debiteur —
   Sommatie tot betaling — ons dossiernummer". Let op: dit is de regel in de
   brieftekst; het mail-ONDERWERP is al huisformaat. Alle brieftypen meenemen
   (ook WEDEROM/LAATSTE MOGELIJKHEID-varianten), wachter-test voor de soort.

## Taak B — Testvondsten S225
4. **Gmail filtert zware brieven stilletjes weg (onderzoek eerst):** 25
   sommaties/aanmaningen/14-dagenbrief kwamen direct aan, maar de
   dagvaarding-PDF-mail en beide dreigbrieven niet — ook niet in spam, geen
   bounce, wel geaccepteerd door smtp.basenet.nl. Check SPF/DKIM/DMARC van
   kestinglegal.nl op de BaseNet-SMTP-route; check bounce-logboek alsnog.
   Dit raakt échte debiteuren met gmail.
5. **Dossiernummer-hergebruik:** nummers van verwijderde dossiers worden
   hergebruikt → de mailsync plakt oude mails met dat nummer aan het nieuwe
   dossier (2× waargenomen). Fixrichting: teller nooit hergebruiken, óf de
   matcher maildatum vs. dossier-aanmaakdatum laten vergelijken.
6. **Testdata opruimen:** dossiers 2026-00007 t/m 2026-00019 + 13
   TEST-contacten + 12 taken "Tweede sommatie genereren" (dry-run/telling +
   GO). Testdossier 2026-00006 blijft ACTIEF (vast testkanaal, besluit B5).
   NB: rechtsvorm-afkorting "bv" wordt niet herkend als beperkt aansprakelijk
   (veilige kant) — geen actie nodig, KvK-backfill lost op.

## Taak C — S221b-restant (zoveel als past)
Review-scherm classificatie+concept naast elkaar; voortgangsindicator bij
genereren; échte HTML-tabellen in AI-mails (injectie-oppervlak — behoedzaam);
tijdlijn-mailregel klikbaar (eerst id-betekenis verifiëren); follow-up
sorteerbare koppen (server-side sortering); intake-detectie dempen;
Blok 6-beslismemo b2b/b2c (105 dossiers, geen code).

## Constraints
Geen echte debiteuren mailen (testkanaal: 2026-00006 = Arsalans gmail).
Prod-mutaties: dry-run/telling + GO. Geen `git add -A`. Bayar IN100613 NIET
aanraken (B4 — Arsalan bekijkt zelf). Kruispunt-check (skill `breed-testen`)
bij elk gedeeld effect.

## Verificatie
- Backend: relevante `pytest` (detached bij full suite), `uvx ruff check app/`.
- Frontend: `npx tsc --noEmit`.
- CI groen na push (`gh run list`) — vaste afsluitcheck.

## Afsluiten
`/sessie-einde` (SESSION-NOTES max 10 entries + roadmap één-prioriteit + git
tag + PROMPT-S227).

## Nog open na S225
- Auto-concept-gate: menselijke steekproef Lisanne (~10 echte concepten) vóór
  activering.
- V2c (klein): classificatie-antwoord-onderwerp naar `build_reply_subject`.
- KvK-backfill zodra sleutel binnen (~22 juli) — houdt voorrang.
