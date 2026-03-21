# UX-22 Frontend Design Audit — Luxis

**Datum:** 21 maart 2026
**Auditor:** Claude (Frontend Design Skill als lens)
**Doel:** Inventarisatie verbeterpunten per pagina, gesorteerd op impact. NIET fixen — alleen documenteren.

---

## Samenvatting

Luxis is functioneel sterk — alle features werken, de flow is logisch, en de data-density is goed. Maar visueel mist het de **productlook** die nodig is om het op ProductHunt of een demo te presenteren. De belangrijkste patronen:

1. **Geen visuele identiteit** — geen eigen font, geen kleurpersoonlijkheid, alles voelt als "standaard shadcn/ui"
2. **Inconsistente spacing en compositie** — sommige pagina's voelen krap, andere te leeg
3. **Geen microinteracties of polish** — geen hover-effecten, geen smooth transitions, geen "delight"
4. **Typografie is generiek** — system fonts overal, geen hiërarchie-verschil tussen pagina's
5. **Kleurgebruik is functioneel maar saai** — blauw als enige accent, geen warmte of karakter

**Overall Design Score: 5.5/10** — Functioneel prima, visueel onder het niveau van een premium SaaS product.

---

## Per Pagina — Verbeterpunten

### 1. Login Pagina (audit-01)
**Score: 6/10**

| Prioriteit | Issue | Toelichting |
|-----------|-------|-------------|
| HIGH | Geen branding/persoonlijkheid | Generieke login, geen achtergrond, geen illustratie, geen kleur. Vergelijk met Clio of HubSpot login. |
| HIGH | Logo is standaard/klein | Het weegschaal-icoon in blauw vierkantje is te klein en zegt niets over het merk. |
| MEDIUM | Geen "welkom" gevoel | Geen tagline, geen visueel element dat de gebruiker verwelkomt. |
| MEDIUM | Footer tekst te klein/zwak | "Luxis v0.1.0" voelt als dev-versie, niet als product. Versienummer weghalen voor productie. |
| LOW | Wachtwoord vergeten link styling | Staat inline bij het label, wat ongebruikelijk is. Beter onder het formulier. |

**Wat goed is:** Clean, werkt, niet overweldigend.

---

### 2. Dashboard (audit-02)
**Score: 6/10**

| Prioriteit | Issue | Toelichting |
|-----------|-------|-------------|
| HIGH | KPI-kaarten missen visueel gewicht | De 5 kaarten bovenin (Actieve dossiers, Relaties, Openstaand, Vandaag gewerkt, Open facturen) zijn functioneel maar visueel vlak. Geen gradient, geen schaduw, geen icoon-kleur die opvalt. |
| HIGH | Pipeline sectie te simpel | Alleen een blauwe balk met "Nieuw 12" — geen breakdown per stap, geen visuele kanban-feel. |
| HIGH | Taken sectie mist prioriteitsgevoel | Verlopen taken hebben een klein driehoekje, maar de rode urgentie valt niet genoeg op. |
| MEDIUM | Uren deze week & Recente facturen secties | Goed qua data, maar de twee-kolom layout onderaan voelt gedrongen op smallere schermen. |
| MEDIUM | "Actie nodig" sectie te minimaal | Slechts één link "Nieuw 12 dossiers" — kan rijker. |
| MEDIUM | Recente activiteit lijst is monotoon | Alleen "Zaak aangemaakt" entries, allemaal hetzelfde icoon. Visueel onderscheid per type activiteit zou helpen. |
| LOW | Welkomstbericht mist warmte | "Goedenavond, Lisanne" is goed, maar de datum eronder is klein/grijs. |

**Wat goed is:** Data-dense, alle relevante info op één scherm, goede KPI keuze.

---

### 3. Sidebar (audit-03)
**Score: 7/10**

