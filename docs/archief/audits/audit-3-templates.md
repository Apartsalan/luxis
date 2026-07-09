# Audit 3 - Incasso brieven / e-mailtemplates

**Datum:** 22 april 2026
**Auditor:** Domeinexpert incassorecht (Lisanne-perspectief)
**Scope:** 5 meest gebruikte brieven: herinnering, aanmaning, 14-dagenbrief, sommatie, tweede_sommatie (met shared helpers).
**Methode:** code-lezen van alle _render_* functies in backend/app/email/incasso_templates.py, context-builder in backend/app/documents/docx_service.py, WIK-calc in backend/app/collections/wik.py, en compose-router met DF122-07 attach-logica. Mentale render voor 3 testcases: consument EUR 500, B2B EUR 15.000 met compound rente, consument EUR 2.500 met deelbetaling. Kruis-check met art. 6:96 lid 6 BW, HR 25 november 2016 (Arno/RS Bekking), art. 6:44 BW, art. 6:119/119a BW.

---

## Severity-samenvatting

| Severity | Aantal |
|---|---:|
| Critical | 6 |
| High | 7 |
| Medium | 5 |
| Low | 3 |

---

## CRITICAL

### C1 - 14-dagenbrief: termijn verkeerd geformuleerd (na dagtekening i.p.v. na ontvangst)

**Template:** _render_14_dagenbrief in backend/app/email/incasso_templates.py op r. 585-587.

**Evidence:** De brief opent met een correcte zin (binnen veertien dagen na ontvangst, r. 575-579), maar in r. 585-587 staat:

    Ik verzoek u het totaal verschuldigde bedrag van [totaal_verschuldigd]
    binnen veertien dagen na DAGTEKENING van deze brief over te maken.

**Analyse:** Dit is exact de formulering die de Hoge Raad in HR 25 november 2016, ECLI:NL:HR:2016:2704 (Arno/RS Bekking) als ongeldig heeft bestempeld. De termijn moet 14 volle dagen zijn, ingaand op de dag NA ontvangst van de brief. HR 10 maart 2017 (ECLI:NL:HR:2017:388) en HR 17 januari 2020 (ECLI:NL:HR:2020:55) bevestigen: als de brief ook maar een variant van na dagtekening / na verzenddatum / 14 dagen vanaf heden gebruikt, voldoet deze NIET aan art. 6:96 lid 6 BW en wordt de BIK niet toegewezen. Een wederpartij-advocaat vindt dit binnen 30 seconden. Voor elke consumentenzaak is de BIK mogelijk verbeurd.

**Fix:** Vervang op r. 587 "na dagtekening van deze brief" door "na ontvangst van deze brief". Unit-test toevoegen die assert: html.count("na dagtekening") == 0 EN html.count("na ontvangst") >= 2.

---

### C2 - BIK zonder 21% BTW-opslag wanneer schuldeiser NIET BTW-plichtig is

**Locatie:** backend/app/documents/docx_service.py:366 (build_base_context) + backend/app/collections/wik.py:50 (calculate_bik signature).

**Evidence:**

    # docx_service.py r. 366:
    bik = calculate_bik(total_principal)   # include_btw defaults naar False

    # wik.py r. 50:
    def calculate_bik(principal, *, include_btw: bool = False) -> dict:

**Analyse:** build_base_context roept calculate_bik ZONDER include_btw=True. Gevolg: bik[btw_amount] is altijd 0, has_btw is altijd False, btw_regel_label/btw_regel_bedrag/btw_toelichting zijn altijd leeg, en totaal_verschuldigd mist de 21% BTW.

**Testcase:** ZZP-tandarts (BTW-vrijgesteld), factuur EUR 3.750 aan consument.
- Hoofdsom: EUR 3.750
- BIK-staffel: 15% x 2500 + 10% x 1250 = EUR 375 + EUR 125 = EUR 500
- BIK + BTW (verplicht want tandarts kan BTW niet verrekenen): EUR 500 x 1,21 = EUR 605
- Luxis toont: bik_bedrag = EUR 500,00 en GEEN BTW-regel. Debiteur wordt EUR 105 te weinig gevorderd.

Rechtsgrond: als de schuldeiser BTW niet kan verrekenen is deze BTW een schadepost die op de debiteur verhaald kan worden (standaard rechtspraak). Het include_btw mechanisme bestaat al in calculate_bik maar wordt nergens doorgegeven. Er is geen Contact/Client flag, geen UI-toggle, geen context-veld dat dit triggert.

