# UX Review — Luxis Practice Management System

**Datum:** 19 februari 2026
**Scope:** Alle bestaande features vs. marktstandaard
**Doel:** Eerlijke, kritische analyse per feature — wat hebben we, wat doen concurrenten beter, wat moet anders
**Benchmark:** Clio, PracticePanther, Smokeball, MyCase, LegalSense, Basenet, + best-in-class SaaS (HubSpot, Stripe, Linear, Toggl)

---

## Samenvatting

Luxis heeft een solide technische basis (Next.js 15, FastAPI, multi-tenant) en de kernfeatures staan. Maar vergeleken met de markt zijn er **significante UX-gaps** die het product onaf laten voelen. De grootste problemen:

1. **Dashboard is een zwakke eerste indruk** — statische widgets zonder personalisatie of echte KPI's
2. **Dossierbeheer mist diepte** — geen timeline, geen tabs, geen quick actions
3. **Tijdschrijven heeft geen timer** — de #1 verwachte feature in elke PMS
4. **Facturatie is barebones** — geen betalingstracking, geen herinneringen, geen credit notes
5. **Documentgeneratie werkt maar voelt niet intuïtief** — geen preview, geen template management UI
6. **Navigatie en zoeken zijn onderontwikkeld** — geen global search, geen keyboard shortcuts
7. **Agenda is functioneel maar mist integratie** — geen drag-and-drop, geen Outlook/Google sync

**Verdict:** Het product is ~40% van waar het moet zijn om marktklaar te zijn. De *functionaliteit* is er grotendeels, maar de *UX polish* en *workflow-optimalisatie* ontbreken.

---

## 1. Dashboard (Startpagina)

### Wat we hebben
- Statistiekenkaarten bovenaan: openstaande zaken, lopende taken, uren deze week, openstaande facturen
- Recente zaken widget (lijst met status badges)
- Komende deadlines widget (taken op korte termijn)
- KYC waarschuwingswidget (conditioneel, alleen bij wwft-module)
- Incasso pipeline widget (conditioneel, alleen bij incasso-module)

### Wat concurrenten doen
**Clio:** Customizable dashboard met drag-and-drop widgets. KPI's: billable hours target vs. actual (gauge chart), outstanding receivables aging, task list met due dates, recent activity feed, firm-wide vs. personal toggle. Widgets zijn verplaatsbaar en aan/uit te zetten.

**PracticePanther:** Dashboard met "Today" focus — wat moet je vandaag doen? Timer direct zichtbaar. Billable hours chart (week/maand), outstanding invoices met aging breakdown (30/60/90 dagen), calendar widget met dag-overzicht.

**Smokeball:** Productiviteits-dashboard: uren per dag automatisch bijgehouden (geen timer nodig), productivity score, vergelijking met team. Focus op "heb je genoeg uren gemaakt vandaag?"

**HubSpot (best-in-class CRM):** Volledig customizable dashboard builder. Elke metric als widget toevoegbaar. Filters per tijdsperiode. Vergelijkingen met vorige periode. Charts: bar, line, funnel, table. Delen met team.

**Stripe (best-in-class fintech):** Omzet-grafiek prominant. Today's activity stream. Quick actions prominent. Alles clickable naar detail.

### Wat beter kan
| Issue | Ernst | Oplossing |
|---|---|---|
| **Geen personalisatie** — elke gebruiker ziet hetzelfde | 🔴 Hoog | Widget systeem met drag-and-drop, show/hide per widget |
| **Geen grafieken/trends** — alleen kale getallen | 🔴 Hoog | Omzetgrafiek, uren-trend (week), factuur-aging chart |
| **Geen "vandaag" focus** — wat moet ik NU doen? | 🔴 Hoog | "Vandaag" sectie: taken due today, afspraken vandaag, deadlines |
| **Geen quick actions** — moet navigeren voor alles | 🟡 Midden | Quick action buttons: + Zaak, + Tijdregistratie, + Factuur |
| **Geen activity feed** — wat is er recent gebeurd? | 🟡 Midden | Recent activity: nieuwe zaken, facturen betaald, taken afgerond |
| **Geen targets/goals** — geen motivatie-element | 🟡 Midden | Billable hours target vs. actual (weekly gauge) |

**Prioriteit:** 🔴 HOOG — Het dashboard is het eerste wat gebruikers zien. Een zwak dashboard = zwakke eerste indruk.
**Geschatte impact:** Groot. Bepaalt dagelijks gebruikspatroon.

---

## 2. Dossierbeheer (Zaken)

### Wat we hebben
- Zakenlijst met zoekbalk, statusfilter, tabel (zaaknummer, naam, type, status, cliënt, datum)
- Paginering
- Zaak-detailpagina met:
  - Basisinfo (zaaknummer, type, status, cliënt, wederpartij)
  - Status transitie dropdown (workflow-enforced transitions)
  - Workflow taken sectie
  - Case activities/notities (API bestaat: POST/GET `/api/cases/{id}/activities`)
  - Case parties (meerdere rollen: deurwaarder, rechtbank, etc.)
  - Incasso-specifieke sectie (indien module aan)
  - Conflictcheck knop
- Nieuwe zaak formulier (single form, ~8 velden)
- **Backend is sterker dan frontend:** Activities, parties, en workflow zijn goed gebouwd in de API maar de frontend toont ze niet optimaal

