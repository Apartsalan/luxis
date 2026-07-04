# Premortem-transcript — Kennisbank & Learning Loop (4 juli 2026)

**Gepremortemd:** architectuurkeuze + gefaseerd plan voor de Luxis AI-kennisbank en
learning loop (selectieve prompt-injectie zonder RAG; kennisbank met voorwaarden per
vaste opdrachtgever; leren uitsluitend via door Lisanne goedgekeurde voorbeelden;
meetbaarheid via edit-rate).

**Frame:** het is januari 2027, zes maanden verder — het plan is mislukt. Waarom?

**Context verzameld:** wat (architectuur + K1/K2/K3-plan), voor wie (Kesting Legal /
Lisanne; later andere kantoren), succes (concepten die vrijwel ongewijzigd de deur uit
gaan, juridisch gegrond, geen AVG-incidenten, geen autonomie-drift, generaliseerbaar).

**Methode:** 7 faalredenen uit de ruwe premortem; per reden één parallelle
diepte-analyse (verhaal, onderliggende aanname, vroege signalen); daarna synthese.

---

## Faalreden 1 — De kennisbank blijft leeg

**Faalverhaal.** Juli 2026: K1 gaat live. De tabel bestaat, de UI werkt, de injectie is
getest met één dummy-document. "Content: aan te leveren door Lisanne/Arsalan" — een
actiepunt zonder eigenaar, deadline of formaat. Arsalan mailt Lisanne of ze de
voorwaarden van de 7 opdrachtgevers kan sturen. Zij antwoordt "komt eraan" en gaat door
met dagvaardingen schrijven. Augustus–oktober: elke sessie begint met "kennisbank nog
leeg, wachten op Lisanne". Het patroon was al zichtbaar: de 130 verweer-kandidaten
stonden op dát moment al drie weken onaangeroerd — het bewijs dat Lisanne geen
review-/aanleverwerk doet naast haar praktijk was er vóór de bouw begon. Niemand
definieerde wat "aanleveren" betekent: PDF mailen? Knippen in fragmenten per artikel?
Dat laatste is juridisch curatiewerk dat alleen Lisanne kan, en juist dát is nooit als
taak benoemd. Januari 2027: de verweer-prompt draait nog exact als daarvoor. K2 nooit
gestart — wachtte op een review-ronde die ook nooit kwam. Twee features, geblokkeerd op
dezelfde persoon.

**Onderliggende aanname.** "Als de techniek er staat en de waarde evident is, levert
Lisanne de content wel aan" — terwijl 130 wachtende kandidaten al lieten zien dat
evidente waarde niet tot handelen leidt zonder dat iemand het werk tot bijna-nul
reduceert.

**Vroege signalen.** (1) Staat de kandidaten-teller bij K1-launch nog >100, dan komen de
voorwaarden ook niet. (2) Veertien dagen na K1: aantal actieve knowledge_documents = 0
→ het plan faalt al.

---

## Faalreden 2 — Verouderde/verkeerde voorwaarden, en de AI bouwt erop

**Faalverhaal.** September 2026: Lisanne uploadt de voorwaarden die ze toevallig als PDF
had. Niemand vraagt: van welk jaar, en welke versie hoorde bij welke overeenkomst?
"Versie" bestaat niet als concept in de tabel. In oktober vernieuwt de grootste
opdrachtgever zijn voorwaarden (annuleringskosten verhuizen van art. 9.3 naar art. 10.2,
percentages gewijzigd). Niemand merkt het. November: een verweerbrief citeert vol
vertrouwen "artikel 9.3: 25% annuleringskosten" in een dossier waar de overeenkomst ná
de wijziging gesloten was. Juist doordat het concept er juridisch degelijk uitzag — écht
artikelnummer, écht citaat — las Lisanne het minder kritisch dan haar eigen tekst; de
kennisbank had haar waakzaamheid verláágd. De wederpartij-advocaat wijst er fijntjes op.
December: Lisanne vertrouwt geen citaat meer en controleert alles regel voor regel; het
tijdsvoordeel verdampt en het wantrouwen straalt af op de hele leer-loop.

