# PLAN — Wet- en regelgeving-proof vóór livegang (+ bankaansluiting)

**Rang: loopt parallel aan alles — de papieren acties (A) kunnen nu, de brieven-audit (B)
moet af vóór de eerste sommatie de deur uit gaat.**
Onderzoek uitgevoerd 7 juli 2026 (Fable, S181-F) met bronnen van de NOvA, de wetgever en
de eigen code/prod. Dit plan is de compliance-tegenhanger van de technische plannen.

## Samenvatting: waar staan we

Veel zit al goed (zie §6). De echte gaten zijn: **papierwerk dat nog niet bestaat**
(verwerkersovereenkomsten, verwerkingsregister, bewaarbeleid), **één inhoudelijke
brieven-audit** tegen de nieuwe incassowet, en **twee menselijke besluiten** rond de
stichting derdengelden. Er is géén blokkerende technische verbouwing nodig.

---

## §1. De incassowet (Wki/Bki) — geldt inhoudelijk WÉL voor advocaten

Vastgesteld (bron: NOvA-achtergrondartikel + Besluit kwaliteit incassodienstverlening,
in werking 1 april 2024): advocaten hoeven zich **niet te registreren** in het
incassoregister, maar de **materiële kwaliteitseisen gelden volledig** zodra zij
buitengerechtelijke incassowerkzaamheden verrichten — precies wat Kesting voor de
opdrachtgevers doet. Toezicht: de deken.

**Wat het Bki concreet eist in de schriftelijke specificatie aan de debiteur:**
- naam + adres van debiteur, incassodienstverlener én schuldeiser;
- de overeenkomst/grondslag van de vordering;
- betaaltermijn en verlengde termijn;
- rente-specificatie: bedrag, percentages, periodes én grondslag (wettelijk/contractueel);
- totaalspecificatie: hoofdsom, rente, incassokosten, btw (indien van toepassing) met tarief;
- benadering "transparant, ondubbelzinnig, herkenbaar en correct".

**Actie B — brieven-audit (Claude-sessie, ~half dagdeel, vóór de eerste verzending):**
1. Leg elk actief e-mailsjabloon (Eerste t/m laatste sommatie, straks ook 14-dagenbrief)
   naast de bovenstaande checklist. De data bestaat al in Luxis (bedragen-tabel +
   rente-details per periode via de financiële samenvatting) — de vraag is alleen of de
   sjablonen álle verplichte elementen tonen. Let vooral op: rente-grondslag
   (wettelijk vs contractueel 2%/mnd) en de opdrachtgever-naam+adres (schuldeiser).
2. Gaten → sjabloonteksten aanvullen (via Instellingen → Workflow, geen deploy).
3. Vraag aan Lisanne/deken meenemen: moet er een klachtmogelijkheid-vermelding in de
   brieven? (Advocaten vallen onder het eigen klacht- en tuchtrecht; de kantoor-
   klachtenregeling bestaat al — alleen de vermelding in incassobrieven is een keuze.)

**Al gedekt:** deugdelijke administratie (volledige audit trail, betalingshistorie,
stap-historie), correcte kostenberekening (WIK-staffel met wettelijke grenzen, getest),
14-dagenbrief-flow (eigen plan).

## §2. Derdengelden (Voda art. 6.22) — systeem klaar, besluiten open

Vastgesteld (bron: NOvA/Voda + tuchtrechtspraak): de stichting derdengelden wordt
vertegenwoordigd door **twee gezamenlijk handelende bestuurders** (min. één advocaat);
voor betalingen geldt een **tweehandtekeningenvereiste dat uit de administratie moet
blijken** — hierop wordt daadwerkelijk tuchtrechtelijk gehandhaafd.

**Luxis is hierop gebouwd** (geverifieerd in de code): uitbetalingen en verrekeningen
vereisen twee goedkeuringen (vier-ogen), stortingen niet; zodra de tenant ≥2 actieve
gebruikers heeft is strikt vier-ogen afgedwongen (dat is nu al zo); alles met audit trail.

