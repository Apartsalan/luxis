cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 210 — provisie-afspraak + land op de Word-brieven (vervolg op S209)

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant modules,
laadt de verbindingskaart). Ga daarna zonder te wachten door met de taak hieronder.
Extra taak-context (alleen wat `/sessie-start` NIET al leest):
`docs/research/S208-veldaudit-basenet.md` §4 (provisie-veld) en de S209-entry in SESSION-NOTES.

## Taak

### 1. Provisie-afspraak (EERST UITVRAGEN, niet bouwen)
Arsalan noemde (14 juli): treft Lisanne een regeling met de debiteur voor een lager bedrag
(bijv. 80% i.p.v. 100%), dan krijgt zij **15% over die deal**; haalt zij het volledige bedrag
binnen, dan krijgt zij gewoon de **incassokosten**. Nog niet scherp genoeg om te bouwen. Doe in
deze volgorde:
1. **Vraag Arsalan concreet uit** (één keer alle vragen tegelijk):
   - Waarover wordt de 15% berekend — het deal-bedrag, het verschil, de hoofdsom, iets anders?
   - Per dossier, per opdrachtgever, of per deal? Wie int het en wanneer?
   - Is dit dezelfde 15% als de BaseNet-`incprovisie` bij 39 zaken (5 opdrachtgevers, veld
     `provisie_percentage` bestaat al op `Case`) — of staat dat los?
   - Nieuwe afspraak of bestaat hij al (mondeling/Excel) en moet Luxis 'm alleen zichtbaar maken?
2. **Pas na de antwoorden** samen een werkwijze ontwerpen (Plan Mode, premortem bij niet-triviaal).
3. Als de 39 BaseNet-zaken dezelfde afspraak blijken: de **provisie-15%-backfill** uitvoeren
   (dry-run + akkoord + tel-verificatie; recept-aanpak zoals S209). Anders: apart houden.

### 2. Land op de eigenlijke Word-brieven (klein)
Het land staat al in de gegevens en in de brief-context (`{{ wederpartij.land }}`), maar de
built-in DOCX-sjablonen in de DB (`managed_templates`: sommatie, 14_dagenbrief, aanmaning, …)
missen de regel nog. Voeg `{{ wederpartij.land }}` toe onder het adresblok (alleen tonen indien
gevuld) via de sjabloon-editor / re-upload, met **visuele controle** dat het adres netjes staat.
Mailslot blijft DICHT; niet versturen.

### 3. WIK-rentebijlage — alleen als Arsalan meldt dat de KvK-API-sleutel er is
Anders overslaan.

## Verificatie
- Relevante tests: `docker compose exec backend python -m pytest tests/ -k "provisie or invoice or contact or basenet" -q`
- Lint: `uvx ruff check backend/app/` (lokaal, vóór push). Frontend geraakt? `cd frontend && npx tsc --noEmit`
- Elke prod-mutatie: dry-run-rapport tonen → akkoord → uitvoeren → tel-verificatie achteraf

## Constraints (wat NIET doen)
- GEEN provisie wegschrijven vóór de afspraak scherp is (S209 bewust geparkeerd).
- GEEN rente-wijzigingen (in S208 eind-geverifieerd, 607/607).
- BSN's NIET importeren. Mailslot DICHT. Geen `git add -A` (expliciete paden). Parallelle
  S207-track (`PROMPT-S207.md`) niet mengen — 5 ongecommitte bestanden in de werkkopie.

## Commit
Commit + push naar main met conventional commit message per afgerond onderdeel. Deploy via SSH
(skill `deploy-regels`); DOCX-sjablonen zitten in de DB (geen deploy, wel back-up vóór re-upload).