### Wat concurrenten doen
**Clio:** Matter detail is een **hub met tabs**: Overview, Calendar, Tasks, Time & Expenses, Documents, Communications, Billing. Elke tab heeft eigen functionaliteit. Timeline/activity feed op Overview. Quick actions: "Log Time", "Create Document", "Add Note" altijd zichtbaar. Custom fields per matter type. Kanban board view optioneel.

**PracticePanther:** Matter detail met sidebar voor quick info + main area met tabs. Drag-and-drop file upload. Inline time entry vanuit zaak. Notes met rich text editor. Tags en custom fields. Bulk actions op zakenlijst (status wijzigen, toewijzen).

**Smokeball:** Automatische document tracking — elk bestand dat je opent/bewerkt wordt automatisch aan de zaak gekoppeld. Deep OS integration. Matter creation wizard (stap-voor-stap).

**Linear (best-in-class project management):** Issue detail als slide-over panel (niet hele pagina navigatie). Properties sidebar rechts. Activity/comment stream. Keyboard shortcuts voor alles (C = comment, L = label, etc.). Sub-issues. Relations (blocks, is blocked by).

**Jira:** Tabbed interface, custom workflows, subtasks, linked issues, watchers, time tracking inline.

### Wat beter kan
| Issue | Ernst | Oplossing |
|---|---|---|
| **Geen tabs op zaakdetail** — alles op één pagina gemixt | 🔴 Hoog | Tabbed interface: Overzicht, Taken, Uren, Documenten, Facturatie, Notities |
| **Activity feed niet prominent** — backend heeft activities API, maar frontend toont ze niet als timeline | 🔴 Hoog | Chronologische timeline op Overzicht tab: statuswijzigingen, notities, documenten, facturen |
| **Geen quick actions vanuit zaak** — te veel navigatie nodig | 🔴 Hoog | Action bar: + Uren loggen, + Document, + Notitie, Factuur maken |
| **Notities bestaan maar zijn verborgen** — API ondersteunt activities, UI maakt het niet makkelijk | 🟡 Midden | Prominent notes/comments sectie met rich text, inline toevoegen |
| **Geen inline time entry** — moet naar aparte pagina | 🟡 Midden | Timer/quick time entry direct vanuit zaakpagina |
| **Geen custom fields** — elke zaak heeft dezelfde velden | 🟡 Midden | Configurable extra velden per zaaktype |
| **Geen kanban/board view** — alleen tabel | 🟡 Midden | Optionele kanban view gesorteerd op status |
| **Geen drag-and-drop documenten** — handmatige upload flow | 🟡 Midden | Drop zone op zaakdetail voor documenten |
| **Zaak aanmaken is basic** — geen wizard, geen templates | 🟢 Laag | Zaaktype templates met vooringevulde velden/taken |

**Prioriteit:** 🔴 HOOG — Dossierbeheer is de kern van een PMS. Hier besteden advocaten 80% van hun tijd.
**Geschatte impact:** Zeer groot. Dit is make-or-break voor adoptie.

---

## 3. Relatiebeheer (Contacten/CRM)

### Wat we hebben
- Relatielijst met zoekbalk en typefilter (persoon/bedrijf)
- Tabel: naam, type, email, telefoon, stad, aantal zaken
- Relatiedetail: contactinfo, gekoppelde zaken, KYC status (indien wwft-module)
- Nieuwe relatie formulier (persoon of bedrijf)
- Conflictcheck functionaliteit
- **Contact links:** API ondersteunt persoon-bedrijf koppelingen (POST/DELETE `/api/relations/links`)
- **Case parties:** Meerdere rollen per zaak (deurwaarder, rechtbank, etc.) via API

### Wat concurrenten doen
**Clio:** Contact detail met tabs: Details, Matters (gekoppelde zaken met rol), Bills, Documents, Communications. Meerdere adressen, meerdere emails/telefoons. Company-person hiërarchie (bedrijf met meerdere contactpersonen). Custom fields. Duplicate detection bij aanmaken. Contact activity feed.

**HubSpot (best-in-class CRM):** Contact record als single page met alles zichtbaar. Left sidebar: properties. Main area: activity timeline (emails, calls, meetings, notes, tasks — chronologisch). Right sidebar: associated companies, deals, tickets. Quick actions bovenaan. Smart lists en segmentatie.

**Salesforce:** 360° klantbeeld. Elk touchpoint zichtbaar. Relatie-netwerk visualisatie. Lead scoring. Communication history compleet.

**PracticePanther:** Contact met billing history, trust accounting, document links. Quick matter creation vanuit contact. Email integration.

### Wat beter kan
| Issue | Ernst | Oplossing |
|---|---|---|
| **Geen activity timeline** — contact is statisch | 🔴 Hoog | Timeline: zaken, facturen, documenten, notities chronologisch |
| **Geen meerdere contactmethoden** — 1 email, 1 telefoon | 🟡 Midden | Multiple emails, telefoons, adressen per contact |
| **Company-person hiërarchie bestaat in API maar is onzichtbaar in UI** — links API werkt, frontend toont het niet | 🟡 Midden | UI voor persoon-bedrijf koppelingen, organogram view |
| **Geen billing history op contact** — moet via facturen zoeken | 🟡 Midden | Tab met alle facturen van deze relatie |
| **Geen duplicate detection** — geen waarschuwing bij dubbele namen | 🟡 Midden | Fuzzy matching bij aanmaken, merge tool |
| **Geen contactrollen per zaak** — alleen client/wederpartij | 🟢 Laag | Rollen: client, wederpartij, getuige, curator, etc. |
| **Geen import/export** — handmatig invoeren | 🟢 Laag | CSV import, vCard export |

