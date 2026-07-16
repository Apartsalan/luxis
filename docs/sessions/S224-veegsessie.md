# S224 — Veegsessie (Fable, 16 juli 2026)

De éénmalige kruispunt-veegsessie uit de skill `breed-testen`: de volledige
huisregel-lijst × alle bestaande routes, cel voor cel gemeten in de broncode en
de productie-database (read-only), gevonden fouten gefixt, en de twee
kandidaat-wachters gebouwd zodat de teller ook op nul BLIJFT.

Voorrang-check KvK-sleutel: **niet binnen** (0 treffers in beide env-bestanden op
de VPS, niets in de container) → direct door met de veegsessie.

## 1. De route-inventaris (grond-waarheid uit de code)

Er zijn precies **twee provider-uitgangen** (`compose_router.py::send_via_provider`
en `send_service.py::send_with_attachment`) en **één rauwe SMTP-functie**
(`email/service.py::send_email`, mailslot-check ingebouwd). Alle mail loopt door
een van deze drie. De routes daarbovenop:

| # | Route | Status |
|---|-------|--------|
| 1 | compose/send (vrij, AI-concept, antwoord, doorsturen) | live |
| 2 | compose/cases/{id} → .eml ("Open in Outlook") | live |
| 3 | follow-up 'Uitvoeren' — inline e-mail | live |
| 4 | follow-up 'Uitvoeren' — DOCX+PDF | live |
| 5 | batch — inline e-mail | live |
| 6 | batch — DOCX+PDF | live |
| 7 | documents/{id}/send (document per mail) | live |
| 8 | facturen — send_invoice (aan de opdrachtgever) | live |
| 9 | classificatie-antwoord — execute_classification | live |
| 10 | /api/email/cases/{id}/send (legacy SMTP) | endpoint leeft, UI-dood* |
| 11 | AI-tool email_compose (tools-registry) | dood: registry heeft géén aanroepers |
| 12 | e-mail-test (instellingen) + wachtwoord-reset | systeem-mail, geen dossier-regels |

\* De hook `useSendCaseEmail` wordt geïnstantieerd maar nooit aangeroepen (alleen
`.isPending` voor een spinner). SMTP staat op prod wél geconfigureerd
(smtp.gmail.com), dus het endpoint zou echt versturen als iemand hem via de API
aanroept.

Routes 8 en 9 stonden **niet** in de skill-lijst — de inventaris zelf was dus al
een vondst.

## 2. De matrix — wat gemeten is en wat eruit kwam

**Prod-ijkpunten (read-only):** tenant-e-mail = incasso@kestinglegal.nl mét
verbonden imap-account (kantoorkanaal werkt dus echt); mailslot open; 0 open
concepten op gesloten zaken; **1 open advies op een gesloten zaak (IN100613,
gesloten 15/7, advies van 13/7)** — het bewijs voor vondst 4.

| Regel | 1 compose | 2 .eml | 3/4 follow-up | 5/6 batch | 7 documents | 8 facturen | 9 classificatie |
|-------|-----------|--------|---------------|-----------|-------------|------------|-----------------|
| M1 afzender | ✅ | n.v.t.¹ | ✅ | ✅ | ✅ | ⚠️ B1 | ❌→✅ **gefixt** |
| M2 drieluik | ✅ | n.v.t.¹ | ✅ | ✅ | ✅ | ✅ | ✅ |
| M3 slot+gate | ✅ | ❌→✅ **gefixt** | ✅ | ✅ | ✅ | n.v.t.² | n.v.t.³ |
| M4 onderwerp | ✅ | ✅ | ✅ | ✅ | ❌→✅ **gefixt** | ⚠️ eigen formaat⁴ | ⚠️ V2c⁵ |
| M5 bijlagen | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ (factuur-PDF) | n.v.t. |

¹ .eml verstuurt niet zelf (gebruiker verstuurt via Outlook); drieluik komt via de
mailsync terug. ² Factuur aan de opdrachtgever is geen BIK-sommatie. ³ Antwoord op
een inkomende mail, geen verse sommatie. ⁴ "Factuur {nr}" — bewust eigen formaat,
zie beslispunt B1. ⁵ Onderwerp uit het beheerde ResponseTemplate (curated, geen
stale BaseNet) — kandidaat om naar `build_reply_subject` te verhuizen.

**DOCX-tak zonder rente-bijlage is GEEN gat** (aanname weerlegd): alle drie
rente-set-types (`14_dagenbrief`, `sommatie_drukte`, `sommatie`) zijn
e-mailsjablonen (`_RENDERERS`) en nemen dus altijd de inline-tak.

**Pijplijn:** P1 ✅ (alleen stap-concepten schuiven door, S223-fix in de bron
bevestigd); P2 ✅ (`move_case_to_step` superseded adviezen + gooit stale
stap-concepten weg); P3 concepten ✅ / adviezen ❌→✅ **gefixt** (vondst 4).

