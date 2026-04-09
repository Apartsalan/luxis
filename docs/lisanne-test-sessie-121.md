# Testlijst voor Lisanne — sessie 120 + 121

**Datum:** 9 april 2026
**Inlog:** luxis.kestinglegal.nl
**Wat te testen:** alle nieuwe dingen uit de afgelopen twee sessies. Graag gewoon even doorklikken en zeggen wat je er van vindt, wat fout gaat of wat beter kan.

---

## 1. Mail-sjablonen (het grote werk van deze sessie)

Ik heb alle 15 briefen die je mij had gestuurd uit je Basenet-export één-op-één overgenomen in Luxis, zowel Nederlands als Engels. Ze staan nu allemaal in de mail-sjablonen lijst.

### Zo test je dit

1. **Open een willekeurig incasso-dossier**
2. **Klik op "Nieuwe e-mail"** (of waar je compose-scherm ook staat)
3. **Klik op de "Sjabloon" dropdown**

   Je ziet nu **7 groepen met in totaal 22 sjablonen**:
   - Aanmaningen (herinnering, aanmaning, 14-dagenbrief, tweede sommatie)
   - Eerste sommatie (met AV, met drukte-notitie, eerste opgave)
   - Na reactie debiteur (sommatie na reactie, wederom sommatie met of zonder inhoudelijke reactie)
   - Niet-nakoming regeling
   - Schikking & regeling (eenmalig schikkingsvoorstel, vaststellingsovereenkomst)
   - Faillissement (sommatie laatste mogelijkheid, verzoekschrift faillissement)
   - English (4 demand for payment varianten)

4. **Kies "Sommatie tot betaling (eerste, AV)"** en controleer:
   - Dossiernummer, cliëntnaam, wederpartij en alle bedragen zijn automatisch ingevuld
   - Termijn is "3 DAGEN NA HEDEN"
   - IBAN is NL20 RABO 0388 5065 20 — Stichting Beheer Derdengelden Kesting Legal
   - Je kunt de tekst bewerken in het bericht vóór je verstuurt

5. **Kies "Eenmalig schikkingsvoorstel"** en controleer:
   - De gele markering `[VUL SCHIKKINGSBEDRAG IN]` is zichtbaar
   - Je kunt er op klikken en er je eigen bedrag intikken
   - Termijn is 24 uur, en de tekst over "aanbod zonder nadelige erkenning" staat erin

6. **Kies "Treffen van een regeling (vaststellingsovereenkomst)"** en controleer:
   - Clausule 1 heeft het openstaand-bedrag al **automatisch** ingevuld (bijv. € 5.956,25) — **NIEUW**: je hoeft dit dus niet meer zelf in te tikken. Als er onderhandeld is tot een lager bedrag kan je het overschrijven
   - Clausule 2 heeft nog wel een gele markering `[VUL TERMIJNEN IN]` — die moet je zelf invullen met de afgesproken betalingstermijnen
   - Akkoord-termijn is "2 x 24 uur"
   - Er staan precies 6 clausules in de vaststellingsovereenkomst

7. **Kies "Wederom sommatie (met verweer-weerlegging)"** en controleer:
   - Er is een gele markering `[HIER INHOUDELIJKE REACTIE OP VERWEER INVULLEN]`
   - Je kunt er je inhoudelijke reactie in typen
   - Termijn is 3 dagen
   - Aan het einde staat een "Stuiting vordering"-blok met verwijzing naar artikel 3:317 BW

8. **Kies "Verzoekschrift faillissement"** en controleer dat:
   - De body vermeldt "Een kopie van het verzoekschrift treft u in de bijlage aan"
   - Termijn 2 dagen, derdengelden IBAN

### Concept verzoekschrift als bijlage

Dit is nieuw. Je kon in Basenet het concept verzoekschrift PDF meesturen als bijlage — dat kan nu ook in Luxis, **automatisch gevuld met de dossierdata**.