**Fix:** 1) Contact.is_btw_plichtig bool toevoegen (default True). 2) In build_base_context: bik = calculate_bik(total_principal, include_btw=not case.client.is_btw_plichtig). 3) In get_financial_summary idem, zodat grand_total en total_outstanding correct worden berekend. 4) UI-toggle op relatiekaart bij clienten. 5) Unit-test: tandarts-scenario met verwachte grand_total = 3.750 + rente + 605.

---

### C3 - 14-dagenbrief noemt GEEN IBAN om naar te betalen

**Template:** _render_14_dagenbrief in backend/app/email/incasso_templates.py r. 578-579.

**Evidence:**

    f"na ontvangst van deze brief te voldoen op het rekeningnummer "
    f"van onze cli&euml;nt.</p>"

**Analyse:** De brief zegt dat de debiteur moet betalen op het rekeningnummer van onze client, maar de IBAN van de client wordt NERGENS in de brief getoond. Andere brieven (herinnering, aanmaning, sommatie) noemen de derdengeldenrekening van Kesting Legal (NL20 RABO 0388 5065 20), maar in het 14-dagenbrief-stadium wordt expliciet naar de client verwezen zonder diens IBAN te noemen. Zonder IBAN is betalen praktisch onmogelijk.

**Effect:** Een rechter kan twijfelen aan de deugdelijkheid van de ingebrekestelling. Een wederpartij-advocaat voert aan dat de debiteur geen werkbare betalingsinstructie ontving.

**Fix:** Render client.iban en client.name (tenaamstelling) in het 14-dagenbrief-betalingsblok. Fallback: derdengeldenrekening met expliciete vermelding dat Kesting Legal namens client int.

---

### C4 - Dubbel valutasymbool in vorderingstabel

**Locatie:** _vordering_table_basenet r. 338-339 + _fmt_currency in docx_service.py r. 169.

**Evidence:**

    # docx_service.py r. 169:
    return f"EUR {formatted}"   # levert: "EUR 1.234,56"

    # incasso_templates.py r. 338-339:
    f"<td>&euro;</td>"            # euro-entity in een aparte kolom
    f"<td>{value}</td>"           # value is al "EUR 1.234,56"

**Analyse:** De BaseNet-stijl vorderingstabel wordt gebruikt in 17 van de 25 templates (sommatie, schikkingsvoorstel, reactie_9_3, reactie_20_4, reactie_ncnp_9_3, reactie_verlengd_9_3, VSO, faillissement_dreigbrief, sommatie_na_reactie, sommatie_eerste_opgave, sommatie_laatste_voor_fai, wederom_sommatie_inhoudelijk, wederom_sommatie_kort, sommatie_drukte, engelse_sommatie, alle demand_for_payment_*). Elke samenvattingsregel toont:

    [euro-teken] [spatie] EUR 5.956,25

Dus twee valutasymbolen naast elkaar. Onprofessioneel; in een juridische brief ronduit slordig. Contrast met BaseNet (waar Kesting Legal vandaan komt) is direct zichtbaar - BaseNet toont consequent slechts een euro-teken.

**Fix:** 1) _fmt_currency aanpassen naar euro-entity + non-breaking-space + bedrag. 2) De aparte <td>&euro;</td> kolom in _vordering_table_basenet verwijderen. 3) Regression-test: assert dat "EUR " (als tekst) niet voorkomt in gerenderde html (op IBAN/BTW na).

---

### C5 - Automatische factuur-bijlage alleen voor template "sommatie", niet voor 14-dagenbrief of andere sommatie-varianten

**Locatie:** backend/app/email/compose_router.py r. 38 (constante) en r. 279 (check).

**Evidence:**

    SOMMATIE_TEMPLATE_TYPES = {"sommatie"}
    ...
    if data.template_type in SOMMATIE_TEMPLATE_TYPES:
        # haalt claim.invoice_file_id op en voegt PDF toe

