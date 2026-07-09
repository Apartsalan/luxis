# Testlijst voor Lisanne — sessie 120 + 121

**Datum:** 9 april 2026
**Inlog:** luxis.kestinglegal.nl
**Wat te testen:** alle nieuwe dingen uit de afgelopen twee sessies. Graag gewoon even doorklikken en zeggen wat je er van vindt, wat fout gaat of wat beter kan.

> **Let op:** alle namen van knoppen, tabbladen en secties hieronder staan **exact zoals ze op het scherm** staan in Luxis. Als je iets niet ziet onder de naam die hier genoemd wordt, laat het weten — dan klopt mijn uitleg niet.

---

## 1. Mail-sjablonen (het grote werk van deze sessie)

Ik heb alle 15 briefen die je mij had gestuurd uit je Basenet-export één-op-één overgenomen in Luxis, zowel Nederlands als Engels. Ze staan nu allemaal in het sjablonen-menu van de mailcompose.

### Zo test je dit

1. **Ga in de linker sidebar naar "Dossiers"** en open een willekeurig incasso-dossier.
2. **Klik bovenaan in de dossier-header op de knop "E-mail versturen"** (met het envelope-icoon, in de rij naast "Factuur", "Nieuwe taak", enz.).
3. Het pop-upvenster **"E-mail opstellen"** wordt geopend.
4. **Klik op de "Sjabloon"-dropdown** onder de onderwerpregel.

Je ziet nu **7 groepen met in totaal 22 sjablonen**:
- **Aanmaningen** (Herinnering, Aanmaning, 14-dagenbrief, Tweede sommatie)
- **Eerste sommatie** (Sommatie tot betaling (eerste, AV), Sommatie tot betaling (eerste, met drukte-notitie), Sommatie tot betaling (eerste opgave))
- **Na reactie debiteur** (Sommatie na reactie debiteur, Wederom sommatie (met verweer-weerlegging), Wederom sommatie (kort, zonder verweer))
- **Niet-nakoming regeling** (Niet voldaan aan regeling — sommatie)
- **Schikking & regeling** (Eenmalig schikkingsvoorstel, Treffen van een regeling (vaststellingsovereenkomst))
- **Faillissement** (Sommatie laatste mogelijkheid (vóór verzoekschrift), Verzoekschrift faillissement (laatste mogelijkheid))
- **English** (Demand for payment — 4 varianten)

5. **Kies "Sommatie tot betaling (eerste, AV)"** en controleer:
   - Dossiernummer, cliëntnaam, wederpartij en alle bedragen zijn automatisch ingevuld
   - Termijn is "3 DAGEN NA HEDEN"
   - IBAN is NL20 RABO 0388 5065 20 — Stichting Beheer Derdengelden Kesting Legal
   - Je kunt de tekst in het bericht-vak bewerken vóór je verstuurt

6. **Kies "Eenmalig schikkingsvoorstel"** en controleer:
   - De gele markering `[VUL SCHIKKINGSBEDRAG IN]` is zichtbaar in de tekst
   - Je kunt er op klikken en er je eigen bedrag intikken
   - Termijn is 24 uur, tekst over "aanbod zonder nadelige erkenning" staat erin

7. **Kies "Treffen van een regeling (vaststellingsovereenkomst)"** en controleer:
   - Clausule 1 heeft het openstaand-bedrag al **automatisch** ingevuld (bijv. € 5.956,25) — **NIEUW**: je hoeft dit niet meer zelf in te tikken. Als er onderhandeld is tot een lager bedrag kan je het overschrijven
   - Clausule 2 heeft nog wel een gele markering `[VUL TERMIJNEN IN]` — die moet je zelf invullen met de afgesproken betalingstermijnen
   - Akkoord-termijn is "2 x 24 uur"
   - Er staan precies 6 genummerde clausules in de vaststellingsovereenkomst

8. **Kies "Wederom sommatie (met verweer-weerlegging)"** en controleer:
   - Er is een gele markering `[HIER INHOUDELIJKE REACTIE OP VERWEER INVULLEN]`
   - Je kunt er je inhoudelijke reactie in typen
   - Termijn is 3 dagen
   - Aan het einde staat een "Stuiting vordering"-blok met verwijzing naar artikel 3:317 BW

9. **Kies "Verzoekschrift faillissement (laatste mogelijkheid)"** en controleer:
   - De body vermeldt "Een kopie van het verzoekschrift treft u in de bijlage aan"
   - Termijn 2 dagen, derdengelden IBAN
   - Betreft-regel start met "VERZOEKSCHRIFT FAILLISSEMENT (LAATSTE MOGELIJKHEID)"

### Concept verzoekschrift als bijlage (nieuw)

Je kon in Basenet het concept verzoekschrift PDF meesturen als bijlage — dat kan nu ook in Luxis, **automatisch gevuld met de dossierdata**.

