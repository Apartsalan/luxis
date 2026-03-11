
## Volgende grote module: Microsoft 365 Email Integratie

**Doel:** "Best of breed" email — het beste van BaseNet, Kleos, Hammock, Smokeball en Clio combineren. Lisanne werkt in Outlook, Luxis regelt de rest automatisch op de achtergrond.

**Email strategie (beslissing 21 feb 2026):**
- **F11 (SMTP vanuit Luxis)** is een **tijdelijke brug** — werkt nu, maar emails verschijnen niet in Outlook's Verzonden map
- **M1-M6 (email integratie)** is de **eindoplossing** en wordt nu **prioriteit**
- **Abstractielaag:** `EmailProvider` interface met `OutlookProvider` (productie, M365 via Graph API)
- **Huidige status:** OutlookProvider gebouwd en werkend met seidony@kestinglegal.nl op M365. GmailProvider bestaat nog maar wordt NIET meer gebruikt.
- **LET OP: GEEN Gmail gebruiken — alles via OutlookProvider/Graph API met M365 account.**
- **Overgangspad:** F11 blijft werken totdat M4 live is → dan vervangt de email provider de Luxis SMTP compose dialog

**Technisch fundament:** OAuth 2.0 + OutlookProvider via Microsoft Graph API (M365)

**Prereq: Mail migratie BaseNet → Microsoft 365**

**Aanpak: Risicovrij testen via Optie 2 (beslissing 23 feb 2026)**

Arsalan test eerst met eigen mailbox `seidony@kestinglegal.nl` op M365. Lisanne merkt niks — MX blijft bij BaseNet tot alles bewezen werkt.

**Fase M0a — Arsalan's test-mailbox (kan zelfstandig, geen Lisanne nodig):**
1. M365 Business Basic kopen (~€5,60/mnd) op admin.microsoft.com
2. Domein `kestinglegal.nl` toevoegen — alleen TXT-record voor verificatie, **MX NIET wijzigen**
3. Mailbox `seidony@kestinglegal.nl` aanmaken in M365
4. Bestaande mail importeren van BaseNet via IMAP migratie tool
5. Outlook instellen (web/desktop) — versturen werkt direct, ontvangen gaat nog via BaseNet
6. OutlookProvider bouwen in Luxis + Graph API testen met dit account
7. Luxis email-integratie volledig testen (sync, compose, correspondentie tab)

**Fase M0b — Lisanne overzetten (samen met Lisanne, pas als M0a 100% werkt):**
- Mailbox `lisanne@kestinglegal.nl` aanmaken in M365
- Oude mails migreren via IMAP migratie tool (gratis van Microsoft)
- MX records wijzigen bij domeinregistrar → alle mail naar M365
- Outlook instellen op laptop/telefoon
- BaseNet email opzeggen

**Waarom deze aanpak:**
- Nul risico voor Lisanne — haar mail blijft op BaseNet tot alles werkt
- Graph API/OutlookProvider kan al gebouwd en getest worden
- Oude mail wordt geïmporteerd — geen dataverlies
- MX-wijziging pas op het allerlaatst, als alles bewezen werkt

| Fase | Feature | Wat het oplevert | Status |
|------|---------|-----------------|--------|
| M0a | Test-mailbox Arsalan op M365 | seidony@kestinglegal.nl op M365, Graph API testbaar, OutlookProvider bouwen | ✅ Compleet (23 feb) — mailbox actief, Azure App Registration klaar, OutlookProvider gebouwd, OAuth flow getest en werkend |
| M0b | Lisanne overzetten naar M365 | Alle mail op M365, volledige integratie live | ⏳ Wacht op M0a succes + Lisanne |
| M1 | OAuth + abstractielaag | EmailProvider interface, OutlookProvider (Graph API), OAuth flow, token opslag | ✅ Gebouwd (21 feb) |
| M2 | Inbox sync + auto-koppeling | Inkomende mails automatisch aan dossiers koppelen (afzender → relatie → dossier) | ✅ Gebouwd (21 feb) |
| M2+ | Dossiernummer-matching | Emails met "2026-00003" in onderwerp/body → automatisch aan juiste dossier | ✅ Gebouwd (21 feb) |
| M2+ | Klantreferentie-matching | Emails met bekende Case.reference → automatisch aan dossier | ✅ Gebouwd (21 feb) |
| M2+ | Zaaknummer rechtbank-matching | Emails met Case.court_case_number in tekst → automatisch aan dossier | ✅ Gebouwd (21 feb) |
| M2+ | body_html doorzoeken | HTML-only emails (Gmail/Outlook) worden nu ook doorzocht na HTML-stripping | ✅ Gefixt (21 feb) |
| M2+ | Bijlagen sync | Attachments downloaden via provider, opslaan, tonen in detail panel + download | ✅ Gebouwd (21 feb) |
| M2+ | Auto-sync (5 min) | APScheduler synct alle verbonden accounts elke 5 minuten automatisch | ✅ Gebouwd (21 feb) |
| M2+ | Re-match ongelinkte emails | Bestaande ongelinkte emails worden bij elke sync opnieuw gematcht (altijd, ook vanuit dossier-context) | ✅ Gebouwd + gefixt (21 feb) |
| M3 | Correspondentie tab (unified view) | Alle in- + uitgaande mails per dossier, split-view met detail panel + bijlagen | ✅ Gebouwd (21 feb) |
| M4 | Compose via provider | Send via OutlookProvider/Graph API (verschijnt in Verzonden), fallback naar SMTP | ✅ Gebouwd (21 feb) |
| M5 | AutoTime op emails | Automatische tijdregistratie bij mail-activiteit (à la Smokeball) | 🔵 Backlog (bestaande timer dekt dit grotendeels) |
| M6 | "Ongesorteerd" wachtrij | Mails die niet auto-gekoppeld zijn handmatig toewijzen met suggesties | ✅ Gebouwd (22 feb) |