**Analyse:** Alleen het exact-gematchte template-type "sommatie" krijgt factuur-bijlagen. Alle varianten (sommatie_na_reactie, sommatie_eerste_opgave, sommatie_drukte, sommatie_laatste_voor_fai, tweede_sommatie, wederom_sommatie_inhoudelijk/kort, niet_voldaan_regeling, faillissement_dreigbrief, demand_for_payment_*) krijgen GEEN facturen mee. En het belangrijkste: de 14-dagenbrief - juridisch de cruciaalste brief omdat deze BIK-verschuldigdheid onderbouwt - heeft ook geen factuur-bijlage.

**Testcase:** Lisanne kiest "14-dagenbrief" in de compose-dialog. Brief gaat uit naar consument zonder factuur-PDF. Debiteur heeft geen documentaire basis om de hoofdsom te verifieren. Bij incasso-geschil staat Lisanne zwakker: de debiteur kan stellen dat hij niet wist welke factuur openstond.

**Fix:** Breid SOMMATIE_TEMPLATE_TYPES uit met 14_dagenbrief, aanmaning, tweede_sommatie en alle sommatie-varianten + demand_for_payment_*. Hernoem naar AUTO_ATTACH_INVOICES_TEMPLATE_TYPES. Laat herinnering en bevestiging_sluiting expliciet buiten.

---

### C6 - Alle geldbedragen tonen "EUR" als tekst i.p.v. het euro-symbool

**Locatie:** _fmt_currency in backend/app/documents/docx_service.py r. 161-169.

**Evidence:**

    def _fmt_currency(value):
        """Format value as Dutch currency: EUR 1.234,56."""
        ...
        return f"EUR {formatted}"

**Analyse:** De standaard-output voor ALLE geldbedragen in alle 25 e-mail-templates en alle DOCX-uitvoer is "EUR 1.234,56". Nederlandse zakelijke standaard is het euro-symbool met non-breaking-space. De BaseNet-referentiemails in de repo-root (EENMALIG SCHIKKINGSVOORSTEL.eml, SOMMATIE TOT BETALING.eml) tonen consequent het euro-teken. Een debiteur leest "EUR 5.956,25" in een Nederlandse brief als buitenlands/slordig.

**Fix:** _fmt_currency aanpassen naar euro-entity + NBSP + bedrag. Indien DOCX echt "EUR" nodig heeft, een aparte helper _fmt_currency_docx behouden. In HTML-email-context is &euro; altijd ondersteund.

---

## HIGH

### H1 - Aanmaning / tweede_sommatie gebruiken termijn_14_dagen (today+15) zonder weekend/feestdag-correctie

**Templates:** _render_aanmaning (r. 440-442) en _render_tweede_sommatie (r. 528-530).

Beide briefsoorten interpoleren ctx[termijn_14_dagen] = today + 15 dagen. Op 22 april wordt dat "7 mei 2026" - helder voor de debiteur. Maar today+15 is niet gekalibreerd op weekenden of (Nederlandse) feestdagen. Als de uiterste datum op een zondag of feestdag valt, kan een debiteur aanvoeren dat hij niet tijdig kon overmaken. HR-rechtspraak vereist dit niet dwingend, maar een wederpartij-advocaat heeft een handvat.

**Fix:** Helper die termijn_14_dagen op de eerstvolgende werkdag zet als de berekende datum in weekend/feestdag valt. Alternatief: formuleer expliciet "uiterlijk op de eerstvolgende werkdag na [datum]". Low-risk maar professionele finetuning.

---

### H2 - E-mail subject is onprofessioneel geformatteerd

**Locatie:** compose_router.py r. 392.

**Evidence:**

    subject=f"{data.template_type.replace('_', ' ').title()} inzake dossier {case.case_number}"

**Output:**
- 14_dagenbrief -> "14 Dagenbrief inzake dossier 2026-00042" (koppelteken verdwenen, rare hoofdletter)
- tweede_sommatie -> "Tweede Sommatie inzake dossier 2026-00042" (Title Case is on-Dutch)
- reactie_ncnp_9_3 -> "Reactie Ncnp 9 3 inzake dossier 2026-00042" (onleesbaar)
- sommatie -> "Sommatie inzake dossier 2026-00042" (acceptabel)

Vergelijk met de interne betreft_regel uit de briefkop: "SOMMATIE TOT BETALING / 2026-00042 / Test Debiteur BV" - wel correct. De brief zelf heeft dus een goed onderwerp, maar de e-mail komt met een slordig subject binnen bij de debiteur.