1. Blijf in het venster "E-mail opstellen" met "Verzoekschrift faillissement (laatste mogelijkheid)" geselecteerd.
2. **Klik onderaan op de knop "Bijlage"** (met het paperclip-icoon).
3. In het dropdown-menu zie je nu 4 opties: "Uit dit dossier", "Uploaden", "Ander dossier", en **"Uit sjablonen-bibliotheek"** (deze laatste is nieuw).
4. **Klik op "Uit sjablonen-bibliotheek"**.
5. Je ziet een paneel met één item: **"Concept verzoekschrift faillissement"**.
6. **Klik erop** → Luxis rendert het DOCX-template met dossierdata → converteert naar PDF → voegt het toe als bijlage in de compose.
7. **Download de bijlage vanuit de compose** en open hem in Word/Acrobat.
8. Controleer dat in het verzoekschrift staan:
   - Jouw cliënt als verzoeker
   - De debiteur als verweerder
   - Dossiernummer als kenmerk
   - Juiste bedragen (hoofdsom, rente, incassokosten, totaal)
   - Drie pagina's: begeleidende brief + verzoekschrift ex art. 1 Fw + slotpagina

**Belangrijk:** de bijlage wordt **altijd als PDF** verstuurd, nooit als DOCX. Zo kan de ontvanger niks wijzigen aan de inhoud.

### Wat ik graag van je wil weten

- **Kloppen alle 15 briefen inhoudelijk?** Wijkt een zin, een termijn of een IBAN af van hoe je het in Basenet had staan?
- **Mis je nog een variant die wel in je Basenet-lijst stond?**
- **De 3 placeholders die ik nog handmatig heb gelaten** (schikkingsbedrag, VSO-termijnen, verweer-reactie): moeten die zo blijven, of wil je voor één van de drie een automatische suggestie? Voorbeeld: wil je dat Luxis standaard 70% van het openstaand voorstelt als schikkingsbedrag, die je kunt overschrijven?

---

## 2. Creditnota BTW bij gemixte tarieven (uit sessie 120)

Ik heb in sessie 120 de bug gefixt waarbij creditnota's bij gemixte BTW (bijv. 21% advies + 0% griffierecht) alles naar één tarief forceerde.

### Zo test je dit

1. **Ga in de sidebar naar "Facturen"** en klik rechtsboven op **"Nieuwe factuur"**.
   (Je kunt ook vanuit een dossier testen: open een dossier → tab **"Facturen"** → knop "Nieuwe factuur".)
2. Maak een factuur aan met **twee factuurregels bij verschillende BTW-tarieven**, bijvoorbeeld:
   - 1 regel `Juridisch advies` à € 100 met 21% BTW
   - 1 regel `Griffierecht` à € 50 met 0% BTW
3. Klik de factuur door naar status **Goedgekeurd** en daarna **Verzonden**.
4. Open de factuur en **klik op "Creditnota aanmaken"** (of de gelijke knop die je in de factuurdetail ziet).
5. Maak een **volledige creditnota** met beide regels.
6. Controleer:
   - Totaal creditnota = **−€ 171,00** (NIET −€ 181,50). De 0%-regel krijgt géén 21% BTW erbij.
   - **In het dossier-overzicht** (open het dossier → tab **"Facturen"**): originele factuur +€ 171 en creditnota −€ 171 → netto € 0.

### Wat ik graag van je wil weten

- Loopt dit nu soepel of merk je nog gekkigheden?
- **BUG-check:** na het maken van een creditnota, klopt het facturen-overzicht in het dossier-tab "Facturen"? Ik had nog een openstaande verificatie-vraag (DF120-02) of dit sinds sessie 120 nu oké is.

---

## 3. Rente-periode en minimum provisie per cliënt (uit sessie 120)

Twee nieuwe velden op de cliënt-instellingen. Let op: de "Periode"-dropdown is **alleen zichtbaar bij rentetype "Contractuele rente"** — bij wettelijke/handels-/overheidsrente is het per definitie per jaar en verschijnt het veld niet.

### Zo test je dit

1. **Ga in de sidebar naar "Relaties"**.
2. **Klik op een cliënt** om de detailpagina te openen.
3. **Klik rechtsboven op de knop "Bewerken"**.
4. Scroll naar de sectie **"Facturatie"** (grijze hoofding, ongeveer halverwege de pagina onder de adresgegevens).
5. Je zou hier onder andere moeten zien:
   - **"Standaard rentetype"** (dropdown: Wettelijke rente / Handelsrente / Overheidsrente / Contractuele rente)
   - **"Contractueel rentepercentage (%)"** — alleen bij rentetype "Contractuele rente"
   - **"Periode"** — alleen bij rentetype "Contractuele rente", met opties "Per jaar" / "Per maand" — **dit is nieuw in sessie 120**
   - **"Standaard incassokosten"** (dropdown: WIK-staffel / Vast bedrag / Percentage van hoofdsom)
   - **"Minimum provisie (€)"** — **dit is nieuw in sessie 120**
