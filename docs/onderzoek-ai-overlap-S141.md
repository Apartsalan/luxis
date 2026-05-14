# Onderzoek demo-feedback Lisanne — Sessie 141

**Datum:** 2026-05-14
**Type:** Onderzoek-only (geen code-wijzigingen)
**Bron:** 7 punten uit Lisanne's demo-feedback sessie 140 + verduidelijking sessie 141

> **Update t.o.v. eerste rapportversie:** Punten 2, 4+5 en 7 zijn herzien na verduidelijking van Lisanne. Bij punt 2 gaat het om de handmatige Sync Mail-knop (niet de auto-sync). Bij 4+5 gaat het om een bolletje/pop-up IN het dossier zelf — niet de bel-icon rechtsboven. Punt 7 voegt een nieuwe component toe: layout van gegenereerde concepten (logo, handtekening met foto, disclaimer-positie) klopt niet.

---

## Executive Summary

**De vier punten 4, 5, 6 en 7 zijn één onderliggend probleem** met twee gezichten:

1. **Inhoud klopt, maar staat versnipperd of helemaal niet in beeld.** Lisanne wil één plek op het dossier waar staat: "Er is een update, dit is wat je kan doen, ik kan een concept maken." Dat was er voorheen (banner-systeem uit sessie 129+132), is in sessie 134 weggehaald omdat Lisanne overspoeld raakte door 3 parallelle systemen, en is nu te ver opgeruimd: nu is er niks meer.
2. **Eén AI-systeem dat zowel batch als single dekt, met sjabloon-trouwe layout.** Er zijn nu drie aparte AI-flows en de twee niet-pipeline-flows gebruiken een andere render-pijplijn dan de pipeline-batch — dáár zit de afwijkende layout.

**De andere drie punten zijn losse bugs/UX-issues:**
- **Tijdstempels** — overal datum-only, helper-functie ontbreekt
- **Mail-sync handmatige knop** — werkt niet; auto-sync werkt wel maar 60% emails wordt niet auto-gekoppeld (matching werkt op afzender, terwijl één klant alles via hetzelfde mailadres aanlevert)
- **Status pipeline** — 45 van 48 dossiers hebben geen `incasso_step_id`, pipeline-advance werkt niet voor de meesten

**Aanbevolen volgorde:**
1. **Quick wins eerst (S142):** Tijdstempels + bel-icon devtools-check + disclaimer-positie fixen + Sync Mail-knop diagnose
2. **Pipeline-advance + data herstel (S143):** 45 dossiers in juiste stap + batch-flow status-update bug
3. **Email-matching slimmer (S144):** Dossiernummer-first matching + Ongesorteerd-badge prominent
4. **Unified AI-flow + Actie-Feed op dossier (S145-S147):** één systeem voor batch + single, sjabloon-trouwe layout, één centrale widget op Overzicht-tab

---

## Punt 1 — Tijdstempels (datum + tijd)

**Lisanne:** "Overal alleen datum, ik wil ook HH:MM zien."

### Bevindingen

Helper-bestand: `frontend/src/lib/utils.ts`

| Bestaande functie | Output | Heeft tijd? |
|---|---|---|
| `formatDate` | "17 februari 2026" | Nee |
| `formatDateShort` | "17-02-2026" | Nee |
| `formatRelativeTime` | "5 min geleden" / "17 feb" | Hybride |
| `formatDateTime` | **bestaat niet** | — |

7 componenten tonen datum zonder tijd, terwijl het backend-veld (`email_date`, `created_at`, `entered_at`) wel een timestamp bevat:

| Component | File | Veld |
|---|---|---|
| Correspondentie e-maillijst | `CorrespondentieTab.tsx:555` | `email.email_date` |
| Correspondentie e-maildetail | `CorrespondentieTab.tsx:135` | `email.email_date` |
| Dossier-header (geopend) | `DossierHeader.tsx:228` | `zaak.date_opened` |
| Dossier-sidebar | `DossierSidebar.tsx:110` | `zaak.date_opened` |
| Dashboard recente activiteit | `dashboard/page.tsx:402` | `activity.created_at` |
| Details-tab activiteit-feed | `DetailsTab.tsx:875` | `activity.created_at` |
| Staphistorie | `StaphistorieTab.tsx:113,118` | `entered_at`, `exited_at` |

**Curiosum:** `StaphistorieTab` heeft een lokale formatter (regel 23-30) met `hour`+`minute` opties die wel tijd toont. Niet hergebruikt elders.

