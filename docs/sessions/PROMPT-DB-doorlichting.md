# Sessie-prompt — Kijk-sessie D-B: kern-motor doorlichten (Fable, read-only)

Kopieer alles onder de streep in een nieuwe sessie (model: Fable).

---

**Stap 0 — sessiestart.** Draai eerst `/sessie-start`. Dat leest via de researcher-subagent
SESSION-NOTES.md + LUXIS-ROADMAP.md, scant de bestaande modules/pagina's, en laadt (via de
SessionStart-hook) automatisch `docs/ARCHITECTUUR-KAART.md`. Geef daarna de korte
start-samenvatting en ga zonder te wachten door met de taak hieronder (de prioriteit van
deze sessie staat vast — dit is 'm).

**Stap 1 — extra taak-context lezen** (bovenop wat `/sessie-start` al las):
- `docs/plans/PLAN-doorlichting-menu.md` — het plan + de 3 lagen per onderdeel
- `docs/research/audit-DA-werkschil.md` — kijk-sessie 1 (D-A), klaar. Zelfde stijl/diepgang aanhouden.

**Stap 2 — Taak: kijk-sessie D-B.** Licht deze menu-onderdelen door: **Relaties, Dossiers,
Incasso, Follow-up, Intake.** 100% read-only op prod (queries, code lezen, doorklikken in de
ingelogde app als seidony@kestinglegal.nl / Hetbaken-KL-5 op https://luxis.kestinglegal.nl).
Niets muteren, niets versturen, geen Akkoord/Afwijzen klikken.

Per onderdeel de 3 lagen uit het plan (techniek/5 vragen, partner-blik, UX/UI). Meet in de
bron — niet gokken vanaf roadmap/memory (skill `fable-diepte`). Let op — al bekend terrein,
niet herhalen: security/RLS (S183-audit), rekenkernen (S183 "aantoonbaar op orde"), mail
(S185-188). Wel meenemen uit D-A (raakvlakken):
- Follow-up: 13 aanbevelingen zijn 1-op-1 gekopieerd op Mijn Taken; "Akkoord" =
  genereren+versturen zonder bevestiging; interne slugs in beeld (sommatie_drukte).
- Intake: statusfilter-bug op Mijn Taken (`pending` vs `pending_review`); prod = 6 pending_review.
- Incasso: dubbele stap "Eerste sommatie" (1 actief, 1 inactief); 394 e-mail-classificaties
  allemaal onverwerkt (eiland).
- Verjaring: IN100015/IN100127 formeel verjaard, IN100016 volgt 23-09-2026 — hoe tonen
  Dossiers/Incasso dit?

**Stap 3 — Uitkomst.** `docs/research/audit-DB-kernmotor.md` in dezelfde vorm als D-A
(samenvattingstabel, per onderdeel 3 lagen met bewijs, "niet geverifieerd"-lijst,
werkorder-kandidaten B1…Bn). Committen + pushen. SESSION-NOTES bijwerken (max 10 entries,
oudste → archief) + plan-status D-B afvinken + git tag. Maak aan het eind de laatste
kijk-sessie-prompt aan: `docs/sessions/PROMPT-DC-doorlichting.md` (Bankimport, Derdengelden,
Uren, Facturen, Rapportages, Instellingen) — zelfde opzet mét `/sessie-start` bovenaan.

**Deploy-regel:** read-only sessie, dus geen deploy. Alleen docs committen+pushen.