**Bouwvolgorde:** M0a ✅ → OutlookProvider ✅ → M0b (samen met Lisanne) → live (M5 op backlog)

**Wat Lisanne ervaart na afronding:**
- Template aanklikken → opent direct in Outlook met alles pre-filled
- Inkomende mails worden automatisch aan het juiste dossier gekoppeld (op dossiernummer, referentie, of contactpersoon)
- Bijlagen worden automatisch meegesynced en zijn downloadbaar vanuit Luxis
- Op elk dossier: volledige correspondentie (in + uit) met bijlagen zichtbaar
- Email sync draait automatisch elke 5 minuten — geen handmatige actie nodig
- Tijdschrijven op email-activiteit gaat automatisch
- Ze hoeft Outlook niet te verlaten, maar alles staat ook in Luxis

---

## Toekomstige module: AI Incasso Agent

**Doel:** Een AI agent die repetitief incassowerk zelfstandig oppakt — het meeste incassowerk volgt vaste patronen met vaste templates en voorspelbare antwoorden.

**Wat de agent kan doen:**
- **Dossier aanmaken**: cliënt stuurt factuur + gegevens → agent maakt dossier aan, vult alle velden in
- **Workflow volgen**: herinnering → aanmaning → 14-dagenbrief → sommatie automatisch versturen op de juiste momenten
- **Reacties verwerken**: standaard-antwoorden herkennen ("ik betaal volgende week", "ik betwist de factuur", "ik heb al betaald") en juiste vervolgactie voorstellen
- **Betalingen matchen**: binnenkomende betalingen automatisch aan dossiers koppelen, restant berekenen, volgende stap bepalen
- **Rente berekenen**: automatisch bijwerken bij elke actie
- **Escaleren**: complexe situaties of onbekende reacties doorsturen naar Lisanne met context

**Hoe het werkt:**
1. Agent leert van Lisanne's bestaande dossiers (patronen, beslissingen, timing)
2. Nieuwe dossiers worden door de agent opgestart en gevolgd
3. Lisanne reviewt alleen: escalaties, onbekende situaties, dagvaardingen
4. Dashboard toont wat de agent heeft gedaan en wat Lisanne's aandacht nodig heeft

**Dependency:** Microsoft 365 Email Integratie (M1-M6) moet eerst af — de agent heeft email nodig om te functioneren.

**Technisch:** Claude API / Anthropic API + tool use, getraind op Lisanne's dossierpatronen en templates.

---

## Data Migratie: BaseNet → Luxis

**Doel:** Alle data uit BaseNet naadloos overzetten naar Luxis zodat Lisanne direct kan werken zonder dataverlies.

**Wat BaseNet exporteert (onderzocht 23 feb 2026):**
1. **Volledige backup** — dossiers, relaties, documenten, correspondentie als bestanden + CSV/Excel
2. **CRM/Relaties** — export naar Excel
3. **Boekhouding** — mutaties export naar Excel

**Mapping BaseNet → Luxis:**

| BaseNet Export | Luxis Tabel(len) | Complexiteit | Aanpak |
|---|---|---|---|
| Relaties (Excel/CSV) | `contacts` + `contact_links` | Laag | pandas parse → bulk insert |
| Dossiers (CSV) | `cases` + `case_parties` | Middel | ID-mapping, relatie-linking |
| Documenten (bestanden) | `generated_documents` / `case_files` + file storage | Middel | Bestanden kopiëren + metadata records |
| Correspondentie | `synced_emails` / `generated_documents` | Middel | Email parsing + dossier-linking |
| Boekhouding/mutaties | `invoices` + `payments` | Middel-Hoog | Extra validatie (totalen matchen) |
| Uren | `time_entries` | Laag | Directe mapping |

**Aanpak:**
1. **Parse-scripts** — Python scripts die BaseNet CSV/Excel inlezen met pandas
2. **Mapping & transformatie** — BaseNet velden → Luxis schema's (UUID generatie, tenant_id toewijzing, relatie-linking)
3. **ID-mapping tabel** — BaseNet ID's → Luxis UUID's zodat relaties intact blijven
4. **Dry-run modus** — rapporteert wat er geïmporteerd wordt zonder te schrijven
5. **Import** — Bulk insert via SQLAlchemy met transactie-rollback bij fouten
6. **Documenten** — Bestanden kopiëren naar Luxis storage volume, metadata records aanmaken
7. **Verificatie-rapport** — Telling per entiteit: verwacht vs geïmporteerd

**Aandachtspunten:**
- Boekhouding is het meest gevoelige deel → extra validatie
- Documentenvolume kan groot zijn → upload-tijd afhankelijk van VPS bandbreedte
- BaseNet export moet door Lisanne gedaan worden (toegangsrechten)

**Planning:** 1 sessie voor migratie-scripts + 1 sessie voor testen en uitvoeren
**Dependency:** Lisanne moet BaseNet export klaarzetten
**Status:** 📋 Gepland — wacht op BaseNet export van Lisanne

---

## Overige toekomstige modules (niet gepland, zie FEATURE-INVENTORY.md)

- Insolventiemodule (faillissement, WSNP, Recofa)
- Cliëntportaal
- Boekhoudkoppeling (Exact Online)
- Bulk operaties
- Management rapportages
- Mobiele app
- E-signing
- KvK API integratie
- Online betaling (Mollie/iDEAL)

---

