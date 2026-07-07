# Rapport S181-F — Heropeningsaudit (Fable, 7 juli 2026)

Laatste Fable-sessie. Doel: de heropening van de werkvoorraad volledig voorbereiden en
aftesten, zodat S181 (Opus) na Lisanne's akkoord alleen nog hoeft uit te voeren.
**Alles read-only** — geen enkele schrijfactie op productie gedaan.

## Bronnen (allemaal deze sessie zelf gelezen)

- Productie-DB via SSH (alle 607 zaken, betalingen, regelingen, stappen, regels).
- Productie-API `financial-summary` (Luxis' eigen saldo-berekening, ingelogd als seidony@).
- BaseNet-XML-export van 2 juli (lokaal, `Xml_02-07-2026_2400.zip`): 607 Incasso-records
  + statusdecodetabel (`CustomProjectStatus`) + regeling-termijnen.
- Code op commit `ec633c6` — **geverifieerd identiek aan wat op de VPS draait.**

## A. Het is veilig om te heropenen (bewezen)

1. **Niets staat op scherp.** 604 zaken afgesloten, 3 proefzaken open (`nieuw`),
   **0 zaken met pijplijnstap** → geen enkele automatische opvolging actief.
2. **Geen enkel automatisch pad verstuurt iets.** Tenant-vlag
   `pipeline_auto_drafts_enabled = false` op prod. Zelfs mét vlag maakt de batch alleen
   AI-concepten + een reviewtaak ("Bekijk en verstuur"); de opvolg-scan (elke 30 min)
   maakt alleen aanbevelingen. Versturen is altijd een menselijke klik.
3. **Data is consistent.** Alle 607 zaaknummers matchen 1-op-1 BaseNet↔Luxis (0 wezen).
   `total_paid` == som losse betalingen bij alle gecontroleerde zaken. Alle 372 lopende
   zaken hebben een rente-instelling (0 zonder).
4. **Regeling-bewaking werkt onafhankelijk van zaakstatus.** De dagelijkse job (06:30)
   markeert vervallen termijnen ook op afgesloten zaken. Termijnkalender juli:
   IN100019 → 9 juli (!), IN100215 → 12 juli, IN100454 → 13 juli, IN100535 → 15 juli,
   IN100494/IN100505/IN100543 → 18 juli, IN100329 → 19 juli.

## B. De werkvoorraad (recept-tabel: `S181-werkvoorraad-recept.csv`)

**372 zaken "Lopend" in BaseNet, €1.889.750 hoofdsom.** Voorgestelde Luxis-stap per zaak
in de CSV (kolommen: opdrachtgever, BaseNet-fase, hoofdsom, betaald, rente, voorstel-stap,
vlaggen). Verdeling:

| Voorgestelde stap | Zaken |
|---|---|
| Voorstel dagvaarding (4e sommatie gehad / "Procederen?") | 145 |
| Verweer beantwoorden (betwist) | 86 |
| 14-dagenbrief (B2C, nog niet gehad) | 34 |
| Derde sommatie | 24 |
| Eerste sommatie | 17 |
| Tweede sommatie | 12 |
| Bijhouden regeling (actieve regeling) | 12 |
| Treffen van regeling | 11 |
| BEOORDELEN: regeling gestopt/afgelopen | 11 |
| Sommatie laatste mogelijkheid | 8 |
| NIET HEROPENEN (8 voldaan + D-Break) | 9 |
| AFRONDEN: factureren + sluiten | 2 |
| UITZOEKEN (IN100409, leeg dossier) | 1 |

Per opdrachtgever: Incassocenter 156, INC Zakelijk 90, Collect 1 85, LegalWork 15,
SYN Finance 14, CM Zakelijk 9, Verfijnd Bouw 2, D-Break 1 (blijft dicht).

**Tweede schil (niet in de 372): 69 zaken "Wacht"** — Voorstel dagvaarden 37, Akkoord
dagvaarden 11, Stukken opgevraagd 10, Aanhouden 9, Dagvaarding naar DW 1 (= IN100019,
met actieve regeling!), "Arno gestuurd" 1.

**Advies eerste groep: LegalWork B.V.** — 15 zaken, waarvan 9 direct een Eerste sommatie
kunnen krijgen (systeem bewijst zich meteen), 3 Voorstel dagvaarding, 2 verweer, 1 voldaan.
Alternatief klein: CM Zakelijk (9, maar vooral verweer/dagvaarding = handwerk).

## C. Bevindingen die aandacht vragen (vóór of bij heropening)

### C1. Rente op creditfacturen is fout (32 werkvoorraad-zaken, −€2.781)
45 zaken hebben creditfacturen als **negatieve vordering**; de rente-motor rekent daar
negatieve rente over (en "kapitaliseert" die zelfs). Juridisch loopt er geen rente over
een creditfactuur. Over de 32 getroffen werkvoorraad-zaken is de som −€2.780,90 —
de fout valt in het **voordeel van de debiteur** (nooit te veel geëist), maar
sommatiebedragen zijn te laag. Ergste gevallen: IN100015 (−763), IN100334 (−404),
IN100070 (−236), IN100596 (−214). **Fix-voorstel (niet gebouwd):** claims met negatieve
hoofdsom uitsluiten van renteberekening (`interest.py`) + test; alternatief is verrekening
per creditdatum (juridisch mooier, complexer). Keuze aan Lisanne/Arsalan.

### C2. De "8 feitelijk voldaan" verdienen nuance (Luxis-berekening t/m 7 juli)
| Zaak | Luxis zegt nog open | Advies |
|---|---|---|
| IN100547 | €0,00 | afsluiten |
| IN100210 | €1,03 | afsluiten (afronding) |
| IN100456 | €8,31 | afsluiten (bagatel) |
| IN100457 | €100,47 | keuze: innen of kwijtschelden |
| IN100256 | €288,32 | keuze |
| IN100197 | €456,36 | keuze |
| IN100166 | €587,86 | keuze |
| IN100334 | −€216,84 (vervuild door C1; na fix ≈ €187 open) | eerst C1 uitzoeken |

Oorzaak restanten: art. 6:44 BW rekent betalingen eerst toe aan kosten en rente;
"betaald ≥ hoofdsom" (S180-maatstaf) is dus niet hetzelfde als "niets meer verschuldigd".

### C3. Dubbele doorloop-regel op "Tweede sommatie" (latent, fix vóór vlag aan)
Twee actieve default-timeout-regels vanaf de actieve stap Tweede sommatie: → Derde
sommatie (4 dgn) én → **oude inactieve** stap Ingebrekestelling (14 dgn). De code pakt
"de eerste" (geen ORDER BY → toeval). Pakt hij de oude, dan faalt draft-generatie
dagelijks (stap heeft geen sjabloon). Nu onschadelijk (vlag uit), maar **opruimen vóór
de vlag aangaat**: de 4 regels die van/naar inactieve stappen (sort ≥100) wijzen
deactiveren. Data-fix, 1 UPDATE — voorstel, niet uitgevoerd.

### C4. Opvolg-scanner negeert wacht-stappen
`create_followup_recommendations` slaat `is_hold_step`-stappen niet over → elke zaak op
"Bijhouden regeling"/"On hold"/"Verweer beantwoorden" krijgt direct een
"handmatige beoordeling nodig"-aanbeveling (min_wait 0). Bij heropening van ~100+ zaken
op die stappen = evenveel ruis-aanbevelingen op dag 1. Kleine code-fix (skip hold-steps)
of accepteren als werkvoorraadlijst. **Verweer beantwoorden heeft wél een sjabloon**
→ die krijgen "document genereren"-aanbevelingen; dat is misschien juist gewenst.

### C5. 14-dagenbrief-stap heeft geen sjabloon
Geen e-mail- én geen documentsjabloon op de actieve stap. 34 B2C-zaken starten daar
(wettelijk verplicht vóór BIK). Sjabloon instellen vóór die groep opengaat, anders kan
er geen concept gegenereerd worden (ESCALATE-aanbeveling is het enige dat verschijnt).

### C6. Verweer-vinkje staat overal uit
Alle 88 betwiste zaken hebben `has_verweer = false` (import zette het niet). Bij
heropening van betwiste zaken: vinkje zetten (of accepteren dat alleen de stap het toont).

### C7. Regelingen: 3 aandachtspunten
- **IN100019** (regeling, termijn 9 juli) staat in BaseNet op **Wacht** → valt buiten
  "heropen wat Lopend is". Meenemen met de regeling-groep.
- **11 zaken** "Bijhouden regelingen" zonder actieve Luxis-regeling: regelingen gestopt/
  afgelopen (laatste termijnen 2025 – april 2026): IN100189, IN100229, IN100296, IN100313,
  IN100350, IN100408, IN100438, IN100469, IN100490, IN100500, IN100553 → per zaak
  beoordelen: nieuwe regeling of sommatiepad.
- 5 actieve regelingen hangen aan zaken in een ándere BaseNet-fase (IN100019, IN100305,
  IN100329, IN100535, IN100543) → regeling wint: stap "Bijhouden regeling".

### C8. Gedrag dat wél vanzelf gebeurt na heropening (geen verzending, wel actie)
Een binnenkomende e-mail die als verweer wordt geclassificeerd, verplaatst een zaak op
het hoofdpad automatisch naar "Verweer beantwoorden" en zet een concept + reviewtaak
klaar (sessie-134-gedrag, by design). Er gaat niets uit, maar de stap wijzigt zonder
menselijke klik — goed om te weten bij de eerste weken live.

### C9. IN100409 — leeg dossier
Fase "Vordering betwist", 0 vorderingen, hoofdsom €0, opdrachtgever INC Zakelijk.
Uitzoeken (bij BaseNet/Lisanne) vóór heropening.

## D. Wat bewust NIET is gedaan

Geen fixes gebouwd, geen data gewijzigd, niets verstuurd, geen zaak heropend
(scope: onderzoek; alle fixes hierboven zijn voorstellen). De 3 proefzaken zijn
ongemoeid gelaten.