### Voorgestelde fix — **S (1-2u)**

1. Voeg `formatDateTime(date, "short" | "long")` toe aan `utils.ts`
2. Lokale formatter in `StaphistorieTab` vervangen door centrale helper
3. Vervang `formatDate`/`formatDateShort` in 6 andere componenten door `formatDateTime`
4. Visuele check in browser per scherm

**Risico:** laag. Pure UI-wijziging, geen backend-impact.

---

## Punt 2 — Sync Mail-knop + slimmere matching

> **Correctie:** Eerste rapportversie ging over de automatische 5-minuten sync. Die werkt prima. Lisanne bedoelt de **handmatige Sync Mail-knop** op de Correspondentie-tab van het dossier. Plus: ze legt uit dat één klant alles aanlevert vanaf hetzelfde mailadres, dus afzender-matching faalt structureel. Sortering moet op dossiernummer.

**Lisanne:** "Het knopje Sync Mail bij correspondentie werkt niet. En meerdere dossiers met hetzelfde emailadres gaat vaker gebeuren — één klant levert alles via hetzelfde mailadres aan. Sortering moet op dossiernummer. Mails die hij niet kan koppelen moeten we kunnen zien en zelf doen, maar liever Luxis zo slim mogelijk."

### Bevindingen — twee aparte sub-issues

**Sub-issue A: Handmatige Sync Mail-knop**

Locatie: `frontend/src/app/(dashboard)/zaken/[id]/components/CorrespondentieTab.tsx`. Knop roept waarschijnlijk een endpoint als `POST /api/email/sync` of `POST /api/email/accounts/{id}/sync` aan. Volgens commit-historie (`d3d23ff feat(compose): dossier-zoekveld`) is er recent veel gewijzigd in de compose-flow. Mogelijke faalmodi:
- Endpoint bestaat niet meer (hernoemd zonder frontend-update)
- Frontend stuurt `account_id` niet mee waar backend dat verwacht
- Backend laadt secret-encryption verkeerd en geeft 500 zonder duidelijke fout
- Mocht het endpoint wel werken maar 0 nieuwe mails opleveren: knop lijkt "kapot" terwijl er gewoon niks nieuws is sinds laatste auto-sync 4 minuten geleden

**Definitief check vereist:** Lisanne klikt knop, browser-devtools → Network-tab → welke call gaat eruit, welke response komt terug? Dat is 5 minuten verificatie en weten we precies wat stuk is.

**Sub-issue B: Auto-koppeling faalt door verkeerde matching-strategie**

Productie-data: 143 emails gesynced, **87 unlinked (60%)**, allemaal omdat `kesting@kestinglegal.nl` aan 3 dossiers gekoppeld is. De huidige matching-volgorde in `sync_service.py` is:
1. Dossiernummer in onderwerp/body (slaagt soms)
2. Klantreferentie (slaagt soms)
3. Zaaknummer rechtbank
4. Afzender-email → contact → dossier (faalt bij multi-dossier-klanten)

Probleem: stap 4 is een **vangnet** maar slaat over bij ambiguïteit ("Meerdere dossiers gevonden"). Bij Lisanne's praktijk is dit de norm, niet de uitzondering — één klant met meerdere dossiers gebruikt één mailadres.

### Hoe doen concurrenten dit?

