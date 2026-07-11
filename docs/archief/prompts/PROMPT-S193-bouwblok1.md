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

## Taak 0 — ✅ KLAAR (S192, 10 juli). Codex staat.
Codex bleek al geïnstalleerd (OpenAI desktop-app) + ingelogd op Arsalans ChatGPT-account
(`gpt-5.6-sol`/`ultra`). Werkafspraak vastgelegd in `docs/research/advies-codex-samenwerking.md`
(sectie "Werkafspraak vastgesteld 10 juli"). **Besluit: volledig drie-bedrijven-model AAN,
inclusief Codex-bouwt.** Gereedschap staat globaal klaar:
- `/codex-review` — plan door Codex laten grillen (read-only, VERDICT APPROVED/REVISE).
- `/codex-build` — Codex bouwt van bevroren spec; Claude leest diff + draait bewijstest;
  Arsalan keurt goed vóór commit; commit/deploy uitsluitend Claude.
- `codex` werkt als gewoon commando (shim in `~/.local/bin/`).

⚠️ **Nog te doen vóór/bij gebruik:** vraag Arsalan of de sleutels afgeschermd mogen worden
— `.codex/config.toml` bevat leesbare API-sleutels, is untracked maar NIET in `.gitignore`.
`.codex/` toevoegen aan `.gitignore` na zijn "ja". Nooit die sleutels laten meecommitten.

**Gebruik bouwblok 1 hieronder als eerste echte proefrit:** `/codex-review` op het plan,
dan `/codex-build` per werkorder (of begin met alleen B1). Zo zie je het werkmodel live.

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