**Onderliggende aanname.** "Algemene voorwaarden zijn statisch: één keer uploaden is
genoeg" — terwijl het tijdgebonden versies zijn waarvan de toepasselijkheid per dossier
verschilt (datum overeenkomst).

**Vroege signalen.** (1) Aantal knowledge_documents mét ingevulde geldigheidsperiode = 0
bij intake. (2) Lisanne corrigeert een artikelnummer/percentage dat rechtstreeks uit de
kennisbank kwam — dat is een bron-fout, geen stijl-edit: direct alarm.

---

## Faalreden 3 — Meer context maakt concepten slechter (verwatering + kosten)

**Faalverhaal.** Augustus 2026: K1 live. Bij het vullen ontstaat de glijdende schaal:
Lisanne kan niet vooraf zeggen wélk artikellid relevant is, dus "voor de zekerheid" gaat
het hele artikel erin — soms drie. De deterministische selectie injecteert exact wat in
de tabel staat; niemand bewaakt wát er in de tabel staat. De prompt groeit van ±4.000
naar 10.000+ tekens juridische brontekst. Het model gaat op de dominante context leunen:
concepten parafraseren voorwaarden, in het register van de voorwaarden — formeel, wollig.
De drie stijl-voorbeelden verdrinken. Lisanne herschrijft vaker "fors" maar wijt het aan
"lastige zaken". Niemand heeft een baseline vastgeklikt op de livegang-datum, dus de
trendbreuk is niet aan K1 toe te schrijven. Input-tokens per verweer-call verdubbelen;
de kosten-afspraak werd bij lancering nagekomen maar nooit herhaald toen de tabel
groeide. Pas in december valt de kostenstijging op; terugkijkend bleek de edit-rate
sinds september structureel verslechterd.

**Onderliggende aanname.** "Meer relevante juridische context maakt een concept
automatisch beter" — terwijl het kwaliteitsanker de stijl-voorbeelden zijn, die door
volume worden verdrongen.

**Vroege signalen.** (1) Gemiddelde injectiegrootte per verweer-call boven een vooraf
gestelde limiet (bv. 1.500 tekens) → "selectief" is al fictie. (2) Edit-rate gesplitst
vóór/ná K1 én mét/zónder injectie: verschil zichtbaar binnen twee weken i.p.v. vier
maanden.

---

## Faalreden 4 — De loop verstopt: Lisanne reviewt niet structureel

**Faalverhaal.** Juli 2026: 130 kandidaten klaar, dashboard herbouwd, "morgen of
overmorgen" al twee keer verschoven. Augustus: onder lichte druk doet Lisanne een eerste
sessie, komt tot kandidaat 40, vindt het mentaal zwaarder dan verwacht en stopt "voor
nu". Niemand definieert wat "klaar genoeg" is, dus K2 blijft formeel wachten op "de
eerste ronde" — die nooit officieel eindigt. September–november: de wachtrij groeit van
90 naar 200+. Elke keer dat ze het dashboard opent is de berg gróter — de achterstand
zelf wordt de reden om niet te beginnen. Arsalan wil niet blijven pushen (zij is de
klant). De AI produceert concepten zonder goedgekeurde voorbeelden; Lisanne merkt geen
kwaliteitsverschil, dus review voelt als onbetaald huiswerk zonder beloning. Januari
2027: K1 half aangeleverd, K2 nooit gestart, de "loop" was een eenrichtings-wachtrij.
Drie kwartalen tooling rond een knop die de gebruiker niet indrukte.

**Onderliggende aanname.** "Als reviewen maar makkelijk genoeg is, maakt een overbelaste
solo-advocaat vanzelf structureel tijd vrij voor werk zonder deadline of cliënt."

**Vroege signalen.** (1) Veertien dagen na dashboard-oplevering: 0 beoordeeld (of één
sessie <30 zonder vervolg binnen een week) — staat begin juli al op rood. (2) Instroom
nieuwe kandidaten per week > beoordeeld per week, twee weken op rij — de wiskundige
definitie van een verstopte loop.

