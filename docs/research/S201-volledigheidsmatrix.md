# S201 — Volledigheidsmatrix BaseNet → Luxis

**Status:** read-only gap-analyse, 12 juli 2026  
**Hoofdconclusie:** de eerdere IN-migratie is voor relaties, incassodossiers en IN-correspondentie grotendeels sluitend. De grootste echte ontbrekende ruggengraat is **187 D-dossiers**; daardoor ontbreken ook vrijwel alle D-correspondentie en kunnen 1.236 urenregels niet correct worden gekoppeld.

## 1. Reikwijdte en bewijs

De volledige parserrun las 137 XML-bestanden, herkende **133 entiteiten** en telde **65.761 records**. Twee fragmenten in `rela.lettertemplate` konden niet worden geparseerd; alle andere gemelde entiteiten en tellingen zijn verwerkt. De matrix hieronder bevat exact 133 rijen en telt terug op tot 65.761.

Fresh read-only productiebeeld voor tenant `seidony@kestinglegal.nl`:

| Luxis-object | Productie |
|---|---:|
| Relaties | 1.169 |
| Relatie↔organisatie-links | 0 |
| Dossiers | 607 |
| Vorderingen | 1.563 |
| Dossierbetalingen | 272 |
| Betalingsregelingen | 13 |
| Regelingstermijnen | 121 |
| Gesynchroniseerde e-mails totaal | 6.509 |
| Geïmporteerde BaseNet-archiefmails | 6.393 |
| Dossierbestanden | 2.619 |
| Facturen / regels / factuurbetalingen | 0 / 0 / 0 |
| Tijdregels | 0 |
| Toekomstige actieve Luxis-agenda-items vanaf 02-07-2026 | 0 |

“Geïmporteerd” betekent functioneel in Luxis aangetroffen, niet dat alleen het gelijknamige BaseNet-record rechtstreeks is gekopieerd. “Nee” betekent evenmin automatisch “moet mee”: veel rijen zijn systeemlogs, lookups of oude configuratie.

## 2. Prioriteit: wat werkelijk nog moet gebeuren

| Prioriteit | Besluit | Gemeten omvang |
|---|---|---:|
| **P0 — nu handmatig controleren** | Agenda vergelijken met Lisannes echte Outlook-agenda; niets blind importeren | 7 nog toekomstige D-afspraken plus 1 reeks van 94 “Facturen met Stephanie” |
| **P1 — aparte migratie bouwen** | D-dossiers importeren zonder incassopipeline en met behoud van bronstatus | 187 dossiers: 84 Lopend, 74 Gereed, 15 Geannuleerd, 14 Wacht |
| **P1 — volgens apart recept** | Conflict-vrije definitieve kantoorfacturen importeren | 439 koppen, 630 regels, € 302.750,39 bruto; 7 Mollie/kop-conflicten eerst reconciliëren |
| **P2 — na D-dossiers** | Uren en D-correspondentie migreren | 1.320 uren; 8.637 D-correspondentierecords |
| **P2 — gerichte datacorrectie** | Contactpersonen koppelen en echte persoonsgegevens aanvullen | 145 links, 28 geboortedatums, 83 afwijkende/gesplitste e-mailwaarden |
| **P2 — menselijke review** | BaseNet-taakrestant niet bulkimporteren; alleen actuele tegenstrijdigheden tonen | 29 open taken op 26 actieve dossiers plus 2 toekomstige taken op gesloten dossiers |
| **P3 — inhoudelijke inventarisatie** | Oude e-mail-, brief- en rapporttemplates vergelijken met ManagedTemplate | 48 e-mail-, 64 brief- en 7 rapporttemplates |

### Waarom de D-dossiers eerst komen

De export bevat 187 D-dossiers. Daarvan worden **183/187** door minimaal één andere gegevenssoort gebruikt:

- 1.236 uren op 54 D-projecten;
- 528 factuurregels op 137 D-projecten;
- 8.637 brieven/mails/documenten op 183 D-projecten;
- 72 taken en 93 agenda-items op D-projecten.

Luxis ondersteunt algemene dossiers al, maar productie bevat nu alleen de 607 IN-dossiers. De D-migratie is daarom geen nieuwe productmodule: zij vult de ontbrekende dossiers waarop bestaande facturen, uren en correspondentie moeten kunnen landen.

## 3. Correspondentie sluitend verklaard

`rela.letter` bevat 17.928 records:

| Groep | Records | Verklaring |
|---|---:|---|
| IN-projecten | 9.106 | Hieronder exact uitgesplitst |
| D-projecten | 8.637 | Niet geïmporteerd omdat de D-dossiers ontbreken |
| Zonder project | 185 | Handmatig classificeren; geen veilige dossierkoppeling |
| **Totaal** | **17.928** | Exact |