1. **Blijf in het compose-scherm met Verzoekschrift faillissement geselecteerd**
2. **Klik op "Bijlage"** onderaan
3. **Klik op "Uit sjablonen-bibliotheek"** (dit is de nieuwe optie)
4. Je ziet een modal met één item: **"Concept verzoekschrift faillissement"**
5. **Klik erop** → Luxis rendert het DOCX-template met dossierdata → converteert naar PDF → voegt het toe als bijlage
6. **Download de bijlage vanuit de compose** en open hem in Word/Acrobat
7. Controleer dat in het verzoekschrift staan:
   - Jouw cliënt als verzoeker
   - De debiteur als verweerder
   - Dossiernummer als kenmerk
   - Juiste bedragen (hoofdsom, rente, incassokosten, totaal)
   - Drie pagina's: begeleidende brief + verzoekschrift ex art. 1 Fw + slotpagina

**Belangrijk:** de bijlage wordt **altijd als PDF** verstuurd, nooit als DOCX. Dit is zo omdat de ontvanger anders de inhoud zou kunnen wijzigen. Interne bewerking van het template zelf doen we later (als je het anders wilt hebben).

### Wat ik graag van je wil weten

- **Kloppen alle 15 briefen inhoudelijk?** Wijkt een zin, een termijn of een IBAN af van hoe je het in Basenet had staan?
- **Mis je nog een variant die wel in je Basenet-lijst stond?**
- **De 3 placeholders die ik nog handmatig heb gelaten** (schikkingsbedrag, VSO-termijnen, verweer-reactie): moeten die zo blijven, of wil je voor één van de drie een automatische suggestie?
  - Voorbeeld schikkingsbedrag: wil je dat Luxis standaard 70% van het openstaand voorstelt, en jij kan dat overschrijven?
  - Voor de verweer-weerlegging komt later AI-ondersteuning uit je verweer-bibliotheek (5 voorbeelden die ik in sessie 122 ga toevoegen), dus dat blijft voorlopig handmatig.

---

## 2. Creditnota BTW (uit sessie 120)

Ik heb in sessie 120 de bug gefixt waarbij creditnota's bij gemixte BTW (bijv. 21% advies + 0% griffierecht) alles naar één tarief forceerde. In sessie 121 heb ik daar nog 3 extra tests bij gebouwd die 3 BTW-tarieven tegelijk, meerdere deelcredits en credits op goedgekeurde facturen dekken.

### Zo test je dit

1. **Maak een factuur met verschillende BTW-regels**, bijvoorbeeld:
   - 1 regel `Juridisch advies` à € 100 met 21% BTW
   - 1 regel `Griffierecht` à € 50 met 0% BTW
2. **Goedkeuren en versturen**
3. **Maak een volledige creditnota** voor deze factuur via de creditnota-knop
4. **Controleer:**
   - Totaal creditnota = **−€ 171,00** (NIET −€ 181,50). De 0%-regel krijgt géén 21% BTW erbij
   - In het dossier-overzicht zie je: originele factuur +€ 171 en creditnota −€ 171 → netto € 0
5. **Maak een deelcreditnota** met alleen de 0%-regel en controleer: −€ 50,00 zonder BTW

### Wat ik graag van je wil weten

- Loopt dit nu soepel of merk je nog gekkigheden?
- **BUG-check (DF120-02):** na het maken van een creditnota, klopt het facturen-overzicht in het dossier? Ik had nog een openstaande verificatie-vraag of dit sinds sessie 120 nu oké is.

---

## 3. Rente-periode en minimum provisie per klant (uit sessie 120)

### Zo test je dit

1. **Open Relaties → kies een cliënt**
2. **Bewerken** → kijk naar het tabje met rente-instellingen
3. Je zou nu moeten zien:
   - **Standaard rente-percentage** (bijv. 8%)
   - **Periode** (per maand / per jaar) — dit was nieuw in sessie 120
   - **Minimum provisie** (bijv. € 150) — ook nieuw in sessie 120