**AI-output:** A1 (dossierdata op de cent) en A2 (huisstijl) live bewezen in
S223 (IN100607); A3 (instructie laatste blok) test-gedekt. **Geld:** 0 losse
`float(` in collections/invoices/trust_funds; Decimal-suite bestaat. **Toegang:**
de bestaande drift-guards deze sessie gedraaid — 4/4 groen (gespiegeld, niet
aangeraakt). **Zichtbaarheid:** leeskant van het drieluik per pagina in S223
geverifieerd; live-pass hieronder.

## 3. Gevonden fouten → gefixt + wachter

1. **M1 × classificatie-route** (`execute_classification`): verstuurde het
   antwoord aan de wederpartij via het persoonlijke account van de klikker
   (zelfde soort als S220-hoofdvondst N1). Fix: `send_as_tenant_account=True`;
   assertie toegevoegd aan `test_execute_send_template_sends_email`.
2. **M3 × .eml-route**: de 14-dagenbrief-gate bestond op 4 van de 5 deuren
   (S205: batch/follow-up/compose; S207: documents) — de .eml-route ("Open in
   Outlook", Lisanne's meest gebruikte route) bleef open. Fix: zelfde gedeelde
   helper + 'Toch openen'-override + onuitwisbaar spoor, voor- én achterkant.
   2 nieuwe gate-tests.
3. **M4 × documents/send**: onderwerp was "{titel} — {dossiernr}" (dossiernummer
   dubbel, buiten de bouwer om; deze route ontbrak in het S223-rijtje "gedekte
   onderwerp-routes"). Fix: server-fallback én dialoog-prefill via het
   huisformaat; assertie in de bestaande override-test.
4. **P3 × adviezen**: zaak sluiten ruimde wél concepten maar géén follow-up-
   adviezen op (handmatige route + betaling-hook; de pijplijn-eindstap dekte het
   toevallig via de stap-wissel). Prod-bewijs IN100613. Fix:
   `supersede_open_recommendations` op beide routes; P3-wachter uitgebreid naar
   adviezen op alle 3 sluit-routes.

## 4. De wachters (nieuw, `tests/test_send_route_drift_guard.py`)

AST-gebaseerd, exact het patroon van de auth/RLS-drift-guards:

- **M2-drieluik-wachter:** enumereert álle aanroepers van `provider.send_message`
  en de rauwe SMTP-functie rechtstreeks uit de broncode; alles buiten de twee
  geloggde uitgangen + gemotiveerde allowlist = rood. Plus: de geloggde uitgangen
  moeten aantoonbaar `write_outbound_log` aanroepen.
- **M4-onderwerp-wachter:** elke verzend-aanroep geeft óf rechtstreeks een
  bouwer-resultaat als onderwerp mee, óf staat mét motivering op de allowlist.
- **Eerlijkheids-test:** elke allowlist-regel moet naar een échte aanroep wijzen
  — een gefixte route moet uit de lijst (geen dode vrijstellingen).

Dat de wachters bij de eerste run meteen groen waren op exact de verwachte sets
is tegelijk de onafhankelijke bevestiging van de route-inventaris hierboven.

## 5. Beslispunten voor Arsalan (niet zelf besloten)

- **B1 — afzender facturen:** `send_invoice` verstuurt via het persoonlijke
  account van de klikker. Moet een factuur aan de OPDRACHTGEVER ook via
  incasso@ (kantoorkanaal), of is persoonlijk hier juist gewenst? 1-regel-fix
  als het incasso@ moet zijn.
- **B2 — dode AI-tool `email_compose`:** registry zonder aanroepers, maar mét
  gat (geen vangrail/gate) als hij ooit aangesloten wordt. Voorstel: verwijderen.
- **B3 — legacy endpoint `/api/email/cases/{id}/send`:** UI-dood, wel levend en
  functioneel (SMTP geconfigureerd), geen gate + half drieluik (geen SyncedEmail).
  Voorstel: endpoint + hook verwijderen.
- **B4 — opruimen prod:** het ene wees-advies op IN100613 op SUPERSEDED zetten
  (1 UPDATE, natelling erbij). Wacht op GO.

## 6. Live-pass (Taak B)

_Wordt aangevuld na de live-verzendtoets._

## 7. Eerlijke beperkingen

- Mailslot op de .eml-route blijft principieel onafdwingbaar (de gebruiker
  verstuurt zelf via Outlook); de gate-blokkade dekt nu wel het juridische risico.
- De M4-wachter toetst de vorm (bouwer-aanroep), niet de inhoud van het
  onderwerp; de allowlist-regels zijn handmatig gemotiveerde uitzonderingen.
- V2c (classificatie-onderwerp via ResponseTemplate i.p.v. `build_reply_subject`)
  is geregistreerd maar bewust niet verbouwd: de template-onderwerpen zijn
  beheerde inhoud, geen stale data.