De 9.106 IN-records sluiten als volgt:

- 3.308 uitgaande + 3.115 inkomende e-mailrecords = 6.423 verwachte mails;
- 6.393 BaseNet-archiefmails staan op productie, dus **30** richting-3/4-records ontbreken; de precieze oorzaak is niet geverifieerd;
- 2.683 niet-maildocumenten = 2.619 geïmporteerde dossierbestanden + 64 bewust overgeslagen geüploade `.eml`-bestanden;
- `6.393 + 30 + 2.619 + 64 = 9.106`.

Er is dus geen onverklaard gat van duizenden stukken binnen IN. Het grote ontbrekende blok is D. De 30 IN-mailverschillen en 185 projectloze records verdienen een kleine uitzonderingenlijst, niet een nieuwe bulkimport.

## 4. Taken en agenda

### Taken

Van 1.613 taken zijn 1.150 gereed, 461 open en 2 wachtend. De meeste open taken zijn oude BaseNet-pipelinestappen. Op de 27 momenteel actieve Luxis-IN-dossiers vallen **29** open BaseNet-taken op 26 dossiers; alle zijn gedateerd op of vóór 27 juni 2026. Slechts twee bron-taken liggen ná 12 juli: IN100588 op 13 juli en IN100305 op 15 december. Beide zaken zijn in Luxis gesloten. Productie heeft twee andere actieve workflowtaken.

Aanbeveling: geen 463 oude open/wacht-taken bulkimporteren. Maak één leesbare reviewlijst van de 29 actieve-dossiertreffers en controleer daarnaast de twee toekomstige taken op gesloten dossiers. De huidige Luxis-dossierstand blijft leidend.

### Agenda

Van 229 agenda-items liggen 103 na de exportdatum 2 juli 2026. Daarvan zijn 94 instanties van één terugkerende afspraak “Facturen met Stephanie”; de overige 9 zijn losse D-dossierafspraken. Twee van die negen vonden op 9 juli plaats. Op de onderzoeksdatum 12 juli resteerden dus **7** toekomstige losse afspraken. Productie heeft in totaal nul agenda-items. Een externe Outlook-agenda kon in deze sessie niet worden gecontroleerd.

| Datum | Dossier | Onderwerp |
|---|---|---|
| 14-07-2026 | D100156 | Zitting Gromic faillissement |
| 14-07-2026 | D100153 | Faillissement Yaha Stone / Paskov |
| 14-07-2026 | D100162 | Faillissementszitting Bathroom Solutions |
| 17-07-2026 | D100163 | Memorie van antwoord inzake Liem |
| 12-08-2026 | D100120 | Van der Kooij Besters Advocaten |
| 03-09-2026 | D100031 | Voortzetting enquête |
| 10-09-2026 | D100108 | Mondelinge behandeling na aanbrengen |

Aanbeveling: dit is de enige P0-handcontrole. Eerst in Lisannes echte agenda zoeken naar de reeks en deze zeven afspraken. Alleen aantoonbaar ontbrekende afspraken mogen later worden ingevoerd.

## 5. Relaties en aanvullende gegevens

- De 815 organisaties, 208 personen en 145 contactpersonen zijn als relaties aanwezig.
- De bron koppelt alle 145 contactpersonen aan een organisatie, maar `contact_links` telt op productie 0. De personen bestaan dus; hun organisatieverband ontbreekt.
- Van 940 `RelationEmailAddress`-records zijn 854 gelijk aan het primaire adres, 83 afwijkend/gesplitst en 3 weesrecord. BaseNet bevat bij 39 relaties meerdere adressen.
- `RelaPhoneNumber` bevat 28 regels: 24 koppelen aan geïmporteerde relaties en zijn semantisch gelijk aan het primaire nummer na normalisatie (`+31`/`06`, spaties en `+39`/`0039`); 4 zijn weesrecords. Er zijn dus 0 bewezen aanvullende nummers.
- In `Person` staan 28 echte geboortedatums. Productie heeft daar een veld voor; de afgeleide `RelaBirthDayOfYear`-lookup zelf hoeft niet mee.
- `Dcinfo` heeft overal de standaard betaaltermijn 0; alleen 6 IBAN/BIC-combinaties en 5 e-mails zijn potentieel aanvullend.

## 6. Boekhouding en facturatie

Exact blijft het financiële grootboek. `Journal`, `Ledger`, dagboeken en verdichtingen worden daarom niet rauw in Luxis gerepliceerd.

Voor facturen is wél een gecontroleerde operationele import nodig. Het bouwrecept staat in `docs/research/S201-facturatie-recept.md`. Kern: 439 conflict-vrije definitieve kantoorfacturen importeren; 7 Mollie/kop-conflicten eerst reconciliëren; 90 derdengelden-/verrekenposten uitsluiten; 12 WIP-koppen handmatig beoordelen; 19 lege koppen en 31 losse conceptregels overslaan.