**Fix:** Mapping template_type -> Nederlands onderwerp maken (bijv. "Ingebrekestelling en 14-dagenbrief" voor 14_dagenbrief). Of beter: hergebruik de betreft_regel uit de template-render als subject (met HTML-tags gestript).

---

### H3 - BaseNet-vorderingstabel toont oorspronkelijke hoofdsom per vordering, niet openstaand saldo per vordering

**Locatie:** _vordering_table_basenet r. 300-308.

De kolom Bedrag rendert v[hoofdsom] - de originele factuurwaarde. Bij deelbetalingen (art. 6:44 BW) verandert de allocatie per claim (eerst kosten, dan rente, dan hoofdsom), maar de tabel blijft de oorspronkelijke hoofdsom tonen. Voor een debiteur met meerdere facturen en meerdere deelbetalingen wordt dit onoverzichtelijk.

**Fix:** Extra kolom Openstaand (hoofdsom - allocated_to_principal per claim). Vereist join met Payment allocaties per claim.

---

### H4 - "Voldaan bij klant" en "Door ons ontvangen" tonen dezelfde waarde

**Locatie:** _vordering_table_basenet r. 324-329.

**Evidence:**

    summary_rows.append(("Voldaan bij klant", ctx.get("betalingen_aftrek_bedrag", ""), False))
    summary_rows.append(("Door ons ontvangen", ctx.get("betalingen_aftrek_bedrag", ""), False))

Beide regels tonen hetzelfde bedrag. Semantisch verschillend: Voldaan bij klant = rechtstreeks aan client betaald; Door ons ontvangen = op derdengeldenrekening binnengekomen. Luxis heeft maar een Payment-type dus beide regels zijn de som van alles. Debiteur ziet twee aftrekposten met hetzelfde bedrag - verwarrend.

**Fix:** Kies een label ("Reeds ontvangen"). Als onderscheid nodig blijft: Payment.received_by enum (client / trust_account) en toon beide regels alleen als er daadwerkelijk beide stromen zijn.

---

### H5 - Geen guard tegen 14-dagenbrief naar B2B-debiteur

**Locatie:** geen check in compose_router of render-endpoint.

14-dagenbrief is volgens art. 6:96 lid 6 BW alleen verplicht voor **consumenten** (B2C). Voor B2B-debiteuren geldt deze niet: een zakelijke debiteur is van rechtswege in verzuim na vervaldatum en BIK mag direct worden gevorderd. Als Lisanne per vergissing "14-dagenbrief" kiest voor een B2B-dossier, gaat er een consumentenbeschermingsbrief naar een BV. Niet illegaal, wel professioneel pijnlijk - de wederpartij-advocaat merkt de overgeserveerde procedure direct op en kan er misbruik van maken ("uw client erkent klaarblijkelijk dat hij zich als consument gedraagt").

**Fix:** Op render-endpoint check of case.debtor_type == "b2c" voor 14_dagenbrief. Zo niet: 400 error "14-dagenbrief is uitsluitend voor consumenten" OF een waarschuwing in de compose-dialog met override-knop.

---

### H6 - Geen validatie dat 14-dagenbrief daadwerkelijk is verzonden voor BIK wordt gevorderd

**Locatie:** _financial_summary helper toont BIK ongeacht of 14-dagenbrief is verzonden.

De aanmaning en volgende sommaties presenteren BIK als verschuldigd. Als Lisanne de 14-dagenbrief overslaat (bug, haast, of menselijke fout), claimt de brief onrechtmatig BIK bij de consument. Een wederpartij-advocaat laat die BIK afwijzen.

**Fix:** Case.14dagenbrief_sent_at veld. In get_financial_summary voor B2C: BIK = 0 als 14dagenbrief_sent_at IS NULL of als (now - 14dagenbrief_sent_at < 14 dagen). Dit is business-critical voor de hele pipeline.

---

### H7 - De 4 meest gebruikte templates hebben geen expliciete render-tests

**Locatie:** backend/tests/test_incasso_templates.py.

De test suite dekt: sommatie, schikkingsvoorstel, VSO, faillissement_dreigbrief, sommatie_na_reactie, sommatie_eerste_opgave, niet_voldaan_regeling, sommatie_laatste_voor_fai, wederom_sommatie_inhoudelijk/kort, sommatie_drukte, alle demand_for_payment_* (4 stuks). GEEN test voor: aanmaning, herinnering, 14_dagenbrief, tweede_sommatie. Juist de 4 juridisch centrale, dagelijks gebruikte briefsoorten.

