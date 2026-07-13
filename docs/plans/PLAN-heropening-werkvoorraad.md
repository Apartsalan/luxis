# PLAN — Heropening werkvoorraad (uitvoering S181)

**Rang: 1 (hoogste leverage) — maar GEBLOKKEERD tot Lisanne's akkoord op het A4**
(`docs/sessions/LISANNE-A4-heropening.md`). Zonder dat akkoord: niet starten.

## Doel

De door Lisanne goedgekeurde groep(en) uit de 372 lopende BaseNet-zaken heropenen in
Luxis, mét de juiste pijplijnstap per zaak, zonder dat er iets verstuurd wordt en zonder
saldi te raken. Bron per zaak: `docs/sessions/S181-werkvoorraad-recept.csv` (kolom
`voorstel_stap`). Achtergrond en bewijs: `docs/sessions/RAPPORT-S181F-heropeningsaudit.md`.

## Waarom SQL en niet de API

Status 'afgesloten' is terminaal in de service-laag (S175b-precedent: proefzaken zijn ook
via SQL heropend). Batch-SQL per groep is sneller en atomisch. De API-route zou 372 calls
en een niet-bestaand "heropen"-endpoint vergen.

## Exacte gegevens (geverifieerd op prod, 7 juli 2026)

- Toewijzen aan Lisanne's eigen account: `assigned_to_id = 'c9b134ef-5115-4715-ac3f-0fcbe4102f11'`
  (lisanne@kestinglegal.nl, rol advocaat). NIET het admin-account (…0002, seidony@).
- Actieve stap-ID's (verifieer vóór gebruik met de query in stap 1):

| Stap | id |
|---|---|
| 14-dagenbrief | a31f9658-06ff-4b3f-893b-c806b579f49b |
| Eerste sommatie | b45261b0-2fed-438e-bee2-a27242d715b7 |
| Tweede sommatie | e0c75608-e331-4f80-8849-7ada25b48c96 |
| Derde sommatie | 1d91fbb2-bb41-4cd0-8a6e-33f596732ed7 |
| Sommatie laatste mogelijkheid | 7659a724-e084-4e2f-be5c-3bd8eba1bad9 |
| Verweer beantwoorden | bad2f285-01ae-4c9e-b822-404699d1fe19 |
| Opvragen stukken bij cliënt | bc4a4289-1aa9-43d9-b40f-73fba35a4ee4 |
| Voorstel dagvaarding | 4769771f-864d-4f49-ad5e-e3e385a1c121 |
| Treffen van regeling | 61ada7f3-f190-48ac-a220-ef4d117031c2 |
| Bijhouden regeling | 5a02cca3-f9b2-454f-a11a-894d0c7a5746 |

- DB-toegang: `ssh -i ~/.ssh/luxis_deploy root@46.225.115.216` →
  `cd /opt/luxis && docker compose exec -T db psql -U luxis -d luxis`

## Stappenplan

