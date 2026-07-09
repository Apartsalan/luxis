# Sessie-prompt — EERST Codex-onderzoek, DAN kijk-sessie D-C (Fable, read-only)

Kopieer alles onder de streep in een nieuwe sessie (model: Fable).

---

**Stap 0 — sessiestart.** Draai eerst `/sessie-start`. Dat leest via de researcher-subagent
SESSION-NOTES.md + LUXIS-ROADMAP.md, scant de bestaande modules/pagina's, en laadt (via de
SessionStart-hook) automatisch `docs/ARCHITECTUUR-KAART.md`. Geef daarna de korte
start-samenvatting en ga zonder te wachten door met taak 0 hieronder.

**Taak 0 — EERST (verzoek Arsalan, 9 juli): onderzoek Claude Code + Codex samenwerken.**
Arsalan heeft een OpenAI-abonnement (~€103/mnd) met de nieuwste modellen (GPT-5.6 "Sol" /
"Sol Ultra") en wil Codex in déze terminal naast/samen met Claude Code gebruiken. Doe
web-onderzoek (niet uit het hoofd — modellen/tools zijn nieuw) en lever een kort advies:
1. **Installatie/aansluiting:** hoe draait Codex CLI op deze Windows-machine naast Claude
   Code, en hoe roept Claude Code Codex aan (of andersom) — CLI-aanroep, MCP-koppeling, of
   een plugin/skill.
2. **Samenwerk-patronen vergelijken:** de "grill-me"-skill (Chase AI) waarbij Claude en
   Codex elkaars werk bediscussiëren, én alternatieven (andere skills/plugins, zelfgebouwde
   review-loop, planner-bouwer-splitsing). Wat bestaat er, wat is volwassen, wat past hier?
3. **Concreet werkmodel voorstellen** voor dit huishouden (Luxis + Recruit): wie plant, wie
   bouwt, wie reviewt — bijv. Fable/Opus plant + reviewt, GPT-5.6 bouwt mee of grillt het
   plan, met de bestaande fable-skills als tegenspreker-laag. Benoem ook wat het NIET moet
   worden (dubbel werk, twee kapiteins op prod).
4. **Kosten/risico's:** wat kost het per sessie extra, en welke afspraken zijn nodig
   (bijv. alleen Claude deployt/commit, Codex alleen voorstellen).
5. **Toepassen op de HUIDIGE manier van werken (belangrijk, verzoek Arsalan):** nadat het
   plan er staat, meteen concreet maken hoe Codex past in het ritme dat NU al draait —
   niet abstract. Dat ritme is: Fable doet nu het kijk-/onderzoekswerk (deze menu-
   doorlichting D-A/D-B/D-C = "de grote review"), en straks bouwt Opus de werkorders uit.
   Vertaal het advies dus naar: waar zou GPT-5.6 in díe keten passen — grillt hij het
   Fable-onderzoek/rapport (tegenspreker op de bevindingen), of reviewt hij straks de
   Opus-bouwblokken (tweede paar ogen op de code vóór deploy), of allebei? Geef een
   concreet voorbeeld met een bestaand stuk werk uit deze review (bv. werkorder B1
   verstuurpad sommaties: Opus bouwt → Codex grillt → Fable/Opus verwerkt). Zo weet
   Arsalan meteen wat het maandag praktisch betekent, niet alleen "het kan".
Uitkomst: kort adviesdocument `docs/research/advies-codex-samenwerking.md` + voorstel aan
Arsalan (incl. het concrete toepas-voorbeeld op de lopende review/bouw). Pas daarna door
naar de doorlichting hieronder.

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
