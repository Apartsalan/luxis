cd Documents\luxis && claude --dangerously-skip-permissions

# Luxis — vervolg op demo Lisanne (13 juli). FABLE neemt over.

Lees eerst: SESSION-NOTES.md (entry "demo Lisanne" + de 4 kopregels), `docs/ARCHITECTUUR-KAART.md`,
en de memory `session_2026-07-13_luxis_demo`. De vorige (Opus-)sessie heeft LIVE gezet:
rentecorrectie 2%/mnd **samengesteld** (matcht BaseNet IN100197 op de cent, 598 dossiers) + 6
demo-punten (adres, 24 regelingen, rentedatum-bevriezing, heropenen bij nieuwe factuur,
factuur-prompt). Migratie `s207b_interest_freeze_date` is toegepast.

Jij bent Fable: eerst meten in de bron, jezelf weerleggen, dán handelen.

## Hoofdtaak (in deze volgorde)

1. **Review deze bouwsprint** (adversarieel). Kernpunten om te toetsen:
   - `calculate_monthly_compound_interest` (backend/app/collections/interest.py) — klopt de
     kapitalisatie/afronding tegen de BaseNet-spec? Randgevallen (creditfactuur, betaling op
     verzuimdatum, maandgrens op de 31e). Tests: `test_interest_monthly.py`, `test_interest_freeze_date.py`.
   - De rente-uitrol raakte óók gesloten zaken → zie punt 2.
2. **Backfill bevriesdatum op de ~574 gesloten zaken** = de juiste ingreep (het moet in de
   huidige tijd kloppen; niets "openlaten"). Zet `Case.interest_freeze_date` = laatste betaaldatum
   (of `date_closed` als er geen betaling is) op elke zaak met status afgesloten/betaald. Dry-run +
   backup + rollback, net als `rollout_av_rente.py`. Meet vooraf hoeveel zaken/euro dit verschuift.
   De 100 "€22k spookrestant"-zaken gaan hierin mee; wat dan nog rest = verschil oude-vs-nieuwe
   rente, per-zaak signaal voor Lisanne (géén bulk-afboeking zonder haar akkoord).
3. **WIK-bijlage** (demo-punt 6). Renteberekening-PDF bij de EERSTE sommatie, **alleen bij VOF,
   eenmanszaak, particulier/consument** (WK-partij). Uitzoeken: (a) klopt de WIK-eis juridisch +
   voor precies wie; (b) is er een KvK-API om de rechtsvorm op te halen (kosten/haalbaarheid);
   (c) Lisanne's template invullen per debiteur + als bijlage meesturen. Eerst plan, dan bouwen.
4. **Invoer-map met nieuwe zaken** — die zaten NIET in de export van 2 juli (nieuwer). Uitzoeken
   hoe we die overhalen (verse export nodig? handmatig?).

## Grenzen
- Prod-datamutaties (backfill, correcties): eerst dry-run + akkoord Arsalan, per geval.
- Mailslot staat DICHT — niet openzetten.
- Aparte S207-track (L4/L5/L6 + M4, `docs/sessions/PROMPT-S207.md`) staat hier LOS van — niet mengen.
- Taal naar Arsalan: gewoon Nederlands, geen vaktermen (harde regel).