| Prioriteit | Issue | Toelichting |
|-----------|-------|-------------|
| HIGH | Geen visueel onderscheid secties | Alle items staan in één lijst. Groepering (bijv. "Dossiers" groep vs "Financieel" groep vs "Systeem") zou helpen. |
| MEDIUM | Badge styling inconsistent | Sommige badges (Incasso 9, Correspondentie 24) zijn rode cirkels, Mijn Taken 2 ook. Geen visueel verschil in urgentie. |
| MEDIUM | Sidebar header/logo klein | "Luxis" met klein icoon — meer ruimte/groter logo zou professioneler ogen. |
| LOW | Geen collapse-animatie | Sidebar opent/sluit zonder smooth transition. |

**Wat goed is:** Donkere sidebar, duidelijke iconen, actieve staat is zichtbaar.

---

### 4. Mijn Taken (audit-04)
**Score: 7/10**

| Prioriteit | Issue | Toelichting |
|-----------|-------|-------------|
| MEDIUM | Sectiescheiding te subtiel | "TE LAAT", "VANDAAG", "LATER" headers zijn klein. Meer visueel gewicht (kleur, bolder font) zou de urgentie versterken. |
| MEDIUM | Taakkaarten te uniform | Alle taken zien er hetzelfde uit. Het type taak (Handmatige beoordeling vs Document genereren) verdient meer visueel onderscheid. |
| LOW | "Overslaan" knop is verborgen | Pas zichtbaar bij hover — goed voor clean look, maar discoverability kan beter. |

**Wat goed is:** Goede groepering op urgentie, "Te laat" badge is duidelijk rood, filter buttons zijn clean.

---

### 5. Relaties Lijst (audit-05)
**Score: 5.5/10**

| Prioriteit | Issue | Toelichting |
|-----------|-------|-------------|
| HIGH | Veel lege kolommen | CONTACT en PLAATS zijn bij 7 van 9 relaties leeg ("-"). Dit voelt als een lege tabel. |
| HIGH | Geen visueel verschil bedrijf/persoon | Alle relaties hebben hetzelfde blauwe gebouw-icoon. Personen zouden een ander icoon moeten hebben. |
| MEDIUM | Aangemaakt kolom is niet informatief | Alle relaties tonen "21-03-2026" — dezelfde datum. Dit voegt weinig toe; "Laatst actief" zou nuttiger zijn. |
| MEDIUM | Geen avatar/logo per relatie | Initialen-avatar of bedrijfslogo zou de lijst visueel aantrekkelijker maken. |
| LOW | "laak" en "paak" als relatienamen | Dit is testdata die er onprofessioneel uitziet — maar dat is content, geen design. |

**Wat goed is:** Clean tabelopbouw, filter buttons, zoekfunctie.

---

### 6. Dossiers Lijst (audit-06)
**Score: 6/10**

| Prioriteit | Issue | Toelichting |
|-----------|-------|-------------|
| HIGH | Tabel wordt afgesneden rechts | De HOOFDSOM kolom is niet volledig zichtbaar — er is geen horizontale scroll indicator. |
| HIGH | Status badges zijn te klein/subtiel | "nieuw" in klein blauw is nauwelijks zichtbaar. Statussen verdienen meer prominentie. |
| MEDIUM | Geen kleurcodering per type | "Incasso" en "Advies" hebben verschillende kleuren (blauw/groen) maar het verschil is subtiel. |
| MEDIUM | Beschrijving wordt afgekapt | "Waarneming zitting rb Groni..." — truncation is noodzakelijk maar er is geen tooltip of expand. |
| MEDIUM | Checkboxes links suggereren bulk-acties | Maar er is geen duidelijke "Geselecteerd: X — Actie" balk. |
| LOW | Export CSV knop is klein/onopvallend | Staat rechts boven de tabel, makkelijk over het hoofd te zien. |

**Wat goed is:** Goede filter-opties (type, status, meer filters), export functie, zoekbalk.

---

### 7. Dossier Detail — Overzicht (audit-07)
**Score: 6.5/10**