---

## Faalreden 5 — Per-voorbeeld attributie stuurt op ruis

**Faalverhaal.** Juli 2026: K2 live, dashboard toont per voorbeeld een gemiddelde
edit-rate. Met ~25 verzonden concepten per maand en 3 voorbeelden per concept verzamelt
elk voorbeeld hooguit 10–15 "observaties" per kwartaal — en elke observatie deelt zijn
uitkomst met twee andere voorbeelden. Augustus: voorbeeld #12 kleurt rood (0.55 over 6
concepten). Niemand ziet dat 4 van die 6 één lastige debiteur betroffen. Het voorbeeld
wordt vervangen. Elk kwartaal sneuvelen 2–3 "slechte" voorbeelden op 5–8 datapunten;
omdat de bibliotheek verandert resetten de metingen telkens — er ontstaat nooit genoeg
data om één verwijdering te valideren. December: concepten voor een bekend verweer-type
zijn ineens slechter — het "slechte" voorbeeld van augustus was juist het enige goede
voor die situatie; het scoorde slecht omdat het bij moeilijke zaken werd meegestuurd.
Januari 2027: bibliotheek drie keer deels ververst, niemand kan reconstrueren waarom,
vertrouwen in het leersysteem weg. De cijfers zágen er alleen wetenschappelijk uit.

**Onderliggende aanname.** "Als we het meten, betekent het iets" — dat correlatie op
deze schaal (tientallen n, drievoudige confounding, heterogene zaken) attributie-
informatie bevat.

**Vroege signalen.** (1) Ranking-instabiliteit: de volgorde beste/slechtste klapt om bij
elke herberekening of bij leave-one-out. (2) Rood/groen-labels bij n < 20 solo-toewijsbare
observaties → er wordt al op ruis gestuurd.

---

## Faalreden 6 — Scope-drift naar de autonome agent

**Faalverhaal.** Augustus 2026: de bibliotheek draait maanden foutloos, 95% van de
concepten gaat ongewijzigd de deur uit. Iemand zegt: "waarom moet ik standaardgevallen
nog klikken?" Er komt "auto-verstuur bij exacte sjabloonmatch" — verdedigbaar, het is
letterlijk sjabloontekst. September: opgerekt naar "hoge zekerheid"-drafts, want de
K2-meetdata laat zien dat die óók 95%+ halen. De meetinfrastructuur wordt zo het
argument vóór autonomie in plaats van de bewaker ertegen. November: auto-versturen en
pipeline-doorschuiving gekoppeld — de oude roadmap-droom draait de facto; niemand heeft
S160 formeel teruggedraaid, het is geërodeerd in tien kleine commits. December: een mail
die op standaardverweer lijkt maar een echte betwisting bevat (het S164-patroon:
model-flakiness op randgevallen) wordt "simpel" geclassificeerd en automatisch
beantwoord. De wederpartij-advocaat citeert die mail. Lisanne hoort het van de
opdrachtgever — en stopt met álle AI-concepten, want ze kan niet meer zien welk deel
"alleen assistent" is.

**Onderliggende aanname.** "Een hoog goedkeuringspercentage in het verleden bewijst dat
menselijke controle in de toekomst overbodig is" — terwijl de 5% afwijzingen juist de
gevallen zijn waar controle voor bestond.

**Vroege signalen.** (1) Elke commit die een verzend- of statuswijzigende actie
toevoegt zonder expliciete gebruikersklik — meetbaar, moet nul blijven. (2) Lisanne's
review-tijd per concept zakt onder ~10 seconden of ze keurt batches blind goed — dat is
geen vertrouwen, dat is controle die al verdwenen is.

---

## Faalreden 7 — Kesting-maatwerk dat niet generaliseert