**Acties (mens):**
1. Lisanne: wie is de tweede stichtingsbestuurder? → die krijgt een eigen Luxis-account
   als tweede goedkeurder (de 3 vragen staan al in ARSALAN-TODO §4 en het Word-bestand).
2. Check bij de **bank** dat het mandaat op de stichtingsrekening ook echt twee
   handtekeningen vereist voor uitbetalingen — dat regelt Luxis niet, dat is een
   bankinstelling.
3. Verrekenclausule-vraag (mag Kesting verrekenen met openstaande facturen) — bepaalt of
   de "verrekening"-transactiesoort gebruikt mag worden.
4. Geen echte uitbetalingen vóór 1-3 rond zijn. (De generale repetitie kan wél — met een
   symbolisch klein bedrag of op papier tot de tweede goedkeurder bestaat.)

## §3. Bankaansluiting — geen koppeling nodig, wel één bevestiging

Vastgesteld in de code: Luxis leest bankafschriften via **handmatige CSV-upload**; de
parser ondersteunt precies één formaat: **Rabobank zakelijk (26 kolommen)**, en boekt
bewust alleen bijschrijvingen (het is een derdengeldrekening). Er is dus **geen
technische bankkoppeling (PSD2 e.d.) nodig voor livegang** — het werkritme is: bij de
bank inloggen → CSV-export downloaden → in Luxis uploaden → voorgestelde matches
goedkeuren.

**Acties:**
1. Arsalan/Lisanne: bevestig bij welke bank de stichting-derdengeldenrekening loopt.
   **Rabobank zakelijk → niets te doen.** Andere bank → klein bouwklusje: tweede
   CSV-parser (zelfde patroon als de Rabobank-parser, ~1 sessie incl. tests).
2. Werkafspraak vastleggen: wie uploadt, hoe vaak (voorstel: 2× per week tijdens de
   eerste maand, daarna wekelijks).
3. Dit is ook het antwoord op "hoe doen we de generale repetitie zonder koppeling":
   met een echte CSV-export van de rekening — zie PLAN-generale-repetitie-geldstromen.

## §4. AVG — vooral papierwerk dat nog ontbreekt

Luxis verwerkt persoonsgegevens van debiteuren en cliënten. Rollen: **Kesting Legal =
verwerkingsverantwoordelijke**, **Arsalan/Luxis = verwerker**, met subverwerkers
(Hetzner (DE) hosting, Anthropic (AI), Microsoft (e-mail/M365), Backblaze (backup),
Sentry (foutmeldingen, EU-regio, zonder persoonsgegevens — al goed ingesteld)).

**Acties (papier, kunnen nu, ~1 dagdeel samen):**
1. **Verwerkersovereenkomst Kesting ↔ Luxis/Arsalan** opstellen en tekenen — bestaat
   nog niet en is verplicht (ook, juist, tussen bevriende partijen).
2. **Subverwerkerslijst + verwerkingsregister** opstellen (1 A4 per verwerking: doel,
   categorieën gegevens, bewaartermijn, verwerkers). Model: AP-website.
3. **Anthropic**: verwerkersovereenkomst (DPA) accepteren op het API-account en de
   instellingen voor dataretentie/training controleren en vastleggen — niet geverifieerd
   in deze sessie, moet aantoonbaar op papier.
4. **Backblaze B2-regio EU bevestigen** — staat al open als ARSALAN-TODO §3, nu urgent
   want onderdeel van het register.
5. **Bewaarbeleid vastleggen** (bron: NOvA-archiveringshandleiding + art. 7:412 BW):
   dossiers 5 jaar na afsluiting, financiële administratie en derdengelden-stukken
   7 jaar (fiscaal), langer bewaren overwegen i.v.m. aansprakelijkheid. Luxis verwijdert
   nu niets automatisch — dat is voor de livegang prima (bewaren mag), een
   opschoonfunctie is een latere bouwklus, geen blokkade.
