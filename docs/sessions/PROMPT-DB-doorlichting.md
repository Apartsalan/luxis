# Sessie-prompt — Kijk-sessie D-B: kern-motor doorlichten (Fable, read-only)

Kopieer dit in een nieuwe sessie (model: Fable, `/effort high`):

---

Lees eerst:
- `docs/plans/PLAN-doorlichting-menu.md` (het plan + de 3 lagen per onderdeel)
- `docs/research/audit-DA-werkschil.md` (kijk-sessie 1, klaar — stijl en diepgang aanhouden)

**Taak: kijk-sessie D-B — licht deze menu-onderdelen door: Relaties, Dossiers,
Incasso, Follow-up, Intake.** 100% read-only op prod (queries, code lezen, doorklikken
in de ingelogde app als seidony@kestinglegal.nl / Hetbaken-KL-5 op
https://luxis.kestinglegal.nl). Niets muteren, niets versturen, geen Akkoord/Afwijzen
klikken.

Per onderdeel de 3 lagen uit het plan (techniek/5 vragen, partner-blik, UX/UI).
Let op — al bekend terrein, niet herhalen: security/RLS (S183-audit), rekenkernen
(S183 "aantoonbaar op orde"), mail (S185-188). Wel meenemen uit D-A (raakvlakken):
- Follow-up: 13 aanbevelingen zijn 1-op-1 gekopieerd op Mijn Taken; "Akkoord" =
  genereren+versturen zonder bevestiging; interne slugs in beeld (sommatie_drukte).
- Intake: statusfilter-bug op Mijn Taken (`pending` vs `pending_review`).
- Incasso: dubbele stap "Eerste sommatie" (1 actief, 1 inactief); 394 e-mail-
  classificaties allemaal onverwerkt (eiland).
- Verjaring: IN100015/IN100127 formeel verjaard, IN100016 volgt 23-09-2026 —
  hoe tonen Dossiers/Incasso dit?

Uitkomst: `docs/research/audit-DB-kernmotor.md` in dezelfde vorm als D-A
(samenvattingstabel, per onderdeel 3 lagen met bewijs, "niet geverifieerd"-lijst,
werkorder-kandidaten B1…Bn). Committen + pushen. SESSION-NOTES bijwerken (max 10
entries) + plan-status afvinken. Daarna is D-C de laatste kijk-sessie
(`docs/sessions/PROMPT-DC-doorlichting.md` aanmaken aan het eind van D-B).