**Prioriteit:** 🟡 MIDDEN — Belangrijk maar niet urgent. CRM is een "nice to have" verbetering, niet een blocker.
**Geschatte impact:** Middelgroot. Verbetert dagelijkse workflow.

---

## 4. Tijdschrijven (Urenregistratie)

### Wat we hebben
- Urenlijst met datumfilter en zaakfilter
- Tabel: datum, zaak, omschrijving, duur, tarief, bedrag
- Handmatige invoer: datum, zaak (dropdown), omschrijving, duur in minuten
- Bewerken en verwijderen
- Totalen onderaan
- Billable/non-billable onderscheid (backend ondersteunt dit)
- Summary endpoint met per-zaak breakdown
- **Backend is timer-ready:** `/api/time-entries/my/today` endpoint bestaat al voor timer widget
- **Onkosten (expenses):** Aparte module (`/api/expenses`) met billable/uninvoiced tracking

### Wat concurrenten doen
**Clio:** Floating timer altijd zichtbaar in de app (rechtsonder). Meerdere timers tegelijk. One-click start vanuit zaak. Timer pauze/hervat. Rounding rules (6-min increments). Weekly timesheet view (matrix: dagen vs. zaken). Activity codes. Billable/non-billable toggle. Bulk edit. Keyboard shortcut (T) om timer te starten.

**Toggl Track (best-in-class):** Timer is het HELE product — altijd prominent. Keyboard shortcut. Calendar view van uren. Pomodoro timer optie. Idle detection ("je was 15 min idle, wil je stoppen?"). Weekly reports met charts. Tags en projecten. Browser extension.

**Harvest:** Timer + handmatig. Timesheet grid (week-view). Per-project budgets met progress bars. Invoicing direct vanuit uren. Team capacity view.

**PracticePanther:** Timer in top navigation bar. Voice-to-text beschrijving (dicteren). LEDES billing code support. Timer vanuit elke pagina.

**Smokeball:** AUTOMATISCHE tijdregistratie — tracked welke documenten je opent, welke emails je leest, welke telefoongesprekken je voert. Geen timer nodig. AI-assisted categorisatie.

### Wat beter kan
| Issue | Ernst | Oplossing |
|---|---|---|
| **GEEN TIMER** — dit is de #1 verwachte feature | 🔴 Kritiek | Floating timer component, altijd zichtbaar, start/stop/pauze |
| **Geen weekly timesheet view** — standaard bij alle concurrenten | 🔴 Hoog | Grid: rijen=zaken, kolommen=dagen, cellen=uren. Snel invullen |
| **Duur in minuten i.p.v. uren:minuten** — onnatuurlijk | 🔴 Hoog | Input als HH:MM of decimaal (1.5u), niet 90 minuten |
| **Geen rounding rules** — advocaten werken in 6-min eenheden | 🟡 Midden | Auto-round naar 6-min (0.1 uur) increments, instelbaar |
| **Geen billable/non-billable toggle** — alles is hetzelfde | 🟡 Midden | Toggle per entry, standaard billable |
| **Geen activity codes** — geen categorisatie van werktype | 🟡 Midden | Codes: correspondentie, onderzoek, zitting, reistijd, etc. |
| **Geen quick entry vanuit zaak** — moet naar urenpagina | 🟡 Midden | Inline time entry op zaakdetail + sidebar quick entry |
| **Geen keyboard shortcuts** — alles met muis | 🟢 Laag | T = start timer, Enter = opslaan, etc. |
| **Geen idle detection** — timer loopt door bij afwezigheid | 🟢 Laag | "Je was X min inactief, wil je aanpassen?" |

**Prioriteit:** 🔴 KRITIEK — Tijdschrijven zonder timer is als een auto zonder stuur. Elke concurrent heeft dit. Het is DE reden dat advocaten een PMS gebruiken.
**Geschatte impact:** Zeer groot. Dit is de feature die dagelijks het meest gebruikt wordt.

---

## 5. Facturatie

### Wat we hebben
- Facturenlijst met statusfilter en zoekbalk
- Tabel: factuurnummer, cliënt, zaak, bedrag, status, datum
- Factuur aanmaken: selecteer zaak → onbefactureerde uren → genereer
- PDF generatie (via WeasyPrint)
- Status lifecycle: concept → goedgekeurd → verzonden → betaald/geannuleerd
- BTW berekening (21%)
- Factuurregels toevoegen/verwijderen (in concept-status)
- Approve/send/mark-paid/cancel status transities
- **Onkosten koppelbaar:** Expenses module bestaat, kan aan factuurregels gekoppeld worden
- **Immutable na goedkeuring:** Facturen zijn niet meer bewerkbaar na approve (correcte business logic)

