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
> Bijwerken: alleen bij een nieuwe vondst of nieuwe wachter — geen onderhoudsplicht per sessie.

## Geld (het duurste om fout te hebben)

- ✅ Een brief toont exact dezelfde bedragen als het scherm — `test_brief_bedragen_gelijk_aan_scherm.py`
- ✅ Een consument (b2c) krijgt nooit meer kosten dan de wettelijke staffel — `test_b2c_kosten_grendel.py` + gedeelde grendel op aanmaak- én wijzigpad
- ✅ De kostenstaffel klopt over de hele bedragenreeks — `test_bik_staffel_sweep.py`
- ✅ Rente en kosten rekenen op de cent nauwkeurig (Decimal, nooit float) — financiële testsuite
- ✅ Samengestelde rente kapitaliseert op de verzuimdatum, niet op 1 januari — rente-tests
- ✅ Deelbetalingen worden verdeeld volgens de wet: eerst kosten, dan rente, dan hoofdsom — verdelings-tests
- ⚠️ Het etiket zakelijk/consument klopt met de werkelijke rechtsvorm van de wederpartij — vergelijking bestaat nog niet (S252: Kaandorp stond fout, €6.300 verschil; komt na de 438 KVK-opzoekingen)

## Brieven & verzending (naar buiten = onomkeerbaar)

- ✅ Nieuwe brief-/mailroutes passeren de gedeelde verzendregels (14-dagenbrief-gate, WIK-bijlage) — compliance-tests
- ✅ Een consument krijgt eerst de 14-dagenbrief met het juiste bedrag, anders geen kosten claimen — gate + tests
- ✅ De rentebijlage gaat mee bij privé-aansprakelijke wederpartijen en niet bij BV/NV/stichting — besluit A/B-tests
- ⚠️ Een gesloten dossier verstuurt nooit meer automatisch iets — aanname, nooit als wachter vastgelegd
- ⚠️ Het sjabloonmenu biedt per pijplijnstap de juiste brief aan (stap schuift correct door) — S252 met de hand gefixt, geen wachter
- ❓ Horen 'aanmaning' en 'tweede_sommatie' in menugroep 2? — inhoudelijke keuze Lisanne

## Beveiliging & gegevens

- ✅ Elk kantoor ziet alleen zijn eigen gegevens; nieuwe tabel zonder schot blokkeert de start — RLS-opstartcontrole + drift-guard-test
- ✅ Elke route vereist inloggen (behalve bewust-publieke) — router-tests
- ⚠️ Mailkoppeling-sleutels versleuteld met eigen sleutel (TOKEN_ENCRYPTION_KEY) — bekend restpunt Kimi-scan, gepland met Lisanne
- ⚠️ Kennisregel-beheer alleen voor admin — bekend restpunt Kimi-scan

## Werking (het dagelijkse vertrouwen)

- ✅ De pijplijn verspringt alleen volgens de toegestane stap-overgangen — workflow-tests
- ⚠️ Elke meldingsoort in het systeem heeft een label/kleur op de bel (nieuw type zonder label = grijs vangnet) — S253 met de hand nageteld, geen automatische natelling
- ❓ Wat is de afgesproken volgorde/timing van de belroutes en verstuur-later-bedragen? — S252-restpunten, wachten op keuze

*(Deze lijst is de start — de oogst-sessie (S254-voorstel) loopt alle sessienotities, huisregels
en het compliance-hart na en vult hem aan. Daarna geldt: elke nieuwe vondst = nieuwe regel hier.)*
