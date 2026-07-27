---
target: luxis.kestinglegal.nl — dashboard, dossiers, incasso, dossierdetail
total_score: 28
p0_count: 0
p1_count: 1
timestamp: 2026-07-27T11-34-32Z
slug: luxis-kestinglegal-nl
---
# Ontwerp-review Luxis (dashboard, dossierlijst, incassolijst, dossierdetail)

Gemeten op productie, 27 juli 2026, 1440x900 en 390x844. Register: product (werkgereedschap).

## Design Health Score

| # | Heuristiek | Score | Belangrijkste bevinding |
|---|-----------|-------|-------------------------|
| 1 | Zichtbaarheid van systeemstatus | 3 | Skeletons + toasts zijn er; bij laden flitsen 7-9 mislukte verzoeken (401) voordat de sessie geldig is |
| 2 | Aansluiting op de echte wereld | 4 | Nederlands, dossiernummers, incassostappen en juridische termen kloppen; sterkste punt van de app |
| 3 | Controle en vrijheid | 3 | Annuleren/terugdraaien bestaat op de zware routes; geen algemene ongedaan-maken na bulkacties |
| 4 | Consistentie en standaarden | 2 | 877 rauwe kleurklassen naast het tokensysteem, 15 kleurfamilies met dubbelingen, 5 hoekrondingen, 4 knophoogtes op één scherm, kale keuzelijsten naast eigen knoppen |
| 5 | Foutpreventie | 3 | Sterke poorten (14-dagenbrief, dubbele mail, blokkades vóór verzending) |
| 6 | Herkennen boven onthouden | 3 | Rode badges en gekleurde stippen zonder legenda; kolomkoppen zonder uitleg |
| 7 | Flexibiliteit en snelheid | 3 | Ctrl+K, batch-acties, filters aanwezig; geen dichtheids- of thema-keuze voor 8-uur-per-dag-gebruik |
| 8 | Esthetiek en eenvoud | 2 | Dashboard = 15 kaarten over 2,8 schermhoogtes, ragged vijfde KPI-kaart, twee lege kolommen |
| 9 | Herstellen van fouten | 3 | Foutmeldingen in gewone taal met reden en vervolgstap |
| 10 | Hulp en documentatie | 2 | Vrijwel geen inline uitleg; alleen het leer-scherm legt zichzelf uit |
| **Totaal** | | **28/40** | Degelijk werkgereedschap met een systeemprobleem in de vormtaal |

## Anti-patronen

**Eigen beoordeling:** dit ziet er niet uit als door AI uitgespuugd. Geen kleurverlopen, geen glaseffecten, geen marketing-hero. De tells die er wél zijn: de KPI-kaartenrij bovenaan het dashboard (groot getal + klein label + pastel icoontegel, vijf keer naast elkaar) is de lichte versie van het hero-metric-sjabloon, en het paars/violet in AI-schermen is precies de kleur die het productdocument als anti-referentie noemt.

**Deterministische scan:** 1 treffer, een 3px gekleurde linkerrand op agenda-items. Dat is hier een gerechtvaardigde uitzondering: een gekleurde balk links van een agenda-item is de conventie van elke agenda (Google, Outlook). Geen actie.

Wat de scanner niet ziet maar wel telt: 877 rauwe kleurklassen door de app heen, met dubbele families voor dezelfde betekenis (emerald 194x naast green 31x, slate 51x naast gray 22x, violet 59x naast purple 17x).

## Gemeten contrastfouten (echte pagina, echte kleuren)

| Element | Verhouding | Nodig |
|---|---|---|
| Amber tekst op wit (dagen-teller, waarschuwingen) | 3,19 | 4,5 |
| Groen tekst op wit ("teveel betaald", positieve bedragen) | 3,77 | 4,5 |
| Wit op rood badge (telling in zijbalk, 9+ in de bel) | 3,76 | 4,5 |
| Lichtrood op lichtroze badge | 2,13 | 4,5 |
| Grijze telling op grijze chip | 4,39 | 4,5 |

