# Geld-audit — 29 juli 2026 (S251)

**Aanleiding.** Arsalan zag op IN100602 een verschil tussen het Financieel-tabblad
(€ 2.840,12 incassokosten) en de zojuist verstuurde sommatie (€ 964,34), en op
IN100612 tussen tabblad-rente (€ 58,41) en briefrente (€ 202,79). Opdracht: **alles**
opnieuw doorrekenen — kosten, rente, instellingen per cliënt, alle dossiers, alle
brieven/sjablonen/AI-concepten — vóór er iets gebouwd wordt.

Alles hieronder is op de productieomgeving gemeten (29 juli), niet uit documentatie
overgenomen.

## Wat gezond bleek

| Onderdeel | Meting |
|---|---|
| Hoofdsommen | 627 dossiers: cache-hoofdsom == som losse vorderingen, **0 afwijkingen** |
| WIK-staffel | tot de cent correct (3 onafhankelijke wegen: eigen SQL, app-API, verstuurde brief) |
| B2C boven staffel | **0** overtredingen (S230-schoonmaak houdt stand) |
| Rekenroutes mét alle instellingen | Financieel-tabblad, betalingsverdeling (art. 6:44 BW), dashboard/portfolio, facturen naar cliënt, bank-matching, AI-conceptbedragen |
| Rente-instellingen bureaus | 6/6 klantkaarten AV-rente 2%/mnd samengesteld (art. 13.3), alle actieve bureau-dossiers `contractual` 2% behalve IN100077 |
| Stopdatums | 0 afgesloten zaken zónder stopdatum, 0 actieve zaken mét; de 91 "afwijkende" bleken terecht (rente stopt op betaaldatum, dossier later administratief gesloten) |

## Vondst 1 (hoofdvondst) — de briefmachine rekende zijn eigen som

`docx_service.build_base_context` en `documents.service._build_template_context`
stelden hun eigen `get_financial_summary`-aanroep samen **zonder** de
zaakinstellingen (`bik_override`, `bik_override_percentage`, `nakosten_type`) en
mét een harde `calc_date=today`. Daardoor:

- élke brief toonde de **kale WIK-staffel** in plaats van de kosten-afspraak;
- élke brief rekende rente **t/m vandaag**, ook op een dossier met een
  rente-stopdatum.

Dit raakte alle briefroutes (mail-sjablonen, DOCX, batch, follow-up, voorbeeld,
renteoverzicht-bijlage) omdat ze allemaal die ene context gebruiken. Het zat er
vanaf de eerste versie in — git-historie: de koppeling heeft nooit bestaan. Eerdere
controles keken alleen naar "te veel vragen bij consumenten", niet naar "te weinig
vragen bij bedrijven".

**Verstuurde brieven met een verkeerd bedrag** (34 brieven met bedragen-tabel sinds
de import van 3 juli doorgemeten; testdossiers 2026-000xx uitgefilterd):

| Dossier | Verzonden | In brief | Moest zijn | Verschil |
|---|---|---|---|---|
| IN100598 | 22-7 | € 1.221,10 | € 6.691,46 | € 5.470,36 te weinig |
| IN100592 | 22-7 + 23-7 | € 976,04 | € 3.015,61 | € 2.039,57 te weinig |
| IN100602 | 22-7 + 29-7 | € 964,34 | € 2.840,12 | € 1.875,78 te weinig |
| IN100599 | 22-7 | € 896,00 | € 1.815,00 | € 919,00 te weinig |
| IN100605 | 20-7 | € 232,75 | € 0,00 (afspraak) | € 232,75 te veel |

Totaal € 10.304,71 te weinig gevorderd bij 4 debiteuren. Rente-kant: één brief
(IN100613, 23-7) rekende 8 dagen rente door na de stopdatum. Consumentenbrieven
(14-dagenbrief) toonden wél het juiste bedrag — daar ís de staffel dwingend.

## Vondst 2 — 15%-afspraak stond niet als standaard

Twee verschillende 15%-afspraken liepen door elkaar:

- **provisie 15%** (verdienmodel richting opdrachtgever) — stond correct op alle 6
  bureaukaarten (S210);
- **incassokosten 15%** (richting debiteur) — kwam alleen mee met de BaseNet-import
  als vast bedrag per dossier. Als *standaard* op de klantkaart stond hij op **1 van
  de 6** (COLLECT 1). Nieuwe dossiers erfden dus niets en vielen terug op de staffel.
  Geen sessiebesluit gevonden waarin dit breed is doorgevoerd — de twee 15%'s zijn
  bij het opstellen vermoedelijk verward.

Verder gemeten: Incassocenter stond op 14,97% (typefout, tijdens de audit door het
kantoor zelf naar 15,00 gezet); IN100605 had € 0,00 uit BaseNet (leeg bronveld —
12 dossiers kwamen zo binnen, 11 daarvan afgesloten).

## Vondst 3 — waakhond keek maar naar één vorm

`find_bik_above_staffel` (dagelijkse sweep, S230) filterde op `bik_override IS NOT
NULL` en zag een **percentage**-afspraak dus nooit. Nul slachtoffers op het moment
van meten, maar zodra de klantkaarten een percentage-standaard krijgen, erft élk
nieuw dossier precies de vorm waar de wachter blind voor is.

## Kleinere gaten (benoemd, niet gebouwd)

1. Een "Verstuur later"-mail bevriest de bedragen op het moment van **inplannen** —
   dagen later klopt de rente niet meer.
2. Cosmetisch: lege "Voldaan bij klant € "-regels in brieven zonder betalingen.
3. Slapende agent-laag (`ai_agent/tools/handlers/collections.py`) roept
   `get_financial_summary` zonder zaakinstellingen aan — geen productie-impact,
   wel dezelfde fout-soort.
4. **153 dossiers** staan nog dicht uit de import met de rentemeter bevroren op de
   openingsdatum → hoort bij `docs/plans/BASENET-STATUS-HERSTEL.md` (wacht op GO
   per groep).

## Wat er is gebouwd (commit `f31bc39`, live)

1. `case_payment_kwargs` → **`case_calc_kwargs`**: gedeelde bron voor betalingen
   *en* brief-context; beide contextbouwers gaan er nu doorheen, zonder peildatum
   (respecteert `interest_freeze_date`). BIK-velden volgen het effectieve bedrag.
2. **Alle 6 bureaukaarten op 15% + bodem € 40**; IN100602 en IN100605 op 15% als
   percentage (self-correcting). Back-up: `_s251_bik_backup_contacts` /
   `_s251_bik_backup_cases`.
3. `find_bik_above_staffel` kijkt nu ook naar percentage + bodem.
4. Wachters: 5 in `test_brief_bedragen_gelijk_aan_scherm.py` (vast bedrag /
   percentage / € 0,00 / geen afspraak / bevriesdatum) + 3 in
   `test_bik_staffel_sweep.py`. Rood bewezen via `git stash`, daarna groen.

**Natelling na deploy: 43 van 43 actieve incassodossiers — brief == Financieel-tabblad,
0 afwijkingen.** 751 tests groen in de geld-, brief- en documentmodules.

## Openstaand voor Lisanne (inhoudelijk)

- De 4 dossiers met een te lage brief herstellen zich vanzelf bij de volgende brief.
- IN100605: € 232,75 was toevallig het juiste bedrag → geen correctie naar de debiteur.
- **IN100077** (Incassocenter, actief) staat op wettelijke rente i.p.v. 2%/mnd
  contractueel — bewust of niet?