| Prioriteit | Issue | Toelichting |
|-----------|-------|-------------|
| HIGH | Te veel verticale ruimte boven de tabs | De pipeline-stappen + KPI-kaarten + actieknoppen nemen veel ruimte in voordat je bij de tabs komt. De tabs zouden sticky moeten zijn. |
| HIGH | Quick actions bar is visueel druk | 7 knoppen (Uren loggen, Notitie, Telefoonnotitie, Document, Factuur, E-mail, Renteoverzicht) op één rij — overweldigend. |
| MEDIUM | Pipeline stappen zijn niet klikbaar | De 1-2-3-4-5 stappen zijn informatief maar niet interactief. Klikken op een stap zou de status moeten wijzigen. |
| MEDIUM | Procesgegevens sectie is leeg maar neemt veel ruimte in | Alle velden zijn "-" — dit voelt als een leeg scherm. Sectie collapsen als leeg? |
| MEDIUM | Debiteurinstellingen sectie | Staat helemaal onderaan, maar is belangrijk. Locatie overdenken. |
| LOW | Notitie editor is basaal | Alleen B/I/list — geen @mentions, geen links, geen afbeeldingen. |
| LOW | Recente activiteit has truncated text | Sommige activiteiten zijn moeilijk leesbaar door afkapping. |

**Wat goed is:** Goede informatie-architectuur, pipeline visueel, KPI cards bovenin, breadcrumbs.

---

### 8. Incasso Pipeline (audit-08)
**Score: 7/10**

| Prioriteit | Issue | Toelichting |
|-----------|-------|-------------|
| HIGH | "Zonder stap" sectie is te prominent | 8 dossiers zonder stap nemen het meeste ruimte in — dit zou visueel als warning/actie-items gestyled moeten worden (meer oranje/geel). |
| MEDIUM | Lege secties nemen ruimte in | "Aanmaning 0", "2e Sommatie 0", "Executie 0", "Dagvaarding 0" — 4 lege secties die de pagina verlengen. Collapse lege secties. |
| MEDIUM | Geldbedragen in rood vs zwart | Openstaande bedragen zijn rood, maar de kleur is vrij subtiel op grotere bedragen. |
| LOW | Filter tabs bovenaan | "Alle dossiers", "Klaar voor volgende stap", "14d verlopen", "Actie vereist" — goed, maar de badges (10, 1, 9) zijn klein. |

**Wat goed is:** Structuur per pipeline-stap is uitstekend, batch acties met selecteer-alles, deadline kleuren (dagen in rood).

---

### 9. Facturen Lijst (audit-09)
**Score: 5.5/10**

| Prioriteit | Issue | Toelichting |
|-----------|-------|-------------|
| HIGH | Tabel kolommen zijn slecht gebalanceerd | FACTUUR, STATUS, RELATIE, DOSSIER, DATUM, VERVALDATUM, TOTAAL — te veel kolommen voor de breedte, bedragen worden afgesneden. |
| HIGH | Factuur/Debiteuren tabs onderbenut | Het tabblad "Debiteuren" is interessant maar er is geen visuele indicator hoeveel debiteuren er zijn. |
| MEDIUM | Status badges inconsistent | "Concept" is grijs, "Deels betaald" is paars, "CN" is klein grijs — geen duidelijk kleurensysteem. |
| MEDIUM | Creditnota (CN2026-00001) styling | Het "CN" label is te klein en onduidelijk. Creditnota's verdienen meer visueel onderscheid. |
| LOW | Geen chart/summary boven de tabel | Een totaal-overzicht (totaal open, totaal betaald) zou context geven. |

**Wat goed is:** Zoekbalk, statusfilter, tabbladen.

---

### 10. Uren (audit-10)
**Score: 6.5/10**

