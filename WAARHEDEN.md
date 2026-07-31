# WAARHEDEN.md — wat waar hoort te zijn in Luxis

> **Dit bestand definieert wat "af" betekent.** Eén regel per waarheid: iets dat in Luxis
> ALTIJD moet gelden, in gewone taal. Drie statussen:
> ✅ **bewaakt** — er is een test/blokkade die dit automatisch controleert (naam erbij)
> ⚠️ **onbewaakt** — waar, maar niets waakt erover; schending kost geld/reputatie → wachter bouwen
> ❓ **onzeker** — inhoudelijke keuze die Lisanne of Arsalan eerst moet maken
>
> **De zeef (bewust streng):** alleen waarheden waarvan schending geld, reputatie of
> juridische fouten kost, verdienen een wachter. Cosmetiek en zeldzame randgevallen
> staan er niet op — anders wordt deze lijst zelf een bouwproject.
>
> **Luxis is AF wanneer:** (1) deze lijst geen ⚠️ en ❓ meer bevat, én (2) twee weken echt
> gebruik geen nieuwe geschonden waarheid oplevert. Tot die twee dingen waar zijn, is
> "ik denk dat we er zijn" een gevoel, geen feit.
>
> Stand: **33 ✅ / 4 ⚠️ / 2 ❓** (S255).
>
> Bijwerken: alleen bij een nieuwe vondst of nieuwe wachter — geen onderhoudsplicht per sessie.
> *(Oogst S254 gedaan: archief S200-S253, compliance-hart, huisregels `breed-testen`,
> roadmap — elke status hieronder is tegen de echte testbestanden gecheckt, niet gegokt.
> Vier wachters gebouwd in S254; elk is bewezen rood gemaakt door de regel te slopen,
> want een wachter die niet kan bijten is geen wachter.)*

## Geld (het duurste om fout te hebben)

