cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 218 — UX-sprint menu-doorlichting (S217-bevindingen)

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant modules,
laadt de verbindingskaart). Ga daarna zonder te wachten door met de taak hieronder.
Extra taak-context: SESSION-NOTES entry **S217** (de doorlichting waar deze taken uit komen).

## ⚠️ Voorrang-check EERST
Vraag Arsalan: **is de KvK-productiesleutel binnen?**
- JA → doe eerst de KvK-rechtsvorm-backfill (stappen + kosten in `docs/sessions/PROMPT-S217.md`;
  726 relaties, ~€14,50 per run, overweeg 1 echte run met vooraf-akkoord i.p.v. dry-run+run).
  Daarna pas de blokken hieronder, zover de sessie reikt.
- NEE → direct door met de blokken hieronder.

## Context (gemeten in S217, niet opnieuw uitzoeken)
- Follow-up: werkt end-to-end (bewezen met testsommatie), maar 15 échte aanbevelingen staan
  onbeoordeeld; UI-gaten hieronder.
- Intake: 17 kandidaten ooit, 0 echte zaak — ruis; Mail-pagina heeft al een tabblad "Aanvragen"
  met dezelfde wachtrij (`useIntakes` in `correspondentie/page.tsx`) → menu-item is dubbelop.
- Bankimport (menu → `/betalingen`): 0 uploads ooit; alle betalingen kwamen via scripts.
- Rapportages: KPI "incassoratio 4,7%" = geïnd/hoofdsom van alléén actieve zaken
  (`reports_service.py`, formule klopt, label misleidt).
- Agenda-blok dossier (`AgendaBlok.tsx`): rendert niets bij 0 toekomstige afspraken; er staat
  momenteel 0 actieve afspraak in heel Luxis → Lisanne ziet de functie nooit.
- Outlook-agendasync bestaat al: scheduler elk kwartier (`calendar_auto_sync`), werkt per
  gekoppeld outlook-account (seidony@ is gekoppeld; M365-agenda is leeg).

## Taak — blokken in deze volgorde, elk: bouwen → tsc/pytest → deploy → visueel checken

### Blok 1 — Follow-up bruikbaar maken (grootste dagelijkse waarde)
1. Dossiernummer in de tabel = directe link naar `/zaken/{case_id}` (niet pas na openklappen).
2. Kolom "Dagen" toont nu altijd "0d": laat hem de échte dagen-in-stap tonen, of haal de kolom weg
   als dat niet zinvol kan (meet eerst wat de bron is).
3. Kolomkoppen sorteerbaar (minimaal Bedrag, Stap, Dossier) — zelfde patroon als de dossierlijst
   (`zaken/page.tsx`); een stap-filter (Eerste sommatie / Voorstel dagvaarding / …) erbij.
4. Eén Playwright e2e-test: pagina laadt → rij openklappen → dossierlink klopt (NIET op Uitvoeren
   klikken in e2e — dat verstuurt echte mail).

### Blok 2 — Intake ont-dubbelen + ruis dempen
1. Menu-item "Intake" + badge verwijderen uit `app-sidebar.tsx`; de Mail-tab "Aanvragen" is
   voortaan de enige ingang (check dat de detailpagina `/intake/[id]` bereikbaar blijft vanaf die tab).
2. Ruis dempen: intake-detectie alleen laten vuren op afzenders die als relatie/opdrachtgever
   bekend zijn, óf de AI-drempel verhogen — kies wat in `ai_agent/intake_*` het kleinst en
   veiligst is. De 15 bestaande ruis-kandidaten (status detected/pending_review) afwijzen met reden.

### Blok 3 — Kleine labels & zichtbaarheid
1. Menu "Bankimport" hernoemen naar "Betalingen" (dekt de lading; de importknop staat al op de pagina).
2. Rapportages: label "Incassoratio" → iets als "Geïnd op lopende zaken" (+ tooltip die uitlegt
   waarom dit laag hoort te zijn), of toon de all-time ratio ernaast. Kleinste zinvolle ingreep.
3. Agenda-blok dossier: lege staat tonen ("Geen komende afspraken — [Afspraak plannen]" met knop
   die het nieuw-afspraak-venster opent met case vooringevuld) i.p.v. niets renderen.
4. Soft-deleted dossier via directe URL: toon een duidelijke "Dit dossier is verwijderd"-banner
   (read-only), zodat oude links/meldingen niemand verwarren.

## Verificatie
- Backend: `docker compose exec backend pytest tests/ -k "followup or intake" -v` (vol alleen bij refactors)
- Lint: `uvx ruff check app/` (lokaal, vóór push)
- Frontend: `cd frontend && npx tsc --noEmit && npm run build`
- Visueel op prod na deploy: follow-up sorteert/linkt, menu toont geen Intake meer, Betalingen-naam,
  agenda-lege-staat op een dossier.

## Constraints (wat NIET doen)
- NIET op "Uitvoeren" klikken bij de 15 échte follow-up-aanbevelingen (echte sommaties!).
  Beoordelen daarvan is werk voor Arsalan/Lisanne, niet voor deze sessie.
- Mailslot staat OPEN — niet dichtzetten, niet "even testen" met echte mail.
- Intake-detectielogica niet herbouwen; alleen dempen/filteren.
- Geen nieuwe afhankelijkheden.

## Commit
Per blok commit + push naar main (conventional commits, expliciete paden — NOOIT `git add -A`).
Deploy na push zelf via SSH (skill `deploy-regels`); frontend-blokken = alleen frontend rebuilden.
Sluit af met `/sessie-einde`.