## Overall

De app is een echt werkgereedschap en dat is te zien: dichte tabellen, correcte bedragen, Nederlandse taal die klopt. Het probleem is niet dat het te simpel is, het is dat er geen vormtaal áchter zit. Elk scherm is los gebouwd met de kleuren die op dat moment goed voelden. Daardoor voelt het "gewoon" in plaats van gemaakt.

De grootste kans: één kleurensysteem met betekenis, en het dashboard terugbrengen van 15 kaarten naar wat Lisanne 's ochtends echt nodig heeft.

## Wat werkt

- **Incassolijst.** Dichte tabel, cijfers op decimaal uitgelijnd, stap-badges, filterchips bovenaan. Dit is het beste scherm van de app en het bewijst dat de dichtheid aankan.
- **Zijbalk in donker.** Tweede neutrale laag onder de content, precies zoals werkgereedschap hoort. Rust in de navigatie.
- **Taal.** Geen jargon waar het niet hoort, foutmeldingen die zeggen wat er misging en wat je nu doet.

## Prioriteit

**[P1] De zwevende Timer-knop dekt inhoud af.** Gemeten op het dashboard: de knop staat pal over de AI-suggesties-balk; in de incassolijst over een bedrag in de tabel. Hij staat er altijd, ook als er geen timer loopt, en is niet weg te klikken. In een app waar bedragen exact moeten kloppen, is een knop die er willekeurig eentje afdekt de ergste vorm van decoratie. Fix: alleen tonen als er een timer loopt, en anders in de kopbalk zetten.

**[P2] Het kleursysteem lekt.** Er zijn tokens, maar de app schildert met rauwe kleuren: 877 plekken, 15 families, drie keer twee families voor dezelfde betekenis. Gevolg zijn de vijf gemeten contrastfouten en het gevoel dat elk scherm nét iets anders is. Fix: vier statuskleuren vastleggen (goed, let-op, fout, neutraal) in dieper amber en dieper groen, en de rauwe klassen daar naartoe verhuizen.

**[P2] Alarmmoeheid.** Drie permanent rode tellingen in de zijbalk, rode bedragen, rode dagen, rode data en rode driehoekjes in dezelfde lijst. Als alles rood is, is niets urgent. Fix: rood alleen voor wat vandaag misgaat; de rest neutraal met alleen een cijfer.

**[P2] Het dashboard is een stapel kaarten.** 15 kaarten, 2,8 schermhoogtes scrollen, een vijfde KPI-kaart die alleen op een tweede rij hangt omdat het raster op vier staat, en twee lege staten (agenda, uren) die samen 260 pixels kosten om te zeggen dat er niets is. Fix: KPI-rij naar vier, lege kaarten samenvouwen tot één regel, taken en termijnen naast elkaar.

**[P3] Componentwoordenschat.** Kale keuzelijsten van de browser naast eigen knoppen in dezelfde filterbalk, vier knophoogtes op één pagina, vijf hoekrondingen door de app. Los van elkaar onzichtbaar, samen de reden dat het niet "af" oogt.

**[P3] Focus is de browserstandaard.** Toetsenbordbediening werkt, maar de focusring is wat de browser toevallig tekent, geen ontworpen staat.

## Persona's

**Lisanne (8 uur per dag, geen techneut):** opent het dashboard en moet 2,8 scherm scrollen langs kaarten die grotendeels leeg zijn voordat ze bij haar termijnen is. De zijbalk zegt 28, 51, 36, 49 in rood zonder uit te leggen waarvan. Het amber van "12d te laat" haalt op haar scherm de leesbaarheidsnorm niet.

**Power-user (snelle route):** Ctrl+K en batchacties zijn er, dat is goed. Maar er is geen dichtheidsstand en geen donker thema voor een werkdag van acht uur, en de timer moet je wegwerken in plaats van oproepen.