### Wat concurrenten doen
**Clio:** Invoice creation wizard: selecteer uren/expenses → review/edit line items → preview → customize cover letter → send via email. Online betaling (credit card, ACH). Payment tracking met partial payments. Automated reminders (3-5-7 dagen na due date). Trust accounting (derdengelden). Aging report (30/60/90/120 dagen). Batch invoicing. Credit notes. Invoice templates customizable. Client portal voor factuurinzage.

**Stripe Invoicing (best-in-class):** Beautiful invoice editor. Drag-and-drop line items. Live preview. One-click send. Payment link in email. Auto-reminders. Partial payments. Credit notes. Multi-currency. Tax auto-calculate. Branding customization. Dashboard: MRR, outstanding, paid, overdue — allemaal met charts.

**Xero / Exact Online (best-in-class accounting):** Invoice aging dashboard. Bank reconciliation. Recurring invoices. Multi-currency. Quote-to-invoice flow. Credit notes. Payment matching. Automated follow-ups.

**PracticePanther:** Drag uren naar factuur. Preview before send. Payment plans. Trust accounting. QuickBooks/Xero integration. E-payment via LawPay.

### Wat beter kan
| Issue | Ernst | Oplossing |
|---|---|---|
| **Geen betalingstracking** — factuur is "verzonden" of "betaald", geen tussenweg | 🔴 Hoog | Partial payments, betalingsdatum, betaalmethode tracking |
| **Geen automatische herinneringen** — handmatig opvolgen | 🔴 Hoog | Auto-reminders: 7, 14, 30 dagen na vervaldatum |
| **Geen aging report** — geen overzicht van openstaande bedragen per periode | 🔴 Hoog | Dashboard: 30/60/90/120 dagen outstanding |
| **Geen credit notes** — fouten niet te corrigeren | 🟡 Midden | Credit nota aanmaken, koppelen aan originele factuur |
| **Geen factuur-preview voor verzenden** — blind vertrouwen op PDF | 🟡 Midden | Preview mode met "verstuur" bevestiging |
| **Geen batch invoicing** — één voor één | 🟡 Midden | "Factureer alle onbefactureerde uren" bulk actie |
| **Geen email verzending** — PDF downloaden en handmatig mailen | 🟡 Midden | Direct vanuit Luxis factuur per email versturen |
| **Geen online betaling** — geen payment link | 🟢 Laag | Mollie/Stripe payment link op factuur |
| **Geen recurring invoices** — handmatig elke maand | 🟢 Laag | Terugkerende facturen (retainers) |
| **Geen accounting export** — geen koppeling met boekhoudsoftware | 🟢 Laag | Export naar Exact Online, Twinfield, of UBL formaat |

**Prioriteit:** 🔴 HOOG — Facturatie is direct gekoppeld aan omzet. Slechte facturatie = geld mislopen.
**Geschatte impact:** Groot. Directe financiële impact.

---

## 6. Documentgeneratie

### Wat we hebben
- Documenttemplates beheer (admin)
- Template upload (docx met merge fields)
- Document genereren: selecteer template → kies zaak → genereer DOCX/PDF
- Merge fields: zaakgegevens, cliëntgegevens, datums, bedragen
- Gegenereerde documenten per zaak inzichtbaar
- Incasso-specifieke templates (aanmaningen, sommaties, dagvaardingen)

### Wat concurrenten doen
**Smokeball (marktleider in documentautomatisering):** 20.000+ templates ingebouwd. Document assembly met conditional logic (als X dan paragraaf Y). Auto-save naar zaak. Version tracking. Co-editing. Deep Word/Outlook integration. Template builder met drag-and-drop velden.

**Clio:** Document automation add-on (Lawyaw). Template library met categorieën. Conditional logic. E-signature integration (DocuSign). Client portal voor document sharing. Version history. Bulk document generation.

**PandaDoc (best-in-class):** WYSIWYG template builder. Drag-and-drop content blocks. Conditional content. Electronic signatures built-in. Analytics (opened, viewed, signed). Comments/approval workflow. Template library met zoeken en categorieën.

**NetDocuments:** Enterprise document management. Version control. Check-in/check-out. Folder structure per zaak. Full-text search in documenten. Access control per document.

### Wat beter kan
| Issue | Ernst | Oplossing |
|---|---|---|
| **Geen template preview** — moet genereren om te zien wat je krijgt | 🟡 Midden | Preview met dummy data voordat je genereert |
| **Geen template management UI** — upload only, geen editor | 🟡 Midden | Template library met categorieën, zoeken, beschrijvingen |
| **Geen version control** — document overschrijft zonder historie | 🟡 Midden | Versies bijhouden per gegenereerd document |
| **Geen conditional logic in templates** — statische merge fields | 🟡 Midden | IF/ELSE blokken in templates (als incasso dan X) |
| **Geen e-signature integratie** — handmatig ondertekenen | 🟢 Laag | DocuSign/HelloSign integratie |
| **Geen bulk generation** — één document per keer | 🟢 Laag | Batch: zelfde template voor meerdere zaken |
| **Geen document viewer in-app** — moet downloaden om te bekijken | 🟢 Laag | In-browser PDF viewer |

**Prioriteit:** 🟡 MIDDEN — Documentgeneratie werkt, maar kan flink verbeterd worden qua gebruiksgemak.
**Geschatte impact:** Middelgroot. Bespaart tijd bij veelvoorkomende documenten.

