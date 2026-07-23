# S241 — Testronde 3: verse brillen (parallel aan S240-afronding)

**Vooraf (discipline S239/S240):** per scenario staat het verwachte resultaat er vóór
de uitvoering. Vondsten in drie bakken: 🅰 fout (fixen, rode test eerst) · 🅱 ergernis
(fixen) · 🅲 gemis (voorstel-lijst). Elke prod-mutatie terugdraaien + natellen.
Testterrein: wegwerpdossiers + testkanaal 2026-00006. Niets naar echte debiteuren；
de 2 open mails (IN100128, IN100586) en het IN100592-verweer blijven onaangeraakt.

**Model:** Fable (testwerk — klopt met de prompt). Sessie draait parallel aan de
S240-afronding in een andere terminal: geen sessie-einde-administratie hier,
`git pull` vóór elke commit, alleen expliciete paden stagen.

---

## Bril A — de nieuwe S240-functies op hun kruispunten (geen AI-kosten)

| # | Scenario | Verwacht (vooraf opgeschreven) | Resultaat |
|---|----------|-------------------------------|-----------|
| A1 | Belofte + lopende regeling tegelijk (zaak in 'Bijhouden regeling') | Belofte-taak wordt gewoon aangemaakt (poort blokkeert alleen gesloten/betaald); er ontstaat dus dubbel bewakingswerk naast de termijn-bewaking + regeling-afgerond-taak. Vraag is of dat logisch of dubbelop is — vaststellen, dan bak kiezen. | 🅲 Live bewezen op wegwerpdossier 2026-00021: regeling aanmaken zette de zaak zelf op 'Bijhouden regeling', en de belofte-taak kwam er gewoon naast (pending, due 1-8 = zelfde datum als termijn 1). Twee bewakingen voor dezelfde betaling → voorstel-lijst (bv. belofte-taak onderdrukken of samenvoegen bij actieve regeling). Geen fout: niets gaat stuk, er is hooguit dubbel werk. |
| A2 | Belofte-datum in het verleden (oude mail gesynct) | Taak krijgt direct status 'due' (code: `promise_date > vandaag` → anders due), niet 'overdue'; de 06:00-job zet hem de volgende ochtend op 'overdue'. Geen crash op een datum in het verleden. | ✅ Live: taak direct 'due' met vervaldatum 10-7 (13 dagen terug), netjes toegewezen aan de zaakbehandelaar. Nuance (acceptabel): hij kleurt pas de eerstvolgende ochtend om 08:00 NL-tijd 'te laat' — tot die tijd staat hij als 'due' bovenaan de werklijst, dus zichtbaar is hij sowieso. |
| A3 | Belofte herkend, daarna betwisting op dezelfde zaak | Belofte-taak blijft open (sluit alleen bij volledige betaling of zaak-sluiten); de verweer-keten loopt er los naast. Verwachting: ze bijten elkaar niet hard — vaststellen en bak kiezen. | ✅ Droog met codebewijs: de verweer-keten wisselt alleen de pijplijnstap ('Verweer beantwoorden'), maakt een eigen concept + eigen taak, en raakt belofte-taken nérgens aan. Op een zijpad-stap (zoals 'Bijhouden regeling') doet de verweer-keten bewust niets. De open belofte-taak blijft inhoudelijk zinvol: óók bij een betwisting wil je op de beloofde datum weten of er betaald is. Geen beet. |
| A4 | Zaak heropend na betaling-verwijderen, belofte-taak was al afgevinkt | Heropening-vangnet zet de zaak terug open; de taak blijft 'completed' (geen her-open-logica). Acceptabel — documenteren als bewust gedrag. | ✅ Live: volledige betaling €291,42 → zaak automatisch 'betaald' + belofte-taak automatisch 'completed' (ook de handmatig-sluiten-route gaf keurig 'skipped'). Betaling verwijderd → zaak heropend (status terug, sluitdatum gewist), taak blijft 'completed'. Gedocumenteerd als bewust gedrag: bij heropening staat er geen belofte-bewaking meer; de heropende zaak zelf is het signaal. |
| A5 | Ongesorteerd-melding bij dossier-sync + storm van 3 tegelijk | Dossier-sync: mail zónder dossiernummer wordt force-gekoppeld → géén onterechte ongesorteerd-melding; mail mét onbekend dossiernummer blijft ongelinkt → melding (terecht). Storm: 3 verschillende mails in één autosync → 3 losse meldingen per gebruiker (geen bundeling — bekend voorstel 3 uit S239). Zelfde mail her-gesynct → 0 (dedup). | ✅ Alle drie bewezen met nieuwe wachters (lokaal testharnas, geen AI, geen prod): force-koppeling meldt niet; onbekend dossiernummer meldt wél (terecht — hij ís ongesorteerd); 3 mails = 3 losse meldingen (bundeling blijft bekend voorstel 3). Her-sync zelfde mail = 0 meldingen (bestaande wachter). |
| A6 | Dismissed-mail her-gesynct → geen nieuwe melding | Dedup slaat de mail over → geen nieuwe rij, geen melding. Diepere kruispunt-check: het her-koppelpad voor bestaande óngelinkte mails checkt `is_dismissed` NIET — bij een dossier-sync kan een genegeerde mail stil aan het dossier worden force-gekoppeld. Vaststellen + bak kiezen. | 🅰 **Vondst 1, GEFIXT.** Melding-deel klopt (geen nieuwe melding). Maar de diepe check was raak: een genegeerde mail werd bij een dossier-sync stil aan het dossier gekoppeld (rode test bewees het), en dat kon óók via een dossiernummer dat later pas een zaak kreeg. De mail verscheen dan op de correspondentie-tab terwijl de gebruiker hem expliciet had genegeerd. Fix: 'Negeren' wint van elke sync (zelfde regel als de re-match uit S188c); bounces (systeem-genegeerd) mogen wél blijven koppelen op dossiernummer — tegenproef bewaakt dat. |