Daarbij gebruikt de mock_context (r. 25-73) "euro 5.000,00" als input, terwijl de productie-pipeline via _fmt_currency "EUR 5.000,00" oplevert. Tests zouden dus zelfs bij bestaan de dubbel-symbool-bug en het EUR-i.p.v.-euro-bug NIET vangen omdat ze met niet-realistische data werken.

**Fix:** 1) Tests toevoegen voor de 4 core-templates. 2) Mock_context vervangen door build_base_context-aanroep op een gefixturde in-memory case, zodat tests daadwerkelijk de productie-pipeline valideren. 3) Expliciete assertion: assert "EUR " not in html (na C6 fix) en assert "&euro;" in html.

---

## MEDIUM

### M1 - Rente-label hardcoded "Rente" negeert handelsrente-case

**Locatie:** _financial_summary r. 182 ("Rente t/m {vandaag}"); _financial_summary_compact r. 203.

De context biedt rente_type_label (bijv. "Handelsrente (art. 6:119a BW)", "Wettelijke rente (art. 6:119 BW)"). Het _financial_summary helper gebruikt deze niet en rendert alleen generiek "Rente t/m [vandaag]". B2B-debiteur ziet dus niet welk type rente wordt gevorderd. 14-dagenbrief hardcodet expliciet "Wettelijke rente" in r. 567 (correct, want B2C only), maar aanmaning/tweede_sommatie/herinnering zijn vager dan nodig.

**Fix:** _summary_row(f"{ctx[rente_type_label]} t/m {ctx[vandaag]}", ...).

---

### M2 - Herinnering zegt "voor [datum]" - ambigu

**Locatie:** _render_herinnering r. 615-616.

"voor 7 mei 2026 over te maken" - een Nederlandse lezer kan dit interpreteren als "voor de datum 7 mei, dus uiterlijk 6 mei". Juridische correspondentie hoort "uiterlijk op" te gebruiken.

**Fix:** "uiterlijk op [termijn_14_dagen]".

---

### M3 - Signature en derdengelden-IBAN zijn hardcoded - multi-tenant failure mode

**Locatie:** _signature r. 215-246 en betalings-blokken in vrijwel alle templates.

Hardcoded in de code: "mr. L. Kesting", "incasso@kestinglegal.nl", "Kesting Legal B.V.", en derdengelden-IBAN "NL20 RABO 0388 5065 20". Luxis is multi-tenant (TenantBase), maar alle signature- en IBAN-data zijn specifiek voor Kesting Legal. Zodra er een tweede advocaat/tenant komt, is dit fout. Ook als Kesting Legal zelf een tweede behandelaar zou krijgen.

**Fix:** Tenant-velden: trust_iban, trust_stichting_naam, lawyer_signature_html, incasso_email. Template-render gebruikt kantoor.trust_iban, kantoor.lawyer_signature, etc.

---

### M4 - Placeholders worden NIET geblokkeerd bij verzenden

**Locatie:** _render_schikkingsvoorstel r. 732-734; _render_wederom_sommatie_inhoudelijk r. 1301-1303; VSO termijnen_tekst default.

Als Lisanne vergeet placeholders in te vullen ([VUL SCHIKKINGSBEDRAG IN], [VUL TERMIJNEN IN], [HIER INHOUDELIJKE REACTIE INVULLEN]), gaat de brief letterlijk met die teksten naar de debiteur. Extreem genant en schadelijk voor het dossier.

**Fix:** Server-side validatie voor verzenden: if "[VUL " in body_html or "[HIER " in body_html: raise 400 "Er staan nog niet-ingevulde placeholders in de brief".

---

### M5 - Briefkop mist behandelaar/doorkiesnummer

**Locatie:** _BASE_EMAIL r. 67-73.

Het layout-blok toont vandaag + "Ons kenmerk" + "Uw kenmerk" (optioneel). Standaard advocatencorrespondentie noemt ook "Behandelaar: [naam]" en "Doorkiesnummer: [tel]". Niet aanwezig.

**Fix:** Behandelaar en doorkiesnummer toevoegen in de kop (uit user/tenant context).

---

## LOW

### L1 - Trailing slash in betreft-regel als wederpartij-naam leeg is

