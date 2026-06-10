# Connectie-audit Luxis — is alles aan elkaar verbonden?

*Sessie 158 (10 juni 2026, Fable). Vraag: klik je op het ene, kom je dan logisch bij het andere? Volledige link-graaf (alle `href`/`router.push` over 26 routes) + zes gebruikersreizen nagetrokken in de code. Statische analyse: "bestaat de verbinding" is hier objectief vaststelbaar.*

**NB:** PowerShell-glob slaat `[id]`-mappen over (bracket-globbing) — link-extractie daarom met ripgrep per map gedaan. Raw graaf: `.audit/linkgraph-raw.txt` (+ aparte `[id]`-greps).

---

## 1. Eindoordeel

**De kern is een echt web, geen eilanden.** Het dossier (`/zaken/[id]`) is de hub met 11 tabs; álle satellieten (agenda, taken, mail, documenten, bankimport, derdengelden, uren, facturen, follow-up, intake-resultaat, notificaties) linken ernaartoe, vaak met tab-deep-links. Dashboard is een volwaardige cockpit (±25 uitgaande links). Relaties↔dossiers werken in beide richtingen inclusief voor-ingevulde "nieuw dossier voor deze klant". Facturen↔dossier↔relatie idem.

**Maar:** 14 verbindingsgaten, waarvan 3 de belofte "het product werkt vanzelf" echt breken. Patroon: de *administratie* is af (alles wordt correct opgeslagen en getoond), de *signalering* niet (het systeem trekt zelden zelf aan je mouw). Luxis toont; het stuurt nog niet.

## 2. Wat aantoonbaar goed verbonden is

| Verbinding | Bewijs |
|---|---|
| Dossier-hub: 11 tabs (overzicht/taken/uren/vorderingen/betalingen/staphistorie/facturen/documenten/correspondentie/activiteiten/partijen) + `?tab=`-deep-links + sneltoetsen 1-9/t/n/d/e/f | `zaken/[id]/page.tsx:371-483` |
| Alles → dossier: agenda, taken, mail, documenten (`?tab=documenten`), bankimport, derdengelden (`?tab=betalingen`), uren, followup, incasso, dashboard, notificaties, zoekresultaten | link-graaf |
| CaseActionFeed → juiste tab per itemtype (taken/correspondentie/staphistorie) | `CaseActionFeed.tsx:347-425` |
| Relatie → dossiers + "nieuw dossier" voor-ingevuld (client/tegenpartij) | `LinkedCasesSection.tsx:37-105` |
| Dossier → factuur: 3 ingangen (header-knop, facturen-tab, provisie-sectie `&provisie=true`) → `facturen/nieuw?case_id=` met IncassoKostenPanel | DossierHeader:535 e.a. |
| Factuur → dossier, relatie, gekoppelde credit-nota's, origineel | `facturen/[id]:651-1232` |
| Debiteuren-tab → gefilterde facturenlijst per klant | `facturen/page.tsx:692` |
| Intake-resultaat → aangemaakt dossier + relatie | `intake/[id]:413-421` |
| Timer (overal) → uren; uren → dossier; dashboard → uren per dag | floating-timer:395 |
| Ctrl+K command palette: zoeken (cases/contacts/documents) + quick actions | command-palette.tsx |
| Breadcrumbs met dossiernummer-labels | useBreadcrumbs |

## 3. De gaten (CONN-1 t/m CONN-14)

### Zwaar — breken de keten

**CONN-1 · Eigen facturen kennen geen opvolging.** Factuurstatus `overdue` wordt **nergens** gezet: geen scheduler-job (scheduler doet alleen taken/agenda/dossier-deadlines), geen UI-actie, niets. De status bestaat alleen in het statusdiagram (`invoices/service.py:100`). Gevolgen: lijstfilter "te laat" levert altijd 0; geen notificatie of taak wanneer een declaratie vervalt; de keten *factuur verstuurd → vervalt → signaal → herinnering naar cliënt* stopt na stap 1. Aging op de debiteuren-tab werkt wél (rekent op `due_date`, los van status) — maar je moet er zelf heen. Een incassokantoor dat andermans vorderingen bewaakt maar de eigen declaraties niet: pijnlijk. *Fix-richting: dagelijkse job `sent→overdue` na vervaldatum + notificatie + (later) herinneringsflow; rij-badge "te laat" in lijst.*

**CONN-2 · Vier-ogen wacht in stilte.** `pending_approval` trust-transacties genereren geen notificatie en geen taak (geen enkele `create_notification`-aanroep in trust_funds; notificatietypes zijn alleen email_received / ai_draft_ready / classification_done / deadline_overdue). De goedkeurder ziet het pas als hij zelf de derdengelden-pagina of de KPI opent. Met straks 2+ gebruikers (vier-ogen verplicht, H14): uitbetalingen blijven onzichtbaar hangen → talm-risico Voda 6.19. *Fix-richting: notificatie + taak voor de aangewezen goedkeurder bij elke pending transactie; notificatie-link mét tab-context (zie CONN-5).*

**CONN-3 · Intake-wachtrij is onvindbaar.** `/intake` staat niet in de sidebar en niet in de command palette. Enige paden: een taak-item op `/taken` (`taken/page.tsx:439`) — als dat er niet (meer) ligt, bestaat de pagina voor de gebruiker niet. De AI vult deze wachtrij (orchestrator); reviewen vereist de URL kennen. *Fix-richting: sidebar-item (sectie Beheer) met pending-badge, zoals Bankimport al heeft.*

### Middel — keten hapert of kost zoekwerk

