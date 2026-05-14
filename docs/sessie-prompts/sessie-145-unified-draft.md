cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 145 — UnifiedDraftService + dynamisch email-adres + logo data-URL

## Context laden bij start

Gebruik de luxis-researcher subagent:
"Lees `docs/onderzoek-ai-overlap-S141.md` (sectie Punt 7 + Architectuur-voorstel),
SESSION-NOTES.md (sessie 141 — alleen samenvatting + 'Volgende sessie' sectie),
en LUXIS-ROADMAP.md (zoek BUG-83 t/m BUG-84 + FEAT-AI-01 t/m FEAT-AI-03).
Geef compacte samenvatting in maximaal 400 woorden — focus op:
1. Welke 3 AI-flows bestaan nu + welke render-pijplijn ze gebruiken
2. Wat `incasso_templates._render_branded()` doet en wie hem nu aanroept
3. Beslissingen Arsalan S141 (geen aparte foto, case_type-afhankelijk email-adres, drempels)
4. Status BUG-83 (bel-icon) en BUG-84 (notification-types) — open issues"

## Taak — Hoofdfocus: AI-flows consolideren naar één render-pijplijn

**Doel:** alle 3 AI-flows (incasso-batch / context-draft / smart-reply) routeren via
`incasso_templates._render_branded()` zodat layout consistent is met sjablonen.
Plus: handtekening email-regel dynamisch op `Case.case_type`, logo embedden als
data-URL.

### Subtaak 1 — `app/ai_agent/unified_draft_service.py` (nieuw)

Eén service met 3 intents. AI levert ALTIJD plain body (subject + body string),
geen raw HTML. Server-side wrap via `_render_branded`.

```python
class DraftIntent(str, Enum):
    NEXT_STEP = "next_step"        # outbound vanuit pipeline-stap
    REPLY_TO_EMAIL = "reply_to_email"  # antwoord op inbound (smart-reply use case)
    FREE_COMPOSE = "free_compose"  # vrije generatie op case-context


async def generate_draft(
    db, tenant_id, user_id, *, case_id, intent, tone=None, source_email_id=None
) -> AIDraftResponse:
    case = await get_case(...)
    base_context = await build_base_context(db, case)

    if intent == DraftIntent.NEXT_STEP:
        # Vul step-sjabloon via AI (alleen body), wrap via _render_branded
        plain_body = await _ai_complete_template(case, case.incasso_step, ...)
        html = _render_branded(base_context, betreft=..., content_html=plain_body,
                               afsluiting_html=_signature(base_context),
                               disclaimer_html=_schuldhulp_disclaimer(base_context))
    elif intent == DraftIntent.REPLY_TO_EMAIL:
        # AI maakt reply met tone, classification context, defense library
        plain_body = await _ai_reply_to_email(case, source_email_id, tone=tone, ...)
        html = _render_branded(...)  # zelfde wrap
    else:  # FREE_COMPOSE
        plain_body = await _ai_free_compose(case, base_context, ...)
        html = _render_branded(...)

    draft = AIDraft(case_id=case.id, body=plain_body, body_html=html, status='generated', ...)
    db.add(draft); await db.flush()
    return _draft_to_response(draft)
```

### Subtaak 2 — Endpoint `POST /api/ai/draft`

Body: `{case_id: UUID, intent: str, tone?: str, source_email_id?: UUID}`.
Response: `AIDraftResponse` (zelfde schema als bestaande draft endpoints).

Locatie: `app/ai_agent/router.py` — nieuw endpoint NAAST bestaande
(`/api/ai-agent/draft/{case_id}` blijft bestaan, marked deprecated in docstring).

### Subtaak 3 — Dynamisch email-adres in `_signature()`

`backend/app/email/incasso_templates.py:215-246` huidige `_signature()` returnt
hardcoded `E: incasso@kestinglegal.nl`. Aanpassen:

```python
def _signature(ctx: dict, english: bool = False) -> str:
    case_type = ctx.get("zaak", {}).get("case_type", "incasso")
    email_addr = "incasso@kestinglegal.nl" if case_type == "incasso" else "kesting@kestinglegal.nl"
    # ... rest of function
```

`build_base_context()` moet `case_type` in `ctx['zaak']` zetten. Check
`docx_service.build_base_context` in backend — voeg case_type toe als 't er nog
niet in zit.

### Subtaak 4 — Logo data-URL

`_BASE_EMAIL:35-36` heeft nu `<img src="https://kestinglegal.nl/logo.png">`.
Vervangen door data-URL via bestaand `templates/lisanne/_kesting_logo.b64`.

```python
from pathlib import Path
_LOGO_B64 = (Path(__file__).parent.parent.parent / "templates" / "lisanne" / "_kesting_logo.b64").read_text().strip()
_LOGO_DATA_URL = f"data:image/png;base64,{_LOGO_B64}"
```

En in `_BASE_EMAIL`: `<img src="{{ logo_data_url }}" ...>` — `_render_branded`
geeft `logo_data_url=_LOGO_DATA_URL` mee aan render-context.

### Subtaak 5 — Tests

- `tests/test_unified_draft_service.py` (nieuw) — happy-path per intent
- Test dat email-adres correct switcht op `case_type`
- Test dat logo render-pijplijn data-URL output bevat
- `_assert_base_nl` in `test_incasso_templates.py` uitbreiden met email-check

## Constraints (wat NIET doen)

- **GEEN frontend werk** — `CaseActionFeed` widget is S146-147, niet nu
- **OUDE endpoints blijven** — `/api/ai-agent/draft/{case_id}` + smart-replies
  niet verwijderen. UnifiedDraftService draait parallel, frontend migratie later
- **GEEN bel-icon fix** (BUG-83) — vereist Lisanne devtools-check, niet codebar
- **GEEN nieuwe notification-types** (BUG-84) — onderdeel S146-147 CaseActionFeed
- **GEEN refactor van bestaande** `draft_service.py` of `smart_reply_service.py`
  zelf — alleen parallel-systeem bouwen. Deprecatie in vervolgsessie

## Verificatie

- Backend: `docker compose exec backend pytest tests/test_unified_draft_service.py tests/test_incasso_templates.py -v`
- Lint: `docker compose exec backend ruff check app/`
- Manual: nieuwe endpoint testen via `curl -X POST .../api/ai/draft -d '{"case_id":"...","intent":"next_step"}'` — response moet `body_html` bevatten met logo data-URL + email-adres matchend case_type

## Commit

Conventional commits per subtaak:
- `feat(ai-agent): UnifiedDraftService met intents next_step/reply_to_email/free_compose`
- `feat(email): handtekening email-adres dynamisch op case_type`
- `fix(email): logo embedded als data-URL i.p.v. externe URL`
- `test(ai-agent): UnifiedDraftService happy-path + email/logo regressies`

Push + auto-deploy via SSH na laatste commit.

## Memory-aandacht

- `feedback_grondig_checken` — niet alleen tests, ook visueel checken in browser
- `feedback_kritisch_zijn` — als unified service NIET past in 1 sessie, deel op
- `feedback_test_recipient_safety` — als email-test gedaan wordt: recipient
  ALTIJD `arsalanir@hotmail.com`, NOOIT klant/wederpartij/lisanne@

## Volgende sessie na S145

S146-147 — `CaseActionFeed` widget op Overzicht-tab. Verbruikt UnifiedDraftService
endpoint voor concept-generatie. Plus notification-types uitbreiden
(`email_received`, `draft_ready`, `classification_done`) zodat bel-icon wel
nuttige meldingen toont.