`Memorial`/`MemorialLine` wordt als bewijsbron gebruikt voor 325 betaalde gewone facturen samen € 248.364,17. Van 237 betaallinks zijn 27 ook door Mollie als `paid` bevestigd: 20 sluiten aan op een betaalde kop en leveren een exacte iDEAL-betaaldatum; 7 spreken een volledig open kop tegen. Geen van de 237 bronrecords wordt rauw geïmporteerd.

## 7. Volledige entiteitenmatrix

### Administratie en facturatie

| Entiteit | Records | Geïmporteerd? | Relevant? | Actie |
|---|---:|---|---|---|
| `admin.activagroup` | 4 | Nee | Nee — legacy boekhoud-/configuratiehulp zonder zelfstandig Luxis-doel. | Niet importeren; huidige Luxis/Exact-inrichting blijft leidend. |
| `admin.admindept` | 2 | Nee | Nee — legacy boekhoud-/configuratiehulp zonder zelfstandig Luxis-doel. | Niet importeren; huidige Luxis/Exact-inrichting blijft leidend. |
| `admin.administration` | 2 | Nee | Nee — legacy boekhoud-/configuratiehulp zonder zelfstandig Luxis-doel. | Niet importeren; huidige Luxis/Exact-inrichting blijft leidend. |
| `admin.amortizationmethod` | 8 | Nee | Nee — legacy boekhoud-/configuratiehulp zonder zelfstandig Luxis-doel. | Niet importeren; huidige Luxis/Exact-inrichting blijft leidend. |
| `admin.bankimports` | 425 | Deels, via eerder banktraject | Ja — bronregistratie van bankimports, maar geen factuurboeking. | Niet opnieuw importeren; alleen gebruiken bij gerichte bankreconciliatie. |
| `admin.cashbank` | 7 | Nee | Ja — bronrekening/dagboek voor bankcontext. | Niet als historisch object importeren; huidige bankconfiguratie blijft leidend. |
| `admin.cashbankline` | 425 | Deels, via eerder banktraject | Ja — bankmutaties, deels al functioneel verwerkt. | Geen bulkherimport; alleen ontbrekende transacties gericht reconciliëren. |
| `admin.daybook` | 6 | Nee | Nee — legacy boekhoud-/configuratiehulp zonder zelfstandig Luxis-doel. | Niet importeren; huidige Luxis/Exact-inrichting blijft leidend. |
| `admin.dcinfo` | 1.027 | Nee | Beperkt — vooral standaarddebiteurgegevens; 6 IBAN/BIC-combinaties en 5 e-mails vallen op. | Zes bankgegevens apart beoordelen; geen wholesale-import. |
| `admin.footer_translation` | 6 | Nee | Nee — legacy boekhoud-/configuratiehulp zonder zelfstandig Luxis-doel. | Niet importeren; huidige Luxis/Exact-inrichting blijft leidend. |
| `admin.genericbankline` | 425 | Deels, via eerder banktraject | Ja — generieke bankregelbron. | Niet dubbel importeren; alleen als bewijs bij reconciliatie. |
| `admin.hoofdverdichting` | 6 | Nee | Nee — legacy boekhoud-/configuratiehulp zonder zelfstandig Luxis-doel. | Niet importeren; huidige Luxis/Exact-inrichting blijft leidend. |
| `admin.hour_to_invlines` | 2.742 | Nee | Ja — historie/status voor uren↔factuurregels; geen zelfstandige urensplitsingen. | Later als mappingbron gebruiken na import van D-dossiers. |
| `admin.hourlyrate` | 1 | Nee | Ja — één historisch standaardtarief. | Alleen meenemen in de latere urenmapping als bronwaarde. |
| `admin.invoice_cache_last_sync_date` | 2 | Nee | Nee — legacy boekhoud-/configuratiehulp zonder zelfstandig Luxis-doel. | Niet importeren; huidige Luxis/Exact-inrichting blijft leidend. |
| `admin.invoicecountry` | 5 | Nee | Nee — legacy boekhoud-/configuratiehulp zonder zelfstandig Luxis-doel. | Niet importeren; huidige Luxis/Exact-inrichting blijft leidend. |
| `admin.invoicecountryproduct` | 24 | Nee | Nee — legacy boekhoud-/configuratiehulp zonder zelfstandig Luxis-doel. | Niet importeren; huidige Luxis/Exact-inrichting blijft leidend. |
| `admin.invoicetranslationkeys` | 37 | Nee | Nee — legacy boekhoud-/configuratiehulp zonder zelfstandig Luxis-doel. | Niet importeren; huidige Luxis/Exact-inrichting blijft leidend. |
| `admin.invoicetranslationvalues` | 74 | Nee | Nee — legacy boekhoud-/configuratiehulp zonder zelfstandig Luxis-doel. | Niet importeren; huidige Luxis/Exact-inrichting blijft leidend. |
| `admin.journal` | 2.954 | Nee | Ja voor boekhoudcontrole, niet als Luxis-operationele data. | Exact blijft financieel grootboek; niet rauw importeren. |
| `admin.ledger` | 179 | Nee | Ja als grootboekcodemapping voor factuurregels. | Alleen gebruikte codes overnemen naar `gl_account_code`. |
| `admin.memorial` | 33 | Nee | Ja — bewijst boekingsdatums van historische factuurbetalingen. | Als bron gebruiken voor 325 samengevatte betalingen; koppen zelf niet importeren. |
| `admin.memorialline` | 777 | Nee | Ja — 551 regels sluiten 422 factuursaldi exact. | Als bron gebruiken; niet als zelfstandig Luxis-object. |
| `admin.mollie_update_request_log` | 634 | Nee | Nee — technische statuspoll-historie. | Niet importeren. |
| `admin.molliekassaaccount` | 1 | Nee | Nee — oude Mollie-configuratie. | Niet importeren; nooit credentials kopiëren. |
| `admin.molliepayment` | 237 | Nee | Ja als bewijsbron — 27 zijn hard `paid`; 20 sluiten aan en 7 botsen met de factuurkop. | Niet rauw importeren; gebruik 20 exacte iDEAL-datums en reconcileer 7 conflicten. |
| `admin.newbookyear` | 5 | Nee | Nee — legacy boekhoud-/configuratiehulp zonder zelfstandig Luxis-doel. | Niet importeren; huidige Luxis/Exact-inrichting blijft leidend. |
| `admin.outgoinginvoice` | 567 | Nee | Ja — kern van ontbrekende factuurhistorie. | 439 facturen importeren, 7 bronconflicten reconciliëren en overige groepen uitsluiten/beoordelen. |
| `admin.outgoinginvoiceline` | 773 | Nee | Ja — regels van facturen en losse WIP. | 630 regels importeren; 13 conflictregels, 9 WIP en 31 losse conceptregels niet automatisch. |
| `admin.outgoinginvoicelinekoppeling` | 9 | Nee | Beperkt — aanvullende legacykoppeling bij regels. | Alleen als controlebron gebruiken, niet als apart record. |
| `admin.payment` | 237 | Nee | Ja als koppellaag — dezelfde 27 `payment_status=4`-records koppelen Mollie exact aan facturen. | Niet rauw importeren; gebruik alleen de bewezen eindstatussen als bron. |
| `admin.period` | 25 | Nee | Nee — legacy boekhoud-/configuratiehulp zonder zelfstandig Luxis-doel. | Niet importeren; huidige Luxis/Exact-inrichting blijft leidend. |
| `admin.product` | 43 | Nee | Ja als mappingbron — 14 van 43 producten worden door alle 773 regels gebruikt. | Gebruikte btw-/grootboekvelden mappen; productcatalogus nu niet aanmaken. |
| `admin.reminder` | 26 | Nee | Ja als historische herinneringscontext. | Niet herversturen of bulkimporteren; factuurstatus is leidend. |
| `admin.remindertemplate` | 3 | Nee | Mogelijk — oude herinneringsteksten. | Apart met huidige sjablonen vergelijken, niet automatisch importeren. |
| `admin.remindertemplate_translations` | 6 | Nee | Mogelijk — vertalingen van herinneringsteksten. | Alleen meenemen bij een latere template-inventarisatie. |
| `admin.sepadebetlog` | 71 | Nee | Nee — historische SEPA-logregels. | Niet importeren. |
| `admin.sepavolgnummer` | 13 | Nee | Nee — legacy SEPA-teller. | Niet importeren; Luxis/Exact genereert eigen reeksen. |
| `admin.vatpercentage` | 12 | Nee | Ja als verificatiebron — alleen 21% en 0% worden gebruikt. | Niet als tabel importeren; vaste regelmapping testen. |
| `admin.verdichting` | 30 | Nee | Nee — legacy boekhoud-/configuratiehulp zonder zelfstandig Luxis-doel. | Niet importeren; huidige Luxis/Exact-inrichting blijft leidend. |

