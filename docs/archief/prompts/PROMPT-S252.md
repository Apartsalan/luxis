cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 252 — S251-restjes (bel-labels + verstuur-later-bedragen) + jouw keuze

## Model
Start op **Opus (5)** — de eerste twee taken zijn bouwen. Komt er onderzoek of een
plan bij (optie B/C), wissel dan naar Fable en meld dat zelf (memory
`feedback_model_choice`).

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities, scant modules, laadt de
verbindingskaart). Ga daarna zonder te wachten door met de taak.
Extra taak-context: `docs/audits/geld-audit-2026-07-29.md` (de S251-audit — lees de
secties "Wat er is gebouwd" en "Openstaand voor Lisanne" voor de stand van zaken).

## Vragen die S251 openliet (eerst kort afhandelen)
1. **IN100077** (Incassocenter, actief) staat op wettelijke rente i.p.v. de
   contractuele 2%/mnd die alle andere bureau-dossiers hebben. Vraag Arsalan/Lisanne:
   bewust? Zo nee: omzetten (klein).
2. **IN100605**: de oude € 0,00-afspraak is op besluit Arsalan (S251) 15% geworden —
   alleen melden bij Lisanne, geen actie.

## Taak 1 (klein, uit S251 blijven liggen) — bel-labels
`frontend/src/hooks/use-notifications.ts`: `NOTIFICATION_TYPE_CONFIG` kent
`scheduled_email_failed` en `bik_above_staffel` niet → grijs "Systeem" met
info-icoon. Voeg beide toe aan het type-union én de config (passend label/icoon,
rood/amber), in de stijl van de bestaande regels. Controleer met een echte melding
op prod (er staan `bik_above_staffel`-meldingen in de bel-historie).

## Taak 2 — "Verstuur later" met verse bedragen (voorstel S251, GO Arsalan gevraagd)
Een geplande mail bevriest nu de bedragen op het inplanmoment: plan vandaag, verzend
over 3 dagen → de rente in de brief is 3 dagen oud. Voorstel: bij het ECHTE
verzendmoment de bedragen-tabel opnieuw renderen via de gedeelde rekenroute
(`case_calc_kwargs`, S251) — alleen voor stap-brieven met een bedragen-tabel; een
vrij geschreven antwoord blijft letterlijk wat Lisanne schreef. **Eerst kort plan +
akkoord** (raakt de wachtrij-bezorger, skill `breed-testen`: zelfde poorten als de
S246-lopende-band).

## Taak 3 — Arsalan kiest
- **A. Sjabloonmenu gelijktrekken** met de 5 pijplijnstappen (S251-vondst: de brief
  "Tweede sommatie (standaard herhaling)" telt intern als dérde sommatie → stap
  schuift niet door). Vraagt één afstemmingsrondje welke brief bij welke stap hoort.
- **B. Fase-heropening per groep** (`docs/plans/BASENET-STATUS-HERSTEL.md`, 406
  dossiers — GO per groep; 153 daarvan hebben de rentemeter bevroren op de
  openingsdatum, heropening zet status én rente in één keer goed).
- **C. Ontwerpspoor kleur & leesbaarheid** (`docs/plans/ONTWERP-kleur-en-leesbaarheid-S250.md`,
  ligt klaar; stap 0 = oud-naast-nieuw voorbeeldpagina, pas bouwen na akkoord).
- **D. Beveiligingsknopjes**: aparte TOKEN_ENCRYPTION_KEY (verbreekt Lisanne's
  mailkoppeling — plan het moment), kennisregel-endpoints admin-only.

## Verificatie
- Frontend: `cd frontend && npx tsc --noEmit`; visueel op prod met Playwright
  (desktop + mobiel 390×844), screenshots ook echt bekijken.
- Backend: `docker compose exec backend python -m pytest tests/ -k "<module>"` —
  één run tegelijk (S251-les: parallelle runs botsen op de test-DB).
- Lint: `uvx ruff check backend/app/`.
- Geld geraakt? → wachters draaien: `test_brief_bedragen_gelijk_aan_scherm.py`,
  `test_b2c_kosten_grendel.py`, `test_bik_staffel_sweep.py`.

## Constraints (wat NIET doen)
- Geen echte debiteuren mailen; testen op testdossiers (2026-00006/…-00015), netjes
  terugzetten. Weiger-toetsen op een dossier waar de grens ÉCHT overschreden wordt
  (S251-incident: een "veilige" poging schrijft gewoon door).
- Geen kennisregels aanraken — machine af, wacht op inhoud Lisanne.
- Geen inhoudelijk dossierwerk — signaleren, niet oppakken (rolverdeling S240).
- Nieuwe weergave → eerst plan + goedkeuring. · KvK: niet naar vragen.
- Nooit `git add -A` — expliciete paden.

## Commit
Per onderdeel een conventional commit + push. Deploy automatisch via SSH; login 200;
CI groen natrekken. Afsluiten met `/sessie-einde` (volgende prompt = PROMPT-S253).