| Prioriteit | Issue | Toelichting |
|-----------|-------|-------------|
| HIGH | Layout voelt rommelig | Stopwatch, totalen, dag/week/maand filter, dossier/relatie filters, weekoverzicht — alles staat op elkaar. Geen duidelijke visuele hiërarchie. |
| HIGH | Weekdagen met 0:00 zijn visueel dood | Ma/Di/Do tonen "0:00" in grijs — dat is 60% van de week die leeg voelt. Lege dagen subtiel stylen. |
| MEDIUM | "48:36" als uren-registratie valt op | Maar de omschrijving is "—" en de activiteit "Overig" — dit voegt weinig context toe. |
| MEDIUM | Stopwatch ontwerp is basic | Een grote timer met een groene Start knop — functioneel, maar niet inspirerend. Harvest/Toggl doen dit eleganter. |
| MEDIUM | Filters op dezelfde hoogte als datumnavigatie | "16 mrt — 20 mrt 2026" staat naast de dossier/relatie filters — voelt krap. |
| LOW | "Overzicht per dossier" onderaan | Goede feature maar visueel niet prominent genoeg. |

**Wat goed is:** Week-view met dag-breakdown, declarabel indicator, koppeling met dossiers.

---

### 11. Bank Import (audit-11)
**Score: 5/10**

| Prioriteit | Issue | Toelichting |
|-----------|-------|-------------|
| HIGH | Empty state is te minimaal | "Geen matches" met een klein icoon en twee regels tekst. Vergelijk met Stripe's lege states — die zijn visueel aantrekkelijk en instructief. |
| MEDIUM | Tab "Importgeschiedenis" | Goed dat het er is, maar geen visuele indicator of er imports zijn. |
| MEDIUM | Status filters (Openstaand/Goedgekeurd/Uitgevoerd/Afgewezen/Alle) | Goed concept maar de styling is te subtiel — geen counts per status. |
| LOW | Beschrijving is lang maar nuttig | "Bankafschriften importeren en betalingen automatisch matchen aan dossiers" — kan korter. |

**Wat goed is:** Duidelijke CTA "CSV uploaden", logische workflow tabs.

---

### 12. Correspondentie (audit-12)
**Score: 6/10**

| Prioriteit | Issue | Toelichting |
|-----------|-------|-------------|
| HIGH | Emails zien er rommelig uit | Lange onderwerpen, technische tekst (AbuseID, Hetzner meldingen, delivery failures) — dit is productiemail die er niet uitnodigend uitziet. |
| HIGH | Geen visueel onderscheid in/uit | Alle emails hebben hetzelfde rode pijl-icoon. Inkomend vs uitgaand zou visueel anders moeten zijn. |
| MEDIUM | Preview tekst is te lang/technisch | Body preview toont volledige technische tekst. Beter: max 1 regel, HTML gestript. |
| MEDIUM | "24 ongesorteerde e-mails" als header | Het woord "ongesorteerde" voelt als een probleem, niet als een status. |
| LOW | Geen groepering op datum | Emails van dezelfde dag staan los. "Vandaag", "Gisteren", "Deze week" groepering zou helpen. |

**Wat goed is:** "Sync inbox" knop, selecteer-alles voor bulk, zoekbalk.

---

### 13. Agenda (audit-13)
**Score: 6/10**

| Prioriteit | Issue | Toelichting |
|-----------|-------|-------------|
| HIGH | Maandkalender is basic | Standaard grid zonder visuele diepte. Vergelijk met Google Calendar — kleurcodering per type, drag-and-drop. |
| MEDIUM | Events worden afgekapt | "Ingebrekestel...", "Handmatige ..." — onleesbaar. Tooltip on hover met volledige tekst zou helpen. |
| MEDIUM | Kleurcodering events is onduidelijk | Rode dot, blauwe dot, gele dot — maar geen legenda. |
| LOW | Week-view ontbreekt | Er is een "Week" knop maar geen screenshot hiervan — moet getest worden. |

**Wat goed is:** Clean kalender layout, "Nieuw event" CTA, maand/week toggle.

---

### 14. Documenten / Sjablonen (audit-14)
**Score: 7/10**