### Advocatuur

| Entiteit | Records | Geïmporteerd? | Relevant? | Actie |
|---|---:|---|---|---|
| `advocatuur.dossier` | 187 | Nee | Ja — 187 ontbrekende D-dossiers vormen de ruggengraat voor uren, facturen en correspondentie. | Aparte D-dossiermigratie bouwen, bronstatus bewaren en geen incassopipeline starten. |
| `advocatuur.incasso` | 607 | Ja | Ja — 607 incassodossiers zijn als Luxis-cases aanwezig. | Geen herimport; alleen regressiecontrole. |
| `advocatuur.incassobetaling` | 56 | Ja | Ja — alle 56 bronbetalingen zijn via de BaseNet-marker op productie teruggevonden. | Niet herimporteren; de 17 gecapte bedragen blijven de gedocumenteerde uitzondering. |
| `advocatuur.incassobetalingsregeling` | 323 | Deels, bewust | Ja — 323 brontermijnen op 37 zaken; alleen de toen toekomstige voorraad is gemigreerd. | Niet herimporteren; productie bevat de bedoelde 13 regelingen en 121 bewakingstermijnen. |
| `advocatuur.incassoline` | 1.563 | Ja | Ja — 1.563 vorderingsregels zijn als claims aanwezig. | Geen herimport; financiële driftguard behouden. |
| `advocatuur.incassooverigekostentype` | 8 | Nee | Beperkt — BaseNet-kostenlookup. | Niet als data importeren; huidige Luxis-categorieën zijn leidend. |
| `advocatuur.incassosettings` | 1 | Nee | Beperkt — één legacy-incassoconfiguratie. | Niet overnemen zonder veld-voor-veld beleidsbesluit. |
| `advocatuur.incfinishreason` | 6 | Nee | Ja als mogelijke statusmapping voor gesloten dossiers. | Alleen gebruiken bij D-/statusmapping, niet als eigen tabel. |
| `advocatuur.rechtsgebied` | 1 | Nee | Beperkt — één legacylookup. | Niet importeren. |
| `advocatuur.staffel` | 1 | Nee | Beperkt — één legacy-incassostaffel. | Niet importeren; Luxis gebruikt de juridisch geteste WIK-logica. |

