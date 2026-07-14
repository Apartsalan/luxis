# Sessie Notities — Luxis

<!-- Kop = exact deze 4 regels, elk max 1-2 zinnen. Detail hoort in de sessie-entry. -->
<!-- Max 10 sessie-entries in dit bestand; oudere → docs/archief/SESSION-ARCHIVE.md (regels: /sessie-einde). -->
**Laatst bijgewerkt:** 14 juli 2026 (S210, Opus-bouw + Fable-review — provisie-per-cliënt + land op de brieven, alles LIVE + visueel geverifieerd). Prod op HEAD `4025d43`.
**Laatste feature/fix:** Standaard provisie-% per cliënt (overerft naar nieuw dossier) + 6 klantkaarten & 39 dossiers op 15% + landregel op de 5 debiteurbrieven (alleen bij buitenland). Zie entry S210.
**Openstaand — volgende sessie (startprompt: `docs/sessions/PROMPT-S211.md`):** WIK-rentebijlage bouwen tegen de KvK-testomgeving (plan goedgekeurd: `docs/plans/PLAN-wik-rentebijlage.md`); backfill wacht op de echte KvK-sleutel (~16 juli, Arsalan meldt binnenkomst).
**Volgende sessie:** S211 (WIK-bijlage, bouwen=Opus). NB: aparte S207-track (L4/L5/L6 + M4, `docs/sessions/PROMPT-S207.md`) loopt parallel — niet mengen; werkkopie bevat 5 niet-gecommitte bestanden.


## Sessie 210 (14 juli 2026, Opus-bouw + Fable-review — provisie-per-cliënt + land op de brieven, LIVE)

### Samenvatting
Twee S210-taken volledig af (provisie-afspraak eerst uitgevraagd bij Arsalan → ontworpen → gebouwd;
land op de Word-brieven). Daarna Fable-review van alles + door Opus alle visuele controles gedaan.
Taak 3 (WIK-bijlage) is onderzocht → plan goedgekeurd → apart gezet voor S211 (wacht op KvK-sleutel).

- **Provisie-% per cliënt (LIVE, `2eabd37`).** Nieuw veld `default_provisie_percentage` op `contacts`
  (migratie `s210_contact_provisie`, additief); elk nieuw dossier erft het net als de default_bik_*-
  velden (dossier wint), basis blijft `collected_amount`. Klantkaart (tonen + bewerken) + nieuwe-relatie-
  formulier. **Data (na akkoord, nageteld):** 6 klantkaarten op 15% (INC Zakelijk, Incassocenter,
  COLLECT 1, CM Zakelijk, LegalWork, **+ SYN Finance** — dezelfde afspraak) + 39 dossiers op 15%
  (exact de set die BaseNet zelf op `incprovisie=15` had; set-vergelijking prod↔export 0 verschil).
  Slim doorrekenen was al zo (provisie wordt live berekend, nooit als vast bedrag opgeslagen).
- **Land op de Word-brieven (LIVE, `4025d43`).** Voorwaardelijke regel `{%p if wederpartij.land %}...
  {%p endif %}` onder postcode+stad op de 5 debiteurbrieven (sommatie, tweede_sommatie, aanmaning,
  herinnering, 14_dagenbrief). Bij buitenland op eigen regel; bij binnenland (leeg) verdwijnt de regel
  volledig — brief byte-voor-byte gelijk aan voorheen (render-test per sjabloon). Back-up DB-sjablonen
  vóór her-upload (`/root/backup_managed_templates_pre_s210land.dump`); gerichte reseed van alleen deze
  5, andere 3 (dagvaarding/renteoverzicht/verzoekschrift) ongemoeid.
- **WIK-bijlage: onderzocht + plan goedgekeurd (S211).** KvK-koppeling bewezen in gratis testomgeving
  (rechtsvorm komt terug); besluiten A–D vastgelegd. Volledig plan: `docs/plans/PLAN-wik-rentebijlage.md`.

### Fable-review + visuele controle (zelfde sessie)
Alle dragende claims onafhankelijk herverifieerd: DB-sjablonen byte-identiek aan repo (sha256), de 39
dossiers = exact de export-set, precies 6 bedrijven (0 personen) op 15%, geen ander financieel veld
geraakt. **Live prod-round-trip:** testdossier bij CM Zakelijk kreeg automatisch 15,00% → daarna
verwijderd (verbruikte wel dossiernr 2026-00001; eerstvolgende echte = 2026-00002). Visueel (Opus,
niet Fable): provisie-leesweergave + bewerkweergave + nieuwe-relatie-formulier tonen het veld; 5 brieven op
buitenlandse zaak IN100007 (België onder adres) + binnenlandse tegenproef (geen witregel). Oordeel: GO.

### Gewijzigde bestanden
- Backend: `relations/models.py` + `schemas.py`, `cases/service.py` (erving), migratie
  `s210_contact_provisie`, `tests/test_interest_inheritance.py` (4 nieuwe). Templates: 5 DOCX in
  `templates/` (landregel) + gerichte DB-reseed op prod.
- Frontend: `relaties/[id]/page.tsx`, `relaties/nieuw/page.tsx`,
  `components/relations/detail/ContactInfoSection.tsx`, `hooks/use-relations.ts`.
- Docs: `docs/plans/PLAN-wik-rentebijlage.md` (nieuw), `docs/sessions/PROMPT-S211.md` (nieuw).
- 2 code-commits (`2eabd37` provisie · `4025d43` land). Data-mutaties via read-only-gecontroleerde SQL.

### Bekende issues / bewust niet gedaan
- **WIK-bijlage** wacht op de echte KvK-sleutel (~16 juli) voor de backfill; bouwen kan al tegen test.
- **Landregel op dagvaarding + faillissementsverzoek** bewust niet gedaan (gerechtelijke stukken,
  dagvaarding heeft inline-adres) — los klusje als gewenst.
- Verwijderd testdossier bestaat nog als inactieve rij (zo werkt verwijderen; cosmetisch).
- Parallelle S207-track: 5 bestanden nog ongecommit in de werkkopie — niet aangeraakt.