6. Datalek-werkafspraak: wie meldt, waar, binnen 72 uur (1 alinea in het register).

## §5. AI en geheimhouding (NOvA "Aanbevelingen AI in de advocatuur 2025")

Vastgesteld (bron: NOvA, dec 2025): cliëntgegevens **nooit in gratis/publieke AI-tools**;
de advocaat moet weten waar data staat, hoe de leverancier met input/output omgaat en
welke subverwerkers er zijn; de advocaat blijft **eindverantwoordelijk** voor elk stuk.

Hoe Luxis zich daartoe verhoudt: er wordt géén publieke/gratis tool gebruikt maar de
betaalde Anthropic-API binnen het systeem; élk AI-concept gaat verplicht langs Lisanne
("Bekijk en verstuur") — dat matcht de kernaanbeveling. **Acties:**
1. De Anthropic-DPA/instellingen uit §4.3 — dat is hier het dragende document.
2. Werkinstructie voor Lisanne (½ A4): AI maakt concepten, jij controleert bedragen,
   grondslag en toon vóór verzending; nooit blind versturen. (Zit al in de werkwijze,
   nu ook op papier — de deken kan ernaar vragen.)
3. Transparantie: één zin in de kantoor-privacyverklaring/voorwaarden dat bij het
   opstellen van correspondentie AI-ondersteuning wordt gebruikt onder
   verantwoordelijkheid van de advocaat.

## §6. Wat al aantoonbaar op orde is (niets doen)

- WIK-staffel met wettelijk minimum/maximum + btw-regel, met tests tegen wettelijke
  voorbeelden; rente per factuur vanaf vervaldatum (besluit 6 juli); art. 6:44-
  toerekeningsvolgorde.
- Vier-ogen op derdengelden-uitbetalingen (§2), volledige audit trail.
- Niets verstuurt automatisch; advocaat zit altijd tussen concept en verzending.
- EU-hosting (Hetzner DE), Sentry EU zonder persoonsgegevens, versleutelde tokens,
  backups met bewezen restore-test, fail2ban/ufw (S159-S161).
- Klachten-/tuchtkader: advocaten vallen onder het bestaande advocatentuchtrecht
  (daarom geen apart incassoregister nodig).

## Volgorde en wie

| Stap | Wie | Wanneer |
|---|---|---|
| §4.1-4.6 papierwerk AVG + Anthropic-DPA + B2-check | Arsalan (+ Claude schrijft concepten) | nu, kan vandaag beginnen |
| §1 actie B brieven-audit | Claude (Opus-sessie) | vóór de eerste sommatie-verzending |
| §2 bestuurder + bankmandaat + verrekenclausule | Lisanne via Arsalan | vóór echte uitbetalingen |
| §3 bank bevestigen + werkritme | Arsalan/Lisanne | vóór de generale repetitie |
| §5 werkinstructie + privacyzin | Claude schrijft, Lisanne keurt | vóór livegang |

## Acceptatiecriteria

1. Getekende verwerkersovereenkomst Kesting↔Luxis + subverwerkerslijst + register
   bestaan als documenten in `docs/avg/` (of fysiek, met verwijzing).
2. Anthropic-DPA aantoonbaar geaccepteerd; dataretentie-instelling gedocumenteerd.
3. Backblaze-regio bevestigd EU (of migratie gepland).
4. Brieven-audit uitgevoerd: elk actief sjabloon afgevinkt tegen de Bki-checklist,
   gaten gedicht, resultaat in SESSION-NOTES.
5. Tweede stichtingsbestuurder heeft een Luxis-account; bankmandaat bevestigd.
6. Bewaarbeleid (1 A4) vastgesteld door Lisanne.
7. Werkinstructie AI getekend/bevestigd door Lisanne.