- ✅ Een brief toont exact dezelfde bedragen als het scherm — `test_brief_bedragen_gelijk_aan_scherm.py`
- ✅ Een consument (b2c) krijgt nooit meer kosten dan de wettelijke staffel — `test_b2c_kosten_grendel.py` + gedeelde grendel op aanmaak-, wijzig- én intake-pad
- ✅ De kostenstaffel rekent goed over de hele bedragenreeks — `test_wik.py` + `test_wik_edge_cases.py`
- ✅ Een dagelijkse veegronde betrapt B2C-kosten boven de staffel die búiten de app binnenkwamen (import, direct in de database) — `test_bik_staffel_sweep.py` + dagelijkse job
- ✅ Rente en kosten rekenen op de cent nauwkeurig (Decimal, nooit float) — financiële testsuite
- ✅ Samengestelde rente kapitaliseert op de verzuimdatum, niet op 1 januari — rente-tests (gouden ijkzaak IN100197 op de cent)
- ✅ De rentetabellen (wettelijke + handelsrente) kunnen niet stil verouderen — `test_interest_rate_freshness_guard.py` (ouder dan 7 maanden = rood)
- ✅ Deelbetalingen worden verdeeld volgens de wet: eerst kosten, dan rente, dan hoofdsom — verdelings-tests
- ✅ Een zaak kan nooit stil op "betaald" komen door een rekenfout — fail-closed-tests in `test_cases.py` + `test_incasso_pipeline.py`
- ✅ Een betaling op een volbetaalde zaak wordt geweigerd, en een dubbelklik/tweede tab boekt nooit dubbel — `test_collections_router.py` + `test_payment_double_submit.py`
- ✅ Verwijderde betalingen tellen nergens meer mee (Geïnd-cijfer, provisie op de cliëntfactuur) — `test_dashboard.py` (AUDIT-H3) + `test_incasso_invoice_preview.py`
- ✅ Derdengelden-boekingen (storting, verrekening, storno) zijn test-bewaakt — `test_trust_funds*.py`
- ✅ Het etiket zakelijk/consument klopt met de contactkaart van de wederpartij, **in beide richtingen** — `test_debtor_type_mismatch.py` (8) + dagelijkse veegronde (S255). Richting 1: consument-etiket terwijl de wederpartij een rechtsvorm óf KvK-nummer heeft → er wordt te weinig gevorderd (S252 Kaandorp: €6.300). Richting 2: zakelijk etiket op een persoon zónder KvK-nummer én zonder rechtsvorm → is het tóch een consument, dan gaan er kosten boven de dwingende staffel de deur uit; de b2c-grendel en de staffel-veegronde kijken allebei alleen naar b2c en lieten dit door. De import-regel "persoon = consument" (`scripts/basenet/mapping.py`) blijft bewust staan: het persoonsrecord in de BaseNet-export bevat géén KvK-nummer of bedrijfsveld (S255 nagemeten op de echte export), dus op importmoment is het niet te weten — de veegronde vangt het zodra de contactkaart het verraadt. Stand op prod: 0 treffers in richting 1, **1 in richting 2 (IN100077 Kaandorp — contactkaart mist zijn KvK-nummer)**.
- ⚠️ Griffierechten en nakosten-tarieven zijn actueel — de berekening is getest (`test_nakosten.py`, `test_griffierechten.py`) maar pint de tarieven van nu; een wetswijziging valt niet vanzelf rood (de rente heeft zo'n actualiteitswachter wél)

## Brieven & verzending (naar buiten = onomkeerbaar)

- ✅ De vijf bestaande verzenddeuren passeren de 14-dagenbrief-gate — `test_compose_dagenbrief_gate.py` (compose, document, .eml) + batch/follow-up-tests
- ✅ Een NIEUWE verzenddeur zonder 14-dagenbrief-gate valt automatisch rood — `test_send_route_drift_guard.py::test_elke_verzendroute_passeert_de_dagenbrief_gate` (S254; uitzonderingen alleen mét motivering op de allowlist)
- ✅ Een consument krijgt eerst de 14-dagenbrief met het juiste bedrag, anders geen kosten claimen; de klok loopt vanaf échte verzending — gate + tests
- ✅ De rentebijlage gaat mee bij privé-aansprakelijke wederpartijen en niet bij BV/NV/stichting, op álle routes — `test_rente_bijlage_verzendpaden.py` + besluit A/B-tests. **S255: draait nu op echte gegevens** — 437 van de 438 wederpartijen hebben hun rechtsvorm uit het KvK-Handelsregister (223 eenmanszaak, 172 BV, 35 VOF, 2 stichting, 2 maatschap, 1 VvE, 1 NV, 1 CV), waardoor 175 wederpartijen de bijlage niet meer krijgen (20 lopende dossiers). Eén nummer (Kroon Vleeswaren B.V., KvK 01062787) gaf geen rechtsvorm terug → blijft leeg → besluit B: wél bijlage.
- ✅ Elke verzendroute laat het drieluik achter (vindbaar op Mail, dossier én tijdlijn) en draagt het huisonderwerp; een nieuwe route zonder valt automatisch rood — `test_send_route_drift_guard.py` (leest de broncode zelf uit)
- ✅ Elke dossier-mail vertrekt vanaf het kantooradres (incasso@), nooit vanaf een persoonlijk account — `test_send_route_drift_guard.py::test_elke_verzendroute_gebruikt_het_kantooradres` (S254; toetst dat de instelling AAN staat, niet alleen dat hij meegegeven is)
- ✅ Alleen een stap-brief schuift de zaak precies één stap door; een antwoord of vrij bericht nooit; gesloten zaak, verweer of consument-naar-zakelijke-stap blokkeert — `test_advance_after_send_routes.py` (guard-matrix)
- ✅ Een geplande mail ("verstuur later") controleert de wereld opnieuw op het verzendmoment (betaald/gesloten/stap gewisseld = blokkade + melding) en verstuurt nooit stil dubbel — `test_scheduled_emails.py` (24 wachters)
- ✅ Een gesloten dossier verstuurt nooit meer automatisch iets — `test_closed_case_never_sends.py` (gedrag per route) + `test_send_route_drift_guard.py::test_automatische_verzenders_controleren_of_het_dossier_dicht_is` (soort). **S254 vond hier een echte fout:** de batch-knop verstuurde wél een sommatie op een betaald dossier (`emails_sent=1`, rood bewezen) en de follow-up-knop 'Uitvoeren' ook; beide nu dicht via de gedeelde poort `check_case_closed_gate`. Handmatig mailen op een gesloten dossier blijft bewust toegestaan.
- ⚠️ Het sjabloonmenu biedt per pijplijnstap de juiste brief aan (stap schuift correct door) — S252 met de hand gefixt, geen wachter
- ❓ Horen 'aanmaning' en 'tweede_sommatie' in menugroep 2? — inhoudelijke keuze **Lisanne**

## Beveiliging & gegevens

- ✅ Elk kantoor ziet alleen zijn eigen gegevens; nieuwe tabel zonder schot blokkeert de start — RLS-opstartcontrole + drift-guard-test
- ✅ Elke route vereist inloggen (behalve bewust-publieke) — `test_auth_drift_guard.py`
- ✅ Een geüpload sjabloon kan geen code uitvoeren op de server (sandbox) — `test_docx_sandbox.py` (SEC-25)
- ✅ De inlog-keten is dicht: token-hergebruik trekt alles in, lockout overleeft een herstart, wachtwoordwijziging logt overal uit, een geschorst kantoor komt er niet in — `test_refresh_token_rotation.py`, `test_auth_lockout.py`, `test_auth_token_revocation.py`, `test_tenant_active_guard.py`
- ✅ Mailserver-instellingen kunnen niet naar interne adressen wijzen (SSRF) — `test_imap_ssrf_guard.py`
- ✅ Secrets komen alleen uit de omgeving, nooit uit code — `test_secret_key_guard.py`
- ⚠️ Mailkoppeling-sleutels versleuteld met eigen sleutel (TOKEN_ENCRYPTION_KEY) — bekend restpunt Kimi-scan, mét Lisanne plannen (verbreekt haar mailkoppeling)
- ⚠️ Kennisregel-beheer alleen voor admin — bekend restpunt Kimi-scan

## Werking (het dagelijkse vertrouwen)

- ✅ De pijplijn verspringt alleen volgens de toegestane stap-overgangen — workflow-tests
- ✅ De test-database kan niet stil afwijken van de échte database — `test_migration_timestamp_defaults.py` leest álle migraties (S246: prod-crash die de tests niet zagen)
- ✅ Een dossiernummer wordt nooit hergebruikt (anders plakt oude mail aan een nieuw dossier) — `test_cases.py::test_generate_case_number_does_not_reuse_soft_deleted`
- ✅ Een eigen verstuurde mail komt nooit als "ontvangen post" terug, en een genegeerde mail blijft genegeerd — `test_email_sync.py` + `test_s241_sync_kruispunten.py`
- ✅ Elke meldingsoort heeft een label, icoon én kleur op de bel (nieuw type = geen grijs vangnet meer) — `test_notification_labels.py` (S254; telt de backend-soorten na tegen de bel-config én controleert dat elk icoon/kleur echt bestaat — de drie S252-vondsten in beide smaken)
- ❓ De verjaringsbewaking kent geen stuiting: het is een kaal sommetje (opeisbaar + 5 jaar), terwijl Luxis' eigen sommaties wél een stuitingsclausule bevatten (S242-meting, IN100015). Keuze **Arsalan/Lisanne**: stuitingsdatum op het dossier bouwen, of de melding als handwerk-signaal beschouwen.

## Waar, geen hek nodig (bewust)

- De bel-labels-natelling S252 (21/21) en het besluit "verstuur-later houdt de bedragen
  van het inplanmoment" (S252) zijn afgehandeld — geen open vraag meer.
- Cosmetische restjes (S235-formulier, dubbele naam in testdraad, e.d.) halen de zeef niet.

*(Eerste oogst gedaan in S254. Vanaf nu geldt: elke nieuwe vondst = nieuwe regel hier,
elke gebouwde wachter = ⚠️ → ✅ met testnaam.)*