### Volgende sessie
S211 (`docs/sessions/PROMPT-S211.md`): WIK-rentebijlage bouwen tegen de KvK-testomgeving volgens
`PLAN-wik-rentebijlage.md`; backfill draaien zodra Arsalan de echte sleutel meldt. Bouwen = Opus.


## Sessie 209 (14 juli 2026, Opus-bouw + Fable-review — BaseNet import-gaten uit S208-veldaudit gedicht, LIVE)

### Samenvatting
Vier onderdelen uit de S208-veldaudit, elk als losse stap met dry-run + akkoord Arsalan +
tel-verificatie achteraf. Daarna een volledige Fable-review (model omgezet in dezelfde sessie)
die niet alleen de data hertelde maar ook functioneel testte dat alles vooruit werkt.

- **Onderdeel 1 — werknotities + waarschuwingen (LIVE).** 99 `pmemo` + 13 `palert` uit de
  Incasso-export → `Case.debtor_notes` (waarschuwing bovenaan met `[BaseNet-waarschuwing]`,
  werknotitie onder met `[BaseNet-notitie]`, herkomst-regel blijft ertussen). HTML-opmaak
  opgeschoond. Idempotent via marker. 109 dossiers, tel-geverifieerd 99+13. Herhaalbaar script
  `scripts/basenet/backfill_notes.py` (+ zelf-test).
- **Onderdeel 2 — land bij adressen (LIVE, incl. migratie + deploy).** Nieuwe kolommen
  `contacts.visit_country/postal_country` (migratie `s209_contact_country`, additief). 49
  buitenlandse relaties gevuld met nette NL-landnamen (binnenland leeg = standaard). Getoond in
  relatie-detail (alleen indien gevuld) + bewerkbaar. Land beschikbaar in de brief-context
  (`{{ wederpartij.land }}`) + samenvoegveld-lijst + HTML-fallback-sjablonen.
- **Onderdeel 3 — geboortedatums (LIVE); provisie GEPARKEERD.** 28 personen kregen hun
  `date_of_birth` (gekoppeld op systemid, namen gecontroleerd: 26 exact + 2 tussenvoegsel-only).
  Provisie-15% (39 zaken) BEWUST niet uitgevoerd — hangt aan de provisie-afspraak (zie onder).
- **Onderdeel 4 — mapping uitgebreid (voor de vólgende export).** `scripts/basenet/mapping.py`
  neemt nu land (genormaliseerd), geboortedatum, provisie (alleen >0), pmemo/palert in
  debtor_notes + rentetype-context automatisch mee. Hergebruikt `build_new_notes`/`clean`.
- **Provisie-afspraak (niet gebouwd — eerst uitvragen).** Arsalan (14 juli): treft Lisanne een
  regeling met de debiteur voor een lager bedrag, dan krijgt zij 15% over die deal; haalt zij het
  volledige bedrag binnen, dan krijgt zij gewoon de incassokosten. Nog niet scherp genoeg + het is
  onbekend of dit dezelfde 15% is als de BaseNet-`incprovisie` bij 39 zaken. Vragen staan in
  `PROMPT-S209.md`; wachten op Arsalans antwoorden vóór ontwerp (Plan Mode).

### Fable-review (zelfde sessie, model omgezet)
Data onafhankelijk herteld: 109/109 notities byte-voor-byte gelijk aan herberekening (0 `\r`),
49/49 landen + 28/28 geboortedatums exact + bij de juiste relatie (koppeling in beide richtingen
dicht), 0 andere records geraakt (0 provisie gezet). Live via API + visueel doorgeklikt (Chrome):
land toont "Duitsland", dossiernotitie toont "Failliet" bovenaan, testrelatie aangemaakt→land
opgeslagen→verwijderd. **8 round-trip-tests** toegevoegd (mapping→`_insert_missing`→PUT/GET-API).
**Review-vondst:** `is_btw_plichtig` + `contractual_compound` misten `server_default` in het model
terwijl prod die wél heeft (migratie-drift) → test-DB week af, raw-SQL-insert faalde daar. Model
gelijkgetrokken (geen gedragswijziging op prod). 284 tests rente/dossiers/relaties/btw groen.

### Gewijzigde bestanden
- Backend: `relations/models.py` (2 land-kolommen + server_default-sync), `relations/schemas.py`,
  `cases/models.py` (server_default-sync), `documents/docx_service.py` + `documents/service.py`
  (land in context), `templates/sommatie.html` + `14_dagenbrief.html`, migratie
  `s209_contact_country`.
- Frontend: `relaties/[id]/page.tsx`, `components/relations/detail/ContactInfoSection.tsx`,
  `hooks/use-relations.ts`.
- Scripts/tests: `scripts/basenet/backfill_notes.py` (nieuw), `scripts/basenet/mapping.py`,
  `backend/tests/test_basenet_s209_roundtrip.py` (nieuw).
- 6 commits (`2d51ec5` notities · `3054764` land · `c50d24d` mapping · `166620d` review-tests +
  drift-fix · `f3b2ad4` lint). Data-mutaties via read-only-gecontroleerde SQL op prod.

### Bekende issues / bewust niet gedaan
- **Provisie-15% (39 zaken)** wacht op de provisie-afspraak — eerst uitvragen (PROMPT-S209 §gesprek).
- **Land op de eigenlijke Word-brieven** — de built-in DOCX-sjablonen (in de DB) missen nog de
  `{{ wederpartij.land }}`-regel; kleine klus in de sjabloon-editor met visuele controle. Basis staat.
- Parallelle S207-track: 5 bestanden nog ongecommit in de werkkopie — niet aangeraakt.

### Volgende sessie
S210 (`docs/sessions/PROMPT-S210.md`): provisie-afspraak uitvragen bij Arsalan → ontwerpen (Plan
Mode) → eventueel provisie-backfill; land-regel in de Word-sjablonen. WIK-bijlage zodra KvK-API er is.


## Sessie 208 (13 juli 2026, Fable max — BaseNet-veldaudit + EINDVERIFICATIE rente, read-only)

### Samenvatting
Hoofdtaak S208-prompt: veld-voor-veld door `Xml_02-07-2026_2400.zip` (137 bestanden; 9 in
gebruik door de import; elk veld geteld op vul-graad, kruising met `mapping.py`). Rapport:
`docs/research/S208-veldaudit-basenet.md`. Daarna, op verzoek Arsalan, volledige
eindverificatie van de rente-stand ("100% zeker, dan afsluiten").