### CRM

| Entiteit | Records | Geïmporteerd? | Relevant? | Actie |
|---|---:|---|---|---|
| `crm.batch_job_record` | 4.073 | Nee | Nee — BaseNet-systeem- of gebruikshistorie. | Niet importeren. |
| `crm.coworkersonscreen` | 1 | Nee | Nee — BaseNet-systeem- of gebruikshistorie. | Niet importeren. |
| `crm.document_share` | 38 | Nee | Nee voor actieve migratie — gedeelde-documenthistorie is verlopen. | Niet importeren. |
| `crm.document_share_document` | 399 | Nee | Nee — koppelingen van verlopen shares. | Niet importeren. |
| `crm.document_share_link` | 30 | Nee | Nee — links van verlopen shares. | Niet importeren. |
| `crm.document_share_link_log` | 123 | Nee | Nee — raadpleeg-/loghistorie van verlopen shares. | Niet importeren. |
| `crm.entity_notification` | 122 | Nee | Beperkt — notificatiehistorie kan agenda/taken duiden. | Alleen als bewijs bij agenda-review gebruiken. |
| `crm.filelock` | 1 | Nee | Nee — BaseNet-systeem- of gebruikshistorie. | Niet importeren. |
| `crm.label` | 6 | Nee | Nee — automatische labels dupliceren rollen/partijtypen. | Niet importeren. |
| `crm.label_eligible_for_entity` | 6 | Nee | Nee — labelconfiguratie. | Niet importeren. |
| `crm.label_link` | 1.375 | Nee | Nee — 1.375 automatische labelkoppelingen zijn redundant. | Niet importeren. |
| `crm.recentaction` | 18 | Nee | Nee — BaseNet-systeem- of gebruikshistorie. | Niet importeren. |
| `crm.singlefileentity` | 10 | Nee | Beperkt — technische bestandsverwijzingen. | Alleen raadplegen als een concrete ontbrekende bijlage wordt gevonden. |

### Keuzeteksten

| Entiteit | Records | Geïmporteerd? | Relevant? | Actie |
|---|---:|---|---|---|
| `descriptions.userselectstring` | 39 | Nee | Nee — generieke legacy-keuzeteksten. | Niet importeren. |

### E-mailconfiguratie

| Entiteit | Records | Geïmporteerd? | Relevant? | Actie |
|---|---:|---|---|---|
| `email.eregistered_mail_account` | 1 | Nee | Nee — legacy accountconfiguratie. | Niet importeren; nooit credentials kopiëren. |
| `email.eregistered_mail_setting` | 1 | Nee | Nee — legacy aangetekende-mailconfiguratie. | Niet importeren. |
| `email.mailbox` | 9 | Nee | Nee — oude mailboxconfiguratie. | Niet importeren; Microsoft-koppeling in Luxis blijft leidend. |
| `email.mailboxsendalias` | 1 | Nee | Nee — oude verzendalias. | Niet importeren. |
| `email.mailsubjectparams` | 9.268 | Nee | Nee — 9.268 technische onderwerpmetadata, geen mailinhoud. | Niet importeren. |
| `email.queued_mail` | 2 | Nee | Nee — twee oude wachtrijmails. | Niet importeren en beslist niet versturen. |

