# Sessie-log 20 feb 2026 — Sessie 3

**Wat is er gedaan:** C3 (Credit nota's) volledig afgerond + deployment + roadmap review
**Volgende taak:** T3 + E8 — E-mail vanuit Luxis (SMTP + email templates)
**Repo:** `C:\Users\arsal\Documents\luxis`

---

## Beslissingen

1. **D2 (Gebruikersbeheer) is NIET relevant** — Lisanne is de enige gebruiker, geen rollen/rechten nodig
2. **Volgende feature: T3 + E8 (Email)** — Arsalan koos voor mail. Dit is de meest impactvolle Basenet-vervanger
3. **Credit nota migratie is gestamped** — Kolommen bestonden al in DB, `alembic stamp 021_credit_notes` is uitgevoerd

---

## Wat er al af is (complete feature-lijst)

### Volledig gebouwd en gedeployd
- A1-A7 (alle quick wins)
- B1-B3 (zaakdetail transformatie)
- C1-C3 (dashboard + facturatie + credit nota's)
- D1, D3, D4, D5 (wachtwoord, navigatie, loading states, agenda)
- E1-E7 (alle verbeterpunten behalve E8)
- Alle bugs (BUG-1 t/m BUG-6) gefixt

### Nog te bouwen
| # | Feature | Status |
|---|---------|--------|
| E8 | E-mail templates (onderwerp + body + merge fields) | Niet gestart — wordt onderdeel van T3 |
| T1 | Templates op zaakdetail (status-filtered) | Niet gestart |
| T2 | Workflow-suggesties bij statuswijziging | Niet gestart |
| T3 | E-mail versturen vanuit Luxis (SMTP) | Niet gestart |
| D2 | Gebruikersbeheer | ❌ Niet relevant |

---

## Wat er al bestaat voor E-mail (belangrijk voor volgende sessie!)

### Backend — Email module is al gebouwd!

**`backend/app/email/`** bevat:
- **`models.py`** — `EmailLog` model (tenant_id, case_id, document_id, template, recipient, subject, status, error_message, sent_at)
- **`service.py`** — `send_email()` functie met aiosmtplib (async SMTP), ondersteunt bijlagen
- **`templates.py`** — 5 Jinja2 email templates:
  1. `document_sent()` — document als bijlage sturen
  2. `deadline_reminder()` — deadline herinnering
  3. `payment_confirmation()` — betalingsbevestiging
  4. `status_change()` — status wijziging
  5. Base HTML wrapper met kantoorgegevens

**Alembic migratie:** `011_email_logs` — tabel bestaat al in productie-DB

### Backend — Documents module heeft al een send endpoint

**`backend/app/documents/router.py`** regel 275-370:
```
POST /api/documents/{document_id}/send
```
- Ontvangt `SendDocumentRequest` (recipient_email, recipient_name)
- Re-rendert DOCX template → converteert naar PDF → stuurt via email
- Logt in `email_logs` tabel
- Retourneert `SendDocumentResponse` (email_log_id, recipient, subject, status)

### Backend — SMTP configuratie

**`backend/app/config.py`** bevat:
```python
smtp_host: str = ""       # SMTP server hostname
smtp_port: int = 587      # SMTP port
smtp_user: str = ""       # SMTP username
smtp_pass: str = ""       # SMTP password
smtp_from: str = ""       # From email address
smtp_use_tls: bool = True # TLS encryption
```
Variabelen via environment/docker-compose, **momenteel allemaal leeg** (niet geconfigureerd).

### Backend — DOCX Templates systeem

**`backend/app/documents/docx_service.py`**:
- 7 template types: 14_dagenbrief, sommatie, renteoverzicht, herinnering, aanmaning, tweede_sommatie, dagvaarding
- Templates in `templates/` directory (gemount in Docker)
- Merge fields voor: kantoor, zaak, client, wederpartij, financieel, datums, lijsten
- `render_docx()` functie bouwt context + rendert

### Frontend — Documenten tab op zaakdetail

**`frontend/src/app/(dashboard)/zaken/[id]/page.tsx`** regel ~3072:
- `DocumentenTab` component bestaat al
- Toont template dropdown voor document generatie
- Heeft al upload functionaliteit voor bestanden
- Toont gegenereerde documenten lijst
- **GEEN "verstuur per e-mail" knop** — dit moet gebouwd worden

### Frontend — Instellingen pagina

**`frontend/src/app/(dashboard)/instellingen/page.tsx`**:
- Tabs: Profiel, Kantoor, Modules, Team, Workflow, Meldingen, Weergave
- **GEEN SMTP-instellingen tab** — moet worden toegevoegd

### Frontend — Hooks

**`frontend/src/hooks/use-documents.ts`** — bestaande hooks voor documenten (CRUD, genereren, case-bestanden)
- **GEEN** hook voor document versturen per email

---

## Wat er gebouwd moet worden voor T3 + E8

### Stap 1: SMTP Instellingen UI (frontend)
- Nieuwe tab "E-mail" toevoegen aan Instellingen pagina
- Velden: SMTP host, port, gebruiker, wachtwoord, afzender, TLS toggle
- "Testmail versturen" knop
- **Backend nodig:** endpoint om SMTP settings per tenant op te slaan (nu zijn het env vars, niet per-tenant)

### Stap 2: Backend — Per-tenant SMTP (optioneel, of env-var gebruiken voor nu)
- **Optie A (simpel):** Gebruik de bestaande env-var SMTP config. Lisanne is enige tenant, dus dit is prima voor nu.
- **Optie B (schaalbaar):** SMTP credentials in tenant_settings tabel. Encrypted opslaan.
- **Aanbeveling:** Start met Optie A, bouw later Optie B als er meer tenants komen.

### Stap 3: "Verstuur per e-mail" knop op DocumentenTab
- Na document generatie: knop "Verstuur per e-mail"
- Email compose formulier:
  - Aan: vooringevuld met wederpartij e-mail (uit dossier)
  - CC: optioneel
  - Onderwerp: vooringevuld (bijv. "Sommatie inzake [zaak] - [kenmerk]")
  - Body: standaardtekst per template type (bewerkbaar)
  - Bijlage: gegenereerde PDF (auto)
- Verstuurt via bestaand `POST /api/documents/{id}/send` endpoint

### Stap 4: Email compose modal/dialog
- Herbruikbare component voor email versturen
- Pre-fill velden op basis van context (document, zaak, contact)
- CC-veld met contact picker

### Stap 5: Email templates (E8)
- Bewerkbare email body templates per document type
- Onderwerp template met merge fields
- Backend: email template CRUD of configureerbare templates in tenant settings

### Stap 6: Email log op dossierdetail
- Nieuwe sectie of tab: "Correspondentie" of bij Activiteiten
- Toont verzonden emails met status, datum, ontvanger
- Link naar document

---

## Relevante bestanden voor volgende sessie

### Backend (in `C:\Users\arsal\Documents\luxis\backend\`)
| Bestand | Wat | Regel |
|---------|-----|-------|
| `app/email/service.py` | SMTP email service (aiosmtplib) | Volledig (77 regels) |
| `app/email/templates.py` | 5 email Jinja2 templates | Volledig (196 regels) |
| `app/email/models.py` | EmailLog model | Volledig |
| `app/documents/router.py` | POST /{id}/send endpoint | 275-370 |
| `app/documents/docx_service.py` | DOCX rendering + merge fields | Volledig (525 regels) |
| `app/documents/schemas.py` | SendDocumentRequest/Response | Relevant |
| `app/config.py` | SMTP settings (env vars) | smtp_* velden |
| `app/settings/service.py` | Tenant settings CRUD | Volledig |
| `app/settings/schemas.py` | TenantSettingsResponse/Update | Volledig |
| `app/invoices/router.py` | Factuur endpoints (evt. factuur mailen) | Volledig |
| `alembic/versions/011_email_logs.py` | EmailLog migratie (al in DB) | Volledig |

### Frontend (in `C:\Users\arsal\Documents\luxis\frontend\src\`)
| Bestand | Wat | Regel |
|---------|-----|-------|
| `app/(dashboard)/zaken/[id]/page.tsx` | Zaakdetail met DocumentenTab | ~3072+ (groot bestand, ~3300 regels) |
| `app/(dashboard)/instellingen/page.tsx` | Instellingen (SMTP tab toevoegen) | Volledig (~800 regels) |
| `app/(dashboard)/documenten/page.tsx` | Documenten beheerpagina | Volledig |
| `hooks/use-documents.ts` | Document hooks (send hook toevoegen) | Volledig |
| `hooks/use-settings.ts` | Settings hooks | Volledig |
| `hooks/use-invoices.ts` | Invoice hooks (voor factuur mailen) | Volledig |

### Documentatie (in `C:\Users\arsal\Documents\luxis\`)
| Bestand | Wat |
|---------|-----|
| `PROMPT-TEMPLATES-IN-WORKFLOW.md` | Volledige spec voor T1/T2/T3 |
| `LUXIS-ROADMAP.md` | Source of truth voor status |
| `CLAUDE.md` | Backend + frontend conventies |
| `backend/CLAUDE.md` | Backend-specifieke regels |
| `frontend/CLAUDE.md` | Frontend-specifieke regels |

---

## Git status
- **Branch:** main
- **Laatste commit:** `ee5feef` — feat(invoices): credit notes (creditnota's) with full lifecycle (C3)
- **Working tree:** clean (behalve `UX-RESEARCH-A6-A7.md` untracked)
- **Remote:** up to date met origin/main
- **Productie:** alles gedeployd, `alembic stamp 021_credit_notes` uitgevoerd

---

## Aanbevolen aanpak volgende sessie

1. **Lees dit log eerst** — alle context staat hierin
2. **Optie A (simpel) voor SMTP** — gebruik env-var config, niet per-tenant
3. **Begin met frontend "Verstuur per e-mail" knop** op DocumentenTab — backend endpoint bestaat al
4. **Dan email compose dialog** met pre-fill uit dossiercontext
5. **Dan E8: bewerkbare email templates** — body + onderwerp per document type
6. **Optioneel: SMTP test knop** op instellingen pagina
7. **Lisanne moet SMTP credentials aanleveren** (Outlook/365) — dit is een prerequisite voor testen

---

## SMTP setup voor Lisanne (todo voor Arsalan)

Lisanne gebruikt Outlook/365. Ze heeft nodig:
- **SMTP host:** `smtp.office365.com`
- **SMTP port:** `587`
- **SMTP user:** haar e-mailadres
- **SMTP pass:** app password (als MFA aan staat) of gewoon wachtwoord
- **SMTP from:** haar e-mailadres
- **TLS:** true

Dit moet in `.env.production` op de VPS worden gezet:
```
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=lisanne@kestinglegal.nl
SMTP_PASS=<app-password>
SMTP_FROM=lisanne@kestinglegal.nl
SMTP_USE_TLS=true
```

**Let op:** Microsoft 365 heeft mogelijk "app passwords" nodig als MFA is ingeschakeld. Basic auth is deprecated bij Microsoft — mogelijk is OAuth nodig (dat is T3 fase 2).

---

## Startprompts voor volgende sessie

### HOOFD-TERMINAL (Terminal 1) — Coördinatie + Frontend email compose

```
Ik werk aan Luxis PMS (C:\Users\arsal\Documents\luxis). Lees EERST het sessie-log:
C:\Users\arsal\Documents\luxis\SESSION-LOG-20FEB-SESSIE3.md

Daarna lees:
- C:\Users\arsal\Documents\luxis\LUXIS-ROADMAP.md
- C:\Users\arsal\Documents\luxis\PROMPT-TEMPLATES-IN-WORKFLOW.md
- C:\Users\arsal\Documents\luxis\frontend\CLAUDE.md
- C:\Users\arsal\Documents\luxis\backend\CLAUDE.md

We bouwen T3 + E8: E-mail vanuit Luxis. De backend email module BESTAAT AL (send endpoint, SMTP service, email templates, EmailLog model). We gebruiken Optie A (env-var SMTP, niet per-tenant).

Jouw taak:
1. Bouw een email compose dialog component (frontend/src/components/email-compose-dialog.tsx) — een herbruikbare modal met: Aan, CC, Onderwerp, Body (textarea), bijlage-indicator. Pre-fill vanuit document/zaak context.
2. Voeg een "Verstuur per e-mail" knop toe op de DocumentenTab in frontend/src/app/(dashboard)/zaken/[id]/page.tsx (regel ~3072+) — naast elk gegenereerd document.
3. Maak een useSendDocument hook in frontend/src/hooks/use-documents.ts die POST /api/documents/{id}/send aanroept.
4. Na succes: toast "E-mail verzonden" + invalidate document queries.

Begin met het lezen van de bestaande code en maak dan een plan. Run `npm run build` na elke wijziging.

BELANGRIJK: Twee andere terminals werken parallel:
- Terminal 2 werkt aan backend uitbreidingen (CC-veld, custom subject/body op send endpoint)
- Terminal 3 werkt aan email log UI op dossierdetail + correspondentie tab
Bouw jouw deel zo dat het samenwerkt. Commit NIET zelf — ik doe de git commit vanuit deze terminal als alles klaar is.
```

### TERMINAL 2 — Backend uitbreidingen

```
Ik werk aan Luxis PMS (C:\Users\arsal\Documents\luxis). Lees EERST:
C:\Users\arsal\Documents\luxis\SESSION-LOG-20FEB-SESSIE3.md

Daarna lees:
- C:\Users\arsal\Documents\luxis\backend\CLAUDE.md
- C:\Users\arsal\Documents\luxis\backend\app\email\service.py
- C:\Users\arsal\Documents\luxis\backend\app\email\templates.py
- C:\Users\arsal\Documents\luxis\backend\app\email\models.py
- C:\Users\arsal\Documents\luxis\backend\app\documents\router.py (regel 275-370: send endpoint)
- C:\Users\arsal\Documents\luxis\backend\app\documents\schemas.py (SendDocumentRequest/Response)
- C:\Users\arsal\Documents\luxis\backend\app\config.py (SMTP settings)

We bouwen T3 + E8: E-mail vanuit Luxis. Jouw taak is ALLEEN backend:

1. Breid SendDocumentRequest (schemas.py) uit met optionele velden:
   - cc: list[str] | None = None
   - custom_subject: str | None = None
   - custom_body: str | None = None
   Zodat de frontend een eigen onderwerp/body kan meesturen i.p.v. de standaard template.

2. Pas de send_document endpoint (router.py regel 275-370) aan:
   - Als custom_subject is meegegeven: gebruik die i.p.v. template subject
   - Als custom_body is meegegeven: wrap die in de base HTML layout i.p.v. template body
   - Als cc is meegegeven: stuur CC mee (pas send_email in service.py aan om CC te ondersteunen)

3. Pas send_email() in email/service.py aan om CC te ondersteunen (cc: list[str] | None = None parameter).

4. Maak een nieuw endpoint: GET /api/documents/cases/{case_id}/email-logs
   - Retourneert alle EmailLog entries voor een case
   - Sortering: nieuwste eerst
   - Response schema: EmailLogResponse (id, recipient, subject, status, sent_at, document_id, template)

5. Maak een endpoint: POST /api/email/test — stuurt een test-email naar een opgegeven adres om SMTP configuratie te verifiëren.

Run pytest na elke wijziging. Commit NIET zelf — de hoofdterminal doet de commit.
```

### TERMINAL 3 — Frontend email log + correspondentie (optioneel, als je 3 terminals wilt)

```
Ik werk aan Luxis PMS (C:\Users\arsal\Documents\luxis). Lees EERST:
C:\Users\arsal\Documents\luxis\SESSION-LOG-20FEB-SESSIE3.md

Daarna lees:
- C:\Users\arsal\Documents\luxis\frontend\CLAUDE.md
- C:\Users\arsal\Documents\luxis\frontend\src\app\(dashboard)\zaken\[id]\page.tsx (het hele bestand, ~3300 regels — let op de tab-structuur rond regel 371)
- C:\Users\arsal\Documents\luxis\frontend\src\hooks\use-documents.ts
- C:\Users\arsal\Documents\luxis\frontend\src\app\(dashboard)\instellingen\page.tsx

We bouwen T3 + E8: E-mail vanuit Luxis. Jouw taak:

1. Maak een useEmailLogs hook in frontend/src/hooks/use-documents.ts:
   - GET /api/documents/cases/{caseId}/email-logs
   - Return type: EmailLogEntry[] (id, recipient, subject, status, sent_at, document_id, template)

2. Voeg een "Correspondentie" sectie toe aan het Overzicht-tab van de zaakdetailpagina (of maak een nieuw tab):
   - Toont verzonden emails met: datum, ontvanger, onderwerp, status (sent/failed), link naar document
   - Lege state als er geen emails zijn
   - Styling consistent met de rest van het dossierdetail

3. Voeg een "E-mail" tab toe aan de Instellingen pagina (frontend/src/app/(dashboard)/instellingen/page.tsx):
   - Informatief: toont of SMTP geconfigureerd is (via een nieuw GET /api/email/status endpoint, of gewoon een boolean check)
   - Tekst: "E-mail is geconfigureerd via de server. Neem contact op met de beheerder om de SMTP-instellingen te wijzigen."
   - "Test e-mail versturen" knop die POST /api/email/test aanroept met het e-mailadres van de ingelogde gebruiker

Run `npm run build` na elke wijziging. Commit NIET zelf — de hoofdterminal doet de commit.
```

---

*Einde sessie-log*
