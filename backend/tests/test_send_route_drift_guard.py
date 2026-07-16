"""Wachters M2 + M4 (S224, skill breed-testen) — verzendroute-drift-guards.

Fouten wonen op kruispunten: één gedrag (mail versturen) is via meerdere routes
bereikbaar en één route mist de huisregel. Deze wachters enumereren de routes
rechtstreeks uit de broncode (AST), zodat een TOEKOMSTIGE route die de regel
mist hier automatisch rood valt — het patroon van test_auth_drift_guard.py.

- M2 (drieluik-logging): niemand roept rauw een provider-/SMTP-uitgang aan
  buiten de twee geloggde uitgangen (send_with_attachment, compose/send) en de
  hieronder gemotiveerde uitzonderingen. De twee geloggde uitgangen moeten
  aantoonbaar write_outbound_log aanroepen.
- M4 (onderwerp-bouwer): elke verzend-aanroep bouwt zijn onderwerp via
  build_email_subject/build_reply_subject, of staat mét motivering op de
  allowlist. Een nieuwe route zonder bouwer maakt deze test rood.

Een regel hier weghalen mag alleen samen met de fix die hem overbodig maakt.
"""

import ast
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1] / "app"

# ── M2: verwachte rauwe uitgangen ────────────────────────────────────────────

# Aanroepers van provider.send_message buiten de provider-implementaties zelf.
EXPECTED_PROVIDER_EXITS = {
    # Logt via write_outbound_log (S220 N1) — zie test hieronder.
    ("app/email/compose_router.py", "send_via_provider"),
    # HET gedeelde verzendkanaal; logt zelf via write_outbound_log.
    ("app/email/send_service.py", "send_with_attachment"),
}

# Aanroepers van de rauwe SMTP-functie (app.email.service.send_email).
EXPECTED_SMTP_EXITS = {
    # SMTP-terugval bínnen het gedeelde kanaal (logt via write_outbound_log).
    ("app/email/send_service.py", "send_with_attachment"),
    # Instellingen-test: geen dossier-mail, bewust buiten het drieluik.
    ("app/email/router.py", "send_test_email"),
    # Legacy losse-mail-route: UI-dood sinds S220 (alleen nog als API aanroepbaar);
    # logt EmailLog + CaseActivity maar géén SyncedEmail. Opruimen = beslispunt
    # B3 (S224-veegrapport) — verwijder deze regel zodra het endpoint weg is.
    ("app/email/router.py", "send_case_email"),
    # Wachtwoord-reset: systeemmail, geen dossier-mail.
    ("app/auth/router.py", "_send_reset_email_safe"),
}

# ── M4: verzend-aanroepen waarvan het onderwerp NIET rechtstreeks uit de
# gedeelde bouwer komt — elk mét motivering. Nieuw = rood. ───────────────────

SUBJECT_ALLOWLIST = {
    # data.subject: vrije mail = gebruikers-onderwerp; concept-/sjabloonroutes
    # krijgen het bouwer-onderwerp al server-side mee (S223).
    ("app/email/compose_router.py", "send_via_provider"),
    # Doorgeefluik: subject is een parameter, de aanroepers bouwen hem.
    ("app/email/send_service.py", "send_with_attachment"),
    # DOCX-tak: bouwer-onderwerp via variabele email_subject (regel ~508).
    ("app/ai_agent/followup_service.py", "execute_recommendation"),
    # DOCX-tak: onderwerp via _build_step_email → daarbinnen de bouwer (S223).
    ("app/incasso/service.py", "batch_execute"),
    # custom_subject van de gebruiker; fallback = bouwer via default_subject (S224).
    ("app/documents/router.py", "send_document"),
    # Facturen aan de OPDRACHTGEVER: bewust eigen formaat "Factuur {nr}"
    # (huisformaat is voor debiteur-correspondentie) — beslispunt B1 S224.
    ("app/invoices/service.py", "send_invoice"),
    # Antwoord via goedgekeurde classificatie: onderwerp uit het beheerde
    # ResponseTemplate (geen stale BaseNet-sjabloon). Vondst V2c S224:
    # kandidaat om naar build_reply_subject te verhuizen.
    ("app/ai_agent/service.py", "execute_classification"),
    # Dode route (registry zonder aanroepers) — beslispunt B2 S224: opruimen.
    ("app/ai_agent/tools/handlers/email.py", "handle_email_compose"),
    # Instellingen-test + legacy route + wachtwoord-reset: vaste/systeem-onderwerpen.
    ("app/email/router.py", "send_test_email"),
    ("app/email/router.py", "send_case_email"),
    ("app/auth/router.py", "_send_reset_email_safe"),
}

SUBJECT_BUILDERS = {"build_email_subject", "build_reply_subject"}


# ── AST-hulpjes ──────────────────────────────────────────────────────────────


def _modules():
    for path in sorted(APP_DIR.rglob("*.py")):
        rel = "app/" + path.relative_to(APP_DIR).as_posix()
        yield rel, ast.parse(path.read_text(encoding="utf-8"))


def _walk_calls(node, fname="<module>"):
    """Yield (omsluitende_functienaam, Call-node) voor de hele boom."""
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        fname = node.name
    if isinstance(node, ast.Call):
        yield fname, node
    for child in ast.iter_child_nodes(node):
        yield from _walk_calls(child, fname)