### Import-/exporthistorie

| Entiteit | Records | Geïmporteerd? | Relevant? | Actie |
|---|---:|---|---|---|
| `exportimport.importexportbatch` | 140 | Nee | Nee — import-/exportjobhistorie. | Niet importeren. |
| `exportimport.importexportlog` | 2.454 | Nee | Nee — import-/exportjobhistorie. | Niet importeren. |
| `exportimport.importexportoptions` | 280 | Nee | Nee — import-/exportjobhistorie. | Niet importeren. |

### Logs

| Entiteit | Records | Geïmporteerd? | Relevant? | Actie |
|---|---:|---|---|---|
| `logs.elasticsearch_index_failures` | 9 | Nee | Nee — technische loghistorie. | Niet importeren. |
| `logs.eregistered_mail_per_use_log` | 1 | Nee | Nee — technische loghistorie. | Niet importeren. |
| `logs.report_request` | 211 | Nee | Nee — technische loghistorie. | Niet importeren. |

### Onderhoud

| Entiteit | Records | Geïmporteerd? | Relevant? | Actie |
|---|---:|---|---|---|
| `maintenance.backupxmltask` | 1 | Nee | Nee — technische onderhoudstaak. | Niet importeren. |

### Relaties, projecten en werk

| Entiteit | Records | Geïmporteerd? | Relevant? | Actie |
|---|---:|---|---|---|
| `rela.agenda` | 229 | Nee | Ja en urgent — op 12 juli resteren 94 reeksinstanties en 7 toekomstige losse D-afspraken. | Eerst Outlook handmatig controleren; alleen werkelijk ontbrekende items importeren. |
| `rela.agenda_status` | 22 | Nee | Ja als mappingbron voor agenda. | Alleen gebruiken bij de agenda-review. |
| `rela.agendaherhaal` | 2 | Nee | Ja — beschrijft herhaling van de Stephanie-reeks. | Bron gebruiken om dubbelen te voorkomen. |
| `rela.agendahistory` | 72 | Nee | Beperkt — wijzigingshistorie van agenda. | Niet importeren; alleen bij twijfel raadplegen. |
| `rela.agendameeting` | 2 | Nee | Ja als afspraakmetadata. | Samen met de negen losse afspraken handmatig controleren. |
| `rela.agendameetingattendee` | 5 | Nee | Ja als deelnemersmetadata. | Alleen bij gecontroleerde agenda-overname gebruiken. |
| `rela.agendameetingreceived` | 32 | Nee | Beperkt — ontvangen meetinghistorie. | Niet blind importeren; externe agenda eerst controleren. |
| `rela.agendameetingreceivedattendee` | 48 | Nee | Beperkt — deelnemers van ontvangen meetings. | Alleen als reviewbron gebruiken. |
| `rela.agendatype` | 7 | Nee | Ja als mappingbron voor afspraaktypen. | Niet als eigen tabel importeren. |
| `rela.characteristics` | 5 | Nee | Beperkt — hulp-/lookupdata zonder zelfstandig Luxis-doel. | Alleen gebruiken als mappingbron wanneer een gemarkeerde migratie dat vraagt. |
| `rela.company` | 815 | Ja | Ja — 815 organisaties zijn in de relatie-import verwerkt. | Geen herimport. |
| `rela.contact` | 145 | Ja als losse relatie; koppeling ontbreekt | Ja — 145 contactpersonen bestaan, maar productie heeft 0 `contact_links`. | 145 persoon↔organisatie-links later gericht backfillen. |
| `rela.customprojectstatus` | 39 | Nee | Ja als mappingbron voor D-dossierstatus. | Bij D-migratie bronstatus naar Luxis-status vertalen. |
| `rela.email_address` | 940 | Deels | Ja — 940 adressen: 854 gelijk aan primair, 83 afwijkend/gesplitst en 3 weesrecords. | De 83 extra/gesplitste waarden normaliseren; schema ondersteunt nu één primair adres. |
| `rela.emailtemplate` | 48 | Nee | Mogelijk — 48 oude e-mailsjablonen kunnen kantoorinhoud bevatten. | Apart inhoudelijk vergelijken met ManagedTemplate; niet automatisch importeren. |
| `rela.emailtemplateattachment` | 13 | Nee | Mogelijk — 13 sjabloonbijlagen. | Alleen samen met geselecteerde e-mailsjablonen beoordelen. |
| `rela.employee` | 5 | Deels via Luxis-gebruikers | Ja als mappingbron voor uren en auteurschap. | Vijf medewerkers expliciet op Luxis-gebruikers mappen vóór urenimport. |
| `rela.eregistered_message` | 2 | Nee | Ja — twee aangetekende berichten kunnen dossiercorrespondentie zijn. | Handmatig inspecteren en zo nodig aan een dossier/PDF koppelen. |
| `rela.hour` | 1.320 | Nee | Ja — 1.320 historische tijdregels. | Nog niet importeren; eerst 187 D-dossiers, daarna aparte urenimport. |
| `rela.hour_activity` | 864 | Nee | Ja als activiteit-/historiebron bij uren. | Bij urenmapping gebruiken, niet als zelfstandig object. |
| `rela.hourprojectemployeeprice` | 607 | Nee | Beperkt — alle 607 bronprijzen zijn 0 en leveren dus geen bruikbaar historisch tarief. | Niet als tariefbron importeren; onbekende tarieven expliciet leeg laten. |
| `rela.hourtype` | 70 | Nee | Ja — 70 uurtypen, waarvan 28 gebruikt. | Alleen gebruikte typen mappen; 21 uurregels zonder type expliciet afhandelen. |
| `rela.hourtypetranslation` | 122 | Nee | Beperkt — labels van uurtypen. | Alleen voor Nederlandse weergavenaam bij urenmapping gebruiken. |
| `rela.letter` | 17.928 | Deels | Ja — correspondentie en documenten; IN is vrijwel volledig verwerkt, D ontbreekt. | 30 IN-mailgaten beoordelen en 8.637 D-items meenemen na D-dossiers. |
| `rela.letter_elastic_body_incorrectly_indexed` | 5 | Nee | Nee — zoekindexreparatiehistorie. | Niet importeren. |
| `rela.lettertemplate` | 64 | Nee | Mogelijk — 64 briefsjablonen; twee XML-fragmenten konden niet parsen. | Apart parseren en vergelijken met ManagedTemplate; niet automatisch. |
| `rela.memotemplate` | 2 | Nee | Mogelijk — twee memosjablonen. | Alleen bij template-inventarisatie beoordelen. |
| `rela.pdf_merger_sheduled_job` | 2 | Nee | Nee — technische PDF-jobhistorie. | Niet importeren. |
| `rela.person` | 208 | Ja | Ja — 208 personen zijn in de relatie-import verwerkt. | Geen herimport. |
| `rela.phonenumber` | 28 | Ja voor de 24 gekoppelde nummers | Beperkt — alle 24 gekoppelde waarden zijn na normalisatie gelijk aan primair; 4 zijn weesrecords. | Geen nummer backfillen; alleen de 4 weesrecords als uitzonderingen bewaren. |
| `rela.project` | 794 | Deels, indirect | Ja — 794 projecten bestaan uit 607 IN- en 187 D-trajecten; D ontbreekt. | IN niet herimporteren; 187 D-projecten als dossiers migreren. |
| `rela.project_status` | 22 | Nee | Ja als mappingbron voor project-/dossierstatus. | Bij D-migratie gebruiken. |
| `rela.projectrelation` | 48 | Nee | Ja — 48 aanvullende project-relaties kunnen partijrollen bevatten. | Bij D-migratie veld-voor-veld koppelen. |
| `rela.projectscore` | 424 | Nee | Beperkt — hulp-/lookupdata zonder zelfstandig Luxis-doel. | Alleen gebruiken als mappingbron wanneer een gemarkeerde migratie dat vraagt. |
| `rela.relabirthdayofyear` | 28 | Nee | Ja — afgeleide verjaardaglookup voor 28 personen. | Niet deze lookup importeren; de 28 echte geboortedatums backfillen. |
| `rela.relationscore` | 607 | Nee | Beperkt — hulp-/lookupdata zonder zelfstandig Luxis-doel. | Alleen gebruiken als mappingbron wanneer een gemarkeerde migratie dat vraagt. |
| `rela.relationtag` | 729 | Nee | Nee — 729 grotendeels automatische Client/Wederpartij/Advocaat-tags. | Niet importeren; Luxis-partijrollen zijn leidend. |
| `rela.status` | 22 | Nee | Beperkt — hulp-/lookupdata zonder zelfstandig Luxis-doel. | Alleen gebruiken als mappingbron wanneer een gemarkeerde migratie dat vraagt. |
| `rela.stdaction` | 4 | Nee | Beperkt — hulp-/lookupdata zonder zelfstandig Luxis-doel. | Alleen gebruiken als mappingbron wanneer een gemarkeerde migratie dat vraagt. |
| `rela.task` | 1.613 | Nee | Ja — 461 open en 2 wachtend; 29 raken actieve dossiers en 2 toekomstige taken staan op gesloten dossiers. | Geen bulkimport; maak één menselijke uitzonderingenlijst. |
| `rela.task_activity` | 1.513 | Nee | Beperkt — uitvoeringshistorie bij taken. | Alleen als context voor de 29 reviewtaken gebruiken. |
| `rela.task_status` | 22 | Nee | Ja als statusmapping voor taakselectie. | Alleen gebruiken om open/wacht/gereed te classificeren. |
| `rela.taskhistory` | 1.364 | Nee | Beperkt — wijzigingshistorie van taken. | Niet importeren; alleen reviewbewijs. |
| `rela.template_v5_reference_code` | 118 | Nee | Beperkt — hulp-/lookupdata zonder zelfstandig Luxis-doel. | Alleen gebruiken als mappingbron wanneer een gemarkeerde migratie dat vraagt. |
| `rela.temporaryfile` | 4 | Nee | Beperkt — hulp-/lookupdata zonder zelfstandig Luxis-doel. | Alleen gebruiken als mappingbron wanneer een gemarkeerde migratie dat vraagt. |
| `rela.workflowdefinition` | 26 | Nee | Nee — BaseNet-workflowdefinities passen niet één-op-één op Luxis. | Niet importeren. |
| `rela.workflowevent` | 1.436 | Nee | Nee — 1.436 historische automatiseringsevents. | Niet importeren. |
| `rela.workflowtask` | 39 | Nee | Nee — legacy workflowstappen; huidige Luxis-pipeline is leidend. | Niet importeren. |

