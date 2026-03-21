Sessie 91 — Mega-audit Sprint 2: resterende CRITICAL + HIGH security/frontend
Repo: C:\Users\arsal\Documents\luxis

## Context laden bij start
Gebruik de luxis-researcher subagent:
"Lees LUXIS-ROADMAP.md (sectie 'Mega-Audit Sprint') en SESSION-NOTES.md (sessie 90). Geef compacte samenvatting."

## Taak
Fix ALLE resterende CRITICAL + HIGH issues uit de mega-audit:

**CRITICAL (5 items):**
- SEC-16: Fernet KDF zwak — `backend/app/email/token_encryption.py`. Vervang SHA-256 door PBKDF2HMAC met salt + 600k iteraties
- SEC-17: DB/Redis poorten open in prod — `docker-compose.prod.yml`. Voeg `ports: []` override toe voor db en redis services
- SEC-19: JWT in localStorage — Interim fix: centraliseer tokens in een tokenStore module i.p.v. verspreide localStorage calls. Later: httpOnly cookies
- CQ-12: Silent catch{} blocks — 14+ plaatsen in frontend waar financiele mutatie-errors worden gesliked. Zoek alle `catch` blocks in frontend hooks/components, voeg toast.error() toe
- CQ-13: parseFloat voor geldbedragen — frontend stuurt floats naar backend. Fix: gebruik string transport voor alle geldbedragen

**HIGH (3 items):**
- SEC-21: OAuth callback vertrouwt user_id uit state parameter — `backend/app/email/oauth_router.py`. Fix: server-side nonce opslaan in Redis, valideren bij callback
- SEC-23: Filename injection in Content-Disposition — `backend/app/cases/files_service.py`. Strip speciale chars uit filenames
- CQ-19: Float divisie betalingsregeling — `frontend/src/app/(dashboard)/zaken/[id]/components/incasso/BetalingsregelingSection.tsx`. Laat backend het bedrag berekenen

## Verificatie
- MSYS_NO_PATHCONV=1 docker compose exec backend ruff check app/
- MSYS_NO_PATHCONV=1 docker compose exec backend pytest tests/ -k "auth or invoice or interest" -v
- npx tsc --noEmit (in frontend/)

## Constraints (wat NIET doen)
- Geen nieuwe features
- Geen refactors buiten scope
- Geen MEDIUM/LOW items

## Commit
Commit + push na ALLE fixes. Deploy via SSH automatisch.
