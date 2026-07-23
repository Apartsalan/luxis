"""Wachter (S246) — migratie-drift op tijdstempelkolommen.

Fouten wonen op kruispunten, en dit is er één tussen twee schema-bronnen: de
testdatabase wordt uit de MODELLEN gebouwd (`Base.metadata.create_all`, die de
`server_default` van TimestampMixin meeneemt), productie uit de MIGRATIES. Een
migratie die `created_at`/`updated_at` als not-null aanmaakt zónder
`server_default` is dus groen in de tests en kapot in productie — precies wat er
in S246 live gebeurde bij de eerste ingeplande mail.

Deze wachter leest de migratiebestanden (AST) en eist dat elke `create_table`
die een tijdstempelkolom aanmaakt daar ook een database-standaardwaarde bij
zet. Een nieuwe migratie die dat vergeet, valt hier rood.
"""

import ast
from pathlib import Path

VERSIONS_DIR = Path(__file__).resolve().parents[1] / "alembic" / "versions"

TIMESTAMP_COLUMNS = {"created_at", "updated_at"}

# Migraties van vóór deze wachter die de kolom bewust anders vullen (bv. een
# backfill die de waarde expliciet meegeeft). Nieuw = rood; elke regel hoort een
# motivering te hebben.
ALLOWLIST: set[tuple[str, str]] = set()


def _create_table_calls(tree: ast.AST):
    """Yield elke op.create_table(...)-aanroep."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
        if name == "create_table":
            yield node


def _column_calls(create_table: ast.Call):
    """Yield (kolomnaam, Call-node) voor elke sa.Column(...) in de tabel."""
    for arg in create_table.args[1:]:
        if not isinstance(arg, ast.Call):
            continue
        func = arg.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
        if name != "Column" or not arg.args:
            continue
        first = arg.args[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            yield first.value, arg


def _has_kwarg(call: ast.Call, name: str) -> bool:
    return any(kw.arg == name for kw in call.keywords)


def _table_name(create_table: ast.Call) -> str:
    first = create_table.args[0] if create_table.args else None
    if isinstance(first, ast.Constant) and isinstance(first.value, str):
        return first.value
    return "<onbekend>"


def test_nieuwe_tabellen_geven_tijdstempels_een_database_default():
    overtredingen = []
    for path in sorted(VERSIONS_DIR.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for create_table in _create_table_calls(tree):
            table = _table_name(create_table)
            for col_name, col in _column_calls(create_table):
                if col_name not in TIMESTAMP_COLUMNS:
                    continue
                # Alleen not-null kolommen zijn gevaarlijk: een nullable kolom
                # zonder default levert gewoon NULL op, geen crash.
                nullable = next(
                    (kw.value for kw in col.keywords if kw.arg == "nullable"), None
                )
                is_not_null = isinstance(nullable, ast.Constant) and nullable.value is False
                if not is_not_null:
                    continue
                if _has_kwarg(col, "server_default") or _has_kwarg(col, "default"):
                    continue
                if (path.name, table) in ALLOWLIST:
                    continue
                overtredingen.append(f"{path.name}::{table}.{col_name}")

    assert not overtredingen, (
        "Migratie(s) maken een not-null tijdstempelkolom aan zonder database-"
        f"standaardwaarde: {sorted(overtredingen)}. TimestampMixin vult deze niet "
        "in Python — zonder server_default=sa.text('now()') faalt elke insert in "
        "productie, terwijl de tests (create_all) groen blijven."
    )
