"""Wachters M1 + M2 + M3 + M4 (S224/S254, skill breed-testen) — verzendroute-drift-guards.

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
- M1 (afzender, S254): elke verzendroute vertrekt vanaf het kantooradres —
  `send_as_tenant_account=True` of zelf `resolve_office_channel`. Ging twee keer
  mis (S220 verstuurknop, S224 classificatie-route); toen per geval gefixt,
  nu bewaakt als soort.
- M3 (14-dagenbrief-gate, S254): elke verzendroute die een verse sommatie kan
  versturen passeert de gate, of staat mét motivering op de allowlist. Ging óók
  twee keer mis (S204: follow-up + AI-concept, S224: de .eml-knop).
- Gesloten dossier (S254): elke AUTOMATISCHE verzender controleert of het dossier
  intussen betaald/afgesloten is. Handmatige routes staan gemotiveerd op de
  allowlist — een mens die bewust op een gesloten dossier mailt is legitiem
  (bv. antwoord op een vraag over een afgewikkelde zaak).

Een regel hier weghalen mag alleen samen met de fix die hem overbodig maakt.
"""

import ast
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1] / "app"

# ── M2: verwachte rauwe uitgangen ────────────────────────────────────────────

# Aanroepers van provider.send_message buiten de provider-implementaties zelf.
EXPECTED_PROVIDER_EXITS = {
    # Logt via write_outbound_log (S220 N1) — zie test hieronder. S246: de
    # verzendmachine is afgesplitst van het endpoint (send_via_provider) zodat de
    # wachtrij-bezorger van 'Verstuur later' exact dezelfde functie draait.
    ("app/email/compose_router.py", "perform_compose_send"),
    # HET gedeelde verzendkanaal; logt zelf via write_outbound_log.
    ("app/email/send_service.py", "send_with_attachment"),
}

# Aanroepers van de rauwe SMTP-functie (app.email.service.send_email).
EXPECTED_SMTP_EXITS = {
    # SMTP-terugval bínnen het gedeelde kanaal (logt via write_outbound_log).
    ("app/email/send_service.py", "send_with_attachment"),
    # Instellingen-test: geen dossier-mail, bewust buiten het drieluik.
    ("app/email/router.py", "send_test_email"),
    # Wachtwoord-reset: systeemmail, geen dossier-mail.
    ("app/auth/router.py", "_send_reset_email_safe"),
    # Dagelijkse samenvatting (S256): systeemmail aan de eigen kantoorgebruikers,
    # nooit aan een debiteur; geen dossier-mail, dus buiten het drieluik.
    ("app/notifications/daily_summary.py", "send_daily_summaries"),
}

# ── M4: verzend-aanroepen waarvan het onderwerp NIET rechtstreeks uit de
# gedeelde bouwer komt — elk mét motivering. Nieuw = rood. ───────────────────

SUBJECT_ALLOWLIST = {
    # data.subject: vrije mail = gebruikers-onderwerp; concept-/sjabloonroutes
    # krijgen het bouwer-onderwerp al server-side mee (S223). S246: functie
    # hernoemd bij de afsplitsing van de verzendmachine (zie hierboven).
    ("app/email/compose_router.py", "perform_compose_send"),
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
    # Instellingen-test + wachtwoord-reset + dagelijkse samenvatting (S256):
    # vaste/systeem-onderwerpen aan de eigen gebruikers, geen debiteur-post.
    ("app/email/router.py", "send_test_email"),
    ("app/auth/router.py", "_send_reset_email_safe"),
    ("app/notifications/daily_summary.py", "send_daily_summaries"),
}

SUBJECT_BUILDERS = {"build_email_subject", "build_reply_subject"}

# ── M1: routes die de kantoor-afzender NIET zelf zetten — elk mét motivering ──

