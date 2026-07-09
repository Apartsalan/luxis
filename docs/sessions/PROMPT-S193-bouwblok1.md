# Sessie-prompt S193 — Codex naast Claude opzetten, dan bouwblok 1 (Opus)

Kopieer alles onder de streep in een nieuwe sessie. **Model: Opus** — check na het
opstarten met `/model` dat je NIET op Fable zit (persoonlijke instelling start nu op
Fable; bouwen doen we op Opus).

---

cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 193 — Codex-werkmodel opzetten (taak 0), dan bouwblok 1

## Start
Draai eerst `/sessie-start`. Extra taak-context daarna:
- `docs/research/advies-codex-samenwerking.md` — het Codex-advies (voor taak 0)
- `docs/plans/PLAN-fase2-bouwblokken.md` — de besluiten + bouwblok 1
- `docs/research/audit-DB-kernmotor.md` — details B1 (verstuurpad, §Follow-up/Incasso)
  en B13; `docs/research/audit-DA-werkschil.md` — details A1 (eigenaarloze taken) en A2

## Taak 0 — EERST: Codex naast Claude werkend krijgen (verzoek Arsalan, 9 juli avond)
Arsalan wil dit als eerste geregeld: Codex (GPT-5.6) en Claude Code beide in deze
terminal gebruiken **zonder dat ze elkaar in de weg lopen** — hij is ervan overtuigd dat
dat schoon kan. Doel van dit blok:
1. **Installeren + inloggen** volgens het advies-doc: `npm install -g @openai/codex`
   (Node 22+, mét `@openai/`-scope) → `codex login` met zijn ChatGPT-account. Verifieer
   met `codex --version` en een mini-testopdracht (read-only).
2. **De al klaarliggende inrichting nalopen** (`.codex/` in de repo bestaat al:
   `config.toml`, `hooks.json`, agents). ⚠️ **Belangrijk vóór gebruik:** `.codex/config.toml`
   bevat nu leesbare API-sleutels (OpenAI, Milvus, Stitch, Tavily) in platte tekst.
   Bespreek met Arsalan: sleutels naar omgevingsvariabelen halen en/of `.codex/` in
   `.gitignore` (het staat nu untracked — nog niet gecommit, dat moet zo blijven tot de
   sleutels eruit zijn). Nooit die sleutels in een commit laten belanden.
3. **"Zonder elkaar in de weg lopen" concreet maken** — het model uit het advies vastleggen
   als werkafspraak (niet alleen praten): Claude is de enige die schrijft/commit/deployt;
   Codex draait **read-only** als tegenlezer (`--sandbox read-only` / geen `--yolo`).
   Kies de aanroep-route (directe `codex exec` + bestandsoverdracht is de aanbevolen,
   betrouwbaarste — MCP-koppeling nu niet). Vraag Arsalan hoe híj het voor zich ziet als
   hij zegt "er is een manier om allebei te gebruiken" — misschien bedoelt hij twee aparte
   terminals (Claude in de één, Codex in de ander) i.p.v. de één die de ander aanroept.
   Leg de gekozen afspraak vast in `docs/research/advies-codex-samenwerking.md` (sectie
   "Werkafspraak — vastgesteld 10 juli").
4. **Proefrit**: laat Codex read-only één bestaand stuk grillen — bv. het D-B-rapport of
   de bouwblok-1-diff zodra die er is (zie taak-koppeling hieronder). Beoordeel of de
   uitkomst bruikbaar is.
Pas als taak 0 staat: door naar bouwblok 1. Als Arsalan er bij is, kan Codex bouwblok 1
meteen als eerste echte tegenlezer gebruiken (grillt de diff vóór deploy).

## Taak 1 — Bouwblok 1 (4 werkorders, in deze volgorde)
1. **B1 — verstuurpad sommaties repareren.** De stap-sjabloonsleutels
   (`sommatie_drukte`, `faillissement_dreigbrief`) zijn e-mailsjablonen maar Follow-up-
   "Uitvoeren" en de Incasso-batch proberen er een DOCX mee te renderen → faalt; Follow-up
   markeert tóch "Uitgevoerd". Kies de route die het rapport aanraadt (e-mail/AI-concept-
   route) en zorg dat een gefaalde uitvoering NOOIT meer als geslaagd geregistreerd wordt.
   Eerst rode test die het maskeren aantoont, dan fixen.
2. **B13 — verzend-vangrails.** Vóór elke (batch)verzending: preview verplicht + vast
   afzenderkanaal (incasso@). Geen één-klik-verzenden zonder dat de gebruiker gezien
   heeft wat er uitgaat.
3. **B2 + A1 — verjaring zichtbaar.** Dossier-badge rekenen vanaf de verzuimdatum van de
   oudste vordering (zelfde bron als de monitor); monitor niet meer laten skippen op
   `date_closed`; verjaring-taken een eigenaar geven (of eigenaarloze taken tonen in
   Mijn Taken). IJkpunten uit de rapporten: IN100015 (al verjaard), IN100016
   (23-09-2026, €16.020), IN100064 (jun 2027).
4. **A2 — dashboardblok "Nieuwe Dossiers":** filter `pending` → `pending_review`.

## Verificatie (per werkorder, niet pas aan het eind)
- Backend: `docker compose exec backend pytest tests/ -k "<relevant>" -v` (alleen
  relevante modules; volle suite alleen bij gedeelde-code-wijzigingen)
- Lint: `uvx ruff check backend/app/` · Frontend (indien geraakt): `npx tsc --noEmit` + build
- Live doorklikken in de prod-app ná deploy (seidony@ / Hetbaken-KL-5)

## Constraints
- ⚠️ **MAILSLOT staat AAN en blijft AAN** — er mag niets echt verstuurd worden; B1/B13
  bewijzen via tests + preview, niet via een echte mail. Slot gaat er alleen af op
  expliciet verzoek van Arsalan (~13 juli).
- Alleen deze 4 werkorders — al het andere (stapel 2-5) heeft een eigen blok. Extra
  vondsten = noteren als voorstel, niet bouwen.
- Als Arsalan het stichting-IBAN + BTW-nummer doorgeeft (C2, toegezegd voor 10 juli):
  invullen mag via het Instellingen-scherm ná zijn expliciete akkoord op de waarden —
  dat is de enige toegestane prod-mutatie buiten de 4 werkorders.

## Commit + afronding
Per werkorder committen + pushen (conventional commits); deploy zelf via SSH
(skill `deploy-regels`), containers healthy checken. Afsluiten met `/sessie-einde`
(notities, roadmap, archiefregels, tag sessie-193). Review van dit blok: Fable zolang
beschikbaar (t/m 12 juli), anders Opus met fable-skills — en zodra Codex geïnstalleerd
is, mag die als extra tegenlezer meekijken (alleen-lezen).