---

## 7. Agenda & Deadlines

### Wat we hebben
- Maand- en weekweergave
- Events uit workflow taken + KYC review deadlines
- Kleurcodering per status (overdue=rood, due=oranje, pending=blauw, completed=groen, KYC=paars)
- Dag-klik toont detail panel met event info
- Mobiel responsief (card layout)
- Nederlandse dagweergave (ma/di/wo/do/vr/za/zo)

### Wat concurrenten doen
**Clio:** Calendar synced met Outlook en Google Calendar (bidirectioneel). Court dates, deadlines, events als aparte typen. Recurring events. Drag-and-drop reschedule. Agenda view (lijstweergave). Team calendar (wie is waar?). Conflict detection bij plannen. Automated court deadline calculation (jurisdiction-based).

**Google Calendar (best-in-class):** Drag-and-drop alles. Quick event create (klik op tijdslot). Meerdere calendars (persoonlijk, kantoor, rechtbank). Color coding per calendar. Reminders op meerdere momenten. Side-by-side view van meerdere mensen. Event creation: titel + tijd = klaar (minimal clicks).

**Linear (best-in-class project tools):** Cycle planning. Due date tracking met automated reminders. Sprint/iteration view naast kalender. Timeline/Gantt view voor langere projecten.

**Asana:** Calendar view met taken als events. Drag-and-drop prioritizing. Timeline (Gantt) view. Dependencies (taak B kan niet starten voor taak A klaar is).

### Wat beter kan
| Issue | Ernst | Oplossing |
|---|---|---|
| **Read-only calendar** — kan geen events aanmaken/bewerken vanuit agenda | 🔴 Hoog | Event aanmaken door op tijdslot te klikken, bewerken inline |
| **Geen drag-and-drop** — kan events niet verplaatsen | 🟡 Midden | Drag events naar andere datum/tijd |
| **Geen externe calendar sync** — geen Outlook/Google koppeling | 🟡 Midden | CalDAV/iCal sync, of Outlook/Google API integration |
| **Geen recurring events** — handmatig voor herhalingen | 🟡 Midden | Recurring rules: dagelijks, wekelijks, maandelijks |
| **Geen dag-weergave** — alleen maand en week | 🟢 Laag | Day view met uur-slots |
| **Geen reminders/notificaties** — geen waarschuwing voor deadlines | 🟡 Midden | Email/in-app reminder X dagen voor deadline |
| **Geen team calendar** — kan niet zien wie wat doet | 🟢 Laag | Multi-user kalender view (relevant bij groei) |

**Prioriteit:** 🟡 MIDDEN — Agenda is functioneel maar te passief. Een read-only kalender is een gemiste kans.
**Geschatte impact:** Middelgroot. Wordt dagelijks gebruikt.

---

## 8. Workflow & Taken

### Wat we hebben
- Workflow taken per zaak (gekoppeld aan status transities)
- Automatische taak-aanmaak bij statuswijziging (via workflow rules + scheduler)
- Taken met due date, type, status (pending/in_progress/completed/skipped)
- Taken CRUD: aanmaken, bewerken, verwijderen, status updaten
- Verjaring bewaking (limitation period tracking, automatische check)
- Workflow regels configureerbaar per zaaktype (admin)
- Workflow statuses en transities configureerbaar (admin)
- **Backend heeft `my-tasks` endpoint** (`/api/dashboard/my-tasks`) — persoonlijke takenlijst is klaar in API
- Debtor type awareness (b2b vs b2c transitions)
- Assigned_to filtering op taken

### Wat concurrenten doen
**Clio:** Task management los van zaken mogelijk. Assignable to team members. Priority levels. Recurring tasks. Task templates per matter type. Task lists (checklists). Subtasks. Due date reminders. My Tasks view (persoonlijke takenlijst).

**Smokeball:** Automated workflows — bij zaak aanmaken worden automatisch alle taken voor dat zaaktype aangemaakt met relatieve deadlines. Checklist-stijl afvinken. Progress percentage per zaak.

**Asana/Linear (best-in-class):** Kanban boards. Sprint planning. Dependencies. Custom fields. Automations (if X then create task Y). Templates. Bulk actions. Keyboard shortcuts.

### Wat beter kan
| Issue | Ernst | Oplossing |
|---|---|---|
| **"Mijn taken" bestaat in API maar niet in UI** — `/api/dashboard/my-tasks` is er, geen dedicated pagina | 🔴 Hoog | Centrale "Mijn Taken" pagina: alle taken van alle zaken, gefilterd op gebruiker |
| **Task assignment werkt in backend maar UI is beperkt** — assigned_to_id filter bestaat | 🟡 Midden | Toewijzen aan gebruiker via dropdown, filteren op eigenaar in UI |
| **Geen priority levels** — alle taken zijn gelijk | 🟡 Midden | Urgentie: hoog/midden/laag met visuele indicators |
| **Geen standalone taken** — alleen gekoppeld aan workflow | 🟡 Midden | Ad-hoc taken aanmaken (niet per se workflow-gebonden) |
| **Geen checklist/subtaken** — taken zijn binair (open/dicht) | 🟢 Laag | Subtaken of checklist-items per taak |
| **Geen taak-templates los van workflow** — alles handmatig | 🟢 Laag | Herbruikbare takensets voor veelvoorkomende werkzaamheden |

