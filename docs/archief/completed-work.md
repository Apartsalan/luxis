## Volgorde van werken

**✅ Afgerond:** A1-A7, B1-B3, C1-C3, D1/D3/D4/D5, E1-E8, T1-T3, F1-F10, alle bugs t/m BUG-17
**✅ VPS login gefixt** (21 feb) — DB wachtwoord mismatch opgelost, frontend herbouwd met correcte NEXT_PUBLIC_API_URL
**✅ BUG-7/8/9 gefixt** (21 feb) — edit-modus, zaaknummer op form, advocaat wederpartij
**❌ Niet relevant:** D2 (gebruikersbeheer — Lisanne is enige gebruiker)
**TODO:** SMTP omzetten van Gmail test-credentials naar Lisanne's Outlook (wacht op M365 migratie)
**✅ M0a setup klaar** (23 feb) — M365 Business Basic actief, domein geverifieerd (TXT-record, geen MX), mailbox seidony@kestinglegal.nl actief (versturen werkt), Azure App Registration + Graph API machtigingen klaar. OutlookProvider bouwen in volgende sessie.
**✅ F11 geïmplementeerd** (21 feb) — freestanding e-mail vanuit dossier met recipient quick-select chips
**✅ M6 gebouwd** (22 feb) — Ongesorteerde email wachtrij met split-view, suggesties, bulk link/dismiss, sidebar badge
**✅ Dossier detail refactoring** (sessie 5, 22 feb) — `zaken/[id]/page.tsx` van 4236 → ~236 regels, opgesplitst in 8 componentbestanden + types.tsx
**✅ G3 Procesgegevens** (sessie 6, 22 feb) — 5 nieuwe velden (court_name, judge_name, chamber, procedure_type, procedure_phase) + backend migration 028 + DetailsTab Procesgegevens card met NL rechtbank dropdown
**✅ G5 Keyboard shortcuts** (sessie 6, 22 feb) — T=timer, N=notitie, D=documenten, E=email, F=facturen, 1-9=tabs
**✅ G14 Dossier sidebar** (sessie 7, 22 feb) — Collapsible properties sidebar met dossierinfo, client, wederpartij, advocaat, financieel snapshot (OHW + incasso/non-incasso)
**✅ G10 Task templates** (sessie 7, 22 feb) — Automatische taak-templates bij case creation: incasso 8 taken, advies 4, insolventie 4, overig 2
**✅ BUG-11/12 gefixt** (sessie 8, 22 feb) — Taken zichtbaar na aanmaken + Nieuwe taak knop op Mijn Taken pagina
**✅ Incasso Batch Werkstroom** (sessie 9, 23 feb) — IncassoPipelineStep model + CRUD + batch actions + /incasso pagina met pipeline editor + batch werkstroom + pre-flight wizard + sidebar item. Migration 029.
**✅ Template koppeling + Documentgeneratie + Smart Work Queues** (sessie 10, 23 feb) — template_type op pipeline steps (modern docx systeem), batch "Verstuur brief" genereert documenten via render_docx(), Smart Work Queue tabs (klaar/14d verlopen/actie vereist) + sidebar badge. Migration 030.
**✅ UX Polish — G13 + G9 + G11** (sessie 11, 23 feb) — Budget tracking per dossier (togglebaar via "budget" module), recurring tasks (daily/weekly/monthly/quarterly/yearly + auto-create), inline document preview (eye button + PDF modal). Migrations 031 + 032.
**✅ OutlookProvider gebouwd** (sessie 13, 23 feb) — `backend/app/email/providers/outlook.py` met Microsoft Graph API. Zelfde EmailProvider interface als GmailProvider. OAuth flow, list/get/send/draft/attachments. Config + docker-compose.prod.yml + OAuth router bijgewerkt.
**✅ BUG-13 + BUG-14 gefixt** (sessie 14, 23 feb) — Email-bijlage download met blob URL + Bearer token (BUG-13), "Opslaan in dossier" knop + backend endpoint om bijlage naar case_files te kopiëren (BUG-14).
**✅ Password reset email** (sessie 15, 23 feb) — `forgot_password()` stuurt nu daadwerkelijk email via SMTP (BackgroundTasks + aiosmtplib). HTML template met "Wachtwoord herstellen" knop. Getest: email ontvangen ✅.
**✅ BUG-15 gefixt** (sessie 16, 23 feb → deployed 25 feb) — Next.js rewrite proxy (`/api/*` → `backend:8000`), alle `NEXT_PUBLIC_API_URL` vervangen door relatieve URLs. Deployed en getest.
**✅ BUG-16 gefixt** (25 feb) — Dashboard "Mijn Taken" widget gebruikte verkeerd endpoint (`/api/workflow/tasks?status=due`), nu `/api/dashboard/my-tasks`.
**✅ Advocaat wederpartij volledig gefixt** (sessie 19) — inline aanmaken, auto ContactLink, CaseParty filter in list_cases + relatiepagina
**✅ Sessie 20 QA + bugfix** (25 feb) — Playwright MCP QA over 14 secties, 3 bugs gevonden en gefixt (BUG-22/23/24). Deploy issues opgelost: `.env` ontbrak (`.env.production` → `.env` gekopieerd), notifications import path fout, frontend API prefix mismatch.
**Volgende prioriteit:** Deploy verificatie (BUG-22/23/24), daarna QA-CHECKLIST.md volledig doorlopen, daarna document template editing UI + merge fields uitbreiden.

### Sessie 12 Plan: Document Templates & Merge Fields

**Probleem 1: Templates niet bewerkbaar in UI**
De Documenten-pagina (`/documenten`) toont templates read-only. Lisanne kan ze niet aanpassen. De .docx bestanden moeten handmatig op de server vervangen worden. Oplossing: upload-functie voor .docx templates + preview met voorbeelddata.

**Probleem 2: Niet alle dossierdata komt in documenten terecht**
De `render_docx()` functie in `docx_service.py` bouwt context op maar mist:
- Procesgegevens: `court_name`, `court_case_number`, `judge_name`, `chamber`, `procedure_type`, `procedure_phase` (bestaan op Case model maar worden NIET doorgegeven)
- CaseParty data: deurwaarder, advocaat wederpartij (bestaan in DB maar niet in template context)
- Betalingstermijn: `Contact.payment_term_days` (beschikbaar maar niet doorgegeven)
- Advocaat wederpartij naam/kantoor (uit CaseParty of Case.opposing_party_lawyer)

**Aanpak:** Eerst templates finaliseren met Lisanne, dan merge fields uitbreiden.

> **Sessie-log:** Zie `SESSION-LOG-20FEB-SESSIE3.md` voor gedetailleerde context over wat er al bestaat voor email (backend email module, SMTP service, send endpoint, templates)

---