**Locatie:** _render_sommatie r. 506-509 en alle templates die f"... / {zn} / {ctx[wederpartij][naam]}" gebruiken.

Als wederpartij.naam = "" (fallback van _contact_ctx) dan wordt de betreft: "SOMMATIE TOT BETALING / 2026-00042 / " - trailing whitespace / spatie. Cosmetisch.

**Fix:** strip trailing " / " als wederpartij.naam leeg is.

---

### L2 - reactie_9_3, reactie_20_4, reactie_ncnp_9_3 openen met een alleenstaande komma

**Locatie:** r. 635, 677, 832.

Deze templates openen met "<p>,</p>" - een alleenstaande komma waar een aanhef (Geachte heer, mevrouw,) hoort. reactie_verlengd_9_3 r. 889 heeft de aanhef wel. Inconsistent.

**Fix:** "<p>Geachte heer, mevrouw,</p>".

---

### L3 - Engelstalige templates missen schuldhulp-disclaimer

**Locatie:** _render_engelse_sommatie (r. 767-824) en alle demand_for_payment_* (r. 1458-1633).

De schuldhulp-disclaimer (verwijzing naar Stichting 113 etc.) is een Nederlandse consumentenbeschermingsconventie die in de EN-templates ontbreekt. Voor internationale debiteuren is dit mogelijk bewust - zij vallen niet onder Nederlands schuldhulprecht. Geen harde fix nodig, wel een bewuste keuze om te documenteren.

**Fix (optioneel):** Engelstalige variant van de disclaimer of expliciete comment in de code dat deze bewust ontbreekt.

---

## Cross-cutting observaties

- **Geen render-test valideert bedragen tegen een gouden totaal.** Alle bestaande tests zijn "html bevat string X"-assertions. Er is geen test die build_base_context -> render -> parse -> assert totaal_verschuldigd == hoofdsom + rente + BIK (+ BTW).
- **_fmt_currency heeft geen unit-test voor negatieve bedragen** (betalingen). Edge case: total_paid = 1.000,50 -> _fmt_currency levert "-EUR 1.000,50". In _vordering_table_basenet met zijn eigen <td>&euro;</td> kolom wordt dat "euro -EUR 1.000,50". Dubbel lelijk.
- **btw_toelichting-formulering:** f"{ctx[bik_bedrag]}{ctx[btw_toelichting]}" plakt de strings direct aan elkaar zonder tussenruimte. Als BTW actief wordt (na fix C2), zal het resultaat zijn: "<strong>EUR 500,00 (vermeerderd met EUR 105,00 BTW)</strong>" - kleefschrift. Zet een spatie of HTML-padding tussen de twee delen.
- **Het mock_context in test_incasso_templates.py** gebruikt "euro-teken 5.000,00" als currency-string. Productie-pipeline levert "EUR 5.000,00". De tests worden dus tegen een niet-realistische context gedraaid; eventuele currency-format bugs komen nooit aan het licht in CI.

---

## Samenvatting voor Lisanne

Zes echte bloedingsrisico's:

1. **14-dagenbrief is juridisch kwetsbaar** - "na dagtekening" formulering in de eindzin kan leiden tot BIK-verbeurdverklaring bij elke consumentenzaak (C1).
2. **BIK wordt te laag berekend** als Lisanne of haar client BTW-vrijgesteld is - de 21% wordt nooit opgeteld (C2).
3. **14-dagenbrief noemt geen IBAN** - debiteur kan niet betalen want de brief verwijst naar "het rekeningnummer van onze client" zonder dat nummer te tonen (C3).
4. **Dubbel valutasymbool** "euro-teken EUR 1.234,56" in 17 van de 25 templates (C4).
5. **Alleen "sommatie" krijgt factuur-bijlagen** - de 14-dagenbrief en alle andere sommatie-varianten hebben geen documentaire onderbouwing (C5).
6. **"EUR 1.234,56" overal** i.p.v. euro-teken + bedrag - afwijkend van BaseNet (wat Lisanne gewend is) en Nederlandse typografische standaard (C6).

De 4 meest gebruikte briefsoorten (herinnering, aanmaning, 14-dagenbrief, tweede_sommatie) **zijn ook niet expliciet getest**. De bestaande tests gebruiken bovendien een mock-context met andere valutaformattering dan productie, waardoor die bugs door de test-suite worden gemist.