- **Veld-gaten gevonden (gekwantificeerd):** `incinteresttype` per dossier nooit geïmporteerd;
  99 dossiernotities (`pmemo`) + 13 waarschuwingen (`palert`, o.a. "Failliet", "NIET REAGEREN
  — procedure aanhangig") niet overgenomen; geen land-veld in Luxis-adressen (52 buitenlandse
  relaties); provisie 15% (39 zaken, veld bestaat), 28 geboortedatums, 3 BSN's (bewust NIET
  importeren). Betalingen-aan-cliënt bewezen compleet: €165.697,01 == BaseNet-totaal, 0 verschil.
- **Rente-scare ontzenuwd + eigen rapport gecorrigeerd.** Eerste rapportversie zette 19
  "afwijkende" zaken als beslispunt — fout: besluit S188b (9 juli, plan §4b) dekte ze al
  (b2b holding-opdrachtgevers = AV 2%/mnd). Rapport zelfde dag gecorrigeerd; les: eerst het
  heropening-draaiboek lezen. BaseNet-rentetypen ontcijferd via terugrekening (type 1≈handels-
  rente, 2≈consumentenrente, 5=2%/jr, 9=geen; controlegroep type 8 = 24,6–27,5%/jr ✓).
- **EINDVERIFICATIE (alles prod, read-only):** kruistabel 607/607 in exact 4 besluit-conforme
  combinaties (519 AV-b2b contractual 2,00 / 79 AV-b2c statutory / 8 commercial / 1 statutory);
  machine-match per dossier tegen BaseNet-type: 0 onverklaard (497 identiek, 75 S207c-besluit,
  22 S188b-besluit, 5 b2c-laag, 8 niet-AV); claims-laag 1.373/1.373 monthly (S188b-valkuil
  afwezig); freeze 580/580 gesloten bevroren + 0/27 open + 5 "vóór opening" allemaal exact =
  laatste betaaldatum; motor 107/107 rentetests groen; **ijk IN100197 op prod = €723,31 op de
  cent** (peildatum 8 juli; BaseNet-spec rentedatum 7 juli — S207c-notitie "9 maart" was de
  oude exportdatum) en t/m vandaag €725,39 (loopt correct door).
- **Plan §4b bijgewerkt:** rente-SQL bij heropening VERVALLEN (al uitgerold + geverifieerd);
  verouderde regel "enkelvoudig/`contractual_compound=false`" gecorrigeerd naar samengesteld
  (gouden test `tests/test_interest_monthly.py`). Zonder fix zou een letterlijke uitvoering
  de uitrol deels terugdraaien.

### Gewijzigde bestanden
- `docs/research/S208-veldaudit-basenet.md` (nieuw, 2× gecorrigeerd/aangevuld)
- `docs/plans/PLAN-heropening-werkvoorraad.md` (§4b)
- Geen code, geen migraties, geen prod-mutaties. Deploy niet nodig.

### Bekende issues
- Parallelle S207-track had tijdens deze sessie niet-gecommitte wijzigingen in de werkkopie
  (email/invoices + tests) — bewust niet aangeraakt/gecommit.
- `PROMPT-S207.md` bewust NIET gearchiveerd (actieve parallelle track); archief-regel weer
  toepassen zodra die track afgesloten is.
- Untracked in projectmap: `Renteberekening.docx/pdf` (bron gouden test) — bewust untracked
  laten, zoals de AV-PDF's.

### Volgende sessie
S209: de kleine import-backfills (notities/alerts → dossiernotitie; land-veld + migratie;
provisie/geboortedatums) elk na akkoord; WIK-bijlage zodra KvK-API er is; verse export
voorbereiden. Prompt: `docs/sessions/PROMPT-S209.md`.

## Sessie S207c (13 juli 2026, Fable-review + Opus-uitvoer — rente-review, b2c-terug, bevriesdatum-backfill, BaseNet-herkomst, LIVE)

### Samenvatting
Vervolg op de demo-sprint. Eerst adversariële review van de rentekern (47 tests groen,
6 eigen randgeval-probes, prod IN100197 = €723,31 exact = BaseNet). Daarna 3 prod-acties,
elk met backup + dry-run + akkoord Arsalan.

- **B2C-rente terug (UITGEVOERD).** De AV-uitrol zette 79 consumentenzaken op 2%/mnd.
  Ambtshalve toetsing (Richtlijn 93/13) vernietigt ≥1%/mnd bij consumenten vrijwel altijd
  → veilige route wettelijke rente. `revert_b2c_rente.py`: rente-som 102.876,78 → 19.329,23,
  36 betalingen herverdeeld. `rollout_av_rente.py` slaat b2c voortaan over.
- **Bevriesdatum-backfill (UITGEVOERD).** Alle 580 gesloten zaken kregen `interest_freeze_date`
  (134 laatste betaaldatum / 67 date_closed / 379 BaseNet-rentedatum uit de export van 2 juli).
  Openstaand op gesloten zaken 3.869.871 → 3.338.193 (531.679 spookrente eruit). `backfill_freeze_date.py`.
  ⚠ Export-verwarring rechtgezet: `Xml_02-07-2026_2400.zip` stónd gewoon in de projectmap
  (ik keek eerst naar losse XML). Rentedatum per dossier zat als ongebruikt veld in die export.
- **BaseNet-herkomst als vast veld (GEBOUWD + LIVE).** `Case.basenet_origin_status` (migratie
  s207c, backfill uit de import-notitie). Onderscheid dat Arsalan vroeg: "Nog te openen"
  (Lopend 372 + Wacht 69 = 441; wordt in fases heropend) vs "BaseNet-archief" (Gereed 148 +
  Geannuleerd 15 + Offerte 3 = 166; blijft dicht). Badge in dossierlijst + detailpagina; import
  vult het veld voortaan zelf. Luxis-status ONGEMOEID (heropenen blijft de fase-aanpak).