1. **Verifieer de vaste gegevens** (stap-ID's, user-id, vlag):
   ```sql
   SELECT id, name FROM incasso_pipeline_steps WHERE is_active ORDER BY sort_order;
   SELECT id, email FROM users WHERE email='lisanne@kestinglegal.nl';
   SELECT pipeline_auto_drafts_enabled FROM tenants;  -- MOET false zijn
   ```
   Wijkt iets af van dit plan → stoppen en aan Arsalan melden.
2. **Bepaal de groep** uit Lisanne's akkoord (bv. LegalWork B.V. = adviesgroep 1).
   Filter het recept-CSV op `opdrachtgever`, sluit uit: `voorstel_stap` in
   (NIET HEROPENEN / UITZOEKEN / AFRONDEN…) en de 3 proefzaken (IN100215/IN100040/IN100521
   staan al open — die krijgen alléén een stap, geen status-update).
3. **Maak per stap-bucket een UPDATE** (voorbeeld voor één bucket):
   ```sql
   BEGIN;
   UPDATE cases SET status='nieuw', date_closed=NULL,
     assigned_to_id='c9b134ef-5115-4715-ac3f-0fcbe4102f11',
     incasso_step_id='<stap-id>', step_entered_at=now(), updated_at=now()
   WHERE case_number IN ('IN1000xx', ...) AND status='afgesloten';
   -- rijenaantal MOET exact het verwachte aantal zijn, anders ROLLBACK
   COMMIT;
   ```
4. **Betwiste zaken:** zet in dezelfde transactie het verweer-vinkje:
   ```sql
   UPDATE cases SET has_verweer=true WHERE case_number IN (<betwiste van deze groep>)
     AND has_verweer=false;
   ```
   (88 zaken totaal hebben fase "Vordering betwist" — zie recept-CSV kolom `vlaggen`.)
4b. **Rente — GROTENDEELS AL GEDAAN (S207b-uitrol 13 juli + S208-verificatie).** Het
   S188b-besluit (b2b van de holding-opdrachtgevers = AV-rente art. 13.3, b2c = wettelijke
   rente) is op 13 juli al over ALLE 607 BaseNet-zaken uitgerold en in S208 dossier-voor-
   dossier geverifieerd (607/607 conform, beide lagen: zaken + vorderingen op maandbasis).
   Bij heropening hoeft er dus GEEN rente-SQL meer — alleen controleren, niet zetten.
   ⚠ Gecorrigeerd t.o.v. de oorspronkelijke plantekst: de rente is **samengesteld**
   (`contractual_compound=true`, rente-op-rente per maand) — bewezen met de BaseNet-
   rentespecificatie van IN100197 (€723,31 op de cent; gouden test
   `tests/test_interest_monthly.py`). De oude regel hier zei `false` (enkelvoudig) en
   stamt van vóór de demo-vondst; die letterlijk uitvoeren zou de uitrol deels terugdraaien.
   Controle na heropening van een groep: renteoverzicht van 1 dossier in de UI —
   maandbedrag ≈ openstaande basis × 2%, en de bevriezing is gewist (rente loopt weer).
5. **Rooktest in de UI** (login lisanne@ of seidony@): incasso-werkstroom toont de zaken
   in de juiste kolom; open 3 dossiers: saldo klopt met kolom `open_ruw` uit het recept
   (± rente/kosten — Luxis toont meer dan de ruwe kolom, dat is juist), deadline-kleur
   aanwezig, geen crash op de regeling-sectie.
6. **Volgende groepen** pas na expliciet akkoord per groep (klein beginnen was de afspraak).

## Randgevallen (gevonden bij de audit — mis ze niet)

- **Regeling-zaken ALTIJD naar "Bijhouden regeling"** (hold-stap, geen timeout, geen
  sjabloon), óók als hun BaseNet-fase iets anders zegt. Het zijn er 12 in de 372 + 
  **IN100019 staat in BaseNet op "Wacht" en zit dus NIET in het recept-CSV** — wel
  meenemen bij de regeling-groep (actieve regeling, termijn 9 juli).
- **11 zaken met gestopte/afgelopen regeling** (recept: `BEOORDELEN: regeling gestopt`)
  NIET automatisch een sommatie-stap geven — eerst Lisanne.
- **De 8 "voldaan"-zaken en IN100555 (D-Break) en IN100409 (leeg dossier: 0 vorderingen)
  nooit heropenen** — staan zo in het recept.
- `is_active` staat op prod bij ALLE zaken op true (ook afgesloten) — niet aanraken,
  de opvolg-filters draaien op `status`, niet op `is_active`.
- SQL-update schrijft **geen regel in `case_step_history`** — de eerste stap-overgang
  ontbreekt dan in de historie-weergave. Cosmetisch; deadline-kleuren gebruiken
  `step_entered_at` (kolom op cases) en werken gewoon. Accepteren en benoemen.
- `step_entered_at = now()` betekent: followup-aanbevelingen verschijnen zodra
  `min_wait_days` van de stap verstreken is (0-4 dagen). Dat is gewenst gedrag; het
  verstuurt niets. Verwacht op dag 1 wel ESCALATE-ruis voor hold-stap-zaken zolang
  PLAN-followup-hold-steps niet is uitgevoerd.
- **Rentetype controleren vóór er brieven met bedragen uitgaan (S185):** Arsalan bevestigt
  dat de AV-rente van art. 13.3 (2%/mnd, contractueel) geldt; de 4 herrekende zaken
  (o.a. COLLECT 1) stonden echter op `interest_type='commercial'` (wettelijke handelsrente).
  Per opdrachtgever-groep checken welk rentetype de zaken dragen en zonodig eerst
  voorleggen/rechtzetten — anders rekenen sommaties met het verkeerde tarief.
- Draait de **verweer-mail-trigger**: een binnenkomende mail die als verweer wordt
  geclassificeerd kan een heropende hoofdpad-zaak automatisch naar "Verweer beantwoorden"
  verplaatsen (+ concept + taak). Verstuurt niets; niet als bug rapporteren.
- Proefzaak IN100215 heeft een actieve regeling → stap "Bijhouden regeling"; IN100040
  ("Procederen?") → "Voorstel dagvaarding"; IN100521 (B2C 4e sommatie) → "Voorstel
  dagvaarding" — alleen `incasso_step_id`/`step_entered_at` zetten, status is al 'nieuw'.

## Acceptatiecriteria

1. Query: aantal zaken `status='nieuw' AND incasso_step_id IS NOT NULL` == verwacht
   aantal van de groep (+3 proefzaken als die een stap kregen).
2. Query: 0 heropende zaken zonder `assigned_to_id`; 0 met `date_closed IS NOT NULL`.
3. Query: alle heropende regeling-zaken staan op stap 'Bijhouden regeling'.
4. `SELECT count(*) FROM email_logs` is vóór == ná de operatie (er is niets gemaild).
5. `pipeline_auto_drafts_enabled` is nog steeds false.
6. UI-rooktest (stap 5) gedaan en beschreven in SESSION-NOTES.
7. **Vangnet BaseNet-gesloten dossiers (akkoord Arsalan, S185):** ná elke heropen-batch
   MOET deze query 0 rijen geven — de 163 dossiers die in BaseNet al dicht waren
   (148 Gereed + 15 Geannuleerd) mogen nooit heropend worden:
   ```sql
   SELECT case_number, status FROM cases
   WHERE (debtor_notes LIKE '%BaseNet-status: Gereed%'
          OR debtor_notes LIKE '%BaseNet-status: Geannuleerd%')
     AND status <> 'afgesloten';
   ```
   Nulmeting S185 (8 juli, tegen de originele backup Xml_02-07-2026_2400.zip geverifieerd):
   alle 163 op 'afgesloten', 0 uitzonderingen. Rijen ≠ 0 → direct terugdraaien + Arsalan.
8. SESSION-NOTES + LUXIS-ROADMAP bijgewerkt; commit + push + tag.
9. **Rente-bevriezing wissen bij heropenen (S207c, 13 juli).** Alle 580 gesloten
   zaken kregen een `interest_freeze_date` (rente bevroren op afwikkel-/rentedatum).
   Heropenen via de UI/service (`update_case_status`, `_reopen_case_on_new_debt`)
   wist dat veld automatisch → rente loopt weer door. Maar een heropening via een
   **script dat `case.status` rechtstreeks zet** (zoals `s195_reopen_book.py`) doet
   dat NIET. Voor de fase-heropening dus verplicht: bij het openzetten óók
   `interest_freeze_date = NULL` zetten, anders blijft de rente bevroren staan en
   loopt een heropende, weer-lopende zaak niet meer op. Controlequery ná elke batch:
   ```sql
   SELECT case_number FROM cases
   WHERE status IN ('nieuw','in_behandeling') AND interest_freeze_date IS NOT NULL;
   ```
   moet 0 rijen geven (een handmatig gezette peildatum op een lopende zaak is de
   enige legitieme uitzondering — controleer dan per geval).