def _smtp_aliases(tree) -> set[str]:
    """Namen waaronder app.email.service.send_email in deze module is geïmporteerd."""
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "app.email.service":
            for alias in node.names:
                if alias.name == "send_email":
                    names.add(alias.asname or alias.name)
    return names


def _called_name(call: ast.Call) -> str | None:
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None


def _kwarg(call: ast.Call, name: str):
    for kw in call.keywords:
        if kw.arg == name:
            return kw.value
    return None


# ── M2: drieluik-wachter ─────────────────────────────────────────────────────


def test_geen_rauwe_provider_uitgang_buiten_geloggde_routes():
    """Elke route die rechtstreeks provider.send_message aanroept moet hier
    expliciet staan; alles anders hoort via send_with_attachment te lopen."""
    found = set()
    for rel, tree in _modules():
        if rel.startswith("app/email/providers/"):
            continue  # de provider-implementaties zelf
        for fname, call in _walk_calls(tree):
            if _called_name(call) == "send_message":
                found.add((rel, fname))
    assert found == EXPECTED_PROVIDER_EXITS, (
        f"Provider-uitgangen wijken af.\nNieuw (route zonder drieluik-logging?): "
        f"{sorted(found - EXPECTED_PROVIDER_EXITS)}\n"
        f"Verdwenen (allowlist bijwerken): {sorted(EXPECTED_PROVIDER_EXITS - found)}"
    )


def test_geen_rauwe_smtp_uitgang_buiten_gemotiveerde_routes():
    found = set()
    for rel, tree in _modules():
        if rel == "app/email/service.py":
            continue  # de SMTP-uitgang zelf
        aliases = _smtp_aliases(tree)
        if not aliases:
            continue
        for fname, call in _walk_calls(tree):
            if isinstance(call.func, ast.Name) and call.func.id in aliases:
                found.add((rel, fname))
    assert found == EXPECTED_SMTP_EXITS, (
        f"SMTP-uitgangen wijken af.\nNieuw: {sorted(found - EXPECTED_SMTP_EXITS)}\n"
        f"Verdwenen: {sorted(EXPECTED_SMTP_EXITS - found)}"
    )


def test_geloggde_uitgangen_roepen_write_outbound_log_aan():
    """De twee provider-uitgangen moeten het drieluik aantoonbaar wegschrijven."""
    for rel, expected_fn in sorted(EXPECTED_PROVIDER_EXITS):
        tree = ast.parse((APP_DIR.parent / rel).read_text(encoding="utf-8"))
        calls_in_fn = {
            _called_name(call)
            for fname, call in _walk_calls(tree)
            if fname == expected_fn
        }
        assert "write_outbound_log" in calls_in_fn, (
            f"{rel}::{expected_fn} roept provider.send_message aan maar niet "
            f"write_outbound_log — drieluik (EmailLog+SyncedEmail+CaseActivity) mist"
        )


# ── M4: onderwerp-wachter ────────────────────────────────────────────────────


def test_onderwerp_komt_uit_de_gedeelde_bouwer():
    """Elke verzend-aanroep (send_with_attachment / provider.send_message / SMTP)
    geeft óf rechtstreeks een bouwer-resultaat als subject mee, óf staat mét
    motivering op de allowlist hierboven."""
    violations = set()
    for rel, tree in _modules():
        if rel.startswith("app/email/providers/") or rel == "app/email/service.py":
            continue
        aliases = _smtp_aliases(tree)
        for fname, call in _walk_calls(tree):
            called = _called_name(call)
            is_send = (
                called == "send_with_attachment"
                or called == "send_message"
                or (isinstance(call.func, ast.Name) and call.func.id in aliases)
            )
            if not is_send:
                continue
            subject = _kwarg(call, "subject")
            if subject is None:
                # geen subject-kwarg (bv. doorgegeven positioneel bestaat niet:
                # subject is overal keyword-only) → niets te toetsen
                continue
            if (
                isinstance(subject, ast.Call)
                and _called_name(subject) in SUBJECT_BUILDERS
            ):
                continue  # rechtstreeks uit de bouwer
            if (rel, fname) not in SUBJECT_ALLOWLIST:
                violations.add((rel, fname))
    assert not violations, (
        "Verzendroute(s) zetten een onderwerp buiten de gedeelde bouwer om "
        f"(huisregel M4): {sorted(violations)} — gebruik build_email_subject/"
        "build_reply_subject of voeg een gemotiveerde allowlist-regel toe."
    )


def test_allowlist_bevat_geen_dode_regels():
    """Elke allowlist-regel moet nog naar een échte verzend-aanroep wijzen —
    een gefixte route hoort hier weggehaald te worden (houdt de lijst eerlijk)."""
    live = set()
    for rel, tree in _modules():
        if rel.startswith("app/email/providers/") or rel == "app/email/service.py":
            continue
        aliases = _smtp_aliases(tree)
        for fname, call in _walk_calls(tree):
            called = _called_name(call)
            if (
                called == "send_with_attachment"
                or called == "send_message"
                or (isinstance(call.func, ast.Name) and call.func.id in aliases)
            ):
                live.add((rel, fname))
    dead = SUBJECT_ALLOWLIST - live
    assert not dead, f"Allowlist-regels zonder verzend-aanroep (opruimen): {sorted(dead)}"