## Bril B — twee gebruikers / rollen (droog + read-only)

| # | Scenario | Verwacht | Resultaat |
|---|----------|----------|-----------|
| B7 | kesting@ en seidony@ zien dezelfde tellers/taken | Taken en ongesorteerd-teller zijn tenant-breed (zelfde cijfers); meldingen zijn per-gebruiker rijen (aantallen kunnen verschillen door lees-status en aanmaakmoment). Read-only vergelijken via database. | ✅ Read-only gemeten. Werklijst = eigen taken + eigenaarloze taken (bewust ontwerp, zodat niemand-z'n-taken toch iemand bereiken): seidony ziet 61 (27 eigen + 34 eigenaarloos), kesting ziet 38 (4 eigen + 34 eigenaarloos) — verschil is puur toewijzing, geen fout. Mail-teller (81 ongesorteerd) en dashboard-cijfers zijn tenant-breed en dus identiek. Meldingen per gebruiker: seidony 147 ongelezen, kesting 93 (historie-verschil, per ontwerp). |
| B8 | Medewerker-rol op 3 gevoelige routes (gebruikersbeheer, instellingen, verwijderen) | Conform `docs/security/rollen.md`: medewerker krijgt 403 op gebruikersbeheer + instellingen-schrijf + verwijder-routes. Eerst droog (require_role in code), live steekproef alleen als er al een medewerker-testaccount bestaat (geen nieuwe prod-gebruiker aanmaken zonder noodzaak). | ✅ Droog: gebruikers aanmaken, kantoorgegevens, instellingen (mailslot + kantoor-instellingen) en sjabloon-verwijderen zijn allemaal admin-only in de code; een gebruiker-verwijder-route bestaat niet (alleen aanmaken + lijst). Live steekproef op de LOKALE omgeving (zelfde code, prod niet aangeraakt — prod heeft geen medewerker-account): wegwerp-medewerker kreeg 403 op alle vier de beheer-routes en 200 op dagelijks werk (zakenlijst). Wegwerp-account daarna gewist (natelling 0). Matrix klopt. |

## Bril C — de ochtend van morgen (droog, code + planning lezen)

| # | Scenario | Verwacht | Resultaat |
|---|----------|----------|-----------|
| C9 | Welke jobs draaien 's ochtends en wat doen ze met de S240-taken/meldingen | Kandidaten (code): 06:00 taak-statussen, 06:15 verjaring, 06:20 deadline-meldingen, 06:30 termijnen, 06:35 facturen, 06:40 derdengelden, 06:45 BIK, 08:00 pipeline-drafts; elke 5 min mailsync, 6 min classificatie. Cron-uren vermoedelijk UTC → Lisanne's klok +2. Verifiëren op de server + kwantificeren. | ✅ Server draait op UTC (gecontroleerd) → voor Lisanne is dat 08:00–10:00 's ochtends. Voorspelling morgenochtend, gemeten op prod: de 08:00-taak-job zet precies 1 taak van 'pending' op 'due'; de 08:20-meldingen-job maakt 0 nieuwe meldingen (0 agenda-deadlines in het venster, en alle 64 te-late taken zijn al gemeld binnen hun 30-dagen-slot — geen dagelijkse herhaal-storm, bewust zo gebouwd). De S240-functies voegen 's ochtends niets toe: ongesorteerd-meldingen komen alleen bij NIEUWE mail (5-min-sync), belofte-taken alleen bij nieuwe belofte-mails (6-min-classificatie). Geen dubbele melding-druk. Randgeval genoteerd: te-late taken zónder eigenaar gaan naar de 'eerste' gebruiker van het kantoor (willekeurige volgorde) — met 2 gebruikers onschuldig, wel slordig. |
| C10 | Wat ziet Lisanne morgenochtend (21 adviezen + 16 aanvragen + 61 taken) | Meting op prod (read-only): aantallen + hoeveel daarvan morgen kleurt. Oordeel werkbaarheid — meting, geen fix. | ⚠️ Meting (geen fix, opruimronde is van Arsalan+Lisanne): 65 open taken (64 al 'te laat', 1 wordt morgen 'due'), waarvan 39 op testdossiers en 26 op echte zaken; 21 open adviezen (14 test / 7 echt); 16 aanvragen ter beoordeling (14 al van 15-7); 93 ongelezen meldingen op haar account; 81 ongesorteerde oude mails. Oordeel: de echte werklast (26 taken + 7 adviezen + enkele aanvragen) is op zich werkbaar, maar die verdrinkt visueel in de test-restanten — de geplande opruimronde is de sleutel, niet nieuwe bouw. |

## Optioneel blok D — derde AI-antwoordronde
Bewust overgeslagen (besluit Arsalan + advies Claude, 23-7): de AI-antwoordlaag is
bij S238 vers doorgetest (46 antwoorden, 0 storingen) en de wijzigingen van
S240/S241 raken taken en mail-sortering, niet het antwoordpad. Volgende ronde hoort
bij de eerstvolgende sessie die prompts/schema's/antwoord-logica wijzigt.

## Vondsten

| # | Bron | Bak | Wat | Status |
|---|------|-----|-----|--------|
| 1 | A6 | 🅰 | Genegeerde ("Negeren") ongelinkte mail werd bij een latere sync stil aan een dossier gekoppeld — via dossier-sync (force-koppeling) én via een dossiernummer dat later een zaak kreeg. De Negeren-beslissing van de gebruiker werd zo zonder signaal overschreven; de mail dook op de correspondentie-tab van het dossier op. Re-match respecteerde Negeren al (S188c), dit inline her-koppelpad niet. | GEFIXT (rode test eerst): Negeren wint van elke sync; bounces (systeem-genegeerd) koppelen wél nog op dossiernummer (tegenproef bewaakt). 6 nieuwe wachters in `tests/test_s241_sync_kruispunten.py`; hele email/sync-suite groen (1002 tests). |
| 2 | A1 | 🅲 | Belofte-mail op een zaak met actieve regeling maakt een tweede bewakingstaak naast de termijn-bewaking (zelfde betaling, twee taken). Niet fout, wel dubbel werk. | voorstel-lijst |
| 3 | C9 | 🅲 | Te-late taken zonder eigenaar krijgen hun melding bij de 'eerste' gebruiker van het kantoor — de volgorde is willekeurig (geen sortering). Met 2 gebruikers onschuldig; bij groei kan een melding stil bij de verkeerde landen. | voorstel-lijst |

## Testsporen (bijhouden + terugdraaien)

| Wat | Waar | Status |
|-----|------|--------|
| Wegwerpdossier 2026-00021 (contact, zaak, vordering, regeling+2 termijnen, betaling, 2 belofte-taken, 5 activiteiten, 2 meldingen, stap-historie) | prod | volledig hard gewist, natelling 0 |
| Wegwerp-medewerker s241-medewerker@test.local | lokale dev-omgeving | gewist incl. tokens, natelling 0 |
| Nieuwe wachters `backend/tests/test_s241_sync_kruispunten.py` | repo | blijvend (bewust — wachters bij vondst 1 + A5-kruispunten) |
| Fix her-koppelpad | `backend/app/email/sync_service.py` | blijvend (vondst 1) |

## Eindstand

Bril A: 6/6 gedraaid — 4 ✅, 1 🅰 (vondst 1, gefixt + live gedeployd), 1 🅲 (voorstel 2).
Bril B: 2/2 gedraaid — beide ✅ (werklijst-verschil is bewust ontwerp; rollen-matrix klopt
droog én live op de lokale omgeving).
Bril C: 2/2 gedraaid — morgenochtend voegt vrijwel niets toe (1 taak kleurt, 0 nieuwe
meldingen); werklast-meting zegt: opruimronde is de sleutel, niet nieuwe bouw (voorstel 3
als klein randgeval genoteerd).
Blok D (derde AI-antwoordronde): niet gestart — wacht op expliciete GO van Arsalan.

Fix live: commit `da81429`, backend gedeployd via SSH met verse container, containers
healthy, login 200, prod-logs 0 fouten sinds deploy. Email/sync-suite lokaal 1002 groen;
ruff schoon. CI: liep nog bij schrijven — natrekken vóór sessie-einde.
Testsporen: alles teruggedraaid (natellingen 0, zie tabel); alleen de bedoelde
blijvende sporen (fix + wachters + dit logboek) staan in git.
Sessie-einde-administratie (SESSION-NOTES, roadmap, tag): bewust NIET hier gedaan —
parallel-afspraak met de S240-terminal.

## Nagekomen (zelfde sessie, GO Arsalan): meldingen-bundeling GEBOUWD + LIVE

Na de testronde gaf Arsalan GO voor het sterkste voorstel uit S239 (bundeling,
voorstel 3) — gebouwd op Opus na modelwissel. Commit `275d9f4`, backend +
frontend gedeployd.

**Wat het doet:** typen met 3+ ongelezen meldingen worden in de bel één
bundel-rij ("63 taken of deadlines te laat", teller-badge, ondertitel toont de
nieuwste). Klik → overzichtspagina van dat type (taken/mail/facturen/dashboard)
+ de hele stapel wordt in één keer gelezen gemarkeerd (nieuwe route, alleen
eigen gebruiker + eigen type — wachter bewaakt scoping). Bundels staan altijd
bovenaan (vallen nooit uit de lijst door de 15-rijen-kap). Losse en al-gelezen
meldingen onveranderd; de platte lijst (dossier-actiefeed) expliciet
ongewijzigd — wachter bewaakt dat.

**Bewijs:** 7 nieuwe wachters (33 meldingen-tests groen), tsc + ruff schoon;
live op prod: seidony's bel ging van 15 rijen ruis naar 5 bundels + losse
belangrijke rijen — de 2 verjaringswaarschuwingen ("VERJAARD! Direct actie
vereist") die eerst verdronken zijn nu direct zichtbaar. Klik-flow live
bewezen met 3 wegwerp-meldingen (email_unsorted, type had 0 echte ongelezen):
navigatie klopte, precies die 3 werden gelezen, 0 andere geraakt; wegwerp-rijen
daarna gewist (natelling 0). CI: liep nog bij schrijven.