**Faalverhaal.** September 2026: K1 werkt prima — voor Kesting. De kennisbank verving de
aannames niet, maar stapelde erop: de vijf verweer-typen bleven de as, knowledge_documents
hingen eraan als bijlagen. November: eerste demo bij kantoor 2 (arbeidsrecht). De AI
classificeert een ontslagverweer als "afrekening art. 20.4" omdat de heuristieken
sommatie-patronen zoeken die er niet zijn, en valt terug op het dichtstbijzijnde
Kesting-type; de demo-verweren komen terug met no-cure-no-pay-redeneringen die voor
arbeidsrecht onzin zijn. Het verkoopargument — "de AI kent uw praktijk" — wordt ter
plekke weerlegd door de output zelf. December: "twee weken aanpassen" wordt zes weken
herbouw, want de verweer-typen zaten niet in data maar in promptlogica, categorielijsten
én de leer-loop, die zes maanden Kesting-feedback had ingebakken. Kantoor 2 haakt af;
het GTM-plan ligt stil zonder tweede referentieklant. Kesting draait intussen prima —
het product werkte, maar alleen als maatpak.

**Onderliggende aanname.** "Multi-tenant datamodel = generaliseerbaar product" — terwijl
de echte specificiteit niet in de tabellen zat maar in verweer-typen, heuristieken en
promptlogica die K1 juist dieper verankerde.

**Vroege signalen.** (1) De teller "hardcoded Kesting-begrippen buiten de database"
stijgt tijdens K1 in plaats van te dalen. (2) De synthetische-tenant-test (fictief
kantoor, ander rechtsgebied, 3 dossiers, binnen één dag bruikbaar zonder codewijziging)
wordt nooit gedraaid — zolang niemand hem draait, weet je het antwoord al.

---

## Synthese

**Meest waarschijnlijke faal:** de menselijke bottleneck (redenen 1 + 4 — zelfde wortel).
Het plan hangt op deadline-loos werk van Lisanne, en het signaal staat nú al op rood
(130 kandidaten, ±3 weken, twee keer verschoven).

**Gevaarlijkste faal:** reden 2 (verkeerd/verouderd citaat in een echte zaak) — één
incident raakt Lisanne's vertrouwen in álle AI-features; reden 6 heeft hetzelfde
eindpunt via een andere weg.

**Verborgen aanname (overkoepelend):** het plan behandelt Lisanne's tijd als gratis en
juridische kennis als statisch — "als wij het bouwen, komen content, review en
correctheid vanzelf."

**Herzien plan (verwerkt in het onderzoeksdocument §5):**
1. **K0-gate vóór alle bouw:** voorwaarden verzameld (eerst zoeken in BaseNet-import;
   Lisanne alleen valideren) én eerste review-ronde gebeurd. Na 14 dagen nul → gesprek,
   geen bouw.
2. **Versie-metadata verplicht** (versiedatum + geldig-vanaf) + citaat altijd mét
   versiedatum in beeld.
3. **Injectie-cap (~1.500 tekens) in code** + log injectiegrootte.
4. **Met/zonder-vlag per draft** zodat edit-rate vóór/ná en mét/zónder vergelijkbaar is;
   baseline vastklikken op livegang-datum.
5. **Per-voorbeeld attributie geschrapt** uit K2; vervangen door geaggregeerde trend +
   wachtrij-gezondheid (instroom vs beoordeeld per week).
6. **Autonomie-grendel als test:** geen verzendpad zonder gebruikersklik (S160 in code).
7. **Kesting-begrippen richting data**, hardcoded-teller mag tijdens K1 niet stijgen;
   synthetische-tenant-test inplannen vóór GTM-demo's.

**Checklist vóór K1-start:**
- [ ] ≥5 van 7 voorwaarden-sets binnen, mét versiedatum per document
- [ ] Eerste review-ronde: ≥50 van 130 kandidaten beoordeeld
- [ ] Injectie-cap + met/zonder-vlag in het K1-ontwerp opgenomen
- [ ] Autonomie-grendel-test gespecificeerd
- [ ] Baseline edit-rate genoteerd (datum + cijfers)