### Rapportconfiguratie

| Entiteit | Records | Geïmporteerd? | Relevant? | Actie |
|---|---:|---|---|---|
| `reports.printoption` | 5 | Nee | Nee — legacy afdrukconfiguratie. | Niet importeren. |
| `reports.reporttemplate` | 7 | Nee | Mogelijk — zeven oude rapport-/afdruktemplates. | Apart vergelijken met het Luxis-sjabloonsysteem. |

### Rechten en apparaten

| Entiteit | Records | Geïmporteerd? | Relevant? | Actie |
|---|---:|---|---|---|
| `sessionrights.administration_rights` | 4 | Nee | Nee — BaseNet-rechten en apparaatconfiguratie. | Niet importeren; Luxis-rollenmatrix blijft leidend. |
| `sessionrights.introductionsettings` | 34 | Nee | Nee — BaseNet-rechten en apparaatconfiguratie. | Niet importeren; Luxis-rollenmatrix blijft leidend. |
| `sessionrights.mijnbedrijf` | 1 | Nee | Nee — BaseNet-rechten en apparaatconfiguratie. | Niet importeren; Luxis-rollenmatrix blijft leidend. |
| `sessionrights.mobiledevice` | 1 | Nee | Nee — BaseNet-rechten en apparaatconfiguratie. | Niet importeren; Luxis-rollenmatrix blijft leidend. |