| Prioriteit | Issue | Toelichting |
|-----------|-------|-------------|
| MEDIUM | Kaartjes zijn erg uniform | Alle 7 templates zien er identiek uit — zelfde icoon, zelfde "BESCHIKBAAR" badge, zelfde layout. Een klein preview of type-icoon per template zou helpen. |
| MEDIUM | 2-kolom grid op smalle schermen | De kaartjes zijn breed genoeg, maar op een smaller scherm wordt het 1-kolom en dan is de pagina erg lang. |
| LOW | "HTML Sjablonen" tab is leeg maar zichtbaar | Als er geen HTML templates zijn, hide de tab of toon een melding. |
| LOW | Info banner bovenaan neemt veel ruimte in | De blauwe info-box "Documenten worden gegenereerd vanuit een dossier" is nuttig maar prominent. |

**Wat goed is:** Kaart-layout is visueel aantrekkelijker dan een tabel, beschrijvingen zijn duidelijk.

---

### 15. Instellingen (audit-15)
**Score: 5/10**

| Prioriteit | Issue | Toelichting |
|-----------|-------|-------------|
| HIGH | Navigatie is een verticale lijst zonder groepering | 9 items (Profiel, Kantoor, Modules, Team, Workflow, E-mail, Meldingen, Sjablonen, Weergave) in één lijst zonder secties. |
| HIGH | Profielpagina is leeg en breed | Twee velden (naam + e-mail + uurtarief) nemen de hele breedte — veel lege ruimte. |
| MEDIUM | Actieve tab is blauw highlighted | Maar het contrast is laag — de hele rij is lichtblauw, wat subtiel is. |
| MEDIUM | "Wachtwoord wijzigen" als losse sectie | Staat in een aparte kaart onderaan met veel witruimte ertussen. |
| LOW | Geen avatar/profielfoto upload | Standaard placeholder icoon — een avatar zou persoonlijker voelen. |

**Wat goed is:** Logische tabstructuur, alle instellingen bereikbaar.

---

### 16. Nieuw Dossier Wizard (audit-16)
**Score: 7/10**

| Prioriteit | Issue | Toelichting |
|-----------|-------|-------------|
| MEDIUM | Step indicator is goed maar subtiel | 1-2-3 stappen bovenin zijn zichtbaar, maar de voortgang (welke stap actief is) zou meer visueel gewicht mogen hebben. |
| MEDIUM | AI upload banner is visueel sterk | De blauwe "Upload een factuur" banner is goed — dit is een USP die meer opvalt dan de rest van het formulier. |
| LOW | Formulier is breed | Velden nemen de hele breedte — op een breed scherm is er veel lege ruimte links/rechts. Max-width zou helpen. |

**Wat goed is:** Wizard-flow is logisch, AI upload is prominent, velden zijn duidelijk.

---

### 17. Dossier — Vorderingen Tab (audit-17)
**Score: 6.5/10**

| Prioriteit | Issue | Toelichting |
|-----------|-------|-------------|
| MEDIUM | KPI kaarten (Totale vordering, Betaald, Openstaand) | Goed concept, maar alle drie tonen "€ 0,00" — empty state zou anders gestyled moeten. |
| MEDIUM | Betalingsvoortgang balk | Bij 0% is het een lege grijze balk — weinig informatief. Bij > 0% wordt het nuttiger. |
| MEDIUM | Specificatietabel is goed maar alle nullen | Wanneer alles €0,00 is, voelt de tabel leeg — een "Nog geen vorderingen, voeg een vordering toe" state zou beter zijn. |
| LOW | Facturatie-instellingen onderaan | Provisie/Vaste dossierkosten/Minimumkosten zijn alle "—" — dezelfde empty state probleem. |

**Wat goed is:** Uitstekende informatiearchitectuur, WIK-staffel berekening, specificatietabel.

---

### 18. Dossier — Correspondentie Tab (audit-18)
**Score: 6/10**