6. **Zet rentetype op "Contractuele rente"**, vul rentepercentage in (bijv. 2), kies periode "Per maand", vul minimum provisie in (bijv. 150), klik **"Opslaan"**.
7. **Ga terug naar de detailpagina** (zonder bewerkmodus). Je zou onder "Facturatie" moeten zien:
   - De rente-regel toont "... · per maand" erachter
   - Een regel **"Minimum provisie"** met € 150,00
   Deze twee waren eerst niet zichtbaar in read-only — dat was bug DF120-12, gefixt aan het einde van sessie 120.
8. **Maak een nieuw dossier aan voor deze cliënt** (sidebar → "Dossiers" → "Nieuw dossier", of vanuit de relatie zelf als dat kan). Controleer dat de waarden automatisch zijn overgenomen op het dossier.

### Wat ik graag van je wil weten

- Werken de waarden zoals je had verwacht bij het factureren?
- Is de "Periode"-dropdown intuïtief genoeg op de plek waar die staat (alleen bij Contractuele rente)?

---

## 4. Klik op debiteur → alleen openstaande facturen

Kleine verbetering uit vandaag. Als je in het facturen-overzicht naar het tabblad **"Debiteuren"** gaat en daar op een naam klikt, krijg je voortaan **alleen nog de openstaande facturen** te zien (status Verzonden / Gedeeltelijk betaald / Achterstallig). Voorheen kreeg je álle facturen van die cliënt inclusief betaalde en concepten.

### Zo test je dit

1. **Ga in de sidebar naar "Facturen"**.
2. Bovenaan zie je twee tabbladen: **"Facturen"** en **"Debiteuren"**.
3. **Klik op het tabblad "Debiteuren"**.
4. **Klik op een cliëntnaam** in de lijst.
5. Je komt terug op het tabblad "Facturen" maar nu **alleen met openstaande facturen van die cliënt**.
6. Je kunt dit filter ook handmatig zetten: in de status-dropdown bovenaan het tabblad "Facturen" staat nu als eerste optie **"Alleen openstaand"**.

---

## 5. Vragen waar ik nog een beslissing van je wil

Een paar open vragen die ik niet zonder jou kan beantwoorden:

**A. Placeholder-automatisering in mail-sjablonen**
- Schikkingsbedrag: wil je dat Luxis standaard 70% van het openstaand voorstelt?
- VSO-totaalbedrag: nu al automatisch gevuld met openstaand saldo. Is dat goed?
- VSO-termijnen: verwacht ik handmatig te laten omdat termijnen uit onderhandeling komen. Klopt?

**B. Incassokosten + provisie zichtbaar op factuur naar cliënt (DF117-04)**
De BIK en provisie staan nu als gewone regel op de uitgaande factuur. Wil je dat ze **apart worden gemarkeerd** op de factuur (met een kopje "Incassokosten" boven de regels), of is het goed zoals het is?

**C. Incassokosten shortcut vanuit dossier (DF117-05)**
Je kunt nu via een dossier → tab **"Facturen"** → knop **"Nieuwe factuur"** een incasso-factuur maken, en dan verschijnt op de factuurwizard automatisch het BIK/Rente/Provisie-paneel. **Wil je een extra expliciete knop** "Incassokosten factureren" naast "Nieuwe factuur" in de Facturen-tab van het dossier, of vind je de huidige route duidelijk genoeg?

**D. Verschot toevoegen aan verzonden factuur (DF117-10/11/15)**
Op een factuur met status **"Concept"** kun je al verschotten toevoegen (knop **"Verschot toevoegen"** bovenaan de factuurregels-tabel). Maar wat moet er gebeuren als een factuur al **verstuurd** is en je nog een verschot wilt toevoegen (bv. griffierecht dat later binnenkomt)?
- Optie 1: wijzig de verzonden factuur alsnog (juridisch iffy — de ontvanger heeft al een andere versie in zijn archief)
- Optie 2: automatisch een nieuwe factuur (of creditnota + nieuwe factuur) aanmaken voor de extra verschotten
- Optie 3: handmatig een nieuwe factuur aanmaken — huidige werkwijze

**E. Algemene voorwaarden per cliënt**
Dit stond al langer op de lijst. Heb je de algemene voorwaarden van al je cliënten ergens als PDF (of DOCX)? Dan kunnen we ze per cliënt koppelen en ze bijvoorbeeld automatisch als bijlage bij een eerste sommatie meesturen.

---

## Tot slot

Als je ergens tegenaan loopt tijdens het testen:
- Maak een screenshot
- Schrijf kort op wat je deed en wat er misging
- Stuur het naar Arsalan

Geen stress als niet alles vandaag lukt — neem de tijd en kijk wanneer je een uurtje vrij hebt. **Het belangrijkste vind ik de mail-sjablonen** (sectie 1), want dat is het grootste werk van deze sessie en daar wil ik het meeste van weten of het aansluit bij hoe jij werkt.