**Prioriteit:** 🔴 HOOG — "Wat moet ik vandaag doen?" is de kernvraag. Zonder persoonlijke takenlijst is dat onbeantwoord.
**Geschatte impact:** Groot. Dagelijks gebruik, productiviteitskern.

---

## 9. Incasso Module

### Wat we hebben
- Pipeline dashboard met fases (buitengerechtelijk → gerechtelijk → executie)
- Wettelijke rente berekening (automatisch, conform wettelijke tarieven, compound interest)
- WIK-staffel/BIK berekening (buitengerechtelijke incassokosten, met/zonder BTW)
- Art. 6:44 BW betalingsimputatie (kosten → rente → hoofdsom)
- Incasso workflow (aanmaning → sommatie → dagvaarding → vonnis → executie)
- Automatische deadlines per fase
- Incasso-specifieke documenten (aanmaningen, sommaties)
- Module is togglebaar (aan/uit per tenant)
- **Claims beheer:** Meerdere vorderingen per zaak (CRUD)
- **Betalingen registratie:** Betalingen per zaak met tracking
- **Betalingsregelingen:** Arrangements aanmaken en beheren
- **Derdengelden:** Aparte module voor derdengelden-tracking met saldo-overzicht
- **Financieel overzicht:** Complete financial summary per zaak (claims + rente + BIK + betalingen)
- **Historische rentetarieven:** Reference data voor wettelijke rente per periode

### Wat concurrenten doen
**Basenet (marktleider incasso NL):** Complete incasso-suite: batch import debiteurs, geautomatiseerde aanmaningscyclus, koppeling met deurwaarders, KvK-integratie, BKR check, faillissementscheck, bulk verwerking honderden dossiers tegelijk. Dashboard met recovery rates, success percentages, gemiddelde doorlooptijd.

**Urios/CaseManager:** Gespecialiseerde incassosoftware met bank-koppeling (automatisch betalingen matchen), debiteur communicatiehistorie, SMS/email templates per fase, bulk processing, export naar deurwaarder, Centraal Register Incasso.

### Wat beter kan
| Issue | Ernst | Oplossing |
|---|---|---|
| **Geen batch processing** — één zaak per keer | 🟡 Midden | Bulk import debiteurs, bulk status update |
| **Geen betalingsmatching** — handmatig markeren als betaald | 🟡 Midden | Bank CSV import, automatisch matchen op referentie |
| **Geen recovery rate KPI's** — geen inzicht in succes | 🟡 Midden | Dashboard: % geïncasseerd, gemiddelde doorlooptijd, success rate |
| **Geen communicatiehistorie per debiteur** — geen log | 🟢 Laag | Log van alle communicatie (brieven, calls, emails) |
| **Geen deurwaarderskoppeling** — handmatig overdragen | 🟢 Laag | Export formaat voor deurwaarders |
| **Geen automatische aanmaningscyclus** — handmatig starten | 🟡 Midden | Auto-escalatie: na X dagen zonder betaling → volgende fase |

**Prioriteit:** 🟡 MIDDEN — De basis is goed (rente, WIK, art. 6:44). Verbeteringen zijn efficiency-wins, niet dealbreakers.
**Geschatte impact:** Middelgroot. Vooral relevant bij groter volume.

---

## 10. WWFT/KYC Module

### Wat we hebben
- Cliëntidentificatie (naam, ID type, ID nummer, geboortedatum, nationaliteit)
- UBO registratie (naam, ownership percentage, verificatie)
- PEP controle (ja/nee + beschrijving)
- Sanctiecontrole (ja/nee + beschrijving)
- Risicoclassificatie (laag/midden/hoog)
- Review scheduling (volgende review datum)
- KYC status per contact (compliant, needs_review, overdue, not_started)
- Dashboard widget met KYC waarschuwingen
- Module is togglebaar

### Wat concurrenten doen
**Dedicated WWFT tools (CDD Manager, Scopus):** Automatische PEP/sanctie screening via externe databases (EU, UN, OFAC sanctielijsten). Automatische KvK/handelsregister check. UBO register koppeling. Document upload voor ID kopieën. Audit trail (wie heeft wat wanneer gecontroleerd). Automated periodic review reminders. Risk scoring met gewogen factoren. Compliance reporting voor toezichthouder.

**LegalSense WWFT:** Geïntegreerd in cliënt-intake. Verplichte velden voordat zaak geopend kan worden. Template voor cliëntprofiel. Documentopslag voor ID kopieën.

### Wat beter kan
| Issue | Ernst | Oplossing |
|---|---|---|
| **Geen document upload voor ID** — alleen tekstvelden | 🟡 Midden | Upload zone voor paspoort/ID kopie, opslaan per verificatie |
| **Geen automatische screening** — handmatige PEP/sanctie check | 🟡 Midden | API integratie met sanctielijst-provider (OpenSanctions, etc.) |
| **Geen audit trail** — geen log van wie wat gecontroleerd heeft | 🟡 Midden | Elke wijziging loggen met timestamp + gebruiker |
| **Geen verplichte KYC voor zaakopening** — soft warning only | 🟡 Midden | Configureerbaar: blokkeer zaakopening bij onvolledige KYC |
| **Geen compliance report** — geen export voor toezichthouder | 🟢 Laag | PDF rapport per cliënt met alle KYC gegevens |
| **Geen KvK/handelsregister koppeling** — handmatig invullen | 🟢 Laag | KvK API voor automatisch bedrijfsgegevens ophalen |

