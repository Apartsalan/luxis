# PLAN — Fase 2: bouwblokken na de menu-doorlichting

**Besloten:** 9 juli 2026, beslisgesprek Arsalan + Fable (S191, direct na kijk-sessie D-C).
**Bron:** totaal-beslislijst `docs/research/audit-DC-financieel-systeem.md` §9
(werkorder-details in de rapporten D-A / D-B / D-C, `docs/research/`).
**Spelregel:** verwijderen gebeurt nooit autonoom — per stuk expliciet akkoord in de sessie zelf.

## Besluiten per stapel (letterlijk vastgelegd)

| Stapel | Besluit Arsalan |
|---|---|
| 1 — Repareren | **Akkoord.** = Bouwblok 1 (S193, Opus). |
| 2 — Aansluiten | **Akkoord.** Stichting-IBAN + BTW-nummer levert Arsalan **10 juli** aan (C2); daarna eerste bankimport-proef samen (C1). Punt 7 (termijn-vooruitblik): alléén het overzicht over zaken heen bouwen — op dossierniveau bestaat het al (Betalingen-tab). B11 (3 proefzaken een stap) akkoord. |
| 3 — Beslispunten | 9 (B3): **versimpelen** — status volgt de pijplijn, niet het grote status-systeem optuigen. 10 (A5/B6/A11/C9): **classificatielijn op pauze, meldingen/badges uit**. 11 (C3): **Uren + Facturatie blijven AAN** (keuze Arsalan, "kan geen kwaad") — gevolg: C5 (urenfilter alleen opdrachtgevers) en het nette maken van de lege dashboard-widgets verhuizen naar de veegsessie; module-vlag-route van A4 vervalt. 12 (A3): dagstart-lijst, ná blok 1. 13 (A7): sjabloonbeheer alleen in Instellingen; documentenbibliotheek later. |
| 4 — Veegwerk | **Akkoord**, één veegsessie; verwijderingen (A10 testdossier, B10 test-aanvragen) per stuk akkoord in die sessie. |
| 5 — Laten liggen | **Akkoord** (Exact, PSD2, feed, rapportage-per-opdrachtgever, WWFT/budget — wachten op hun trigger). |

**Extra afspraak (Codex):** proef "GPT-5.6 bouwt onder Claude-toezicht" op een
overzichtelijke klus uit stapel 4, ná de Codex-installatie (~13 juli,
`docs/research/advies-codex-samenwerking.md`). Claude blijft de enige die commit/deployt.

## Bouwvolgorde

1. **Bouwblok 1 (S193, Opus, prompt klaar):** B1 verstuurpad sommaties + nooit meer
   "Uitgevoerd" bij een fout; B2+A1 verjaring zichtbaar (badge op verzuimdatum,
   monitor-gat `date_closed`, taken met eigenaar); B13 verzend-vangrails (preview +
   vast kanaal incasso@); A2 dashboard-filterfix. Alles vóór het mailslot eraf gaat.
2. **Bouwblok 2 (zodra C2-gegevens binnen zijn):** C2 invullen → C1 eerste
   bankimport-proef (samen met Arsalan) → B4/A8 termijn-vooruitblik (alleen overzicht)
   → B11 stappen voor de 3 proefzaken.
3. **Bouwblok 3:** B3-versimpeling (status volgt pijplijn) + A5-pauze
   (classificatie/meldingen) + A3 dagstart + A7 sjablonen-op-één-plek.
4. **Veegsessie:** stapel 4 (incl. C5 urenfilter + dashboard-widgets netjes bij
   aan-blijvende modules, C4 rapportage-fixes, A12 accountnaam).
5. **Los, wanneer het uitkomt:** Codex-installatie + bouwproef.

## Status
- [x] Beslisgesprek (9 juli, in S191 — deze pagina)
- [x] Bouwblok 1 (S193 gebouwd + S194 visueel geverifieerd op prod)
- [~] Bouwblok 2 (S194): C2 ingevuld ✅ + bankimport-parser gefixt + droogloop klaar
      (`docs/sessions/S194-bankimport-droogloop.md`). RESTEERT: C1-import SAMEN met Arsalan
      (beslislijst 4 groepen) → B4/A8 termijn-vooruitblik → B11 stappen 3 proefzaken.
- [ ] Bouwblok 3
- [ ] Veegsessie
- [ ] Codex-proef
