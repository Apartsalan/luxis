# Sessie Notities — Luxis

**Laatst bijgewerkt:** 21 feb 2025
**Laatste feature:** F11 — Freestanding e-mail vanuit dossier

## Wat er gedaan is
- F11 geïmplementeerd: vrije e-mail versturen vanuit een dossier naar elke partij
- Backend: nieuw `POST /api/email/cases/{case_id}/send` endpoint met EmailLog + CaseActivity logging
- Frontend: recipient quick-select chips (Clio/PracticePanther-stijl), E-mail knop in Quick Actions, "Nieuwe e-mail" knop in CorrespondentieTab
- Dossier werkplek competitief onderzoek uitgevoerd (6 concurrenten + 5 SaaS-apps)
- DOSSIER-WERKPLEK-RESEARCH.md aangemaakt met gap-analyse (22 features ✅, 15 gaps G1-G15)
- Plan Mode regel toegevoegd aan CLAUDE.md
- Context Management regels + slash commands toegevoegd

## Wat de volgende stap is
- Dossier workspace verbeteringen uit DOSSIER-WERKPLEK-RESEARCH.md (G3-G15)
- Prioriteiten: G3 (procesgegevens), G5 (keyboard shortcuts), G14 (sidebar), G10 (task templates)
- SMTP migratie van Gmail test-credentials naar Lisanne's Outlook (wacht op M365)

## Bestanden die zijn aangepast (deze sessie)
- `backend/app/email/schemas.py` — NIEUW
- `backend/app/email/router.py` — nieuw endpoint
- `frontend/src/hooks/use-documents.ts` — useSendCaseEmail hook
- `frontend/src/hooks/use-cases.ts` — email veld op CaseSummary
- `frontend/src/components/email-compose-dialog.tsx` — recipient chips
- `frontend/src/app/(dashboard)/zaken/[id]/page.tsx` — E-mail knop + CorrespondentieTab
- `CLAUDE.md` — Plan Mode + Context Management regels
- `DOSSIER-WERKPLEK-RESEARCH.md` — NIEUW, competitief onderzoek
- `LUXIS-ROADMAP.md` — F11 als ✅ gemarkeerd
- `.claude/commands/sessie-einde.md` — NIEUW
- `.claude/commands/sessie-start.md` — NIEUW

## Openstaande issues
- Geen bekende bugs
- SMTP gebruikt nog Gmail test-credentials (werkt, maar moet naar Outlook)
- Dossier detail page is 47K+ regels — refactoring naar losse componenten gewenst (lage prio)

## Beslissingen genomen
- F11 gebruikt bestaande EmailLog model (geen migratie nodig) met template="freestanding" en document_id=None
- Recipient chips gebruiken dezelfde EmailComposeDialog (backward-compatible via optionele `recipients` prop)
- SESSION-NOTES.md vervangt HANDOVER.md als primair handover-document