**Prioriteit:** 🟡 MIDDEN — De basis staat, maar zonder automatische screening en audit trail is het meer een checklist dan echte compliance.
**Geschatte impact:** Middelgroot. Compliance-risico bij ontbrekende audit trail.

---

## 11. Instellingen

### Wat we hebben
- Kantoorgegevens bewerken (naam, KvK, BTW, adres, IBAN, etc.)
- Module beheer (incasso, tijdschrijven, facturatie, wwft aan/uit)
- Basis tenant settings

### Wat concurrenten doen
**Clio:** Uitgebreide settings: firm profile, billing settings (rates, rounding, invoice templates), user management (roles, permissions), integrations marketplace (100+ apps), email settings, calendar sync, security (2FA, SSO), custom fields management, workflow automation builder, notification preferences.

**HubSpot:** Settings als eigen hub: account defaults, users & teams, integrations, properties (custom fields), notifications, security, data management, import/export.

### Wat beter kan
| Issue | Ernst | Oplossing |
|---|---|---|
| **Geen gebruikersbeheer** — single user, geen team support | 🔴 Hoog | Gebruikers CRUD, rollen (admin/advocaat/secretaresse) |
| **Geen uurtarief configuratie** — niet per gebruiker/zaaktype instelbaar | 🟡 Midden | Default uurtarief, per-gebruiker tarieven, per-zaaktype |
| **Geen notificatie-instellingen** — geen controle over alerts | 🟡 Midden | Per-notificatietype aan/uit, email vs. in-app |
| **Geen factuurtemplates beheer** — hardcoded layout | 🟡 Midden | Template customization: logo, kleuren, voettekst |
| **Geen integrations pagina** — geen koppelingen zichtbaar | 🟢 Laag | Overzicht van beschikbare/actieve integraties |
| **Geen backup/export** — geen data portabiliteit | 🟢 Laag | Full data export (JSON/CSV) |

**Prioriteit:** 🔴 HOOG (gebruikersbeheer) — Multi-user is essentieel voor elk kantoor met meer dan 1 persoon.
**Geschatte impact:** Groot. Blocker voor kantoren met meerdere medewerkers.

---

## 12. Navigatie & Algemene UX

### Wat we hebben
- Sidebar navigatie met collapse
- Breadcrumbs (beperkt)
- Responsief design
- Nederlandse UI
- Loading states en empty states
- Toast notifications

### Wat concurrenten doen
**Clio:** Global search (Cmd+K) — zoek in zaken, contacten, documenten, alles. Recent items lijst. Keyboard shortcuts voor navigatie. Notification center (bell icon). Help/support widget.

**Linear (best-in-class):** Command palette (Cmd+K) voor ALLES. Keyboard-first design. Breadcrumbs met dropdowns. Bulk selection met Shift+click. Undo voor destructieve acties. Focus modes. Compact/comfortable view toggle.

**HubSpot:** Global search prominent. Recent items. Notification center. User preferences. Quick create button (+) voor elk object type.

### Wat beter kan
| Issue | Ernst | Oplossing |
|---|---|---|
| **Geen global search (Cmd+K)** — moet per pagina zoeken | 🔴 Hoog | Command palette: zoek zaken, contacten, facturen vanuit elke pagina |
| **Geen notification center** — geen centraal overzicht van alerts | 🟡 Midden | Bell icon met dropdown: deadlines, taken, KYC reviews |
| **Geen keyboard shortcuts** — alles met muis | 🟡 Midden | Sneltoetsen voor veelgebruikte acties |
| **Geen undo voor acties** — verwijderen is definitief | 🟡 Midden | Undo toast: "Verwijderd. Ongedaan maken?" |
| **Geen bulk acties** — alles één voor één | 🟡 Midden | Multi-select met checkboxes, bulk status change |
| **Geen recent items** — geen "laatst bekeken" | 🟢 Laag | Recente zaken/contacten in sidebar of search |
| **Geen dark mode** — alleen licht thema | 🟢 Laag | Theme toggle (niet prioriteit, maar verwacht door moderne gebruikers) |

**Prioriteit:** 🔴 HOOG (global search) — Cmd+K is dé standaard in moderne SaaS. Zonder dit voelt de app gedateerd.
**Geschatte impact:** Groot. Snelheid van dagelijks werk.

---

## 13. Authenticatie & Login

### Wat we hebben
- Email + wachtwoord login
- JWT tokens (access + refresh)
- Tenant-scoped authentication
- User registratie (admin only)
- Wachtwoord wijzigen (PUT + POST endpoints)
- User profiel updaten (naam)
- Tenant details ophalen en updaten