### Verificatie
Rentetests 47 groen + test_cases 32 groen + nieuwe test_basenet_origin_status 9 groen (zelf
gedraaid). `uvx ruff` schoon, `tsc --noEmit` groen. Migraties s207c op prod = head, 607/607
zaken herkomst gevuld (0 leeg), 166 "afgehandeld" matcht exact de eerdere meting. Live API:
`basenet_origin_status` komt mee in dossierlijst. Backups: `backup_pre_s207c` + `backup_pre_backfill`
op de VPS. Mailslot bleef DICHT.

### Vervolg (zelfde dag): werkfase-vondst + S207d
Lisanne herkende 2 "Offerte"-zaken als lopende procedures → bron gecheckt: BaseNet's
werkstatus **"Procedure loopt" (57310) hangt in hun statusconfig onder hoofdgroep "Offerte"**
(inrichtingsfout kantoor). pstatus = hoofdgroep, `incstatus` → CustomProjectStatus = de echte
werkfase. IN100310/IN100407 op prod gecorrigeerd naar 'Lopend' (nu 443/164); IN100167
(Fideal, fase "Invoer", geen vaste opdrachtgever) blijft archief — keuze Lisanne.
**S207d gebouwd + LIVE:** `Case.basenet_origin_phase` (migratie s207d + `backfill_basenet_phase.py`,
607/607 gevuld) — de werkfase per zaak ("B2C 3e sommatie verstuurd", "Procedure loopt", …) als
hard veld, zichtbaar in badge-tooltip + detailpagina. Belang: het S181-heropeningsrecept (CSV,
372 zaken) dekte deze zaken NIET; de fase-heropening kan nu uit de DB zelf de juiste stap bepalen.
Valkuil genoteerd in `scripts/basenet/mapping.py` voor de volgende import.

