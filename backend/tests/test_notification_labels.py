"""Wachter (S254) — elke meldingsoort heeft een label, icoon en kleur op de bel.

S252 vond drie meldingsoorten die op het grijze "Systeem"-vangnet terugvielen,
waaronder juist de twee die moeten opvallen: 'geplande mail mislukt' en
'consument boven de wettelijke kostenstaffel'. Een alarm dat eruitziet als ruis
wordt weggeklikt — daarom staat dit op de waarhedenlijst. Toen met de hand
nageteld; deze wachter doet het voortaan automatisch.

Twee richtingen, want de fout kwam in twee smaken:
1. backend maakt een soort die de bel niet kent → geen label;
2. de bel kent de soort wél, maar het icoon of de kleur ontbreekt in de
   tekenkaarten → alsnog grijs (dat was de derde vondst, 'ai_draft_ready').
"""

import ast
import re
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = BACKEND_ROOT / "app"

# De frontend staat in CI naast de backend (hele repo uitgecheckt) en in de
# dev-container onder /app/frontend_src (alleen-lezen mount, docker-compose.dev).
_FRONTEND_CANDIDATES = [
    BACKEND_ROOT.parent / "frontend" / "src",
    BACKEND_ROOT / "frontend_src",
]

# Doorgeefluik-aanroepen waarvan het type pas op runtime bekend is: het generieke
# create-endpoint geeft doo wat de aanroeper meestuurt. Niet statisch te kennen —
# de aanroepers zelf worden wél gescand.
_DYNAMIC_TYPE_NODES = (ast.Attribute, ast.Subscript)


def _frontend_src() -> Path:
    for candidate in _FRONTEND_CANDIDATES:
        if candidate.is_dir():
            return candidate
    pytest.fail(
        "frontend/src niet gevonden — deze wachter mag NIET stil overgeslagen "
        f"worden. Gezocht in: {[str(c) for c in _FRONTEND_CANDIDATES]}. In de "
        "dev-container komt hij van de read-only mount in docker-compose.dev.yml."
    )


def _resolve(value, bindings: dict[str, set[str]]) -> set[str]:
    """Alle string-waarden die deze expressie kan opleveren (of leeg = dynamisch)."""
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        return {value.value}
    if isinstance(value, ast.Name):
        return set(bindings.get(value.id, ()))
    if isinstance(value, ast.IfExp):  # "x if voorwaarde else y" — beide takken tellen
        return _resolve(value.body, bindings) | _resolve(value.orelse, bindings)
    return set()


def _string_bindings(module_tree) -> dict[str, set[str]]:
    """Namen die aan een string vastzitten — zowel module-constanten
    (`NOTIF_EMAIL_RECEIVED = "…"`) als lokale variabelen in een functie
    (`notif_type = "a" if x else "b"`, zoals de dagelijkse deadline-job doet).
    Bewust over-schattend: dezelfde naam in twee functies levert beide waarden,
    en méér natellen is hier veilig."""
    out: dict[str, set[str]] = {}
    for node in ast.walk(module_tree):
        if not isinstance(node, ast.Assign):
            continue
        waarden = _resolve(node.value, out)
        if not waarden:
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                out.setdefault(target.id, set()).update(waarden)
    return out


def _backend_notification_types() -> set[str]:
    """Elke meldingsoort die de backend aantoonbaar kan aanmaken."""
    types: set[str] = set()
    for path in sorted(APP_DIR.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        bindings = _string_bindings(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            called = (
                func.id
                if isinstance(func, ast.Name)
                else (func.attr if isinstance(func, ast.Attribute) else None)
            )
            if called not in ("Notification", "NotificationCreate"):
                continue
            for kw in node.keywords:
                if kw.arg != "type":
                    continue
                if isinstance(kw.value, _DYNAMIC_TYPE_NODES):
                    continue  # doorgeefluik — de echte aanroepers staan hierboven
                resolved = _resolve(kw.value, bindings)
                assert resolved, (
                    f"{path.name}: meldingsoort niet statisch te bepalen "
                    f"({ast.dump(kw.value)[:80]}) — zet hem in een NOTIF_-constante, "
                    "anders kan deze wachter hem niet natellen."
                )
                types |= resolved
    return types


def _ts_record_keys(source: str, record_name: str) -> set[str]:
    """Sleutels van een TypeScript-record — zowel `foo:` als `"foo-bar":`."""
    start = source.index(record_name)
    # Niet de eerste `{` na de naam pakken: die zit in de type-annotatie
    # (`Record<NotificationType, { label: string }>`). Het echte blok begint
    # bij de toekenning.
    depth, body_start = 0, source.index("= {", start) + 2
    for idx in range(body_start, len(source)):
        if source[idx] == "{":
            depth += 1
        elif source[idx] == "}":
            depth -= 1
            if depth == 0:
                body = source[body_start + 1 : idx]
                break
    else:  # pragma: no cover — onafgesloten record = kapotte bron
        raise AssertionError(f"{record_name}: geen afgesloten blok gevonden")
    return set(re.findall(r'^\s*"?([a-zA-Z_][\w-]*)"?\s*:', body, re.MULTILINE))


def _ts_config_values(source: str, field: str) -> set[str]:
    """Alle gebruikte waarden van één veld in NOTIFICATION_TYPE_CONFIG."""
    body = source[source.index("NOTIFICATION_TYPE_CONFIG") :]
    return set(re.findall(rf'{field}:\s*"([^"]+)"', body[: body.index("};")]))


# ── 1. Backend-soort → label op de bel ───────────────────────────────────────


def test_elke_meldingsoort_heeft_een_label():
    source = (_frontend_src() / "hooks" / "use-notifications.ts").read_text(
        encoding="utf-8"
    )
    gelabeld = _ts_record_keys(source, "NOTIFICATION_TYPE_CONFIG")
    produceerbaar = _backend_notification_types()

    assert produceerbaar, "geen enkele meldingsoort gevonden — scan is stuk"
    ontbreekt = produceerbaar - gelabeld
    assert not ontbreekt, (
        f"Meldingsoort(en) zonder label op de bel: {sorted(ontbreekt)} — ze vallen "
        "terug op grijs 'Systeem' met info-icoon (S252). Voeg ze toe aan "
        "NOTIFICATION_TYPE_CONFIG in frontend/src/hooks/use-notifications.ts."
    )


# ── 2. Label → icoon en kleur bestaan echt ───────────────────────────────────


def test_elk_label_heeft_een_bestaand_icoon_en_kleur():
    src = _frontend_src()
    config_source = (src / "hooks" / "use-notifications.ts").read_text(encoding="utf-8")
    header_source = (src / "components" / "layout" / "app-header.tsx").read_text(
        encoding="utf-8"
    )

    iconen = _ts_record_keys(header_source, "ICON_MAP")
    kleuren = _ts_record_keys(header_source, "COLOR_MAP")

    onbekende_iconen = _ts_config_values(config_source, "icon") - iconen
    onbekende_kleuren = _ts_config_values(config_source, "color") - kleuren

    assert not onbekende_iconen, (
        f"Icoon(en) uit NOTIFICATION_TYPE_CONFIG ontbreken in ICON_MAP: "
        f"{sorted(onbekende_iconen)} — de melding valt terug op het grijze "
        "info-icoon (de derde S252-vondst, 'sparkles')."
    )
    assert not onbekende_kleuren, (
        f"Kleur(en) uit NOTIFICATION_TYPE_CONFIG ontbreken in COLOR_MAP: "
        f"{sorted(onbekende_kleuren)} — de melding valt terug op grijs "
        "(de derde S252-vondst, 'violet')."
    )
