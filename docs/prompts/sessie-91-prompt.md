Sessie 91 — Mega-audit Sprint 2: CRITICAL + HIGH security + frontend error handling
Repo: C:\Users\arsal\Documents\luxis

## Context laden bij start
Gebruik de luxis-researcher subagent:
"Lees LUXIS-ROADMAP.md (sectie 'Mega-Audit Sprint') en SESSION-NOTES.md (sessie 90). Geef compacte samenvatting."

## Taak
Fix resterende CRITICAL + HIGH issues (backend security + frontend error handling):

**CRITICAL (4 items):**
- SEC-16: Fernet KDF zwak — `backend/app/email/token_encryption.py`. Vervang SHA-256 door PBKDF2HMAC met salt + 600k iteraties
- SEC-19: JWT in localStorage — Interim fix: centraliseer tokens in een tokenStore module i.p.v. verspreide localStorage calls. Later: httpOnly cookies
- CQ-12: Silent catch{} blocks — 14+ plaatsen in frontend waar financiele mutatie-errors worden gesliked. Zoek alle `catch` blocks in frontend hooks/components, voeg toast.error() toe
- CQ-13: parseFloat voor geldbedragen — frontend stuurt floats naar backend. Fix: gebruik string transport voor alle geldbedragen

**HIGH (3 items):**
- SEC-21: OAuth callback vertrouwt user_id uit state parameter — `backend/app/email/oauth_router.py`. Fix: server-side nonce opslaan in Redis, valideren bij callback
- SEC-23: Filename injection in Content-Disposition — `backend/app/cases/files_service.py`. Strip speciale chars uit filenames
- CQ-19: Float divisie betalingsregeling — `frontend/src/app/(dashboard)/zaken/[id]/components/incasso/BetalingsregelingSection.tsx`. Laat backend het bedrag berekenen

**UX (uit sessie 93 verplaatst — hoort bij error handling):**
- UX-21: isError niet afgevangen — financiële queries tonen lege lijst i.p.v. error state. Fix: error state component in dezelfde hooks als CQ-12

## Verificatie
- MSYS_NO_PATHCONV=1 docker compose exec backend ruff check app/
- MSYS_NO_PATHCONV=1 docker compose exec backend pytest tests/ -k "auth or invoice or interest" -v
- npx tsc --noEmit (in frontend/)

## Constraints (wat NIET doen)
- Geen docker-compose.prod.yml wijzigen (dat doet sessie 92)
- Geen nieuwe features
- Geen refactors buiten scope
- NIET committen of pushen — meld dat je klaar bent (andere terminals draaien parallel)

## Commit
NIET zelf committen. Terminal A regelt commit + push voor alle terminals.
