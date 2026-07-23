# BaseNet-fases — beslislijst heropening (S243, 23 juli 2026)

**Aanleiding.** Demo-vondst: de 11 "Akkoord dagvaarden"-dossiers waren onvindbaar.
Gemeten (S243): **alle 607 dossiers uit de BaseNet-export staan in Luxis** (1-op-1
vergeleken, 0 ontbreken). Ze waren alleen onvindbaar omdat de BaseNet-fase niet
doorzoekbaar was — dat is gefixt (zoekbalk + fase-filter op de dossierlijst,
commit `062ac4b`). De **11 "Akkoord dagvaarden" zijn 23-7 heropend** op de
gelijknamige stap (eigenaar Lisanne, rente loopt weer, niets gemaild).

**Wat hier ligt.** De overige 406 nog-dichte werkvoorraad-dossiers
(BaseNet-status Lopend/Wacht), per fase, met openstaande hoofdsom. Heropening
blijft **per groep, na expliciet akkoord** — draaiboek:
`docs/plans/PLAN-heropening-werkvoorraad.md` (incl. uitsluitingen: voldaan-zaken,
IN100555, IN100409, S195-correctienotities, gestopte regelingen eerst langs
Lisanne). Vind elke groep in de app: Dossiers → filter "BaseNet-fase".

## Per fase (gemeten op prod, 23-7)

| BaseNet-fase | Aantal | Openstaand (hoofdsom) | Voorstel Luxis-stap |
|---|---|---|---|
| Vordering betwist | 86 | € 496.602,51 | Verweer beantwoorden (+ verweer-vinkje) |
| B2C 4e sommatie verstuurd | 56 | € 67.253,76 | Voorstel dagvaarding |
| Procederen? | 40 | € 363.482,22 | Voorstel dagvaarding |
| Voorstel dagvaarden | 37 | € 280.292,04 | Voorstel dagvaarding |
| B2B 4e sommatie verstuurd | 30 | € 79.656,04 | Voorstel dagvaarding |
| 14-dagen brief | 23 | € 47.983,45 | 14-dagenbrief / Eerste sommatie |
| B2C 2e sommatie verstuurd | 22 | € 52.236,40 | Derde sommatie |
| Bijhouden regelingen | 18 | € 23.831,47 | Bijhouden regeling (o.a. IN100166 — moet innen) |
| Regeling treffen | 13 | € 23.112,57 | Treffen van regeling |
| Eng 4e sommatie verstuurd | 12 | € 41.390,61 | Voorstel dagvaarding (Engels!) |
| B2C Dossier gecontroleerd | 12 | € 46.407,27 | Eerste sommatie (incl. IN100613 — S234-vraag) |
| B2C 1e sommatie verstuurd | 11 | € 16.506,73 | Tweede sommatie |
| Stukken opgevraagd | 10 | € 11.575,81 | Opvragen stukken bij cliënt |
| Aanhouden | 9 | € 46.040,51 | On hold (incl. IN100492 — vraag debiteur ligt er) |
| B2B Dossier gecontroleerd | 8 | € 26.519,61 | Eerste sommatie |
| B2C 3e sommatie verstuurd | 5 | € 4.849,38 | Sommatie laatste mogelijkheid |
| Procedure loopt | 2 | € 15.318,81 | On hold (procedure aanhangig — NIET aanmanen) |
| Factureren | 2 | € −668,22 | Niet heropenen? (negatief saldo — factureren cliënt) |
| B2B 2e sommatie verstuurd | 2 | € 1.427,67 | Derde sommatie |
| B2B 3e sommatie verstuurd | 2 | € 4.406,85 | Sommatie laatste mogelijkheid |
| Dagvaarding naar DW | 1 | € 8.069,35 | On hold (IN100019 — óók actieve regeling, zie draaiboek) |
| Eng 1e-3e sommatie | 3 | € 17.471,13 | Volgende sommatie (Engels!) |
| Sluiten | 1 | € −336,40 | Niet heropenen? (IN100256, negatief) |
| Arno gestuurd | 1 | € 4.487,94 | On hold (IN100038, bij deurwaarder?) |

Dossiernummers per fase: filter in de app, of vraag Claude om de lijst
(query staat in de S243-sessienotities).

## Beslissingen die alleen Lisanne/Arsalan kunnen nemen

1. **Welke groep eerst?** Advies: klein beginnen (zoals bij LegalWork S188b) —
   bv. "Procedure loopt" (2) en "Bijhouden regelingen" (18, daar zitten lopende
   betalingsafspraken bij die nu onbewaakt zijn).
2. **Sommatie-fases**: heropening zet de teller aan — de follow-up-adviseur gaat
   dan per dossier "volgende sommatie" adviseren. Verstuurt niets zelf, maar de
   werklijst groeit met honderden regels als alles tegelijk opengaat.
3. **Verjaring**: heropende oude dossiers kunnen (onterechte) verjaringsmeldingen
   geven — Luxis kent geen stuiting (S242-voorstel ligt er). Bij de 11 van
   vandaag speelt dit niet (vroegste sommetje-datum: feb 2028).
4. **Engelse dossiers** (17): Luxis-sjablonen zijn Nederlands — eerst beslissen
   hoe Engels te bedienen vóór die groep opengaat.
5. **Negatieve saldi** (Factureren/Sluiten, 3 dossiers): afwikkelen, niet incasseren.
