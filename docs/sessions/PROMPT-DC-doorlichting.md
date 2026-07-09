# Sessie-prompt — Kijk-sessie D-C: financieel + systeem doorlichten (Fable, read-only)

Kopieer alles onder de streep in een nieuwe sessie (model: Fable).

---

**Stap 0 — sessiestart.** Draai eerst `/sessie-start`. Dat leest via de researcher-subagent
SESSION-NOTES.md + LUXIS-ROADMAP.md, scant de bestaande modules/pagina's, en laadt (via de
SessionStart-hook) automatisch `docs/ARCHITECTUUR-KAART.md`. Geef daarna de korte
start-samenvatting en ga zonder te wachten door met de taak hieronder (de prioriteit van
deze sessie staat vast — dit is 'm).

**Stap 1 — extra taak-context lezen** (bovenop wat `/sessie-start` al las):
- `docs/plans/PLAN-doorlichting-menu.md` — het plan + de 3 lagen per onderdeel
- `docs/research/audit-DA-werkschil.md` + `docs/research/audit-DB-kernmotor.md` —
  kijk-sessies 1 en 2, klaar. Zelfde stijl/diepgang aanhouden.

**Stap 2 — Taak: kijk-sessie D-C (laatste).** Licht deze menu-onderdelen door:
**Bankimport, Derdengelden, Uren, Facturen, Rapportages, Instellingen.** 100% read-only
op prod (queries, code lezen, doorklikken in de ingelogde app als seidony@kestinglegal.nl /
Hetbaken-KL-5 op https://luxis.kestinglegal.nl). Niets muteren, niets versturen, niets
importeren, geen instellingen wijzigen.

Per onderdeel de 3 lagen uit het plan (techniek/5 vragen, partner-blik, UX/UI). Meet in de
bron — niet gokken vanaf roadmap/memory (skill `fable-diepte`). Het plan verwacht hier de
meeste eilanden/relieken. Al bekend terrein, niet herhalen: rekenkernen + security (S183),
mail (S185-188), betalingen-import zelf (S179/S180 — wél kijken of de bankimport-PAGINA
nog iets doet nu de import via SQL/recept liep). Meenemen uit D-A/D-B (raakvlakken):
- Uren/Facturen: 0 rijen ooit (gemeten D-A/D-B); dashboard-widgets, dossier-tabs én
  menu-items hangen eraan. Beslispunt module-vlaggen bestaat al (A4).
- Bankimport: `bank_statement_imports`/`bank_transactions`/`payment_matches` stonden
  9 juli op 0 rijen — is de pagina een eiland naast de S180-recept-import?
- Derdengelden: 0 transacties; FIN-2 afwikkelflow (S170) + afsluit-guard bestaan wel.
- Instellingen: sjabloonbeheer staat hier dubbel (ook op Documenten, D-A A7);
  module-vlaggen (uren/facturatie/wwft/incasso) — wat staat aan en klopt dat?
- Rapportages: nooit eerder doorgelicht — doet het iets met de echte data?
- `products` (30 rijen) en `expenses`/`invoice_*` (0) — waar horen die bij?

**Stap 3 — Uitkomst.** `docs/research/audit-DC-financieel-systeem.md` in dezelfde vorm
als D-A/D-B (samenvattingstabel, per onderdeel 3 lagen met bewijs, "niet geverifieerd"-
lijst, werkorder-kandidaten C1…Cn). Committen + pushen. SESSION-NOTES bijwerken (max 10
entries, oudste → archief) + plan-status D-C afvinken + git tag. Sluit af met een
totaaloverzicht: alle verdicts van D-A + D-B + D-C in één beslislijst-concept voor
fase 2 (het gesprek met Arsalan).

**Deploy-regel:** read-only sessie, dus geen deploy. Alleen docs committen+pushen.