**CONN-4 · Follow-up Advisor half aangesloten.** `/followup` ("Aanbevelingen voor dossiers die actie nodig hebben" — nota bene de *wat-nu-motor* van incasso) is alleen bereikbaar via één link onderaan het dashboard. Niet in sidebar, niet in palette. *Fix: sidebar-item onder Incasso, badge met pending-count (badge-infra bestaat: `ai-pending` is al gedefinieerd in NavItem maar ongebruikt!).*

**CONN-5 · Notificaties landen zonder context.** Alle notificaties linken kaal naar `/zaken/{id}` (`app-header.tsx:234`). email_received hoort op `?tab=correspondentie`, deadline op `?tab=taken` te landen. Nu: klik → zelf de juiste tab zoeken. Backend-notificatie heeft geen tab/url-veld. *Fix: `link_url`-veld op notificatie of type→tab-mapping in de header.*

**CONN-6 · `?tab=betalingen` breekt op niet-incasso dossiers.** Derdengelden-pagina linkt altijd `/zaken/{id}?tab=betalingen` (`derdengelden/page.tsx:845`), maar die tab bestaat alleen voor `case_type === "incasso"` (`zaken/[id]/page.tsx:371-375`). Trust-transacties kunnen op élk dossier. Niet-incasso → `activeTab="betalingen"` matcht geen enkele render-conditie → **lege pagina onder de tabbar**. Zelfde risico: `tab=staphistorie`/`tab=vorderingen` deep-links. *Fix: onbekende/ontoegestane tab → fallback "overzicht" (één regel guard bij `tabFromUrl`).*

**CONN-7 · Afwikkelroute heeft geen gids** (= FIN-2-rest, hier de navigatiekant). Dossier op "betaald" → niets verwijst naar de vervolgketen verreken → uitbetaal → factureer → sluit. De losse knoppen bestaan op drie verschillende tabs; de archive-guard (S158) vangt alleen het vergeten af. *Fix: afwikkel-wizard of minstens een actiebanner op betaalde dossiers met trust-saldo.*

**CONN-8 · Rapportages is het enige doodlopende scherm.** Nul uitgaande links; KPI's en grafieken zonder drill-down, terwijl het dashboard overal wél doorklikt. *Fix: segmenten/staven linken naar gefilterde lijsten (`/zaken?status=`-patroon bestaat al op het dashboard).*

### Klein — polish

**CONN-9** · Relatie-detail toont geen facturen/openstaand-saldo van die klant; pad "relatie → haar facturen" ontbreekt (alleen via debiteuren-tab tenant-breed). Eén link `facturen?contact_id=` volstaat (patroon bestaat al).
**CONN-10** · Uren-pagina heeft geen "factureer deze uren"-CTA — alleen het omgekeerde pad (import vanuit facturen/nieuw). Knop → `facturen/nieuw?case_id=` met voorgeselecteerde uren.
**CONN-11** · Zoeken (Ctrl+K) dekt cases/contacts/documents — **geen facturen, geen e-mails** (`search/service.py:56-133`). Factuurnummer F2026-xxxx intypen → niets.
**CONN-12** · Palette quick-actions missen: nieuwe factuur, agenda, incasso, bankimport, intake.
**CONN-13** · Factuur-detail toont geen Exact-sync-status (ExactSyncLog bestaat) — pas relevant na Exact-activatie.
**CONN-14** · Sidebar-badge `ai-pending` gedefinieerd maar aan geen item gekoppeld (hangt samen met CONN-3/4).

## 4. Per journey samengevat

| Journey | Status | Breekpunten |
|---|---|---|
| 1. Intake → relatie → dossier | ◐ | CONN-3 (wachtrij onvindbaar); rest compleet incl. terug-links |
| 2. Pipeline → brieven → opvolging | ◐ | CONN-4 (advisor verstopt); pipeline↔dossier↔drafts zelf goed |
| 3. Geld binnen → trust → dossier | ◐ | CONN-2 (vier-ogen stil), CONN-6 (tab-breuk); boekingen zelf sinds FIN-1 consistent |
| 4. Factureren → betaald → Exact | ✗→◐ | CONN-1 (geen opvolging eigen facturen), CONN-13; maken/versturen/verrekening compleet |
| 5. Uren/agenda/taken/mail/docs | ✓ | alleen CONN-5/10/11 polish; alle satellieten linken naar hub |
| 6. Afsluiten → rapportage | ◐ | CONN-7 (geen gids), CONN-8 (doodlopend); archive-guard ✓ |

## 5. Aanbevolen volgorde (alles Opus-uitvoerbaar)

1. **CONN-6** — one-line fallback, voorkomt lege pagina (5 min).
2. **CONN-1** — overdue-job + notificatie + lijstbadge (½ sessie). Grootste functionele gat.
3. **CONN-2** — approval-notificatie/taak (klein, wordt urgent bij 2e gebruiker).
4. **CONN-3 + CONN-4 + CONN-14** — twee sidebar-items + badges (klein, samen).
5. **CONN-5** — notificatie-tab-context (klein).
6. **CONN-7** — afwikkel-wizard (eigen sessie, ontwerpkeuze nodig — zie FIN-2).
7. **CONN-8 t/m 12** — polish-batch (½ sessie).
8. Daarna: **E2E-suite** die de journeys vastzet (aparte opdracht; fundament `frontend/e2e/` bestaat).

## Verwante documenten
- `docs/research/financiele-samenhang.md` — FIN-1 t/m FIN-7 (boekingslogica; dit rapport = navigatie/signalering)
- `.audit/linkgraph-raw.txt` — ruwe link-graaf