### Bekende issues / aandachtspunten
- **Draaiboek-eis toegevoegd** (`PLAN-heropening-werkvoorraad.md` #9): script-heropening moet
  `interest_freeze_date` wissen, anders blijft een heropende zaak bevroren (UI/service doet dit al).
- **Heropening:** IN100310/IN100407 ("Procedure loopt") staan NIET in het S181-recept-CSV —
  meenemen bij de fase-heropening (nu vindbaar via `basenet_origin_phase`).
- Voorstel (niet gebouwd, scope): filter "Nog te openen" op de dossierlijst voor de fase-heropening.
- WIK-rentebijlage: plan klaar, wacht op KvK-API (Arsalan vraagt aan). Bouwen = Opus.

## Sessie demo Lisanne (13 juli 2026, Opus-bouwsprint — rentecorrectie + 6 demo-punten, LIVE)

### Samenvatting
Live demo met Lisanne. Kernbevinding: renteberekening klopte niet (IN100197 toonde
€284,62; BaseNet rekent €723,32). Oorzaak: dossiers op wettelijke handelsrente i.p.v.
AV-rente **2%/maand samengesteld** (rente-op-rente per maand). Nieuwe rekenkern
`calculate_monthly_compound_interest` reproduceert de BaseNet-rentespecificatie van
IN100197 **regel-voor-regel op de cent** (tests: `test_interest_monthly.py`). Daarna 6
demo-punten afgetikt, elk getest + gedeployd. Migratie `s207b_interest_freeze_date` live.

- **Rente** — 2%/mnd samengesteld; uitgerold over 598 dossiers van 8 AV-opdrachtgevers
  (`scripts/rollout_av_rente.py`, backup vooraf). Creditfactuur = negatieve rente die wegvalt.
- **Adres** — kantoor verhuisd per 1 juli → Willem Fenengastraat 16E, 1096 BN Amsterdam,
  tel 020-3086621. Tenant-record + Renteoverzicht-sjabloon (had oud adres hardcoded → nu
  `{{ kantoor.adres }}`). E-mail bewust incasso@ gelaten.
- **Regelingen** — 24 ontbrekende (afgeronde) betalingsregelingen geïmporteerd (13→37);
  status uit meting van echte betalingen (`scripts/import_historical_arrangements.py`).
- **Rentedatum/bevriezing** — `Case.interest_freeze_date`: rente stopt op gekozen datum;
  `get_financial_summary` valt zonder peildatum daarop terug (alle callers respecteren het);
  auto-bevriezen op laatste betaaldatum bij afsluiten; heropenen wist het. UI in DetailsTab.
- **Heropenen** — nieuwe vordering op gesloten zaak → weer in_behandeling + bevriezing weg.
- **Factuur-prompt** — betaal-endpoint geeft `case_fully_paid`; BetalingenTab toont dialoog.

### Meting gesloten zaken (na rente-uitrol)
574/580 gesloten zaken tonen openstaand (€3,95M) — grotendeels legitieme oninbare
archiefschuld. Echte probleemcategorie: **100 zaken "afbetaald maar klein spookrestant"
(samen €22k)** — regelingen onder de oude lagere rente afgesproken; onder de correcte
hogere rente blijft een restant. Bevriezen lost dit NIET op (IN100350: €264,82 blijft).
= zakelijke keuze Lisanne. Dashboard telt alleen actieve zaken, dus niet zichtbaar daar.

### Openstaand — volgende sessie (Fable neemt over)
1. **Backfill bevriesdatum op de ~574 gesloten zaken** = aanbevolen (het moet in de huidige
   tijd kloppen). Zet `interest_freeze_date` = laatste betaaldatum (of `date_closed` als er geen
   betaling is) op elke gesloten zaak → rente stopt op afwikkelmoment, geen doorlopend cijfer.
   Neemt de 100 "€22k spookrestant"-zaken vanzelf mee; het restant dat dan overblijft is het
   verschil oude-vs-nieuwe rente = per-zaak signaal voor Lisanne, geen bulk-afboeking.
2. **WIK-bijlage** — renteberekening-PDF bij eerste sommatie, **alleen VOF/eenmanszaak/particulier**;
   + KvK-API voor rechtsvorm. Fable zoekt wettelijke eis + KvK-koppeling uit.
3. **Invoer-map** met nieuwe zaken (nieuwer dan export 2 juli) — hoe overhalen.
Arsalan: Fable neemt de volgende sessie over (review + uitvoering).

## Sessie 206 (13 juli 2026, Opus autonoom + Fable-review — spoor S202: security/correctheids-fixes H1/H2/H3/M1/M2 + 2 review-must-fixes, LIVE)

### Samenvatting
Spoor S202 gekozen (na checklist S204/S205, zie onder). Alle 5 audit-fixes gebouwd
rood→groen→commit→push, daarna een adversariële **Fable-review** (die 2 extra must-fixes vond),
volledige suite (**1259 passed**), gedeployd (backend-only, geen migratie), live rooktest groen.

- **H1** — `save_attachment_to_case` hing een mailbijlage aan een dossier zónder tenant-check →
  cross-tenant `CaseFile`. Hergebruikt `_assert_case_in_tenant`. **Fable-vervolg:** zelfde gat op
  `POST /api/email/sync?case_id=` (force_case_id zonder check) → guard toegevoegd.
- **H2** — betaald-guard (`update_case_status` + `move_case_to_step`) nam bij een rekenfout stil €0
  aan (fail-open) → dossier mét saldo sloot geruisloos. Nu **fail-closed**. Twee verborgen bugs die
  het fail-open verborg mee-gefixt: `get_case_outstanding` lazy-loadde `case.client` (nu expliciete
  query op `is_btw_plichtig`); `calculate_case_interest` eiste tarieven ook bij een lege zaak (nu
  kortsluiting naar €0 vóór de tarief-check). **Prod ongewijzigd** (tarieven zijn geseed).
- **H3** — "Geïnd" (KPI + maandgrafiek) telde verwijderde betalingen (geen `is_active`-filter).
  **Fable-vervolg (erger):** 2 ongefilterde `Payment`-sommen in de **facturatie** (`calculate_provisie`
  + `get_incasso_invoice_preview`) → provisie op de cliëntfactuur telde verwijderde betalingen mee
  (bij 15% €750 te veel). `is_active` toegevoegd.
- **M1** — `CaseBulkStatusUpdate.case_ids` gecapt op 200 (was ongelimiteerd → lange lock/DoS).
- **M2** — `_try_auto_advance` schoof zonder saldo-check naar de volgende stap → weigert nu een
  terminale (Betaald/Afgesloten) én hold-stap.

### Fable-review-oordeel (adversarieel, read-only, model=fable)
H2 **SOLIDE** (diepst gecheckt: BTW-semantiek exact equivalent — `is_btw_plichtig` is NOT NULL;
kortsluiting raakt geen zaak mét vorderingen — alle aanroepers nagelopen; fail-closed prod-veilig —
batch vangt per zaak). H1/H3-fixes solide maar **onvolledig** → 2 must-fixes gebouwd (commits
`fc84b94` + `7ade2f1`), elk rood→groen bewezen. M1/M2 solide, elk 1 randgeval (backlog). Twee
H2-nitpicks (geen fix nodig): "probeer opnieuw"-tekst misleidend bij een persistente config-fout;
de "lazy-load"-diagnose in de H2-commit is onnauwkeurig (`Case.client` is mapper-`lazy=selectin`,
brak pas ná rollback/expiry — S204-vondst; de expliciete query is hoe dan ook robuuster).

### Gewijzigde bestanden
Backend: `email/sync_router.py` (H1 + sync-guard), `cases/service.py` + `incasso/service.py`
(H2 fail-closed + M2), `collections/service.py` + `collections/interest.py` (H2 wortel-fixes),
`dashboard/reports_service.py` (H3), `cases/schemas.py` (M1), `invoices/service.py` (H3-facturatie).
Test bij elke fix. **7 commits** (`f1800f1` H1 · `bf578e5` H2 · `57952e8` H3 · `f7835fd` M1 ·
`224b07c` M2 · `fc84b94` H3-facturatie · `7ade2f1` sync-guard). Geen migratie.

### Verificatie
Volledige suite **1259 passed** (20 min, detached in container). Elke fix eigen rood→groen bewezen.
`uvx ruff check backend/app/` schoon. Deploy: container healthy, code-markers (AUDIT-H1/H2/H3) in de
draaiende container bevestigd, image-ID matcht, HEAD=`7ade2f1`. Live rooktest (read-only): login +
`reports/kpis` + `reports/monthly` + `dashboard/summary` alle 200. Mailslot bleef DICHT.

### Checklist S204/S205 — afgevinkt
De 5 dagelijkse-job-rijen in `scheduler_heartbeat` ontbraken nog TERECHT: servertijd bij de controle
was 12 juli 20:47 UTC, de jobs draaien 06:00–06:35 UTC, en de backend herstartte 20:25. De opstartlog
toont alle 5 "Added job… Scheduler started" → geregistreerd en ingepland. Verschijnen ná 13 juli
06:35 UTC. Mechanisme gezond (de 5 periodieke jobs draaien vers, foutveld leeg). **Morgenochtend na
06:35 UTC herbevestigen.**

### Bekende issues / bewust NIET gedaan
- **Mail-verstevigingen (M4/M5/L4/L5/L6) overgedragen naar S207.** Reden: mailslot staat DICHT
  (0 actueel risico); **M4** (HTML-escaping van dossierdata in systeemmails, meerdere builders in
  `email/incasso_templates.py` + `invoices/service.py` + `followup_service.py`) raakt de opmaak van
  júridische brieven → verdient visuele controle die met de slot dicht niet kan; **M5** = opschoning
  van 39 bestaande adresvelden = schrijfactie op prod-data → apart akkoord. Locaties + recept per punt:
  `docs/security/S202-delta-audit.md`. **M3** (app-als-DB-superuser / RLS Fase 2) blijft bewust apart.
- Fable-randgevallen (backlog, geen fix): M1 — een selectie >200 dossiers geeft een kale 422-toast
  (later frontend-melding); M2 — zaken schuiven niet meer auto de hold-stap "Verweer beantwoorden"
  in (Lisanne verplaatst handmatig). Idem "Treffen van regeling" → "Bijhouden regeling".
- Mailslot blijft DICHT; niets verstuurd; geen prod-data gewijzigd.

### Volgende sessie
S207: mail-verstevigingen (M4 HTML-escaping + L4/L5/L6, test-baar zónder mailslot; M5-recipient-cap
in code + apart de 39-velden-datacorrectie mét akkoord). Óf ander S202-restspoor (S201-facturatie-import
/ S203-restpunten). Prompt: `docs/sessions/PROMPT-S207.md`.

## Sessie 205 (12 juli 2026, Fable+Opus — S204-beslislijst: 14-dagenbrief-zijdeuren dicht + mailsync-fix, LIVE)

### Samenvatting
Alle 6 punten uit de S204-beslislijst gebouwd, per taak rood→groen→commit→push, en de volledige
stack gedeployd (migratie s205, alle containers healthy).

**Juridisch — 14-dagenbrief-gate (art. 6:96 lid 6 BW) nu op ALLE drie de verzendwegen** via één
gedeelde controle (`check_dagenbrief_gate` in `collections/compliance.py`): (1) de bulk-knop
(bestond al, hergebruikt de helper), (2) de follow-up "Uitvoeren"-knop (`execute_recommendation`,
hard geblokkeerd mét reden — dekt ook approve-and-execute), (3) het AI-concept-verzendpad
(`compose/send`: verse niet-reply case-mail op een sommatie/dagvaarding-stap bij een consument →
422 `DAGENBRIEF_GATE`). **Verstuurd-proxy verstevigd:** de brief telt alleen nog als verstuurd bij
een échte verzending (`CaseStepHistory.email_sent`), niet meer bij stap-binnenkomst — sluit de
"doorschuiven telt als verstuurd"-zijdeur; het batch-pad zet die vlag nu ook na een geslaagde send.

**"Toch versturen"-noodknop — SIMPEL (instructie Arsalan):** géén verplicht redenveld. De frontend
toont bij een blokkade een ja/nee-bevestiging (consequentie in gewone taal); bij doorzetten legt
`record_dagenbrief_override` automatisch een onuitwisbaar spoor vast (CaseActivity + staphistorie-
notitie). ⚠️ Waarschuwingstekst = concept, nog langs Lisanne vóór B2C-livegang (haar beroepsrisico).

**14-dagenbrief zelf verstuurbaar (akkoord Arsalan, "allebei mogelijk"):** `template_type=
'14_dagenbrief'` op de stap (seed + idempotente migratie s205). LIVE bevestigd op prod.

**Mailsync-foutpad (bewezen defect, S204):** `email_auto_sync` deelde één sessie → een rollback bij
één kapotte postbus (verlopen token) expireerde álle accounts → het volgende crashte
(MissingGreenlet) en de hele run stopte. Nu een eigen sessie per account. LIVE bevestigd:
`email_auto_sync` draaide om 20:19 op prod zonder fout.

**Heartbeat "draait maar faalt":** de 5 kritieke dagelijkse jobs leggen bij intern falen nu
`last_error` vast; het dashboard-alarm toont dat (klaart vanzelf op na een schone run).

### Gewijzigde bestanden
- Backend: `collections/compliance.py` (gedeelde gate + sterke proxy + override-spoor),
  `incasso/service.py` (batch hergebruikt helper + mark-sent), `ai_agent/followup_service.py` (gate),
  `email/compose_router.py` (gate + `compliance_override`-veld), `workflow/scheduler.py` (sessie per
  account + heartbeat-fout), `dashboard/service.py` (alarm), migratie `s205_dagenbrief_template.py`.
- Frontend: `zaken/[id]/page.tsx` ("toch versturen"-bevestiging via `useConfirm`).
- Tests: `test_compliance_14dagenbrief`, `test_followup`, `test_compose_dagenbrief_gate` (nieuw),
  `test_scheduler_email_sync` (nieuw), `test_dashboard`. 7 commits (`d440081`…`ee465b9`) + deploy.

### Verificatie
128 tests groen over de geraakte suites (compliance/followup/compose-gate/scheduler-email/dashboard/
incasso-pipeline/s166), `uvx ruff check backend/app/` schoon, `tsc --noEmit` + `npm run build` groen.
Prod: `alembic=s205_dagenbrief_template`, 14-dagenbrief-stap draagt het sjabloon, `email_auto_sync`
draaide vers zonder fout. **Niet live end-to-end getest:** de gate zelf (mailslot DICHT; de 2 actieve
B2C-zaken IN100345/350 zijn stap-loos → gate vuurt niet). Frontend "toch versturen" alleen via
build/tsc, niet doorgeklikt.

### Bekende issues / aandachtspunten
- **Checklist (S204 ⚠a) — nog open:** de 5 dagelijkse-job-rijen in `scheduler_heartbeat` ontbreken
  nog (jobs draaien 06:xx UTC; sinds de heartbeat-deploy niet aan de beurt geweest). De 5 periodieke
  jobs hebben wél rijen → mechanisme werkt. **Opnieuw checken na 13 juli 06:40 UTC.**
- Waarschuwingstekst noodknop moet langs Lisanne vóór echte B2C-verzending.
- Mailslot blijft DICHT; niets verstuurd.

### Volgende sessie
S206: kies één spoor — S201 facturatie-import (439 conflict-vrije facturen, apart akkoord nodig),
S202 security-fixes (H1/H2/H3), of S203-restpunten (35-route-sloop, #7 audittrail, #15 regeling-badge,
log-persistentie). Prompt: `docs/sessions/PROMPT-S206.md`. Eerst de checklist hierboven.

## Sessie 204 (12 juli 2026, Fable — review S203-voorkant-fixes, 100% read-only)

### Samenvatting
Alle S203-fixes (15 commits + na-tag `27842a2`) in de bron nagelezen, tegengesproken en op prod
gecontroleerd (GET-API + read-only SQL). **9 van 11 bevestigd zonder voorbehoud**: tijdlijn (#13),
hernoem-PATCH incl. cross-tenant-404 (#4), €0-markering incl. pop-vóór-prompt + end-to-end test (#3),
1169→1 (#6, prod: 1168/1169 met marker, de ene = "Arsalan"), batch-toast (#9), ratio zelfde populatie
+ cap (#10, prod 5,3), openstaand-labels (#14), intake-startstap = kopie van creatiepad (#8),
logout/Gmail (#16/#17). Heartbeat (#2) werkt bewezen op prod (5 verse rijen). Volledig rapport mét
bewijs per fix: **`docs/sessions/S204-review.md`**.

### Twee gevonden punten (vervolg-bouwsessie nodig)
1. **Mailsync-foutpad (#1) — bewezen latent defect:** `rollback()` in de except expireert álle
   account-objecten (negeert `expire_on_commit=False`); het volgende account crasht op zijn eerste
   attribuutlezing met MissingGreenlet en de log-f-string in de except gooit een tweede → hele run
   stopt. Eén structureel falend account (verlopen token) blokkeert zo elke 5 min de sync van de
   accounts erná, zonder eigen foutmelding en zonder dashboard-alarm. Bewezen met probe op de echte
   sessie-factory. Het gevreesde "geslaagde sync teruggerold" is wél afgedekt (commit per account).
2. **14-dagenbrief-gate (#5) — batch-gate zelf correct, maar 2 zijdeuren + zwakke proxy:**
   follow-up "Uitvoeren" (`execute_recommendation`, 14 pending aanbevelingen op prod) en het
   AI-concept-verzendpad (compose/send + advance-after-send) versturen sommaties zónder gate;
   en `entered_at` = stap-binnenkomst, niet verzending (doorschuiven zonder versturen telt als
   "verstuurd"). Operationeel gat: de 14-dagenbrief-stap heeft op prod geen sjabloon → Luxis kan de
   brief zelf nu niet versturen; beide actieve B2C-zaken (IN100345/350) staan stap-loos → vandaag
   geen acuut risico (batch skipt ze al eerder).

### Verificatie
155 tests groen (8 S203-suites, docker), ruff schoon, prod `alembic_version=s203b`. Prod-API:
`contacts_this_month=1`, `collection_rate=5.3`, `scheduler_alerts=[]`; SQL: 3 sync-accounts vers +
foutveld leeg, heartbeats 18:47, `case_step_history=0` (verwacht: nog geen intake/stap-actie sinds
deploy). Niet geverifieerd: frontend visueel (alleen code + S203-livecheck), dagelijkse
heartbeat-rijen (bestaan pas na de nacht), live logout (zou prod-tokens intrekken — bewust overgeslagen).

### Volgende sessie
S205: beslislijst uit `S204-review.md` §Beslislijst — (1) gate in follow-up, (2) gate in
concept-verzendpad, (3) verzend-proxy verstevigen, (4) mailsync-foutpad, (5) dagenbrief-sjabloon
op de stap (besluit), (6) heartbeat-last_error bij interne jobfouten, (7) check dagelijkse-job-rijen.

## Sessie 203 deel 2 (12 juli 2026, Opus — voorkant-fixes UITGEVOERD + LIVE)

### Samenvatting
Eerst Codex' read-only audits nagecontroleerd (fable-diepte): 8 security-bevindingen zelf in de
bron teruggevonden (alle 8 kloppen), facturatie-onderzoek onafhankelijk hergeteld tegen de
BaseNet-export (567/773/€235.899,91 + de 7 Mollie-conflicten op de seconde) — **Codex-review
betrouwbaar, eerste keer goed gegaan**. Daarna: 11 van 12 S203-taken gebouwd, per fix
rood→groen→commit→push→deploy, 4 deploys, migraties `s203`/`s203b` op prod, alle containers healthy.

**Ronde 1 (klein, live):** (13) tijdlijn-crash `duration_seconds`/`entry_date` → `duration_minutes`/
`date` (+ sibling-bug). (4) hernoem-knop: PATCH `/api/cases/{id}/files/{id}` gebouwd + onError.
(3) AI-concept bij €0-terugval markeert draft + reviewtaak (gegate op €-sjabloon; regressie in
draft-gate zelf gevangen+gefixt). (6) "1169 toegevoegd deze maand" → import-marker uitgesloten,
**live 1169→1**. (9) batch-fouten als waarschuwing mét redenen i.p.v. groene toast. (11/12) nep-tabs
Meldingen+Weergave verwijderd. (10/14) incasso-ratio zelfde populatie + gecapt **49,1%→5,3% live**;
negatief "Openstaand" → "teveel betaald"; lijstkolom "Openstaand (hoofdsom)".

**Ronde 2 (middel, live):** (1) mailsync-gezondheid: `last_sync_error`-veld + banner (rood mislukt /
amber >60min / laatst-gesynct), scheduler zet fout per account atomisch. (2) scheduler-heartbeat:
nieuwe `scheduler_heartbeat`-tabel + APScheduler-listener legt elke job-run vast; dashboard toont
rood alarm als een kritieke dagelijkse job (o.a. verjaringscontrole) >25u niet draaide. (8) intake
wijst nu de eerste pijplijn-stap + historie-rij toe (Staphistorie vult zich weer; going-forward).
(5) 14-dagenbrief-waarborg leest het echte spoor (`CaseStepHistory`) i.p.v. de lege tabel; de batch
blokkeert een B2C-sommatie **hard** als de 14-dagenbrief niet verstuurd is óf binnen 15 dagen daarna
(besluit Arsalan: nooit eerder dan 15 dagen; `DAGENBRIEF_MIN_DAYS=15`). (16/17) logout trekt tokens
server-side in, Gmail-knop verborgen, dode hook `usePendingCount` weg.

### Verificatie
Elke fix: gerichte tests groen (nieuwe tests bij elke fix), `uvx ruff` schoon, `tsc --noEmit` groen.
Betrokken suites samen groen (incasso-pipeline 51, dashboard 23, intake 27, email-sync 28, RLS-drift 8,
compliance-14dagenbrief 3, e.a.). Migraties `s203`+`s203b` op prod = head, containers healthy. Live
via API bevestigd: `contacts_this_month` 1→ (was 1169), `collection_rate` 5.3 (was 49,1), `scheduler_alerts`
veld werkt. Valkuil-les: mijn eerste fix-3 markeerde óók bedragenloze sjablonen + lekte een context-sleutel
in `build_user_prompt` — beide door de draft-gate-tests gevangen vóór deploy (fable-tegenspreker).

### Bekende issues / bewust niet gedaan (scope)
- **35-route backend-sloop niet uitgevoerd** — ⚠️-trace + 3 "niet slopen zonder besluit"-uitzonderingen;
  vraagt een eigen per-route-verificatieronde, niet aan het eind van deze lange sessie geforceerd.
- **#7 document-audittrail** en **#15 regeling-badge** stonden niet in de S203-takenlijst → open.
- **#5 juridisch besloten (Arsalan):** harde blokkade, nooit een sommatie eerder dan 15 dagen ná de
  14-dagenbrief. Open detail voor Lisanne: een buiten Luxis verstuurde 14-dagenbrief moet handmatig
  in het systeem geregistreerd worden, anders blokkeert de gate terecht.
- De 10 bestaande stap-loze intake-zaken zijn een aparte data-actie (going-forward-fix raakt ze niet).
- Mailslot bleef DICHT; niets verstuurd. Statusregel per bevinding: `docs/sessions/S200-BEVINDINGEN.md` (tabel bijgewerkt).

### Incident bij afsluiting — per ongeluk gecommitte bestanden, historie herschreven (mét akkoord)
Bij het sessie-einde veegde één `git add -A` **110 bewust-untracked bestanden** mee in een docs-commit,
waaronder het **derdengelden-bankafschrift** (CSV, 1 jaar), AV-PDF's, `.agents/` en tmp-audit-SQL.
Afhandeling (expliciet akkoord Arsalan): laatste 3 commits vervangen door één schone (`3f5e183`),
force-push, lokaal én op de VPS alle oude objecten vernietigd (reflog+gc; CSV-blob aantoonbaar weg
op beide), VPS-HEAD gelijkgetrokken (ff-pull werkt weer normaal). Tag `sessie-203-fixes` stond vóór
de foute commit → ongemoeid. **Restrisico:** GitHub kan de weggegooide commits server-side nog even
vasthouden tot hun eigen opruiming (privérepo; niet meer bereikbaar via branch/tag). **Borging:**
`.gitignore` dekt de paden nu; harde regel "nooit `git add -A`, stage expliciete paden" toegevoegd
aan CLAUDE.md + AGENTS.md + Claude-memory.

### Volgende sessie
**S204 = Fable-review van deze S203-fixes** (`docs/sessions/PROMPT-S204-fable-review.md`): read-only,
bron + prod nalezen, tests draaien, elke fix tegenspreken. Pas daarna nieuw bouwen (S201-import óf route-sloop).

---

## Sessie 203 deel 1 (12 juli 2026, Sol Ultra — Codex-master Fase A+B, read-only)

### Samenvatting
- **Fase A mailpadaudit afgerond.** Blok 2 in `docs/security/S202-delta-audit.md` is gevuld en onafhankelijk tegengesproken. Nieuwe kern: ongeëscapete dossierdata in systeemmail-HTML, ontvangers niet centraal gevalideerd/begrensd, late bijlagecaps, mailslotcache vóór commit en logvervalsing/PII in logs. Alle drie applicatietransporten controleren het mailslot; prod stond effectief dicht.
- **Fase B BaseNet-onderzoek afgerond.** De parser las 133 entiteiten, 65.761 records en 2 defecte LetterTemplate-fragmenten. De twee gevraagde bouwdocumenten bestaan: facturatierecept plus een volledige 133-rijenmatrix die exact terugtelt.
- **Factuurbesluit:** van 567 koppen/773 regels zijn 439 koppen/630 regels conflict-vrij en automatisch importeerbaar (€302.750,39 bruto; €72.762,09 open). Zeven koppen (€10.854,66) hebben een harde Mollie-`paid` versus volledig-open-koptegenstrijdigheid en blijven buiten automatische import. Negentig derdengeld-/verrekenposten (−€90.718,21) horen niet in omzet.
- **Grootste migratiegat:** 187 niet-geïmporteerde D-dossiers dragen 8.637 correspondentiestukken en 1.236 urenregels. De 1.320 uren worden pas na die dossiers apart geïmporteerd. Donker/Dinc: 12 credits (€21.738,96) zijn geen kantoorfactuurbetalingen; bestaand besluit blijft staan.
- Geen productie-mutatie, geen import, geen mail en geen deploy uitgevoerd.

### Gewijzigde bestanden
- `docs/security/S202-delta-audit.md` — mailpadblok, samenvatting en fixvolgorde bijgewerkt.
- `docs/research/S201-facturatie-recept.md` — gemeten veldmapping, disjuncte importgroepen, betalingen, urenadvies, Donker/Dinc en bouw-/testrecept.
- `docs/research/S201-volledigheidsmatrix.md` — alle 133 entiteiten, relevante gaten en concrete acties.
- `SESSION-NOTES.md` + `LUXIS-ROADMAP.md` — overdracht naar Sol High; S192-entry naar archief.

### Verificatie
- Mailregressie: 26 passed, 1 warning; transports geblokkeerd, geen mail verstuurd. Read-only prod: mailslot dicht, 3 echte accounts versleuteld, 0 `email_logs`.
- Bronasserties: kopgroepen `439+7+12+19+90=567`; regelgroepen `630+13+9+0+90+31=773`; geldsom exact €235.899,91. Regelformule 773/773 en kop-regelsom 542/542 exact. Voor 305 historische betalingen blijft de betaaldatum eerlijk onbekend; memoriaaldatum wordt alleen boekingsmetadata.
- Matrixassertie tegen verse parserrun: 133/133 entiteiten, 65.761/65.761 records, geen ontbrekende/extra/mismatched rij.
- Productie read-only: 58/58 debiteurcodes en 146/146 IN-codes matchen elk exact één Luxis-record; factuur-/uren-doeltabellen staan op 0.

### Bekende issues
- De zeven Mollie/kop-conflicten vereisen per factuur bevestiging door Lisanne/boekhouding vóór import.
- Niet geverifieerd: of de reeks “Facturen met Stephanie” en zeven toekomstige D-afspraken al in Outlook staan; Outlook was niet via een connector beschikbaar.
- S200's 19 voorkantbevindingen en S202-fixes H1/H2/H3/M1/M2 plus mailhardening zijn nog niet gebouwd. M3 (DB-superuser/RLS Fase 2) blijft bewust buiten deze fixronde.

### Volgende sessie
- Zet Codex op Sol High en vervolg `docs/sessions/PROMPT-CODEX-master.md` vanaf Fase C. Werk per fix rood→groen→commit→push→deploy; daarna Fase D en Fable-nacontrole.