| Prioriteit | Issue | Toelichting |
|-----------|-------|-------------|
| HIGH | Sticky header + tabs werken niet goed | De top header (pipeline, KPI's, actions) scrollt mee waardoor de tabs niet altijd zichtbaar zijn. |
| MEDIUM | Email preview is erg lang | Technische bounce-meldingen nemen evenveel ruimte als echte correspondentie — visueel onderscheid per type. |
| MEDIUM | "Sync inbox" en "Nieuwe e-mail" knoppen | Goed geplaatst, maar bij veel emails gaat de focus naar de lijst en zijn de knoppen ver weg. |

**Wat goed is:** In/Uit/Alles filter, bijlage-indicator, datums.

---

### 19. Relatie Detail (audit-19)
**Score: 5.5/10**

| Prioriteit | Issue | Toelichting |
|-----------|-------|-------------|
| HIGH | Veel lege secties | "Facturatie: Geen facturatiegegevens ingesteld", "Notities: Geen notities", "Contactpersonen: Nog geen" — de pagina is 60% empty states. |
| HIGH | Gekoppelde dossiers lijst is goed maar basaal | Geen status-kleurcodering, geen bedrag-formatting (€ 10.000,00 vs € 0,00 verschil is niet visueel). |
| MEDIUM | Header mist context | Alleen naam + type + aanmaakdatum. Geen totaal openstaand, geen aantal dossiers als KPI. |
| LOW | "Bewerken" en verwijder-knop rechts bovenin | Goed geplaatst maar het verwijder-icoon (rood prullenbak) is vrij prominent naast "Bewerken". |

**Wat goed is:** Alle relevante informatie op één pagina, gekoppelde dossiers met bedragen.

---

### 20. Factuur Detail (audit-20)
**Score: 7.5/10**

| Prioriteit | Issue | Toelichting |
|-----------|-------|-------------|
| MEDIUM | Status-acties bovenaan (Goedkeuren/Annuleren) | Goed dat ze er zijn, maar de groene "Goedkeuren" knop is erg prominent voor een concept-factuur. |
| LOW | Factuurregels tabel is clean | Goed ontworpen met subtotaal/BTW/totaal onderaan. |
| LOW | PDF en Bewerken knoppen rechts | Goed geplaatst, logische flow. |

**Wat goed is:** Beste pagina qua design — schone layout, duidelijke KPI cards, goede acties.

---

## Top 10 Verbeterpunten (Impact-gesorteerd)

| # | Issue | Pagina's | Impact | Effort |
|---|-------|----------|--------|--------|
| 1 | **Visuele identiteit: eigen font + kleurenpalet** | ALLE | Zeer hoog | Medium |
| 2 | **Login pagina redesign: achtergrond, branding, warmte** | Login | Hoog | Laag |
| 3 | **Empty states verbeteren: illustraties, instructieve tekst** | Relaties, Bank Import, Vorderingen | Hoog | Medium |
| 4 | **Sticky tabs op dossier-detail** | Dossier detail | Hoog | Laag |
| 5 | **Tabel responsiveness: kolommen niet afsnijden** | Dossiers, Facturen | Hoog | Medium |
| 6 | **Dashboard KPI-kaarten upgraden: gradients, icoon-kleuren** | Dashboard | Hoog | Laag |
| 7 | **Sidebar sectiescheiding** | Sidebar | Medium | Laag |
| 8 | **Microinteracties: hover effects, smooth transitions** | ALLE | Medium | Medium |
| 9 | **Incasso pipeline: collapse lege secties, warning-styling** | Incasso | Medium | Laag |
| 10 | **Correspondentie: in/uit visueel, date grouping** | Correspondentie | Medium | Medium |

---

## Conclusie

Luxis is **functioneel uitstekend** — de features zijn compleet, de workflows zijn logisch, en de data is goed georganiseerd. Het mist echter de **visuele polish** die het verschil maakt tussen "intern tool" en "premium SaaS product".

De grootste winst zit in:
1. Een **coherent design system** (font, kleuren, spacing, shadows)
2. **Empty state design** (veel pagina's voelen leeg bij weinig data)
3. **Microinteracties en transitions** (hover, click, page transitions)
4. **Responsiveness** (tabellen die worden afgesneden, layouts die breken)

Met deze verbeteringen kan Luxis gemakkelijk van 5.5/10 naar 8/10 design score gaan.