# (leeg) — elke verzendroute zet incasso@ zelf, via de kwarg of via
# resolve_office_channel. Een regel hier betekent: deze route mag bewust vanaf
# een ander account vertrekken. Dat was juist de S220-N1-fout, dus motiveer goed.
SENDER_ALLOWLIST: set[tuple[str, str]] = set()

OFFICE_CHANNEL_RESOLVER = "resolve_office_channel"

# ── M3: verzendroutes zonder 14-dagenbrief-gate — elk mét motivering ─────────

GATE_ALLOWLIST = {
    # HET gedeelde kanaal: kent het dossier niet, de aanroepende route gate't.
    ("app/email/send_service.py", "send_with_attachment"),
    # Antwoord op een binnengekomen debiteurenmail (goedgekeurde classificatie) —
    # geen verse BIK-claimende sommatie, dus de gate hoort hier niet te vuren
    # (zelfde redenering als de reply-uitzondering op compose/send, S205).
    ("app/ai_agent/service.py", "execute_classification"),
    # Factuur aan de OPDRACHTGEVER, niet aan de debiteur — art. 6:96 lid 6 BW
    # gaat over consumenten-incassokosten en raakt deze mail niet.
    ("app/invoices/service.py", "send_invoice"),
}

GATE_FUNCTIONS = {"check_dagenbrief_gate", "check_dagenbrief_gate_for_case"}

# ── Gesloten dossier: routes zonder de poort — elk mét motivering ────────────

CLOSED_GATE_ALLOWLIST = {
    # HET gedeelde kanaal: kent het dossier niet, de aanroepende route poort't.
    ("app/email/send_service.py", "send_with_attachment"),
    # HANDMATIG: de gebruiker stelt zelf een mail op vanuit een dossier dat hij
    # voor zich heeft. Mailen over een afgewikkelde zaak is legitiem (S237:
    # debiteur vroeg een update op een gesloten dossier) — een mens beslist.
    ("app/email/compose_router.py", "perform_compose_send"),
    ("app/documents/router.py", "send_document"),
    # ANTWOORD op een binnengekomen mail; ook op een gesloten dossier hoort een
    # vraag beantwoord te worden.
    ("app/ai_agent/service.py", "execute_classification"),
    # Factuur aan de opdrachtgever — die volgt juist NÁ het afsluiten.
    ("app/invoices/service.py", "send_invoice"),
}

CLOSED_GATE_FUNCTION = "check_case_closed_gate"


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


# ── Gedeelde route-inventaris voor M1/M3/gesloten-dossier ───────────────────


def _send_routes() -> dict[tuple[str, str], list[ast.Call]]:
    """Elke functie die een mail de deur uit doet, met zijn verzend-aanroepen.

    Eén enumeratie voor drie huisregels — komt er een verzendroute bij, dan
    beoordelen alle drie de wachters hem automatisch."""
    routes: dict[tuple[str, str], list[ast.Call]] = {}
    for rel, tree in _modules():
        if rel.startswith("app/email/providers/") or rel == "app/email/service.py":
            continue
        for fname, call in _walk_calls(tree):
            if _called_name(call) in ("send_with_attachment", "send_message"):
                routes.setdefault((rel, fname), []).append(call)
    return routes


def _calls_in(rel: str, target_fn: str) -> set[str]:
    tree = ast.parse((APP_DIR.parent / rel).read_text(encoding="utf-8"))
    return {
        _called_name(call) for fname, call in _walk_calls(tree) if fname == target_fn
    }


# ── M1: afzender-wachter ─────────────────────────────────────────────────────


