# Sessie-prompt S192 — Fase-2-beslisgesprek: de totaal-beslislijst met Arsalan

Kopieer alles onder de streep in een nieuwe sessie. Model: Fable als het vóór 12 juli is
(gesprek + scherpe afwegingen), anders Opus met de fable-skills.

---

cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 192 — Fase-2-beslisgesprek "Luxis afmaken"

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant modules,
laadt de verbindingskaart). Extra taak-context daarna lezen:
- `docs/research/audit-DC-financieel-systeem.md` **§9** (de totaal-beslislijst, 34 punten
  in 5 blokken) — dit is de agenda van het gesprek
- De drie rapporten er alleen bij pakken als Arsalan doorvraagt op een punt:
  `audit-DA-werkschil.md`, `audit-DB-kernmotor.md`, `audit-DC-financieel-systeem.md`

## Taak
Dit is een BESLIS-sessie met Arsalan, geen bouwsessie.
1. Presenteer de beslislijst in gewone taal (verhaal, geen vaktermen — Arsalan is geen
   developer): per blok wat het is, wat het kost (klein/middel/groot) en wat je aanraadt.
   Alles in één keer presenteren, niet stap-voor-stap vragen (vaste afspraak).
2. Verzamel per blok de akkoorden/keuzes van Arsalan. Bij de beslispunten (blok 3) één
   aanbeveling per punt geven, geen catalogus.
3. Leg de uitkomst vast in `docs/plans/PLAN-fase2-bouwblokken.md`: gekozen volgorde,
   per bouwblok de werkorders (verwijs naar A/B/C-nummers), en wat bewust NIET gebeurt.
4. Schrijf de prompt voor de eerste Opus-bouwsessie (S193) volgens het format in
   `/sessie-einde` — vermoedelijk blok 1 (B1 verstuurpad + B2/A1 verjaring), vóór het
   mailslot eraf gaat.
5. Optioneel, als Arsalan tijd heeft (maandag 13 juli): Codex CLI installeren volgens
   `docs/research/advies-codex-samenwerking.md` (±30 min) + proefrit: Codex het
   D-B-rapport laten grillen. Alleen op zijn initiatief.

## Verificatie
Geen code deze sessie → geen tests/build. Wel: elke beslissing expliciet in het
plan-document, niets impliciet.

## Constraints (wat NIET doen)
- Niets bouwen, niets muteren op prod, niets verwijderen — ook niet "alvast een kleintje".
- Verwijder-besluiten (bv. testdossier A10, intake-ruis B10) alleen noteren mét expliciet
  akkoord per stuk; uitvoeren pas in een bouwsessie.
- Mailslot NIET aanraken (eraf alleen op expliciet verzoek Arsalan, ~13 juli).

## Commit
Plan-document + S193-prompt + SESSION-NOTES/roadmap committen en pushen (alleen docs).
Sessie afsluiten met `/sessie-einde`-regels (archief-regels, git tag sessie-192).