**BaseNet (Lisanne's huidige systeem):**
- Mails worden via een speciale prefix in onderwerp (zoals "DOSS-2026-00007") naar dossier gerouteerd
- Zonder prefix landen mails in een "te koppelen" inbox die de gebruiker handmatig moet verdelen
- Werkt, maar legt last bij de gebruiker

**Clio (US/UK marktleider):**
- "Communicate" feature: elke klant krijgt een uniek alias-mailadres (`klantA-dossier123@clio-mail.com`). Wederpartij mailt naar die alias → auto-koppeling 100%
- Voor inbound vanaf bekende afzenders: bij ambiguïteit toont Clio een suggestie-popup "we denken dossier X — bevestig of kies"

**Smokeball:**
- "AutoTime" + auto-matching: bij elke binnenkomende mail vergelijkt Smokeball onderwerp, body en bijlagen tegen alle actieve dossiers; ML-model geeft een score per dossier. Boven 80% = auto-koppelen, 50-80% = suggestie, onder 50% = ongesorteerd.

**PracticePanther:**
- Vergelijkbaar met Clio — alias-mailadres per dossier (`@panther-mail`).

### Voorgestelde aanpak voor Luxis

**Stap 1 — Dossiernummer-first matching versterken — S (2-3u)**
- Onderwerp moet **altijd** dossiernummer bevatten als Lisanne zelf de mail verstuurt (templates al goed)
- Inbound: verwachten dat wederpartij/klant in antwoord het dossiernummer behoudt (Re: SOMMATIE / 2026-00007 / ...)
- Body-scan: regex op `\b\d{4}-\d{5}\b` patroon — niet alleen onderwerp
- Score boost: als dossiernummer gevonden + afzender past bij die zaak → 100% confidence

**Stap 2 — Suggestie-flow bij ambiguïteit — M (4-6u)**
- Bij multi-dossier kandidaat: niet weigeren, maar de **meest waarschijnlijke** suggereren op basis van:
  - Welk dossier is "actiefst" (laatste activiteit)
  - Welk dossier had recent uitgaande mail naar deze afzender
  - Welk dossier matcht qua dossierfase
- UI: mail in inbox van dossier-suggestie met label "Voorgesteld — bevestig of verplaats", 1-klik confirm/wijzig

**Stap 3 — "Ongesorteerd" prominenter — S (1-2u)**
- Badge in sidebar met aantal ongesorteerde mails (bestaat module M6 al)
- Dashboard-widget "Wachten op koppeling: X mails"
- Eerste landing-actie na inlog suggereren

**Combinatie van deze drie geeft naar verwachting:**
- 60% unlinked → minder dan 10% binnen 2 weken
- Resterende 10% landt zichtbaar in Ongesorteerd
- Lisanne ervaart sync als "werkt" omdat ze mails zien op haar dossiers

**Risico:** suggestie-flow kan false-positives geven (mail van wederpartij A onder dossier B). Mitigatie: alleen suggereren, niet auto-koppelen tot een drempel of expliciete bevestiging. Audit-log van elke koppeling-actie zodat fouten traceerbaar zijn.

**Niet doen:** alias-mailadres per dossier (Clio-stijl). Vereist DNS + mailserver-werk + leervrije pad. Te zwaar voor de waarde.

---

## Punt 3 — Status blijft op 1e sommatie

**Lisanne:** "Na versturen 1e sommatie blijft status hangen op 1e sommatie. Pop-up komt wel, maar status verandert niet."

### Bevindingen

**Database-stand (productie):**

| Metric | Waarde |
|---|---|
| Totaal dossiers | 48 |
| Met `incasso_step_id` (= pipeline-stap ingesteld) | **3** |
| Zonder pipeline-stap | **45 (94%)** |
| Status `active` | 0 |

Het probleem is dieper dan "status update faalt" — bij 94% van de dossiers is de pipeline-stap überhaupt nooit ingesteld of weer leeggemaakt.

### Code-analyse

**Pop-up flow:**
1. `frontend/src/app/(dashboard)/incasso/page.tsx:1083-1114` — `handleExecuteBatch()` toont preview-dialog
2. Pop-up roept `useBatchExecute()` → `POST /api/incasso/batch` met `action="generate_document"`, `send_email=true`
3. Backend `backend/app/incasso/service.py:980-1234` — `batch_execute()` doet 3 dingen: document genereren, email versturen, `_try_auto_advance()` aanroepen

**Auto-advance logica:**
- `_try_auto_advance()` (service.py:893-975) checkt completed `WorkflowTask` records, niet of email succesvol is verzonden
- AIDraft-status wordt alleen op `'sent'` gezet via `POST /api/incasso/cases/{id}/advance-after-send` (router.py:359-442)
- Maar de **batch-flow roept dit endpoint niet aan**

**Root cause:** Twee aparte verzendpaden:
- **Batch-flow** (incasso-pagina): mail verzonden, geen AIDraft `sent`-update, geen pipeline-advance trigger
- **Single-flow** (advance-after-send): mail verzonden, AIDraft `sent`, pipeline-advance OK

**Bijkomend:** `case.status` legacy veld vs `case.incasso_step_id` leidend veld — frontend toont mogelijk verkeerd veld in status-badge.

### Voorgestelde fix — **M (4-6u)**

1. Batch-flow `batch_execute()` aanvullen: na succesvolle email-verzending de AIDraft-status op `'sent'` zetten (zelfde logica als `advance_after_send`)
2. Status-advance gebeurt dan automatisch via `_try_auto_advance()`
3. Verifiëren dat status-badge op frontend leest van `case.incasso_step_id` → `pipeline_step.name`, niet `case.status`
4. **Eerst:** bestaande 45 dossiers zonder step migreren — alle "active" dossiers krijgen step 1 toegewezen of expliciet markeren als afgerond/concept

**Risico:** medium. Bestaande data herstel is risicovol — eerst dry-run, dan migratie.

---

## Punten 4 + 5 + 6 — Eén plek voor updates en acties op het dossier

> **Correctie:** Eerste rapportversie behandelde 4 (notificaties bel) en 5 (concept-klaar) als losse punten. Lisanne legde uit: ze bedoelt ook een **bolletje of pop-up IN het dossier** dat voorheen er was: "je kan een concept maken" of "antwoord van wederpartij/cliënt — wil je dat ik de volgende stap beantwoord?". Dat is weg.

**Lisanne (volledige quote uit sessie 141):**
> "Voorheen hadden we dat er een pop-up kwam: 'je kan een concept maken' of 'er is een antwoord geweest van de cliënt of de wederpartij'. En dan stond er: 'Wil je dat ik de volgende stappen beantwoord?'. Die pop-up — of niet eens pop-up, gewoon dat bolletje in dossiers — is niet meer te zien. Er moet één plek zijn waar je gewoon ziet: hé er is een update, dit is aan de hand. Niet op verschillende plekken."

**Plus, ontdekt tijdens onderzoek:** Notification-bel rechtsboven heeft een **eigen** bug — 403 ongelezen notificaties in de database, allemaal voor Lisanne, allemaal van type `deadline_overdue`, maar frontend toont ze niet. Dat is een aparte bug bovenop het dossier-bolletje-probleem.

### Bevindingen — wat is er gebeurd?

**Git-historie biedt de exacte uitleg:**

```
d9c7e20 (7 mei 2026) — fix(ui): verberg legacy AI-suggestie + Followup banners op dossier

Drie parallelle systemen toonden tegelijk acties op het dossier:
1. AI-suggestie classification banner (sessie 129)
2. FollowupRecommendation banner (sessie 132)
3. Pipeline /taken queue (sessie 134, nieuwe bron van waarheid)

Lisanne raakte overspoeld. Banners 1 + 2 weggehaald uit page.tsx —
pipeline /taken is nu enige plek waar AI-acties verschijnen.
```

**Wat we hebben gedaan:** in sessie 134 hebben we expliciet 2 van de 3 plekken weggehaald omdat Lisanne overspoeld raakte. Beslissing destijds: "pipeline /taken is nu enige plek voor AI-acties". Plus commit `76996f7` heeft de hooks ook verwijderd. 326 regels code uit het dossier verwijderd.

**Wat Lisanne nu ervaart:** de Taken-tab is voor haar geen "centrale plek" maar een lijstje tussen 11 andere tabs. Ze ziet niks meer op het Overzicht (de hoofdpagina). De prikkel "er is iets voor je klaar" is verdwenen.

**Plus aparte bug — bel-icon:**
- Database: 403 ongelezen notificaties voor Lisanne, alle type `deadline_overdue`, latest vandaag 06:20
- Frontend hook: `useNotifications(15)` + `useUnreadCount()` met 30s polling
- Onbekend waarom UI ze niet toont — vereist devtools-check bij Lisanne (15 min werk)

### Voorgestelde fix — gefaseerd

**Fase 1 — Bel-icon diagnose + Disclaimer/render-fixes (S142) — S (1u totaal)**
- Lisanne laten inloggen → devtools → `GET /api/notifications/unread-count` response checken
- Als response = 403: frontend-bug in badge-rendering
- Als response = 0: backend/RLS-bug
- Snelle fix afhankelijk van diagnose

**Fase 2 — Nieuwe `CaseActionFeed` widget op Overzicht-tab (S145-S146) — M**

Niet de oude banners terugzetten — die waren versnipperd. Eén nieuw component bovenaan de Overzicht-tab dat alles bundelt. Visuele schets:

```
┌─ Dossier 2026-00062 ─ Verweer beantwoorden ───────┐
│                                                    │
│ 🟢 1 update vereist actie                          │
│                                                    │
│ ┌──────────────────────────────────────────────┐ │
│ │ 🤖 Concept klaar voor review                 │ │
│ │    Verweer beantwoorden — 2 min geleden      │ │
│ │    Gegenereerd in 4.3s                       │ │
│ │    [Bekijk concept]  [Verstuur direct]       │ │
│ └──────────────────────────────────────────────┘ │
│                                                    │
│ ┌──────────────────────────────────────────────┐ │
│ │ 📧 Nieuw antwoord van wederpartij            │ │
│ │    "Wij betwisten de vordering omdat..."     │ │
│ │    AI classificeert: Betwisting (78%)        │ │
│ │    [Genereer antwoord — mild/zakelijk/streng]│ │
│ └──────────────────────────────────────────────┘ │
│                                                    │
│ ┌──────────────────────────────────────────────┐ │
│ │ ⏰ Volgende stap: Stap 5 — Dagvaarding       │ │
│ │    Deadline: 21 mei 2026 (over 7 dagen)      │ │
│ └──────────────────────────────────────────────┘ │
│                                                    │
└────────────────────────────────────────────────────┘
```

**Drie typen kaarten, één widget:**
1. AI-draft klaar (data uit `useAiDrafts(caseId)` met status `generated`)
2. Inkomend antwoord met classificatie + smart-reply CTA (data uit `useClassifications(caseId)`)
3. Volgende pipeline-stap met deadline (data uit `useNextStep(caseId)`)

**Verschil met oude banners:**
- 1 widget i.p.v. 3 banners die elkaar opstapelen
- Geen 30s auto-hide (Lisanne komt later terug en wil het nog zien)
- Maximaal 3 kaarten zichtbaar, rest in "alles tonen" toggle (geen overload)
- Persistent — verdwijnt alleen na actie van Lisanne

**Wat oplossing-overlap doet:**
- Punt 5 (concept-klaar): kaart-type 1 in de feed
- Punt 6 (één plek): de feed zelf
- Punt 4-dossier-bolletje: badge bovenop dossier-icoon in sidebar als de feed iets bevat
- Punt 4-bel-icon: aparte fix, gaat over globale notificaties (cross-dossier)

**Risico:** medium. Lisanne raakte vorige keer overspoeld bij 3 banners → balans tussen "zichtbaar" en "rustig" is kritisch. Test eerst met Lisanne op 1 dossier voor we het uitrollen.

---

## Punt 7 — Eén AI-systeem + sjabloon-trouwe layout

> **Correctie:** Eerste rapportversie zag dit puur als architectuur-overlap (3 systemen → 1 systeem). Dat klopt, maar Lisanne voegt twee belangrijke nuances toe: (1) het unified systeem moet zowel batch als single dekken, (2) er is ook een concreet layout-probleem dat los staat van architectuur — logo, handtekening met foto, en disclaimer-positie kloppen niet.

**Lisanne:**
> "De conceptbrieven die worden gegenereerd, zien er anders uit dan de sjablonen. Wat erin staat is correct, dat is geen probleem. Maar de lay-out, hoe de mail eruitziet met de foto en met de handtekening, komt niet overeen met de sjablonen. Ook de disclaimer staat nu boven de handtekening, dat moet onder de handtekening, helemaal onderaan. Het antwoord op de betwisting is perfect — dat stuk werkt wel."
> 
> "Er moet één systeem zijn dat nadenkt over hoe concepten worden geschreven. Dat moet zowel voor batch als voor enkele mails werken. Ze zijn hetzelfde — alleen de een stuurt batch, de ander per dossier. Dat van die correspondentie kan weg, want dat is overbodig."

### Bevindingen — drie aparte sub-issues

**Sub-issue A: Twee aparte render-pijplijnen**

Productie-code heeft twee paden waar email-HTML wordt gemaakt:

| Pad | Gebruikt door | HTML-bron |
|---|---|---|
| `incasso/html_renderer.py` + `incasso/templates.py` | Batch-flow (incasso-pagina), single send-flow (advance-after-send) | Lisanne's .eml-sjablonen als basis, server-side gevuld met regex-replace |
| `ai_agent/draft_service.py` + `smart_reply_service.py` | "Concept genereren" knop op dossier (DetailsTab), Correspondentie-tab smart-reply | AI levert raw HTML/text terug, geen sjabloon-wrap |

`html_renderer.py:1-11` docstring:
> "Het AI-model genereert alleen subject + plain body. De HTML-versie van de email wordt server-side opgebouwd op basis van het template plus dossier-context."

`draft_service.py`: importeert `html_renderer` **niet**. Smart-reply ook niet. Dat is het hele verschil — pipeline-flow krijgt Lisanne's templates, andere flows krijgen kale AI-output.

**Dit verklaart Lisanne's observatie:**
- Smart-reply op betwisting: inhoud klopt (AI doet z'n werk goed)
- Maar layout = generieke AI-HTML zonder logo/handtekening/footer

**Sub-issue B: Disclaimer staat boven handtekening**

In `incasso_templates.py:18-107` — `_BASE_EMAIL` template heeft deze volgorde:
```
<!-- Body content -->
{{ content }}

<!-- Signature -->
{{ afsluiting }}

<!-- Footer (kantoor-info, gold border) -->
<table>...</table>
```

In de 40+ call sites in dezelfde file staat overal:
```python
body += _schuldhulp_disclaimer(ctx)   # disclaimer wordt aan BODY geappend
... _render_branded(content_html=body, afsluiting_html=_signature(ctx))
```

Resultaat: schuldhulp + disclaimer rendert **vóór** handtekening, omdat het in body zit. Lisanne wil onder handtekening helemaal onderaan.

**Fix structureel:**
1. `_BASE_EMAIL` template: nieuwe slot `{{ disclaimer }}` toevoegen **na** `{{ afsluiting }}`
2. `_render_branded()` signature uitbreiden met `disclaimer_html` parameter
3. Alle 40+ call sites: `body += _schuldhulp_disclaimer(ctx)` verwijderen, vervangen door `disclaimer_html=_schuldhulp_disclaimer(ctx)` parameter
4. Tests aanpassen (`test_html_renderer.py` raakt geraakt)

**Geschatte tijd:** S (1-2u). Mechanische refactor, geen logica-wijziging.

**Sub-issue C: Handtekening zonder foto + foute email + ontbrekend logo-pad**

Lisanne's originele BaseNet-sjabloon (uit `templates/lisanne/SOMMATIE TOT BETALING _  _.eml`) heeft deze handtekening-volgorde:

```
Hoogachtend,

Mevr. mr. L. Kesting
INCASSO ADVOCAAT | DEBT COLLECTION ATTORNEY

Kesting Legal B.V.
IJsbaanpad 9
1076 CV Amsterdam
E: kesting@kestinglegal.nl       ← LET OP: kesting@, niet incasso@
W: www.kestinglegal.nl

[https://static.basenet.nl/cms/113646/image_resized_100x100.png]   ← FOTO

Heeft u financiële zorgen...       ← schuldhulp blok hierna
```

Huidige `incasso_templates.py:215-246` — `_signature()`:
- Geeft `incasso@kestinglegal.nl` terug (kantoor-mailadres in origineel)
- Geen `<img>` voor foto
- Tekst klopt verder

Plus `_BASE_EMAIL:35-36`:
```html
<img src="https://kestinglegal.nl/logo.png" alt="Kesting Legal" .../>
```
Externe URL. Commit-message `c8c6039` beweerde "logo embedded as data:image/png;base64" maar dat is niet wat er nu in de code staat. Externe URL werkt soms niet in mailclients (blokkade van remote images).

**Fix:**
- Signatuur-foto toevoegen als `<img src="data:image/...">` (gebruik `_kesting_logo.b64` file in `templates/lisanne/`)
- Email-adres aanpassen naar wat Lisanne wil (`kesting@` of `incasso@`)
- Logo in header omzetten naar base64-data-URL i.p.v. externe URL

**Geschatte tijd:** S (2u). Vraag aan Lisanne welke variant ze wil (incasso@ of kesting@, met of zonder foto), dan implementeren.

### Architectuur-voorstel — Unified AI Draft Service

```
┌──────────────────────────────────────────────────────────────────┐
│              ÉÉN endpoint: POST /api/ai/draft                    │
│              body: { case_id, intent, tone? }                     │
│                                                                   │
│   intent: "next_step" | "reply_to_email" | "free_compose"        │
│   tone:   "mild" | "zakelijk" | "streng" (optioneel)             │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│  UnifiedDraftService (één service, drie strategieën)             │
│                                                                   │
│  intent="next_step":                                              │
│    → kijkt naar case.incasso_step                                 │
│    → laadt managed_template voor die stap                         │
│    → vraagt AI alleen plain body te schrijven                     │
│    → server-side HTML wrap via incasso_templates._render_branded  │
│                                                                   │
│  intent="reply_to_email":                                         │
│    → kijkt naar laatste classified email                          │
│    → past tone toe (mild/zakelijk/streng)                         │
│    → laadt verweer-bibliotheek bij classification "betwisting"    │
│    → vraagt AI alleen plain body te schrijven                     │
│    → server-side HTML wrap via incasso_templates._render_branded  │
│                                                                   │
│  intent="free_compose":                                           │
│    → vrije generatie op case-context                              │
│    → vraagt AI plain body te schrijven                            │
│    → server-side HTML wrap (zelfde branded layout)                │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│         Eén HTML render-pijplijn (incasso_templates.py)          │
│  - Wordt nu al gebruikt door batch-flow                          │
│  - Wordt straks ook gebruikt door single-flow + smart-reply       │
│  - Logo + handtekening + (verplaatste) disclaimer komen           │
│    overal automatisch correct                                     │
└──────────────────────────────────────────────────────────────────┘
```

### Verschillen huidig → unified

| Aspect | Huidig | Unified |
|---|---|---|
| Endpoints | 3 | 1 |
| Hooks | `useGenerateDraft`, `useGenerateDraftForCase`, `useSmartReplies` | `useDraft({intent, tone})` |
| AI-output | Soms HTML, soms text | Altijd plain text body |
| HTML-wrapping | Alleen batch-flow | Alle flows |
| Logo + handtekening + disclaimer | Alleen in batch-flow goed | Overal goed |
| Concept-knop op Correspondentie-tab | Bestaat, gebruikt apart pad | **Verwijderd — overbodig** |

### Voorgestelde fix — **L (2-3 sessies)**

**Sessie A — Layout-fixes vooraf (kan parallel met S142/S143)**
1. Disclaimer-positie fixen in `_BASE_EMAIL` (S, 1-2u)
2. Logo embedden als data-URL (S, 30min)
3. Handtekening uitbreiden met foto + correcte email (S, 1-2u, na Lisanne-input)

**Sessie B — Unified service backend**
1. Nieuw `app/ai_agent/unified_draft_service.py` met 3 intents
2. Nieuwe endpoint `POST /api/ai/draft` met `{case_id, intent, tone?}`
3. AI-prompts aanpassen: altijd plain body terug, geen HTML
4. Server-side HTML-wrap via `incasso_templates._render_branded()` voor alle intents
5. Bestaande 3 endpoints behouden (deprecate, niet meteen verwijderen)

**Sessie C — Frontend consolidatie + cleanup**
1. Nieuw hook `useDraft({intent, tone})`
2. `CaseActionFeed` widget (punt 4+5+6) gebruikt deze hook
3. Smart-reply card op correspondentie-tab → krijgt 1 knop "Genereer antwoord" met tone-dropdown (intent="reply_to_email"), of wordt helemaal weggehaald uit Correspondentie en alleen in CaseActionFeed getoond zoals Lisanne voorstelt
4. Concept-knop op Correspondentie-tab verwijderen (overbodig per Lisanne)
5. Oude 3 endpoints definitief verwijderen na 1 sessie monitoring

**Risico:** L. Migratie raakt 4 modules + bestaande data. Mitigatie:
- Nieuwe service parallel naast oude met feature-flag
- Per scherm overzetten, niet big-bang
- Bestaande templates eerst CSV-exporten als backup

---

## Aanbevolen sessievolgorde

| Sessie | Punten | Grootte | Wat Lisanne merkt |
|---|---|---|---|
| **S142** | Tijdstempels (1) + bel-icon devtools-check (4-deel) + disclaimer-positie (7-deel A) + Sync Mail-knop diagnose (2-deel A) | Dag | Tijden zichtbaar, ze weet waarom bel leeg is, disclaimer goed gepositioneerd, sync-knop werkt of weet waarom niet |
| **S143** | Pipeline-step bug + 45-dossier-migratie (3) | Dag | Status loopt netjes door na batch-versturen |
| **S144** | Dossiernummer-first matching + suggestie-flow + Ongesorteerd-badge (2-deel B) | Dag | Veel meer mails komen automatisch op het juiste dossier |
| **S145** | Unified DraftService backend + logo + handtekening (7-deel A,B,C) | Dag | Conceptbrieven zien er overal hetzelfde uit als Lisanne's sjablonen |
| **S146-S147** | `CaseActionFeed` widget op Overzicht-tab (4+5+6) + cleanup oude endpoints | 1-2 sessies | Eén plek op dossier waar updates en acties verschijnen, niet overspoeld zoals voorheen |

**Strategische opmerking:** S142 levert in één dag 4 zichtbare verbeteringen. Daarna pas grotere klussen. Dat houdt Lisanne's vertrouwen hoog dat we naar haar luisteren.

---

## Wat ik anders deed dan de eerste rapportversie

| Punt | Eerste versie | Deze versie | Reden |
|---|---|---|---|
| 2 | "Sync werkt, maar 60% niet gekoppeld" | "Handmatige Sync Mail-knop is kapot + auto-koppeling moet dossiernummer-first" | Lisanne bedoelde de handmatige knop. Plus zij gaf de matching-strategie aan: dossiernummer, niet afzender. |
| 4+5 | Twee aparte punten | Samen met punt 6 als één onderliggend probleem | Lisanne bedoelde het bolletje IN het dossier; bel-icon is een aparte bug die we ook vonden. |
| 6 | Suggestie voor nieuw widget | Concrete naam + uitleg + verwijzing naar git-historie waarom oude banners weg zijn | Sessie 134 verwijderde de banners expliciet. Nu pendant aan andere kant: te ver opgeruimd. Inzicht is dat we balans moeten vinden. |
| 7 | Architectuur-overlap (3 systemen → 1) | Architectuur + concreet layout-probleem (disclaimer-positie, foto, logo) + verwijzing naar `html_renderer.py` als unified render-pad | Lisanne voegde concrete UI-fout toe. Onderzoek wees uit dat `html_renderer.py` al bestaat maar alleen door batch-flow gebruikt. |

---

## Memory-aandacht — wat te onthouden

Te bewaren na akkoord op dit rapport:

- **`project_demo_feedback_S140_S141.md`** (project) — 7 punten van Lisanne + verduidelijking S141 + status per sessie
- **`feedback_ui_balans.md`** (feedback) — Bij nieuwe AI-feature op dossier: niet 3 parallelle banners (S134 incident) maar ook niet weglaten. Eén `CaseActionFeed` widget op Overzicht-tab is de balans. Past in de feed of helemaal niet — geen losse banner.
- **`reference_email_render_paths.md`** (reference) — `incasso_templates.py` + `html_renderer.py` is de **enige** render-pijplijn die Lisanne's layout respecteert (logo, handtekening, schuldhulp, disclaimer). `draft_service.py` en `smart_reply_service.py` slaan deze pijplijn over. Zie `incasso/automation_service.py:620` voor het enige import-punt.

**Niet bewaren:** dit rapport zelf is in `docs/onderzoek-ai-overlap-S141.md`, geen memory nodig.

---

## Wat dit rapport NIET doet

- **Geen code-wijzigingen** — alleen onderzoek
- **Geen impliciete goedkeuring** — wacht op Arsalan-akkoord op aanpak per punt
- **Geen automatische sessieplanning** — Arsalan beslist welke sessie eerst en in welke volgorde

**Volgende stap:** Arsalan reviewt deze tweede rapportversie, geeft per punt akkoord (en eventueel scope-aanpassingen), daarna pas bouw in S142+.

### Beslissingen Arsalan (sessie 141)

1. **Handtekening-foto:** Geen aparte foto van Lisanne nodig. Het Kesting Legal logo staat al in de huidige gegenereerde mails (header bovenaan + ook onderaan) — dat is correct. Sjabloon-trouw blijven is voldoende.
2. **Email-adres in handtekening:** dynamisch op basis van `Case.case_type` veld (bestaat al). `case_type == "incasso"` → `incasso@kestinglegal.nl`. `case_type in ("dossier", "advies")` → `kesting@kestinglegal.nl`.
3. **Concept-knop op Correspondentie-tab:** Definitief weg (Optie A). Alle concept-generatie gaat via CaseActionFeed op Overzicht-tab. Geen shortcut-knop, geen sticky banner over tabs heen — gewoon één plek.
4. **Suggestie-flow drempels:** 90% match = auto-koppelen, 60-90% = suggereren (1-klik bevestigen), onder 60% = ongesorteerd.

**Wat dit betekent voor de scope van S145:**
- Layout-fixes klein: alleen disclaimer-positie (`_BASE_EMAIL` template aanpassen + 40 call sites) + email-adres dynamisch op `case_type`. Geen foto-toevoeging, geen logo-data-URL migratie nodig.
- Hoofdwerk blijft: `draft_service.py` en `smart_reply_service.py` moeten dezelfde `incasso_templates._render_branded()` render-pijplijn gaan gebruiken als de batch-flow. Dán komt het logo + handtekening + correcte volgorde overal automatisch goed.
