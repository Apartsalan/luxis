cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 253 — Arsalan kiest: ontwerpspoor of beveiliging

## KOERSREGEL (Arsalan, 30 juli — geldt vanaf nu elke sessie)
**Geen nieuwe features.** Luxis moet áf: alles wat er staat afmaken en verbeteren.
Voorstellen zijn herstel-/afmaakklussen (bugs, bestaande fouten rechtzetten, beveiliging
van bestaand werk, data goed zetten). Nieuwbouw alleen als Arsalan erom vraagt of als het
echt niet anders kan. Twijfel → adviseer "niets doen" en zeg dat gewoon.

## Model
Start op **Fable** voor het eerste kwartier (afvinken + keuze bespreken). Kiest Arsalan
een bouwtaak → **actief melden dat je naar Opus wisselt** vóór je begint (memory
`feedback_model_choice`; in S252 ging dat mis en moest Arsalan het zeggen).

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant modules,
laadt de verbindingskaart). Ga daarna zonder te wachten door.
Extra taak-context, alleen bij keuze C: `docs/plans/ONTWERP-kleur-en-leesbaarheid-S250.md`.

## Eerst afvinken (5 minuten, geen keuze nodig)
**Mobiele controle sjabloonmenu (390×844).** In S252 niet gelukt: het testbrowservenster
zakte naar viewport 0x0 en de extensie viel om. Open een dossier → "E-mail versturen" →
sjabloon-keuzelijst op telefoonformaat, screenshot écht bekijken. Verwacht: groepen 0-5
netjes leesbaar, geen overloop. Lukt de resize weer niet → dan Playwright, of meld het en
laat het los (cosmetisch, laag risico).

## Taak — Arsalan kiest C of D
- **C. Ontwerpspoor kleur & leesbaarheid** (`docs/plans/ONTWERP-kleur-en-leesbaarheid-S250.md`).
  Stap 0 = oud-naast-nieuw voorbeeldpagina, pas bouwen na akkoord. Gemeten aanleiding:
  5 contrastfouten onder de norm 4,5 en de zwevende Timer-knop die inhoud afdekt.
  Verbeteren van bestaande schermen — past binnen de koersregel.
- **D. Beveiligingsknopjes** (rest uit de Kimi-scan S248): aparte `TOKEN_ENCRYPTION_KEY`
  (**verbreekt Lisanne's mailkoppeling — moment mét haar plannen, zij moet daarna
  herverbinden**) en kennisregel-endpoints admin-only. Afmaken van bestaand werk.

## Openstaand voor Lisanne (signaleren, niet oppakken — rolverdeling S240)
- Menu-vraag: horen 'aanmaning' (het prod-anker van stap 2, staat nu onder "Overig") en de
  losse 'tweede_sommatie' in menugroep 2? Inhoudelijke keuze, geen technische.
- Kaandorp (IN100077) staat op "Akkoord dagvaarden" en betwist alles fel: groepsrechtszaak
  tegen Incassocenter, FTM/BOOS-onderzoeken, "zie een dagvaarding met vertrouwen tegemoet".
  Context vóór het dagvaarden — haar werk, niet dat van deze sessie.

## Constraints (wat NIET doen)
- Geen nieuwbouw (zie koersregel). Nieuwe weergave → eerst plan + goedkeuring.
- Geen echte debiteuren mailen; testen op testdossiers (2026-00006/…-00015), netjes terug.
- Fase-heropening 406: NIET starten zonder GO per groep. Komt die GO, dan hoort er nu een
  **etiket-controle** vooraf: bij 105 gesloten dossiers zegt de BaseNet-fasenaam "B2C"
  terwijl ons etiket "zakelijk" is (S252-meting) — eerst per groep vergelijken.
- Geen kennisregels aanraken (machine af, wacht op inhoud Lisanne). KvK: niet naar vragen.
- Geen inhoudelijk dossierwerk. Nooit `git add -A` — expliciete paden.

## Verificatie
- Frontend: `cd frontend && npx tsc --noEmit`; visueel op prod (desktop + mobiel 390×844),
  screenshots ook echt bekijken.
- Backend: `docker compose exec backend python -m pytest tests/ -k "<module>"` — één run
  tegelijk (parallelle runs botsen op de test-DB).
- Lint: `uvx ruff check backend/app/`.
- Geld geraakt? → wachters draaien: `test_brief_bedragen_gelijk_aan_scherm.py`,
  `test_b2c_kosten_grendel.py`, `test_bik_staffel_sweep.py`.

## Commit
Per onderdeel een conventional commit + push. Deploy automatisch via SSH; login 200;
CI groen natrekken. Afsluiten met `/sessie-einde` (volgende prompt = PROMPT-S254).
