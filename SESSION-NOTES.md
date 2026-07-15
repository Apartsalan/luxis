# Sessie Notities — Luxis

<!-- Kop = exact deze 4 regels, elk max 1-2 zinnen. Detail hoort in de sessie-entry. -->
<!-- Max 10 sessie-entries in dit bestand; oudere → docs/archief/SESSION-ARCHIVE.md (regels: /sessie-einde). -->
**Laatst bijgewerkt:** 15 juli 2026 (S216, Opus-bouw + Fable-review — dossierpagina-verbouwing blok 1-3 LIVE, alles visueel geverifieerd op prod).
**Laatste feature/fix:** Dossierpagina van 11/8 → 7/6 tabbladen, compacte kop met geldstrook (incl. Openstaand), één notitievenster (cursor-bug gefixt), BaseNet-waarschuwingsbalk, gewone zaak ingericht (agenda-blok + volgende-stap + afsluitknop). Zie entry S216.
**Openstaand:** KvK-prod-sleutel (~16 juli) → rechtsvorm-backfill (gemeten: 726 relaties, ~€14,50/run — zie PROMPT-S215); dossierpolish klein (anker-subnav Financieel, geldstrook-uitbreiding gewone zaak).
**Volgende sessie:** S217 (`docs/sessions/PROMPT-S217.md`, Opus): KvK-backfill zodra de sleutel binnen is (heeft voorrang), anders dossierpolish.

## Sessie 216 (15 juli 2026, Opus-bouw + Fable-review — dossierpagina-verbouwing blok 1-3, LIVE)

### Samenvatting
De dossierpagina (`zaken/[id]`) was onoverzichtelijk: 11 tabbladen (incasso) / 8 (gewone zaak),
een kop die het hele eerste scherm vulde, alles dubbel (partijen op 4 plekken), 3 losse "notitie"-
begrippen. Onderzoek (code + prod-DB-meting per tabblad + visuele doorklik + concurrentiescan
Clio/Smokeball) → plan `docs/plans/PLAN-dossierpagina.md` (4 harde eisen Arsalan: alles klikbaar
blijft klikbaar; één stijl/geraamte beide types; niets onzichtbaar = inklapbaar; Uren blijft tab).
Drie bouwblokken, elk gebouwd → getest (tsc) → gedeployd → visueel geverifieerd op prod, daarna
Fable-review met 2 must-fixes. Alle testzaken/testafspraken opgeruimd.

- **Blok 1 (`4dba5b3`+`4ef4c0a`):** 11/8 → 7/6 tabbladen (tabbalk past nu; was 5 buiten beeld).
  Financieel bundelt vorderingen+betalingen+regeling+derdengelden; lege regeling/derdengelden
  inklapbaar. Tijdlijn = oud Activiteiten + inklapbare stap-historie. Taken + conflictbanner naar
  Overzicht. Provisie naar Facturen. PartijenTab verwijderd. Vertaaltabel oude ?tab=-links.
- **Blok 2 (`3a927fc`):** kop 4 statkaarten → geldstrook Hoofdsom·Betaald·**Openstaand** (ontbrak).
  Notitie+Telefoonnotitie → één `NoteDialog` met autoFocus (**cursor-bug gefixt**, sneltoets n).
  BaseNet-waarschuwing (`[BaseNet-waarschuwing]`) → oranje balk bovenaan Overzicht. Zijbalk
  type-afhankelijk (Debiteur/Rente alleen incasso = advies-lek dicht; OHW alleen bij uren>0).
- **Blok 3 (`ea07c9a`):** agenda-blok op Overzicht (`useCaseEvents` → `/api/calendar/events?case_id`,
  komende afspraken, klikbaar). Kop gewone zaak: "Volgende stap" (eerstvolgende taak+deadline) i.p.v.
  incasso-fasebalk + **afsluitknop** (ontbrak op niet-incasso). Geldstrook gewone zaak: OHW+budget.
- **Fable-review (`ca33ba9`):** 2 must-fixes — (1) overige partijen (rol+ref) weer zichtbaar in
  Partijen-sectie Overzicht (waren met het opgeheven tabblad onzichtbaar geworden); (2) e2e
  bijgewerkt (zaken Z5 → 6 tabs/role=tab, regression C19 → Financieel-tab). Meldingen-links,
  heropenen-transitie, sneltoetsen aangevallen en overeind.

### Gewijzigde bestanden
Frontend `zaken/[id]/`: `page.tsx`, `components/DossierHeader.tsx`, `DossierSidebar.tsx`, `DetailsTab.tsx`,
`incasso/VorderingenFinancieelTab.tsx` + `BetalingenDerdengeldenTab.tsx`; nieuw `CaseConflictBanner.tsx`,
`BasenetWarningBanner.tsx`, `NoteDialog.tsx`, `AgendaBlok.tsx`; verwijderd `PartijenTab.tsx`.
`hooks/use-calendar-events.ts` (useCaseEvents). e2e `zaken.spec.ts` + `regression.spec.ts`.
8 commits, alle frontend-deploys via SSH. Geen backend/migratie. Plan + prompt bijgewerkt.

### Bekende issues / bewust niet gedaan
- Anker-subnav bovenin Financieel (klein; secties al gegroepeerd+inklapbaar).
- Geldstrook gewone zaak kan later uitgebreid met ongefactureerd + openstaande facturen (bronnen bestaan).
- Meldingslink naar stap-historie landt op Tijdlijn met historie ingeklapt (1 klik extra; bewust).
- Taken-blok toont op elk dossier een lege-staat als er geen taken zijn (3/608 hebben taken).

### Volgende sessie
S217: KvK-rechtsvorm-backfill zodra Arsalan de sleutel meldt (voorrang; gemeten 726 relaties/~€14,50 per
run — zie PROMPT-S215 STAND), anders dossierpolish (anker-subnav + geldstrook-uitbreiding). Prompt:
`docs/sessions/PROMPT-S217.md`.

## Sessie 214 (14 juli 2026, Opus-bouw + Fable-matching — S201 kantoorfacturen-import, LIVE)

