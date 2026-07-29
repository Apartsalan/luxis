cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 250 — bouwlijst: mail-conventies + veegpunten

## Model
Start op **Fable** (`/effort max`) als er nog iets onderzocht/gepland moet worden;
wissel naar **Opus** (4.8 of 5 als beschikbaar) zodra er gebouwd/geklikt wordt, en
meld die wissel zelf. Bouwen op Fable en plannen op Opus zijn allebei fout — memory
`feedback_model_choice`.

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant
modules, laadt de verbindingskaart). Ga daarna zonder te wachten door met de taak.
Extra taak-context: entry S249 in SESSION-NOTES (doorlichting kennisregel-keten).

## Werkregel deze sessie (memory `feedback_standaard_conventies_eerst`, S249)
Bij functionaliteit die al lang bestaat (mail, lijsten): NIET het losse gevraagde
stukje bouwen. Eerst kort onderzoeken hoe gevestigde partijen (Gmail/Outlook/
HubSpot e.a.) dit gebied oplossen, dan het COMPLETE beeld in één keer neerzetten;
wat buiten de opdracht valt als voorstel melden, niet ongevraagd bouwen.

## Taak (in deze volgorde, elk een eigen commit)

### 1. Gespreksregels correspondentie op conventie-niveau (hoofdtaak)
Bron: `frontend/src/app/(dashboard)/zaken/[id]/components/CorrespondentieTab.tsx`
(gespreksregel bestaat in een BREDE variant `md:flex` én een SMALLE variant, ~regel
686–749 — allebei aanpassen).

Probleem dat Arsalan zag: een gesprek toont één richting-pijl, en die hoort bij het
LAATSTE bericht. Stuur je een sommatie en de debiteur antwoordt, dan zie je alleen
het inkomend-pijltje — alsof jij nooit iets stuurde.

Bouw de mail-conventie (compleet beeld, niet alleen het pijltje):
- **Deelnemers i.p.v. richting-pijl** — toon de namen in het gesprek, eigen berichten
  als "ik" (bv. "ik, Jansen (3)"). Nu staat er `naam = direction==inbound ? from : to`.
- **Voorbeeldregel (snippet)** — grijs stukje van het laatste bericht ná het onderwerp,
  zoals elk mailprogramma. `thread.latest.snippet` is er al.
- **Alleen-verstuurd gesprek** — zonder antwoord: "Aan: Jansen" i.p.v. kaal "ik".
- **Datum-notatie** — nameten of `formatDateTime(..,"short")` al vandaag=tijd /
  dit-jaar="12 jul" / ouder=volledige datum doet; zo niet, meenemen.
Behoud: vet + blauwe stip = ongelezen, aantal "(3)", paperclip, Review-badge, datum
rechts, nieuwste bovenaan. In het geopende gesprek blijft de per-bericht richting-pijl
staan (daar is het één bericht per regel — correct).

### 2. "X dagen te laat" weg bij afgeronde taken
Cosmetisch: een afgeronde taak toont nog "X dagen te laat" in de regel. Bron:
Taken-pagina `frontend/src/app/(dashboard)/taken/page.tsx`. Alleen tonen bij open taken.

### 3. Melding mislukte geplande mail breder dan alleen inplanner
Nu gaat de faalmelding van een mislukte geplande verzending alleen naar wie hem
inplande; wordt die inactief, ziet niemand het. Bron: `email/scheduled_service.py`
(zoek waar de faalmelding wordt aangemaakt). Overweeg tenant-breed of naar actieve
gebruikers, consistent met de bak-melding (S240). Kruispunt-check: skill `breed-testen`.

### 4. Kostenblokje (als er tijd is)
AI-uitgaven zichtbaar maken in het dashboard (`ai_usage`-tabel bestaat). Eerst kort
plan voorleggen — dit is een nieuwe weergave, geen pure fix.

## Verificatie
- Frontend: `cd frontend && npx tsc --noEmit`; visueel op prod met Playwright
  (desktop + mobiel 390×844), screenshots ook echt bekijken.
- Backend (bij taak 3): `docker compose exec backend python -m pytest tests/ -k "scheduled"`.
- Lint: `uvx ruff check backend/app/`.
- Kruispunt-check skill `breed-testen` bij taak 3 (gedeeld mail-effect).

## Constraints (wat NIET doen)
- Geen echte debiteuren mailen; testen alleen op testdossiers (2026-00006/…-00015),
  netjes terugzetten.
- Geen kennisregels aanraken — machine is af, wacht op inhoud Lisanne (S249).
- Geen inhoudelijk dossierwerk — signaleren, niet oppakken (rolverdeling S240).
- Nieuwe weergave (taak 4) → eerst plan + goedkeuring.
- KvK: niet naar vragen. · Nooit `git add -A` — expliciete paden.

## Commit
Per onderdeel een conventional commit + push. Deploy automatisch via SSH; login 200;
CI groen natrekken. Afsluiten met `/sessie-einde` (volgende prompt = PROMPT-S251).