def test_elke_verzendroute_gebruikt_het_kantooradres():
    """Een dossier-mail vertrekt vanaf incasso@, nooit vanaf het persoonlijke
    account van wie toevallig klikt: óf `send_as_tenant_account=True` meegeven,
    óf zelf het kantoorkanaal kiezen. Ging mis op de verstuurknop (S220 N1) en
    de classificatie-route (S224) — die twee losse fixes staan hier nu als soort."""
    violations = set()
    for (rel, fname), calls in _send_routes().items():
        if (rel, fname) in SENDER_ALLOWLIST:
            continue
        # Niet "is de kwarg meegegeven" maar "staat hij aantoonbaar AAN" — met
        # send_as_tenant_account=False vertrekt de mail alsnog persoonlijk.
        # ponytail: alleen de letterlijke True telt; een variabele als waarde is
        # niet statisch te beoordelen en hoort dus gemotiveerd op de allowlist.
        aan = all(
            isinstance(_kwarg(c, "send_as_tenant_account"), ast.Constant)
            and _kwarg(c, "send_as_tenant_account").value is True
            for c in calls
        )
        if aan or OFFICE_CHANNEL_RESOLVER in _calls_in(rel, fname):
            continue
        violations.add((rel, fname))
    assert not violations, (
        "Verzendroute(s) kunnen vanaf een persoonlijk account vertrekken "
        f"(huisregel M1): {sorted(violations)} — geef send_as_tenant_account=True "
        "mee of roep resolve_office_channel aan."
    )


# ── M3: 14-dagenbrief-wachter ────────────────────────────────────────────────


def test_elke_verzendroute_passeert_de_dagenbrief_gate():
    """Art. 6:96 lid 6 BW: bij een consument mag geen BIK-claimende sommatie de
    deur uit vóór de 14-dagenbrief. De gate stond al op elke bekende deur, maar
    niets betrapte een NIEUWE deur — precies zo ontstonden de zijdeuren van S204
    (follow-up + AI-concept) en S224 (.eml). Nieuw = rood of gemotiveerd."""
    violations = set()
    for (rel, fname), _calls in _send_routes().items():
        if (rel, fname) in GATE_ALLOWLIST:
            continue
        if _calls_in(rel, fname) & GATE_FUNCTIONS:
            continue
        violations.add((rel, fname))
    assert not violations, (
        "Verzendroute(s) zonder 14-dagenbrief-gate (huisregel M3): "
        f"{sorted(violations)} — roep check_dagenbrief_gate(_for_case) aan of "
        "voeg een gemotiveerde allowlist-regel toe."
    )


# ── Gesloten dossier: poort-wachter ──────────────────────────────────────────


def test_automatische_verzenders_controleren_of_het_dossier_dicht_is():
    """Waarheid S254: een gesloten dossier verstuurt nooit meer automatisch iets.
    Handmatige routes staan gemotiveerd op de allowlist; alles wat zonder mens
    aan de knop verstuurt moet `check_case_closed_gate` aanroepen."""
    violations = set()
    for (rel, fname), _calls in _send_routes().items():
        if (rel, fname) in CLOSED_GATE_ALLOWLIST:
            continue
        if CLOSED_GATE_FUNCTION in _calls_in(rel, fname):
            continue
        violations.add((rel, fname))
    assert not violations, (
        "Automatische verzendroute(s) zonder gesloten-dossier-poort: "
        f"{sorted(violations)} — roep check_case_closed_gate aan, of motiveer "
        "waarom deze route handmatig is (CLOSED_GATE_ALLOWLIST)."
    )


def test_nieuwe_allowlists_bevatten_geen_dode_regels():
    """Zelfde eerlijkheidseis als hieronder: een route die verdwijnt of alsnog
    de regel krijgt, hoort uit de allowlist — anders dekt de lijst niets meer."""
    live = set(_send_routes())
    for naam, lijst in (
        ("SENDER_ALLOWLIST", SENDER_ALLOWLIST),
        ("GATE_ALLOWLIST", GATE_ALLOWLIST),
        ("CLOSED_GATE_ALLOWLIST", CLOSED_GATE_ALLOWLIST),
    ):
        dood = lijst - live
        assert not dood, f"{naam} bevat regels zonder verzend-aanroep: {sorted(dood)}"


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