4. **Sla op**
5. **Maak een nieuw dossier aan voor deze cliënt**
6. Controleer dat de nieuwe velden automatisch zijn overgenomen in het dossier (ook in de read-only weergave van de cliënt-detailpagina — dat was een bug (DF120-12) die ik in sessie 120 heb gefixt)

### Wat ik graag van je wil weten

- Werken de waarden zoals je had verwacht bij het factureren?

---

## 4. Klik op debiteur → alleen openstaande facturen

Kleine verbetering uit vandaag. Als je in het facturen-overzicht op het tabje **Debiteuren** klikt en daar een relatie aanklikt, krijg je voortaan **alleen nog de openstaande facturen** te zien (sent + gedeeltelijk betaald + achterstallig). Voorheen kreeg je álle facturen van die relatie, inclusief betaald en concept.

### Zo test je dit

1. **Ga naar Facturen**
2. **Klik op het tabje Debiteuren**
3. **Klik op een relatie-naam**
4. Je ziet nu alleen de openstaande facturen. Je kunt ook bovenin de status-dropdown op **"Alleen openstaand"** zetten om dit filter handmatig toe te passen.

---

## 5. Vragen waar ik nog een beslissing van je wil

Er zijn een paar open vragen die ik niet zonder jou kan beantwoorden. Het zou fijn zijn als je hier even over nadenkt en antwoord geeft (telefoon, mail, wat je prettig vindt):

### A. Placeholder-automatisering in mail-sjablonen
- **Schikkingsbedrag**: nu handmatig. Wil je dat Luxis standaard bijvoorbeeld 70% van het openstaand voorstelt, die je kunt overschrijven?
- **VSO-totaalbedrag**: nu al auto op het openstaand (ik heb dit vandaag toegevoegd). Is dat goed, of wil je het toch handmatig?
- **VSO-termijnen**: nu handmatig. Verwacht ik dat dit handmatig blijft omdat termijnen uit onderhandeling komen. Klopt?

### B. Incassokosten + provisie zichtbaar op factuur naar cliënt (DF117-04)
De BIK en provisie staan nu wel als regel op de uitgaande factuur, maar ze zien eruit als elke andere factuurregel. Wil je dat ze apart worden gemarkeerd (bv. in een aparte sectie met een "Incassokosten" kopje), of is het goed zoals het nu is?

### C. Incassokosten shortcut vanuit dossier (DF117-05)
Je kunt nu via `Dossier → Documenten → Nieuwe factuur` een incasso-factuur maken, en dan verschijnt automatisch het BIK/Rente/Provisie-paneel. **Wil je een extra expliciete knop** "Incassokosten factureren" naast "Nieuwe factuur" in het dossier, of vind je de huidige route duidelijk genoeg?

### D. Verschot toevoegen aan verzonden factuur (DF117-10/11/15)
Op een concept-factuur kun je al verschotten toevoegen. Maar wat moet er gebeuren als een factuur al verstuurd is en je nog een verschot wilt toevoegen (bv. griffierecht dat later binnenkomt)?
- Optie 1: wijzig de verzonden factuur alsnog (juridisch iffy — je ontvanger heeft al een andere versie)
- Optie 2: automatisch een nieuwe factuur (of credit + nieuwe) aanmaken voor de extra verschotten
- Optie 3: handmatig nieuwe factuur aanmaken, huidige flow

Welke wil je?

### E. Algemene Voorwaarden per cliënt
Dit stond al langer op de lijst. Heb je de AV van al je cliënten in een DOCX of PDF? Dan kunnen we ze per cliënt koppelen en ze bijvoorbeeld automatisch als bijlage bij een eerste sommatie meesturen.

---

## Tot slot

Als je ergens tegenaan loopt tijdens het testen:
- Maak een screenshot
- Schrijf kort op wat je deed en wat er misging
- Stuur het naar Arsalan

Geen stress als niet alles vandaag lukt — neem de tijd en kijk wanneer je een uurtje vrij hebt. **Het belangrijkste vind ik de mail-sjablonen** (sectie 1), want dat is het grootste werk van deze sessie en daar wil ik het meeste van weten of het aansluit bij hoe jij werkt.