### Social media / OAuth

| Entiteit | Records | Geïmporteerd? | Relevant? | Actie |
|---|---:|---|---|---|
| `socialmedia.oauth` | 5 | Nee | Nee — legacy OAuth-data en mogelijk geheim materiaal. | Niet importeren of kopiëren. |
| `socialmedia.oauth2` | 5 | Nee | Nee — legacy OAuth-data en mogelijk geheim materiaal. | Niet importeren of kopiëren. |

## 8. Controle en niet geverifieerd

- Matrixcontrole: **133 entiteiten** en **65.761 records**; dit moet exact gelijk blijven aan de parseroutput.
- De 2 mislukte XML-fragmenten binnen `rela.lettertemplate` zijn niet inhoudelijk hersteld.
- Niet geverifieerd: of de 94 Stephanie-reeks en 7 op 12 juli nog toekomstige losse D-afspraken al in Lisannes externe agenda staan.
- Niet geverifieerd: welke van de 12 factuur-WIP-koppen, 29 actieve-dossiertaakmatches en 2 toekomstige taken op gesloten dossiers Lisanne functioneel wil bewaren; daarom is daar geen automatische importbeslissing genomen.
- De 56 BaseNet-`incassobetaling`-records zijn via markers volledig teruggevonden. De 323 regelingrecords zijn bewust slechts als toen toekomstige 13 regelingen/121 termijnen gemigreerd; zij zijn niet bedoeld als rij-voor-rij-kopie.
- Niet geverifieerd: waarom 7 Mollie-betalingen van samen € 10.854,66 in de factuurkop volledig open blijven.
- Geen enkele voorgestelde import of productiedatamutatie is in dit onderzoek uitgevoerd.
