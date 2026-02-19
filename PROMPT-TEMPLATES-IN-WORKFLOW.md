# Templates integreren in zaak-workflow + e-mail versturen

**Status:** Gepland (niet gestart)
**Dependency:** UX-VERBETERPLAN B1 (zaakdetail tabs) moet eerst af
**Splits in 3 deelfeatures voor uitvoering**

---

## Probleem

Nu: Advocaat gaat naar Documenten → kiest template → selecteert zaak → genereert → downloadt → opent Outlook → mailt handmatig → gaat terug naar zaak → past status aan.

Dat zijn 8 stappen voor iets dat 2 stappen zou moeten zijn.

---

## Deelfeature 1: Templates op zaakdetailpagina

**Type:** Frontend (bestaande API's)
**Complexiteit:** Midden
**Dependency:** Zaakdetail tabs (B1)

### Wat bouwen
- Op het Documenten-tab van zaakdetail: relevante templates tonen op basis van huidige zaakstatus
- Niet alle templates — alleen de logische volgende stap:
  - Status "Herinnering" → toon: Aanmaning, Sommatie
  - Status "14-dagenbrief" → toon: 14-dagenbrief template
  - Status "Sommatie" → toon: Tweede sommatie, Dagvaarding
  - Status "Dagvaarding" → toon: Dagvaardingsspecificatie, Renteoverzicht
  - Altijd beschikbaar: Renteoverzicht (als er vorderingen zijn)
- Één-klik document generatie — alle merge fields automatisch gevuld vanuit dossier
- Document preview voordat het wordt verstuurd
- Document opslaan in dossier (bestaande functionaliteit)

### Aandachtspunt
De status→template mapping moet **configureerbaar** zijn (data in workflow rules, niet hardcoded). Anders moet je code aanpassen bij elk nieuw zaaktype of template.

### Benchmark
Bekijk: Clio case document generation, PracticePanther matter documents, Smokeball auto-document linking

---

## Deelfeature 2: Workflow-suggesties bij statuswijziging

**Type:** Frontend (bestaande workflow API's)
**Complexiteit:** Klein-Midden
**Dependency:** Deelfeature 1

### Wat bouwen
- Bij statuswijziging: automatisch de juiste actie voorstellen
  - Status → "14-dagenbrief" → banner: "14-dagenbrief klaarzetten? [Genereer nu]"
  - Status → "Sommatie" → "Sommatiebrief genereren? [Genereer nu]"
  - Deadline verlopen → notificatie: "Termijn verlopen. Escaleren naar Sommatie? [Ja] [Nee, wacht]"
- **Advocaat beslist altijd** — geen automatisch versturen
- Systeem bereidt alles voor, advocaat klikt "ga"

---

## Deelfeature 3: E-mail versturen vanuit Luxis

**Type:** Frontend + Backend (nieuw systeem)
**Complexiteit:** Groot
**Dependency:** Deelfeature 1 (document generatie vanuit zaak)

### Fase 1: SMTP
- Knop "Verstuur per e-mail" op gegenereerd document
- E-mailformulier:
  - Aan: vooringevuld met e-mailadres wederpartij (uit dossier)
  - CC: optioneel (cliënt, deurwaarder — uit case parties)
  - Onderwerp: vooringevuld ("Sommatie inzake [zaaksnaam] - [ons kenmerk]")
  - Body: standaardtekst per template type (configureerbaar, niet hardcoded)
  - Bijlage: gegenereerde PDF
- Versturen via SMTP (Outlook/365 configuratie in instellingen)
- E-mail opgeslagen in dossier als correspondentie
- Activiteit gelogd in timeline

### Fase 2: Outlook/365 integratie (later)
- OAuth i.p.v. SMTP
- E-mails ontvangen en automatisch aan dossier koppelen
- Volledige correspondentie-inbox per dossier

### Technische aandachtspunten
- SMTP credentials encrypted opslaan in tenant settings
- Error handling: retry bij falen, error state, notificatie aan gebruiker
- SPF/DKIM/DMARC configuratie (anders belandt alles in spam)
- Rate limiting
- Development: Mailtrap/Mailhog voor testen
- E-mail body templates: apart beheer nodig (wie beheert ze? waar opgeslagen?)

---

## Bestaande Documenten-pagina

Blijft bestaan als **beheerpagina**:
- Templates uploaden, bewerken, verwijderen
- Preview met dummy data
- Categoriseren (incasso, algemeen, insolventie)
- Versiebeheer

Advocaat komt hier alleen voor template-beheer, niet voor dagelijks gebruik.

---

## Acceptatiecriteria

- [ ] Op zaakdetail zijn relevante templates zichtbaar op basis van huidige status
- [ ] Één-klik document generatie vanuit de zaak (alle merge fields automatisch gevuld)
- [ ] Document preview voordat het wordt verstuurd
- [ ] Status→template mapping is configureerbaar (niet hardcoded)
- [ ] Workflow-suggestie verschijnt bij statuswijziging
- [ ] E-mail versturen vanuit Luxis met vooringevulde velden
- [ ] E-mail en document worden opgeslagen in dossier
- [ ] Activiteit wordt gelogd in timeline
- [ ] Documenten-pagina blijft functioneren als beheerpagina
- [ ] Alle bestaande template-functionaliteit blijft werken

---

## Onderzoek eerst

Voordat je aan elke deelfeature begint:
1. Bekijk hoe Clio, PracticePanther en Smokeball document generation integreren in case detail
2. Bekijk hoe PandaDoc en DocuSign de "generate → preview → send" flow aanpakken
3. Bekijk de huidige zaakdetailpagina en bepaal waar document-acties het best passen
