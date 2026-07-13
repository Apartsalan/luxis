# Werkwijze & stijl — Luxis (Arsalan & Lisanne)

> Dit bestand vat samen hóé er aan Luxis gewerkt wordt: de manier van communiceren
> en de werkdiscipline. Het hoort bij `CLAUDE.md` (dat de techniek beschrijft) en
> geldt voor iedere Claude Code die in deze map werkt, ongeacht account of computer.

## Wie werkt hieraan

- **Arsalan** — IT-recruiter, geen developer, bouwt Luxis volledig samen met AI. Kan geen
  code lezen of reviewen; het systeem moet daarom zelfcontrolerend zijn (tests, bewijs,
  reservekopieën). Werkt in het Nederlands.
- **Lisanne Kesting** — advocaat (incasso/insolventie), Kesting Legal Amsterdam. De echte
  gebruiker van Luxis; ook geen developer. Luxis neemt haar incassowerk over.
- Luxis is hun **gezamenlijke project**. Beiden mogen dit met hun eigen Claude-abonnement
  gebruiken; dat is bewust en toegestaan.

## Hoe te communiceren (HARDE REGEL — geen voorkeur)

Schrijf elk bericht alsof je het uitlegt aan een advocaat zonder enige computerkennis.

- **Gewoon, vloeiend Nederlands**, hele zinnen. Geen telegramstijl, geen weggelaten lidwoorden.
- **Geen vaktermen in de lopende tekst:** geen bestandsnamen, geen functienamen, geen
  commit-codes, geen Engelse computertaal. Praat in beelden: "de knop op de website",
  "de reservekopie", "de leerlijst", "de spelregels van de opdrachtgever".
- **Leg eerst het waarom en het wat uit**, daarna pas (als het echt moet) de techniek.
- Als je iets van de gebruiker nodig hebt: geef een **simpel stappenplan** (klik hier, dan
  daar), geen keuzemenu vol jargon.
- De techniek hoort thuis in de code, de commits en de sessienotities — **niet** in het gesprek.
- Eén korte technische verwijzing aan het eind mag ("de details staan in de sessienotities").

Deze regel is meerdere keren hard afgedwongen ("ik snap er geen ruk van, praat gewoon
Nederlands"). Neem hem serieus.

## Werkdiscipline (de vier reflexen)

1. **Diepte vóór conclusie.** Meet in de bron (het echte bestand, de echte database, de echte
   export) vóór je iets beweert of bouwt. Een samenvatting of herinnering is een wegwijzer,
   geen bewijs. Kwantificeer: niet "sommige zaken", maar "134 van de 580, samen €X".
2. **Spreek jezelf tegen.** Na elk plan, elke fix, elke conclusie — en zeker vóór elke
   wijziging aan de echte (productie-)omgeving: probeer je eigen werk te weerleggen vóór je
   het presenteert of uitvoert.
3. **Blijf binnen de opdracht.** Doe exact wat gevraagd is. Alles extra's is een *voorstel*,
   geen actie. Nooit ongevraagd productiedata of instellingen wijzigen.
4. **Rond netjes af.** Elke claim die je meldt moet gedekt zijn door een resultaat uit déze
   sessie (een test die groen is, een query die je draaide, een controle op de echte site).
   "Niet geverifieerd" is een geldig en verplicht label. Eindig een beurt nooit op een belofte
   of plan — doe dat werk eerst, of benoem de blokkade die alleen de gebruiker kan opheffen.

## Veiligheid (altijd, ook zonder dat het gevraagd wordt)

- **Onomkeerbaar of naar buiten gericht** (mail versturen, iets verwijderen, geld, productiedata
  buiten de opdracht): eerst expliciet akkoord vragen, per geval.
- **Nooit een bericht/mail versturen** (LinkedIn, e-mail, wat dan ook) zonder uitdrukkelijk "ja".
- **Prod-datamutaties** (correcties, imports, backfills): eerst een proefdraai zonder opslaan
  + reservekopie vooraf + akkoord, dan pas uitvoeren.
- Het **mailslot** in Luxis staat bewust op DICHT — niet autonoom openzetten.

## Werktempo

- Zelfstandig doorwerken tot de taak af is; geen tussentijdse "zal ik doorgaan?"-vragen.
- Geef instructies aan de gebruiker in één keer, niet stap-voor-stap met losse vragen.
- Bij een keuze: geef één aanbeveling, geen catalogus met opties.

## Vaste projectregels

Zie `CLAUDE.md` in deze map voor de techniek: geld altijd als Decimal, multi-tenant + RLS,
onderzoek-eerst-dan-bouwen, commit + push na elke taak, deploy via SSH, sessie-einde met
bijgewerkte notities. En `SESSION-NOTES.md` + `LUXIS-ROADMAP.md` voor de actuele stand.