### Samenvatting
De 439 definitieve BaseNet-kantoorfacturen (Lisanne's eigen omzet) staan op prod: 630 regels,
325 betalingen (€248.364,17), 344 betaald/86 te laat/9 verzonden, 137 aan hun IN-dossier,
302 D-facturen bewust contact-only (projectcode reist mee in de marker), 23 creditnota's aan hun
origineel. Bruto €302.750,39, openstaand €72.762,09 — elke som onafhankelijk nageteld in de
prod-database én via de API-rooktest (debiteuren €78.469,57 = exact de 88 open gewone facturen).

**Stap 0 vooraf (eerlijkheidsvoorwaarden, migratie `s214_payment_date_null`):**
`invoice_payments.payment_date` nullable → UI toont "Datum onbekend" (handmatige invoer blijft
datum vereisen); betaalmethode `unknown`/"Onbekend (BaseNet)"; creditnota toont afwikkelstatus
i.p.v. valse "Volledig betaald" (guard in `get_payment_summary` + frontend verbergt betaalbalk).

**Recept getoetst aan de bron — 3 veldniveau-fouten gevonden en gecorrigeerd** (vastgelegd in
`S201-facturatie-recept.md` §0): creditnota's hebben géén `invduedate` (→ terugval factuurdatum);
Mollie-betaaldatums komen uit `Payment.payment_status=4` + `insertdate` (niet uit onbestaande
`paidAt`-velden); dossierkoppeling loopt via kop-veld `invpcode` (niet "inccode").
Derdengelden-herkenning = product 100013 ("Verrekening incassodossiers") + expliciete lijst
{100242, 100363} — een `bedrag<0`-regel vangt 109 facturen en is fout.

**Fable-matchingronde ving 3 gaten:** paid_date op de 20 Mollie-bevestigde facturen,
memoriaal-boekingsdatum als gelabelde metadata op de 305 "Datum onbekend"-betalingen (11 liggen
vóór de factuurdatum — dáárom geen betaaldatum), ruwe bronstatus op de 3 nul-facturen. Prod vooraf
read-only nageteld: 52/52 relaties + 127/127 IN-dossiers matchen deterministisch.

### Gewijzigde bestanden
- `scripts/basenet/import_invoices.py` (nieuw) — classificatie op gemeten velden, harde poorten,
  weigert schrijven als doeltabel niet leeg is (dubbele import onmogelijk).
- Backend: `invoices/models.py`, `schemas.py`, `invoice_payment_service.py`,
  migratie `s214_payment_date_null.py`; tests `test_import_invoices.py` (nieuw, 4) +
  `test_invoice_payments.py` (+2, totaal 22).
- Frontend: `facturen/[id]/page.tsx` (creditnota-afwikkelbalk, "Datum onbekend", methode-label),
  `hooks/use-invoices.ts`. 4 commits (`5920d1b`…), deploy backend+frontend+migratie.

### Verificatie
Dry-run op prod: álle poorten groen (439/7/12/19/90, 0 onopgelost, 137 IN, alle euro-sommen exact,
regelformules 630/630, factuur 100532 bewaart €1.631,74). Execute → natelling in DB + API-login-
rooktest groen. 24 tests groen, ruff schoon, tsc schoon. Mailslot niet aangeraakt, niets verstuurd.

### Bekende issues
- **7 Mollie/kop-conflicten** (€10.854,66; nrs 100314/100316/100321/100332/100342/100441/100533):
  Mollie zegt betaald, kop zegt open — per factuur oordeel Lisanne/boekhouding, daarna evt. na-import.
- 12 WIP/concepten (€13.013,07) + 31 losse conceptregels (€6.779,81): handmatig beoordelen (lijst
  in recept §1); 2 negatieve verrekenposten (100242 −€217,80 / 100363 −€735,00) bewust buiten.
- 302 D-facturen koppelen pas aan een dossier na de latere D-dossier-import (projectcode in marker).
- KvK-sleutel nog niet binnen → S214-hoofdtaak (rechtsvorm-backfill) doorgeschoven naar S215.

### Volgende sessie
S215: KvK-rechtsvorm-backfill zodra Arsalan de echte sleutel meldt (env op VPS → droogloop →
akkoord → run → natelling → meten hoeveel BV's geen rentebijlage meer krijgen).
Prompt: `docs/sessions/PROMPT-S215.md`.

## Sessie 213 (14 juli 2026, Opus-bouw + Fable-review/uitvoer — Facturen-menu 2 tabs + PDF-koppeling, LIVE)

### Samenvatting
KvK-sleutel nog niet binnen → hoofdtaak geparkeerd; taak 2+3 volledig af.

- **Facturen-menu 3→2 tabs (LIVE, `2a9caa3`).** Debiteuren-tab is nu een *Lijst/Per-klant*-
  weergaveschakelaar bínnen Kantoorfacturen (component verplaatst, niets weggegooid).
  Vorderingen-tab kreeg filters à la `zaken/page.tsx`: opdrachtgever-dropdown (nieuw endpoint
  `GET /api/claims/clients`), lopend/afgesloten, factuurdatum-bereik, wel/geen PDF; sorteerbare
  kolomkoppen (factuurdatum, hoofdsom) + filters/sort/tab in de URL (CONN-8/DF139-patroon).
  Backend `GET /api/claims` uitgebreid (client_id/date_from/date_to/has_file/sort_by/sort_dir +
  `invoice_file_id` in payload). 6 endpoint-tests groen; ruff/tsc/build schoon.
- **Factuur-PDF-koppeling UITGEVOERD (Fable, na "go" Arsalan): 1.357/1.563 vorderingen** hebben
  nu hun factuur-PDF (`scripts/link_invoice_files.py`, 3 treden): 1.306 exacte naam-match +
  35 dubbelen (sha256-bewezen byte-identiek, oudste gekozen) + 16 kopie-achtervoegsel
  (`Factuur_140005__1_.pdf`; 1 = .rtf). Bron eerst gelezen (S180-les): IncassoLine-XML heeft
  géén document-verwijzing → naam-match is echt de enige sleutel. **206 rest terecht niet
  gekoppeld:** 8 kostenpost-regels (Griffierecht/Nakosten/…), ±92 dossiers zonder factuurbestand,
  ±96 ander nummerschema. Tekst-inhoud-matching gemeten maar bewust NIET gebruikt (sommatie/vonnis
  dat het nummer citeert zou vals matchen).
- **Natelling (onafhankelijk, SQL):** 1.357 gevuld / 1.563 totaal; som hoofdsom onveranderd
  €3.142.934,72; 0 kruis-dossier, 0 kruis-tenant, 0 dode verwijzingen. End-to-end: paperclip-klik
  op prod → popup `application/pdf`.
- **Klik-verificatie prod (Playwright, échte kliks):** tab-wissel, sorteerklik (desc top =
  €142.961,50 → asc), Per-klant-schakelaar, paperclip → PDF. De eerdere "kliks doen niets" was
  het claude-in-chrome-tool, niet de code (stale Playwright-lockfile opgeruimd).

### Gewijzigde bestanden
- Backend: `collections/schemas.py` + `service.py` + `router.py` (filters/sort/clients),
  `tests/test_claims_overview.py` (6), `scripts/link_invoice_files.py` (nieuw, 3 treden + self-test).
- Frontend: `facturen/page.tsx` (2 tabs + schakelaar + filters + paperclip), `hooks/use-invoices.ts`.
- Commits `2a9caa3` · `9aea91c` · `ce54eb4` + docs; deploy backend+frontend (geen migratie).
- Rapport/bewijs: `docs/sessions/S213-fable-review-brief.md`.

### Bekende issues
- **KvK-rechtsvorm-backfill wacht op de echte sleutel** (~16 juli, Arsalan meldt) → S214.
- 1 gekoppelde vordering verwijst naar een .rtf: verzendpad-bijlage werkt, paperclip-preview
  geeft daar een nette foutmelding (1 record, geaccepteerd).
- Browser-terug binnen een open Vorderingen-tab synct de filter-velden niet live (sortering wél)
  — zelfde huispatroon als de dossierlijst, bewust zo gelaten.
- Dev-omgeving: wachtwoord `seidony@` lokaal op `Devpass-123` gezet (alleen dev, prod ongemoeid).

### Nagekomen (zelfde dag, opdracht Arsalan): Backblaze Class C-cap + oude US-bucket
- **Class C-cap opgelost (`e4ea1c8`, live).** De nachtelijke off-site sync doorzocht de diepe
  `email_attachments`-boom (7.932 bestanden, elk eigen geneste map) zónder `--fast-list` → één
  B2-list per map = duizenden Class C-transacties/nacht, boven de gratis dagcap (2.500). Gemeten:
  maar 93/7.932 bestanden echt nieuw → géén churn, puur de listing. `--fast-list` op alle list-zware
  rclone-stappen (sync + 3 deletes) → hele boom in één gepagineerde lijst. **Bewijs volgt bij de
  03:00-run** (nu niet getest: cap stond op 100%, testen zou meer Class C kosten). Reconcilieerde
  tegelijk de niet-gecommitte VPS-drift (S207-sync-aanpak stond niet in de repo).
- **Oude US-bucket opgeruimd (`d0823d6`).** Arsalan verwijderde de lege Amerikaanse bucket
  `Luxis-backup` (us-east-005, 0 bytes, door niets meer gebruikt — live back-up gaat naar de
  EU-crypt-bucket `luxis-b2-eu:luxis-backup-eu`). Server-kant: `rclone config delete luxis-backup`
  + script-default nu `luxis-backup-eu-crypt`/`backups` (nooit meer per ongeluk naar de VS).

### Volgende sessie
S214 (`docs/sessions/PROMPT-S214.md`): KvK-sleutel → env op VPS → droogloop → akkoord → run →
natelling → meten hoeveel BV's geen rentebijlage meer krijgen. Rest-PDF's (206) alleen op
expliciete vraag (handwerk-lijstje kan uit de dry-run-rapportage).
**Openstaand nachecken (morgen):** back-up-log 03:00 — bevestigen dat het Class C-verbruik laag blijft.

## Sessie 212 (14 juli 2026, Opus-uitvoer — WIK-rentebijlage LIVE + bijlage op resterende verzendpaden + terug-navigatie, LIVE)

### Samenvatting
Drie blokken, elk gebouwd → getest → gedeployd via SSH, met GO van Arsalan op blok 1.

- **Blok 1 — WIK-rentebijlage LIVE.** Tak `s211-wik-rentebijlage` (5 commits) gemerged naar main
  (`0354d5a`, geen botsing — tak raakte de afsluit-docs niet), gedeployd mét migratie
  `s211_contact_legal_form` (3 nullable kolommen op contacts, puur additief). Prod geverifieerd:
  migratie op head, 3 rechtsvorm-kolommen aanwezig, login 200, relatie-detail levert de velden
  (leeg), bewerkweergave toont het rechtsvorm-veld met uitleg. **KvK-sleutel bewust nog leeg
  (slapend)** tot ~16 juli. PROMPT-S207 gearchiveerd (`a3111c7`). Besluit B actief: tot de
  backfill krijgt élke 14-dagenbrief/eerste sommatie de bijlage, óók BV's (GO Arsalan: "kan geen kwaad").
- **Blok 2 — bijlage op de twee resterende verzendpaden** (`612a779`). Gedeelde helper
  `build_rente_bijlage` aangehaakt op (a) het compose/AI-concept-pad (`compose/cases/{id}` → .eml,
  op de plek waar al factuur-PDF's meegaan — Lisanne's meest gebruikte route) en (b) het
  document-verzendpad (`documents/{id}/send`). Beide via een `SimpleNamespace(template_type=...)`
  step-shim; `opposing_party` is `lazy="selectin"` dus geen async-laadrisico. Preview-zinnetje
  in follow-up: "renteoverzicht" i.p.v. "de brief". 4 nieuwe route-tests (bijlage wél/BV niet).
  133 tests groen (`-k kvk/bijlage/compose/followup/document`), ruff schoon, tsc groen.
- **Blok 3 — slimme terug-knop door heel Luxis** (`c577e96` + 2 fixes). Gedeelde `BackButton`:
  `router.back()` naar de pagina van herkomst, met nette terugval op de vaste ouderpagina bij een
  direct bezochte URL. Toegepast op dossier-, relatie-, factuur- en intake-detail + de drie
  nieuw-formulieren; factuurpagina houdt de `?from_case`-terugval. **Twee fixes na live-test
  (fable-diepte):** (1) `history.state.idx` bestaat NIET in Next.js 15 App Router (alleen `__NA`
  + interne tree) → knop viel altijd terug op de vaste ouder; overgestapt op `history.length`.
  (2) kale `history.length>1` was onbetrouwbaar (verse tab kan al op 2 staan → terug naar lege
  pagina) → dashboard-omhulling legt bij binnenkomst één ijkpunt vast (`luxis_entry_history_len`,
  per tab), knop gaat alleen echt terug als de lengte sindsdien is gegroeid.

### Bewijs (Playwright, prod)
incasso→dossier→terug = **incasso** ✓; dossier→relatie→terug = **dossier** ✓; dossier→factuur(nieuw)
→terug = **dossier** ✓; relatielijst→relatie→terug = **relatielijst** ✓ (herkomst beweegt mee);
verse tab rechtstreeks op /zaken/[id]→terug = **/zaken** (terugval, breekt niet) ✓. Rentebijlage:
route-tests bewijzen bijlage wél bij privé aansprakelijk / niet bij BV op beide nieuwe paden.

### Gewijzigde bestanden
- Backend: `email/compose_router.py`, `documents/router.py`, `tests/test_rente_bijlage_verzendpaden.py` (nieuw, 4).
- Frontend: `components/back-button.tsx` (nieuw), `app/(dashboard)/layout.tsx`, `followup/page.tsx`,
  DossierHeader + relaties/[id] + facturen/[id] + facturen/nieuw + zaken/nieuw + relaties/nieuw + intake/[id].
- 5 commits + merge; deploys: alles (blok 1, migratie) → backend+frontend (blok 2) → frontend ×3 (blok 3).

### Fable-review S212 (zelfde dag, model omgezet — 1 must-fix gevonden + LIVE)
De review viel de dragende claims aan. **Must-fix (`498d156`, gedeployd):** de compose-dialoog
stuurde het gekozen sjabloontype alleen mee op de secundaire "Open in Outlook"-knop (.eml);
de PRIMAIRE knop "Versturen" (`/compose/send`) kende geen `template_type` — dus géén
renteoverzicht op de waarschijnlijkste klik voor een sommatie-sjabloon. De blok-2-claim
"Lisanne's hoofdroute gedekt" was daarmee te sterk. Gefixt: frontend stuurt `template_type`
mee, backend haakt dezelfde helper aan (verse case-mail; rollback bij mislukte send); 2 extra
provider-gemockte tests. **Overige aanvallen hielden stand:** AI-concepten (drafts) zijn
antwoorden op debiteursmail, geen sommaties → bijlage daar terecht niet; luid falen bij
render-fout is bewust (wettelijk verplichte bijlage stil weglaten is erger); terug-knop-
randgevallen (hergebruikte tab, browser-terug+klik, reload) vallen terug op correct gedrag
of de nette fallback; prod-staat herbevestigd (health/HEAD/migratie). 135 tests groen.

### Nagekomen (zelfde dag, opdracht Arsalan): factuur-PDF's óók op de verstuurknop (`8e2ee8b`, LIVE)
DF122-07 gespiegeld van het .eml-pad naar `/compose/send`: bij een sommatie-sjabloon gaan de
factuur-PDF's van de actieve vorderingen nu ook op de primaire knop automatisch mee (verse
case-mail, gededupliceerd met handmatige bijlagen). Test bewijst factuur + renteoverzicht samen.
Beide compose-knoppen zijn nu volledig gelijk in bijlagegedrag.

### Nagekomen (zelfde dag, opdracht Arsalan): Vorderingen-tab in het Facturen-menu (`df1b9a7`, LIVE)
Het Facturen-menu toonde alleen de (lege) kantoorfacturen; de vorderingen op de dossiers waren
nergens als totaaloverzicht te zien. Nieuw tenant-breed endpoint `GET /api/claims` (dossier +
debiteur + hoofdsom, paginatie/zoeken/alleen-lopend) + een **Vorderingen**-tab. Eerste tab
hernoemd naar **Kantoorfacturen** voor het onderscheid dat Arsalan vroeg. Prod-bewijs: 1.563
vorderingen, totale hoofdsom €3.142.934,72 — onafhankelijk in de DB nageteld (exact gelijk, geen
dubbeltelling; raw-count 1.563 == endpoint-total). 3 endpoint-tests. **Los blijft:** de factuur-
PDF's zijn niet aan de vorderingen gekoppeld (kolom PDF = "—"); 1.368/1.563 koppelbaar op
factuurnummer — koppel-actie is een aparte prod-schrijfactie (wacht op akkoord Arsalan).

### Bekende issues
- **KvK-rechtsvorm-backfill** wacht op de echte sleutel (~16 juli, Arsalan meldt). Tot dan besluit B
  (élke zakelijke wederpartij, óók BV, krijgt de bijlage). → S213.
- Compose-.eml slaat bij elke "Open in Outlook" een Renteoverzicht-document op het dossier op (zoals
  batch/followup ook doen) — cosmetisch, geen blokkade.

### Volgende sessie
S213 (`docs/sessions/PROMPT-S213.md`, Opus): zodra Arsalan de echte KvK-sleutel meldt → `KVK_API_KEY`
(+ `KVK_API_BASE`) als env op de VPS → herstart backend → `scripts/kvk_backfill_legal_form.py
--dry-run` → akkoord → echt draaien → natelling (±438 relaties, ±€9) → meten hoeveel BV's geen
bijlage meer krijgen. Eventueel: `/compose/send`-bijlage-observatie oppakken als Arsalan dat wil.


## Sessie 211 (14 juli 2026, Opus-bouw + Fable-review/afronding — WIK-rentebijlage + S207 AF, op tak)

### Samenvatting
Alles op tak `s211-wik-rentebijlage` (5 commits, gepusht, **NIET gemerged** — mailslot staat OPEN,
merge = direct actief verzendgedrag → wacht op GO Arsalan). Volledige suite **1338 groen**.

- **WIK-rentebijlage gebouwd** (plan `docs/plans/PLAN-wik-rentebijlage.md`, besluiten A–D):
  `legal_form` (+ herkomst/checked_at) op contacts (migratie `s211_contact_legal_form`, additief);
  KvK-client `integrations/kvk_service.py` (faalt zacht, **slapend zonder `KVK_API_KEY`-env** —
  nooit stil tegen de verkeerde omgeving); auto-vullen bij relatie create/update; beslisregel
  `should_attach_rente_bijlage` in `collections/compliance.py` (kernwoord-match; VOF/CV ≠ BV);
  gedeelde helper `documents/rente_bijlage.py` op batch- én followup-pad (sleutelt op
  template_type `14_dagenbrief`/`sommatie_drukte`, niet sort_order); backfill-script klaar,
  **NIET gedraaid** (wacht op prod-sleutel ~16 juli). UI: rechtsvorm op relatiekaart.
- **Bewijs:** KvK end-to-end tegen testomgeving (eenmanszaak/BV/NV komen terug; 400 → zacht None);
  beslismatrix alle vormen × 4 stappen klopt; echte render: eenmanszaak → 1 renteoverzicht-PDF
  (62kB, %PDF-header), BV → 0. Visueel (Playwright, dev): rechtsvorm tonen/bewerken/opslaan +
  herkomst-label "handmatig".
- **Fable-review = GO-MITS → mitsen direct gefixt:** KvK-sleutel default leeg (was: testomgeving
  zou op prod draaien), afkap op 100 tekens, leegmaken blijft leeg, herkomst flipt niet bij
  ongewijzigde waarde, lege-staat-melding UI.
- **S207 HELEMAAL AF (zelfde sessie, opdracht Arsalan):** M4 HTML-escaping op alle VIER
  mail-bouwers — de twee halve uit de werkkopie afgemaakt + `followup_service` DOCX-route +
  een **vierde die de audit miste**: `incasso/service.py::_build_step_email` (batch;
  onderwerp plat, body autoescape). Rode-test-kluwen ontward: 2 tests waren S211-gedrag
  (bijgewerkt + BV-keerzijde-test), 1 was S207's eigen onaffe test (groen na de fix).
  L4/L5/L6 (`584b63c`) bleek **al live** via de S210-deploy; heartbeat-checklist 12/12 groen.
  `PROMPT-S207.md` status-header bijgewerkt (op de tak).
- **Geheugen-les:** S209-backfills stonden in memory als "openstaand" maar waren AF (S209+S210)
  — memory bijgewerkt; eerst SESSION-NOTES lezen vóór "openstaand" rapporteren.

### Gewijzigde bestanden (alles op tak `s211-wik-rentebijlage`)
- Backend: `relations/models+schemas+service`, `integrations/kvk_service.py` (nieuw),
  `collections/compliance.py`, `documents/rente_bijlage.py` (nieuw), `incasso/service.py`,
  `ai_agent/followup_service.py`, `email/incasso_templates.py`, `invoices/service.py`,
  `config.py`, migratie `s211_contact_legal_form`, `scripts/kvk_backfill_legal_form.py` (nieuw).
- Frontend: `relaties/[id]/page.tsx`, `ContactInfoSection.tsx`, `use-relations.ts`.
- Tests: `test_kvk_legal_form.py` (nieuw, 26), `test_followup.py`, `test_incasso_pipeline.py`,
  `test_incasso_templates.py`, `test_invoice_send_email.py`.

### Bekende issues
- **Rente-bijlage ontbreekt nog op het compose/AI-concept- en document-verzendpad** (Fable-
  bevinding 3; compose hangt voor deze stappen al factuur-PDF's aan → zelfde plek aanhaken). → S212
- Preview-zinnetje followup-frontend zegt "De brief gaat als PDF-bijlage mee" (moet: renteoverzicht). → S212
- Tot de rechtsvorm-backfill draait: élke 14-dagenbrief/eerste sommatie krijgt de bijlage, óók
  BV's (rechtsvorm leeg → besluit B, bewuste veilige kant) — begint bij merge, mailslot is OPEN.
- `PROMPT-S207.md` op main is nog de oude versie (update staat op de tak) — archiveren ná merge.

### Volgende sessie
- S212 (`docs/sessions/PROMPT-S212.md`, **Opus**): GO/merge+deploy s211-tak (migratie!) →
  rente-bijlage op compose- en document-pad + preview-zinnetje → terug-navigatie heel Luxis
  (wens Arsalan). Los moment zodra KvK-sleutel binnen is: env op VPS → backfill droogloop →
  akkoord → run → natelling.


## Sessie 210 (14 juli 2026, Opus-bouw + Fable-review — provisie-per-cliënt + land op de brieven, LIVE)

### Samenvatting
Twee S210-taken volledig af (provisie-afspraak eerst uitgevraagd bij Arsalan → ontworpen → gebouwd;
land op de Word-brieven). Daarna Fable-review van alles + door Opus alle visuele controles gedaan.
Taak 3 (WIK-bijlage) is onderzocht → plan goedgekeurd → apart gezet voor S211 (wacht op KvK-sleutel).

- **Provisie-% per cliënt (LIVE, `2eabd37`).** Nieuw veld `default_provisie_percentage` op `contacts`
  (migratie `s210_contact_provisie`, additief); elk nieuw dossier erft het net als de default_bik_*-
  velden (dossier wint), basis blijft `collected_amount`. Klantkaart (tonen + bewerken) + nieuwe-relatie-
  formulier. **Data (na akkoord, nageteld):** 6 klantkaarten op 15% (INC Zakelijk, Incassocenter,
  COLLECT 1, CM Zakelijk, LegalWork, **+ SYN Finance** — dezelfde afspraak) + 39 dossiers op 15%
  (exact de set die BaseNet zelf op `incprovisie=15` had; set-vergelijking prod↔export 0 verschil).
  Slim doorrekenen was al zo (provisie wordt live berekend, nooit als vast bedrag opgeslagen).
- **Land op de Word-brieven (LIVE, `4025d43`).** Voorwaardelijke regel `{%p if wederpartij.land %}...
  {%p endif %}` onder postcode+stad op de 5 debiteurbrieven (sommatie, tweede_sommatie, aanmaning,
  herinnering, 14_dagenbrief). Bij buitenland op eigen regel; bij binnenland (leeg) verdwijnt de regel
  volledig — brief byte-voor-byte gelijk aan voorheen (render-test per sjabloon). Back-up DB-sjablonen
  vóór her-upload (`/root/backup_managed_templates_pre_s210land.dump`); gerichte reseed van alleen deze
  5, andere 3 (dagvaarding/renteoverzicht/verzoekschrift) ongemoeid.
- **WIK-bijlage: onderzocht + plan goedgekeurd (S211).** KvK-koppeling bewezen in gratis testomgeving
  (rechtsvorm komt terug); besluiten A–D vastgelegd. Volledig plan: `docs/plans/PLAN-wik-rentebijlage.md`.

### Fable-review + visuele controle (zelfde sessie)
Alle dragende claims onafhankelijk herverifieerd: DB-sjablonen byte-identiek aan repo (sha256), de 39
dossiers = exact de export-set, precies 6 bedrijven (0 personen) op 15%, geen ander financieel veld
geraakt. **Live prod-round-trip:** testdossier bij CM Zakelijk kreeg automatisch 15,00% → daarna
verwijderd (verbruikte wel dossiernr 2026-00001; eerstvolgende echte = 2026-00002). Visueel (Opus,
niet Fable): provisie-leesweergave + bewerkweergave + nieuwe-relatie-formulier tonen het veld; 5 brieven op
buitenlandse zaak IN100007 (België onder adres) + binnenlandse tegenproef (geen witregel). Oordeel: GO.

### Gewijzigde bestanden
- Backend: `relations/models.py` + `schemas.py`, `cases/service.py` (erving), migratie
  `s210_contact_provisie`, `tests/test_interest_inheritance.py` (4 nieuwe). Templates: 5 DOCX in
  `templates/` (landregel) + gerichte DB-reseed op prod.
- Frontend: `relaties/[id]/page.tsx`, `relaties/nieuw/page.tsx`,
  `components/relations/detail/ContactInfoSection.tsx`, `hooks/use-relations.ts`.
- Docs: `docs/plans/PLAN-wik-rentebijlage.md` (nieuw), `docs/sessions/PROMPT-S211.md` (nieuw).
- 2 code-commits (`2eabd37` provisie · `4025d43` land). Data-mutaties via read-only-gecontroleerde SQL.

### Bekende issues / bewust niet gedaan
- **WIK-bijlage** wacht op de echte KvK-sleutel (~16 juli) voor de backfill; bouwen kan al tegen test.
- **Landregel op dagvaarding + faillissementsverzoek** bewust niet gedaan (gerechtelijke stukken,
  dagvaarding heeft inline-adres) — los klusje als gewenst.
- Verwijderd testdossier bestaat nog als inactieve rij (zo werkt verwijderen; cosmetisch).
- Parallelle S207-track: 5 bestanden nog ongecommit in de werkkopie — niet aangeraakt.

### Volgende sessie
S211 (`docs/sessions/PROMPT-S211.md`): WIK-rentebijlage bouwen tegen de KvK-testomgeving volgens
`PLAN-wik-rentebijlage.md`; backfill draaien zodra Arsalan de echte sleutel meldt. Bouwen = Opus.


## Sessie 209 (14 juli 2026, Opus-bouw + Fable-review — BaseNet import-gaten uit S208-veldaudit gedicht, LIVE)

### Samenvatting
Vier onderdelen uit de S208-veldaudit, elk als losse stap met dry-run + akkoord Arsalan +
tel-verificatie achteraf. Daarna een volledige Fable-review (model omgezet in dezelfde sessie)
die niet alleen de data hertelde maar ook functioneel testte dat alles vooruit werkt.

- **Onderdeel 1 — werknotities + waarschuwingen (LIVE).** 99 `pmemo` + 13 `palert` uit de
  Incasso-export → `Case.debtor_notes` (waarschuwing bovenaan met `[BaseNet-waarschuwing]`,
  werknotitie onder met `[BaseNet-notitie]`, herkomst-regel blijft ertussen). HTML-opmaak
  opgeschoond. Idempotent via marker. 109 dossiers, tel-geverifieerd 99+13. Herhaalbaar script
  `scripts/basenet/backfill_notes.py` (+ zelf-test).
- **Onderdeel 2 — land bij adressen (LIVE, incl. migratie + deploy).** Nieuwe kolommen
  `contacts.visit_country/postal_country` (migratie `s209_contact_country`, additief). 49
  buitenlandse relaties gevuld met nette NL-landnamen (binnenland leeg = standaard). Getoond in
  relatie-detail (alleen indien gevuld) + bewerkbaar. Land beschikbaar in de brief-context
  (`{{ wederpartij.land }}`) + samenvoegveld-lijst + HTML-fallback-sjablonen.
- **Onderdeel 3 — geboortedatums (LIVE); provisie GEPARKEERD.** 28 personen kregen hun
  `date_of_birth` (gekoppeld op systemid, namen gecontroleerd: 26 exact + 2 tussenvoegsel-only).
  Provisie-15% (39 zaken) BEWUST niet uitgevoerd — hangt aan de provisie-afspraak (zie onder).
- **Onderdeel 4 — mapping uitgebreid (voor de vólgende export).** `scripts/basenet/mapping.py`
  neemt nu land (genormaliseerd), geboortedatum, provisie (alleen >0), pmemo/palert in
  debtor_notes + rentetype-context automatisch mee. Hergebruikt `build_new_notes`/`clean`.
- **Provisie-afspraak (niet gebouwd — eerst uitvragen).** Arsalan (14 juli): treft Lisanne een
  regeling met de debiteur voor een lager bedrag, dan krijgt zij 15% over die deal; haalt zij het
  volledige bedrag binnen, dan krijgt zij gewoon de incassokosten. Nog niet scherp genoeg + het is
  onbekend of dit dezelfde 15% is als de BaseNet-`incprovisie` bij 39 zaken. Vragen staan in
  `PROMPT-S209.md`; wachten op Arsalans antwoorden vóór ontwerp (Plan Mode).

### Fable-review (zelfde sessie, model omgezet)
Data onafhankelijk herteld: 109/109 notities byte-voor-byte gelijk aan herberekening (0 `\r`),
49/49 landen + 28/28 geboortedatums exact + bij de juiste relatie (koppeling in beide richtingen
dicht), 0 andere records geraakt (0 provisie gezet). Live via API + visueel doorgeklikt (Chrome):
land toont "Duitsland", dossiernotitie toont "Failliet" bovenaan, testrelatie aangemaakt→land
opgeslagen→verwijderd. **8 round-trip-tests** toegevoegd (mapping→`_insert_missing`→PUT/GET-API).
**Review-vondst:** `is_btw_plichtig` + `contractual_compound` misten `server_default` in het model
terwijl prod die wél heeft (migratie-drift) → test-DB week af, raw-SQL-insert faalde daar. Model
gelijkgetrokken (geen gedragswijziging op prod). 284 tests rente/dossiers/relaties/btw groen.

### Gewijzigde bestanden
- Backend: `relations/models.py` (2 land-kolommen + server_default-sync), `relations/schemas.py`,
  `cases/models.py` (server_default-sync), `documents/docx_service.py` + `documents/service.py`
  (land in context), `templates/sommatie.html` + `14_dagenbrief.html`, migratie
  `s209_contact_country`.
- Frontend: `relaties/[id]/page.tsx`, `components/relations/detail/ContactInfoSection.tsx`,
  `hooks/use-relations.ts`.
- Scripts/tests: `scripts/basenet/backfill_notes.py` (nieuw), `scripts/basenet/mapping.py`,
  `backend/tests/test_basenet_s209_roundtrip.py` (nieuw).
- 6 commits (`2d51ec5` notities · `3054764` land · `c50d24d` mapping · `166620d` review-tests +
  drift-fix · `f3b2ad4` lint). Data-mutaties via read-only-gecontroleerde SQL op prod.

### Bekende issues / bewust niet gedaan
- **Provisie-15% (39 zaken)** wacht op de provisie-afspraak — eerst uitvragen (PROMPT-S209 §gesprek).
- **Land op de eigenlijke Word-brieven** — de built-in DOCX-sjablonen (in de DB) missen nog de
  `{{ wederpartij.land }}`-regel; kleine klus in de sjabloon-editor met visuele controle. Basis staat.
- Parallelle S207-track: 5 bestanden nog ongecommit in de werkkopie — niet aangeraakt.

### Volgende sessie
S210 (`docs/sessions/PROMPT-S210.md`): provisie-afspraak uitvragen bij Arsalan → ontwerpen (Plan
Mode) → eventueel provisie-backfill; land-regel in de Word-sjablonen. WIK-bijlage zodra KvK-API er is.


## Sessie 208 (13 juli 2026, Fable max — BaseNet-veldaudit + EINDVERIFICATIE rente, read-only)

### Samenvatting
Hoofdtaak S208-prompt: veld-voor-veld door `Xml_02-07-2026_2400.zip` (137 bestanden; 9 in
gebruik door de import; elk veld geteld op vul-graad, kruising met `mapping.py`). Rapport:
`docs/research/S208-veldaudit-basenet.md`. Daarna, op verzoek Arsalan, volledige
eindverificatie van de rente-stand ("100% zeker, dan afsluiten").

- **Veld-gaten gevonden (gekwantificeerd):** `incinteresttype` per dossier nooit geïmporteerd;
  99 dossiernotities (`pmemo`) + 13 waarschuwingen (`palert`, o.a. "Failliet", "NIET REAGEREN
  — procedure aanhangig") niet overgenomen; geen land-veld in Luxis-adressen (52 buitenlandse
  relaties); provisie 15% (39 zaken, veld bestaat), 28 geboortedatums, 3 BSN's (bewust NIET
  importeren). Betalingen-aan-cliënt bewezen compleet: €165.697,01 == BaseNet-totaal, 0 verschil.
- **Rente-scare ontzenuwd + eigen rapport gecorrigeerd.** Eerste rapportversie zette 19
  "afwijkende" zaken als beslispunt — fout: besluit S188b (9 juli, plan §4b) dekte ze al
  (b2b holding-opdrachtgevers = AV 2%/mnd). Rapport zelfde dag gecorrigeerd; les: eerst het
  heropening-draaiboek lezen. BaseNet-rentetypen ontcijferd via terugrekening (type 1≈handels-
  rente, 2≈consumentenrente, 5=2%/jr, 9=geen; controlegroep type 8 = 24,6–27,5%/jr ✓).
- **EINDVERIFICATIE (alles prod, read-only):** kruistabel 607/607 in exact 4 besluit-conforme
  combinaties (519 AV-b2b contractual 2,00 / 79 AV-b2c statutory / 8 commercial / 1 statutory);
  machine-match per dossier tegen BaseNet-type: 0 onverklaard (497 identiek, 75 S207c-besluit,
  22 S188b-besluit, 5 b2c-laag, 8 niet-AV); claims-laag 1.373/1.373 monthly (S188b-valkuil
  afwezig); freeze 580/580 gesloten bevroren + 0/27 open + 5 "vóór opening" allemaal exact =
  laatste betaaldatum; motor 107/107 rentetests groen; **ijk IN100197 op prod = €723,31 op de
  cent** (peildatum 8 juli; BaseNet-spec rentedatum 7 juli — S207c-notitie "9 maart" was de
  oude exportdatum) en t/m vandaag €725,39 (loopt correct door).
- **Plan §4b bijgewerkt:** rente-SQL bij heropening VERVALLEN (al uitgerold + geverifieerd);
  verouderde regel "enkelvoudig/`contractual_compound=false`" gecorrigeerd naar samengesteld
  (gouden test `tests/test_interest_monthly.py`). Zonder fix zou een letterlijke uitvoering
  de uitrol deels terugdraaien.

### Gewijzigde bestanden
- `docs/research/S208-veldaudit-basenet.md` (nieuw, 2× gecorrigeerd/aangevuld)
- `docs/plans/PLAN-heropening-werkvoorraad.md` (§4b)
- Geen code, geen migraties, geen prod-mutaties. Deploy niet nodig.

### Bekende issues
- Parallelle S207-track had tijdens deze sessie niet-gecommitte wijzigingen in de werkkopie
  (email/invoices + tests) — bewust niet aangeraakt/gecommit.
- `PROMPT-S207.md` bewust NIET gearchiveerd (actieve parallelle track); archief-regel weer
  toepassen zodra die track afgesloten is.
- Untracked in projectmap: `Renteberekening.docx/pdf` (bron gouden test) — bewust untracked
  laten, zoals de AV-PDF's.

### Volgende sessie
S209: de kleine import-backfills (notities/alerts → dossiernotitie; land-veld + migratie;
provisie/geboortedatums) elk na akkoord; WIK-bijlage zodra KvK-API er is; verse export
voorbereiden. Prompt: `docs/sessions/PROMPT-S209.md`.

## Sessie S207c (13 juli 2026, Fable-review + Opus-uitvoer — rente-review, b2c-terug, bevriesdatum-backfill, BaseNet-herkomst, LIVE)

### Samenvatting
Vervolg op de demo-sprint. Eerst adversariële review van de rentekern (47 tests groen,
6 eigen randgeval-probes, prod IN100197 = €723,31 exact = BaseNet). Daarna 3 prod-acties,
elk met backup + dry-run + akkoord Arsalan.

- **B2C-rente terug (UITGEVOERD).** De AV-uitrol zette 79 consumentenzaken op 2%/mnd.
  Ambtshalve toetsing (Richtlijn 93/13) vernietigt ≥1%/mnd bij consumenten vrijwel altijd
  → veilige route wettelijke rente. `revert_b2c_rente.py`: rente-som 102.876,78 → 19.329,23,
  36 betalingen herverdeeld. `rollout_av_rente.py` slaat b2c voortaan over.
- **Bevriesdatum-backfill (UITGEVOERD).** Alle 580 gesloten zaken kregen `interest_freeze_date`
  (134 laatste betaaldatum / 67 date_closed / 379 BaseNet-rentedatum uit de export van 2 juli).
  Openstaand op gesloten zaken 3.869.871 → 3.338.193 (531.679 spookrente eruit). `backfill_freeze_date.py`.
  ⚠ Export-verwarring rechtgezet: `Xml_02-07-2026_2400.zip` stónd gewoon in de projectmap
  (ik keek eerst naar losse XML). Rentedatum per dossier zat als ongebruikt veld in die export.
- **BaseNet-herkomst als vast veld (GEBOUWD + LIVE).** `Case.basenet_origin_status` (migratie
  s207c, backfill uit de import-notitie). Onderscheid dat Arsalan vroeg: "Nog te openen"
  (Lopend 372 + Wacht 69 = 441; wordt in fases heropend) vs "BaseNet-archief" (Gereed 148 +
  Geannuleerd 15 + Offerte 3 = 166; blijft dicht). Badge in dossierlijst + detailpagina; import
  vult het veld voortaan zelf. Luxis-status ONGEMOEID (heropenen blijft de fase-aanpak).

### Verificatie
Rentetests 47 groen + test_cases 32 groen + nieuwe test_basenet_origin_status 9 groen (zelf
gedraaid). `uvx ruff` schoon, `tsc --noEmit` groen. Migraties s207c op prod = head, 607/607
zaken herkomst gevuld (0 leeg), 166 "afgehandeld" matcht exact de eerdere meting. Live API:
`basenet_origin_status` komt mee in dossierlijst. Backups: `backup_pre_s207c` + `backup_pre_backfill`
op de VPS. Mailslot bleef DICHT.

### Vervolg (zelfde dag): werkfase-vondst + S207d
Lisanne herkende 2 "Offerte"-zaken als lopende procedures → bron gecheckt: BaseNet's
werkstatus **"Procedure loopt" (57310) hangt in hun statusconfig onder hoofdgroep "Offerte"**
(inrichtingsfout kantoor). pstatus = hoofdgroep, `incstatus` → CustomProjectStatus = de echte
werkfase. IN100310/IN100407 op prod gecorrigeerd naar 'Lopend' (nu 443/164); IN100167
(Fideal, fase "Invoer", geen vaste opdrachtgever) blijft archief — keuze Lisanne.
**S207d gebouwd + LIVE:** `Case.basenet_origin_phase` (migratie s207d + `backfill_basenet_phase.py`,
607/607 gevuld) — de werkfase per zaak ("B2C 3e sommatie verstuurd", "Procedure loopt", …) als
hard veld, zichtbaar in badge-tooltip + detailpagina. Belang: het S181-heropeningsrecept (CSV,
372 zaken) dekte deze zaken NIET; de fase-heropening kan nu uit de DB zelf de juiste stap bepalen.
Valkuil genoteerd in `scripts/basenet/mapping.py` voor de volgende import.

### Bekende issues / aandachtspunten
- **Draaiboek-eis toegevoegd** (`PLAN-heropening-werkvoorraad.md` #9): script-heropening moet
  `interest_freeze_date` wissen, anders blijft een heropende zaak bevroren (UI/service doet dit al).
- **Heropening:** IN100310/IN100407 ("Procedure loopt") staan NIET in het S181-recept-CSV —
  meenemen bij de fase-heropening (nu vindbaar via `basenet_origin_phase`).
- Voorstel (niet gebouwd, scope): filter "Nog te openen" op de dossierlijst voor de fase-heropening.
- WIK-rentebijlage: plan klaar, wacht op KvK-API (Arsalan vraagt aan). Bouwen = Opus.

## Sessie demo Lisanne (13 juli 2026, Opus-bouwsprint — rentecorrectie + 6 demo-punten, LIVE)

### Samenvatting
Live demo met Lisanne. Kernbevinding: renteberekening klopte niet (IN100197 toonde
€284,62; BaseNet rekent €723,32). Oorzaak: dossiers op wettelijke handelsrente i.p.v.
AV-rente **2%/maand samengesteld** (rente-op-rente per maand). Nieuwe rekenkern
`calculate_monthly_compound_interest` reproduceert de BaseNet-rentespecificatie van
IN100197 **regel-voor-regel op de cent** (tests: `test_interest_monthly.py`). Daarna 6
demo-punten afgetikt, elk getest + gedeployd. Migratie `s207b_interest_freeze_date` live.

- **Rente** — 2%/mnd samengesteld; uitgerold over 598 dossiers van 8 AV-opdrachtgevers
  (`scripts/rollout_av_rente.py`, backup vooraf). Creditfactuur = negatieve rente die wegvalt.
- **Adres** — kantoor verhuisd per 1 juli → Willem Fenengastraat 16E, 1096 BN Amsterdam,
  tel 020-3086621. Tenant-record + Renteoverzicht-sjabloon (had oud adres hardcoded → nu
  `{{ kantoor.adres }}`). E-mail bewust incasso@ gelaten.
- **Regelingen** — 24 ontbrekende (afgeronde) betalingsregelingen geïmporteerd (13→37);
  status uit meting van echte betalingen (`scripts/import_historical_arrangements.py`).
- **Rentedatum/bevriezing** — `Case.interest_freeze_date`: rente stopt op gekozen datum;
  `get_financial_summary` valt zonder peildatum daarop terug (alle callers respecteren het);
  auto-bevriezen op laatste betaaldatum bij afsluiten; heropenen wist het. UI in DetailsTab.
- **Heropenen** — nieuwe vordering op gesloten zaak → weer in_behandeling + bevriezing weg.
- **Factuur-prompt** — betaal-endpoint geeft `case_fully_paid`; BetalingenTab toont dialoog.

### Meting gesloten zaken (na rente-uitrol)
574/580 gesloten zaken tonen openstaand (€3,95M) — grotendeels legitieme oninbare
archiefschuld. Echte probleemcategorie: **100 zaken "afbetaald maar klein spookrestant"
(samen €22k)** — regelingen onder de oude lagere rente afgesproken; onder de correcte
hogere rente blijft een restant. Bevriezen lost dit NIET op (IN100350: €264,82 blijft).
= zakelijke keuze Lisanne. Dashboard telt alleen actieve zaken, dus niet zichtbaar daar.

### Openstaand — volgende sessie (Fable neemt over)
1. **Backfill bevriesdatum op de ~574 gesloten zaken** = aanbevolen (het moet in de huidige
   tijd kloppen). Zet `interest_freeze_date` = laatste betaaldatum (of `date_closed` als er geen
   betaling is) op elke gesloten zaak → rente stopt op afwikkelmoment, geen doorlopend cijfer.
   Neemt de 100 "€22k spookrestant"-zaken vanzelf mee; het restant dat dan overblijft is het
   verschil oude-vs-nieuwe rente = per-zaak signaal voor Lisanne, geen bulk-afboeking.
2. **WIK-bijlage** — renteberekening-PDF bij eerste sommatie, **alleen VOF/eenmanszaak/particulier**;
   + KvK-API voor rechtsvorm. Fable zoekt wettelijke eis + KvK-koppeling uit.
3. **Invoer-map** met nieuwe zaken (nieuwer dan export 2 juli) — hoe overhalen.
Arsalan: Fable neemt de volgende sessie over (review + uitvoering).
