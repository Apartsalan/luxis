# Sessie-prompt S194 — visuele controle bouwblok 1 + bouwblok 2 (of 3)

Kopieer alles onder de streep in een nieuwe sessie. **Model: Opus** (check met `/model`
dat je NIET op Fable zit; bouwen doen we op Opus). Codex (Sol Ultra, alleen-lezen) mag
als externe tegenlezer meekijken op bouw-wijzigingen vóór deploy.

---

cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 194 — visuele controle bouwblok 1, dan bouwblok 2 (of 3)

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant modules,
laadt de verbindingskaart). Ga daarna zonder te wachten door met de taak hieronder.
Extra taak-context (alleen wat `/sessie-start` NIET al leest):
- `docs/plans/PLAN-fase2-bouwblokken.md` — de blokken + besluiten.
- Bouwblok 1 is in S193 gebouwd én uitgerold; zie SESSION-NOTES S193-entry.

## Taak 1 — Visuele doorklik bouwblok 1 op prod (mailslot dekt, niets gaat echt uit)
Log in op https://luxis.kestinglegal.nl (seidony@kestinglegal.nl / Hetbaken-KL-5) en
controleer met eigen ogen:
1. **Follow-up "Uitvoeren"** → het voorvertoning-venster verschijnt met afzender/ontvanger/
   onderwerp/tekst; niets wordt verstuurd zonder "Versturen". Escalatie-aanbevelingen voeren
   direct uit (geen venster, geen geblokkeerde knop).
2. **Dossier-badge verjaring** klopt (rekent vanaf verzuimdatum oudste vordering; ijkpunt
   IN100016 = 23-09-2026). **Mijn Taken** toont de eigenaarloze verjaring-alarmen.
3. **Dashboardblok "Nieuwe Dossiers"** toont weer aanvragen (niet leeg).

## Taak 2 — Instellingen-blokkade + afzender + C2-gegevens (uit S193-nagesprek)
Drie samenhangende punten die in S193 boven kwamen:
1. **Admin-rechten-bug (BLOKKEREND):** Arsalan kan Instellingen niet opslaan — melding "admin
   nodig", terwijl hij het éérst aangemaakte account gebruikt. Uitzoeken: waarom heeft dat
   account geen admin-rol, en de wens is dat **alle accounts admin-rechten hebben**. Fix zodat
   opslaan werkt (anders kan geen van onderstaande waarden gezet worden).
2. **Vaste afzender:** op prod staat de kantoor-e-mail (`Tenant.email`) nog op
   `kesting@kestinglegal.nl` — Arsalans wijziging naar incasso@ landde niet. Zet 'm op
   **incasso@kestinglegal.nl** (het incasso@-account ís al gekoppeld → dan werkt B13's vaste
   kanaal). Ná akkoord op de waarde.
3. **Derdengelden-rekening als apart veld (ONDERZOEK + BOUW):** Lisanne heeft een **eigen
   Kesting-rekening** (waar ze straks facturen mee int) én een **derdengeldenrekening**
   (Stg. Beh. Derdengelden Kesting, `NL20 RABO 0388 5065 20`). Instellingen moet dus een apart
   veld "derdengelden-rekening" krijgen, los van de kantoorrekening. C2-waarden van Arsalan om
   in te vullen (ná akkoord): **BTW-nummer `NL869343610B01`**, **derdengelden-IBAN
   `NL20 RABO 0388 5065 20`**. (D-C-audit: derdengelden-IBAN stond nog verkeerd op de kantoor-IBAN.)

## Taak 3 — Bouwblok 2: bankimport (CSV komt volgende sessie van Lisanne)
LET OP: de bestaande Luxis-bankimport leest een **Rabobank-CSV (kommagescheiden, 26 kolommen,
`parse_rabobank_csv`)** — géén MT940/CAMT. Lisanne haalt die CSV van de derdengeldenrekening
(niet via het "Downloadformaat"-scherm met MT940/CAMT, maar via het transactie-overzicht →
Exporteren → CSV). 6 maanden periode.
- **CSV binnen?** → C1 eerste bankimport-proef sámen met Arsalan → B4/A8 termijn-vooruitblik
  (alleen het overzicht over zaken heen; op dossierniveau bestaat het al) → B11 stappen voor
  de 3 proefzaken. Details in `docs/plans/PLAN-fase2-bouwblokken.md` + D-C-rapport.
- **C2 nog niet binnen?** → begin met **bouwblok 3**: B3-versimpeling (status volgt pijplijn),
  A5-pauze (classificatie/meldingen uit), A3 dagstart-lijst, A7 sjablonen op één plek.

## Verificatie (per werkorder, niet pas aan het eind)
- Backend: `docker compose exec backend pytest tests/ -k "<relevant>" -v` (alleen relevante modules)
- Lint: `uvx ruff check backend/app/` · Frontend (indien geraakt): `npx tsc --noEmit` + `npm run build`
- Codex-tegenlezer (alleen-lezen) op de diff vóór deploy; verwerk echte vondsten.
- Live doorklikken in de prod-app ná deploy.

## Constraints
- ⚠️ **MAILSLOT blijft AAN** tenzij Arsalan het expliciet eraf vraagt (~13 juli). Niets echt versturen.
- Alleen de blokken uit het plan; extra vondsten = noteren als voorstel, niet bouwen.
- Prod-mutaties (C2-waarden, kantoor-e-mail) alleen ná expliciet akkoord Arsalan op de waarden.

## Commit
Per werkorder committen + pushen (conventional commits); deploy zelf via SSH (skill
`deploy-regels`), containers healthy checken. Afsluiten met `/sessie-einde` (notities,
roadmap, archiefregels, tag sessie-194).