### Wat beter kan
| Issue | Ernst | Oplossing |
|---|---|---|
| **Geen 2FA** — alleen wachtwoord | 🟡 Midden | TOTP (Google Authenticator) of SMS 2FA |
| **Geen wachtwoord vergeten flow** — moet admin vragen | 🔴 Hoog | "Wachtwoord vergeten" email flow |
| **Geen session management** — kan niet zien waar je ingelogd bent | 🟢 Laag | Actieve sessies overzicht |
| **Geen SSO** — geen Microsoft/Google login | 🟢 Laag | OAuth2 met Azure AD (veel advocatenkantoren gebruiken Microsoft) |

**Prioriteit:** 🔴 HOOG (wachtwoord vergeten) — Basis verwachting van elk product.
**Geschatte impact:** Klein qua dagelijks gebruik, groot qua professionaliteit.

---

## Prioriteitenmatrix

### 🔴 Kritiek (moet eerst)
1. **Timer voor tijdschrijven** — #1 verwachte feature, elke concurrent heeft dit
2. **Global search (Cmd+K)** — moderne standaard, dagelijks gebruikt
3. **Zaakdetail met tabs** — kern van de applicatie, nu te plat

### 🔴 Hoog (kort daarna)
4. **Dashboard personalisatie + grafieken** — eerste indruk
5. **"Mijn taken" pagina** — "wat moet ik vandaag doen?"
6. **Betalingstracking op facturen** — directe financiële impact
7. **Activity timeline op zaak + contact** — context en geschiedenis
8. **Wachtwoord vergeten flow** — basis verwachting
9. **Gebruikersbeheer** — blocker voor multi-user kantoren

### 🟡 Midden (fase 2)
10. Quick actions vanuit zaak (uren loggen, document maken)
11. Facturatieverbeteringen (herinneringen, aging report, preview)
12. Calendar improvements (event aanmaken, externe sync)
13. Notificatie center
14. Weekly timesheet view
15. KYC audit trail + document upload
16. Incasso batch processing

### 🟢 Laag (fase 3, nice-to-have)
17. Kanban board view voor zaken
18. E-signature integratie
19. Online betaling (Mollie)
20. Dark mode
21. Keyboard shortcuts
22. Data import/export
23. Accounting software koppeling

---

## 🔑 Belangrijke Observatie: Backend vs. Frontend Gap

Een rode draad door deze review is dat de **backend vaak verder is dan de frontend**. Dit is goed nieuws — het betekent dat veel verbeteringen puur frontend-werk zijn:

| Feature | Backend status | Frontend status | Gap |
|---|---|---|---|
| Mijn Taken | ✅ `/api/dashboard/my-tasks` endpoint | ❌ Geen pagina | **Alleen frontend nodig** |
| Activity timeline | ✅ `/api/cases/{id}/activities` CRUD | ⚠️ Basis weergave | Frontend verbeteren |
| Contact-bedrijf links | ✅ `/api/relations/links` CRUD | ❌ Niet zichtbaar in UI | **Alleen frontend nodig** |
| Timer widget | ✅ `/api/time-entries/my/today` | ❌ Geen timer component | **Alleen frontend nodig** |
| Case parties (rollen) | ✅ `/api/cases/{id}/parties` CRUD | ⚠️ Basis weergave | Frontend verbeteren |
| Onkosten | ✅ `/api/expenses` full CRUD | ⚠️ Beperkt zichtbaar | Frontend verbeteren |
| Dashboard KPI's | ✅ `/api/dashboard/summary` + recent-activity | ⚠️ Kale getallen | Charts/grafieken toevoegen |
| Derdengelden | ✅ Complete API met saldo | ⚠️ Beperkt zichtbaar | Frontend verbeteren |
| Financieel overzicht | ✅ `/api/cases/{id}/financial-summary` | ⚠️ Basis weergave | Rijker presenteren |

**Conclusie:** ~40% van de "verbeteringen" uit dit rapport vereist GEEN backend-werk. De API's zijn er al. Dit versnelt de roadmap significant.

---

## Conclusie

Luxis heeft een **sterke technische fundering** en de juiste feature-set voor een PMS. Maar het verschil tussen "features hebben" en "een product zijn" zit in de UX details:

- **Clio** voelt als een mature product omdat elke feature geoptimaliseerd is voor minimale clicks en maximale context.
- **Luxis** voelt als een capabel prototype omdat de features er zijn maar de workflow-optimalisatie ontbreekt.

**Het goede nieuws:** De backend is sterker dan de frontend laat zien. Veel verbeteringen zijn puur UI-werk, geen nieuwe API's nodig.

De **drie dingen die het snelst verschil maken**:
1. 🕐 **Timer** — maakt tijdschrijven van een chore naar een seamless habit (backend is klaar!)
2. 🔍 **Cmd+K search** — maakt de hele app sneller en professioneler
3. 📋 **Zaakdetail tabs + timeline** — maakt dossierbeheer van "info bekijken" naar "vanuit zaak werken" (activities API is klaar!)

Deze drie samen transformeren Luxis van een databank naar een werkomgeving.

---

## Bijlage: API Coverage

**Totaal endpoints:** 110+
**Totaal routers:** 13 (auth, relations, cases, time-entries, invoices, expenses, documents, workflow, KYC, collections, dashboard, settings, health)
**Backend maturity:** ~70% (solide CRUD, goede business logic, correcte financial calculations)
**Frontend maturity:** ~40% (features tonen data maar missen workflow-optimalisatie en UX polish)
