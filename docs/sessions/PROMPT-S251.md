cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 251 — bel-labels + jouw keuze uit de openstaande lijst

## Model
Start op **Fable** (`/effort max`) als er nog iets onderzocht/gepland moet worden;
wissel naar **Opus (5)** zodra er gebouwd/geklikt wordt, en meld die wissel zelf.
Bouwen op Fable en plannen op Opus zijn allebei fout — memory `feedback_model_choice`.

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities, scant modules, laadt de
verbindingskaart). Ga daarna zonder te wachten door met de taak.
Extra taak-context: entry S250 in SESSION-NOTES (mail-conventie + kantoorbrede faalmelding).

## Taak 1 (klein, eerst) — twee meldingstypen missen hun label in de bel
`frontend/src/hooks/use-notifications.ts`: `NOTIFICATION_TYPE_CONFIG` kent
`scheduled_email_failed` (mislukte geplande mail) en `bik_above_staffel` niet. Beide
vallen daardoor terug op grijs "Systeem" met een info-icoon — juist de twee meldingen
die om aandacht vragen. Voeg ze toe aan het type-union én de config met een passend
label/icoon/kleur (rood/amber), in de stijl van de bestaande regels. Controleer met een
echte melding in de bel op prod of het klopt.

## Taak 2 — Arsalan kiest de hoofdtaak
Openstaand (roadmap §Huidige prioriteit): fase-heropening per groep
(`docs/plans/BASENET-STATUS-HERSTEL.md`, 406 dossiers — GO per groep nodig), aparte
TOKEN_ENCRYPTION_KEY (verbreekt Lisanne's mailkoppeling), kennisregel-endpoints
admin-only, verweer-parkeerstap-voorstel, rest voorstel-lijst, opmaak-restpunt S227,
S221b-rest, DMARC, 4 restjes S235.

Kostenblokje bewust uitgesteld tot er een volle maand echte cijfers ligt (S250-meting:
1 week, $6,53 waarvan >helft testverkeer).

## Werkregel
Bij functionaliteit die al lang bestaat (mail, lijsten, agenda): niet het losse gevraagde
stukje bouwen, maar eerst kort kijken hoe Gmail/Outlook/HubSpot dit oplossen en het
complete beeld in één keer neerzetten; wat buiten de opdracht valt = voorstel, geen actie.

## Verificatie
- Frontend: `cd frontend && npx tsc --noEmit`; visueel op prod met Playwright
  (desktop + mobiel 390×844), screenshots ook echt bekijken.
- Backend: `docker compose exec backend python -m pytest tests/ -k "<module>"`.
- Lint: `uvx ruff check backend/app/`.
- Kruispunt-check skill `breed-testen` zodra een gedeeld effect geraakt wordt.

## Constraints (wat NIET doen)
- Geen echte debiteuren mailen; testen alleen op testdossiers (2026-00006/…-00015),
  netjes terugzetten.
- Geen kennisregels aanraken — machine is af, wacht op inhoud Lisanne.
- Geen inhoudelijk dossierwerk — signaleren, niet oppakken (rolverdeling S240).
- Nieuwe weergave → eerst plan + goedkeuring.
- KvK: niet naar vragen. · Nooit `git add -A` — expliciete paden.

## Commit
Per onderdeel een conventional commit + push. Deploy automatisch via SSH; login 200;
CI groen natrekken. Afsluiten met `/sessie-einde` (volgende prompt = PROMPT-S252).
