"""S213: eenmalige koppeling van factuur-PDF's aan vorderingen (`invoice_file_id`).

Bij de BaseNet-import kwamen de factuur-PDF's als dossierbestanden binnen
(±1.750 `Factuur_<nr>.pdf`), maar geen enkele vordering verwijst ernaar
(`invoice_file_id` leeg). Daardoor vindt de PDF-kolom in het Vorderingen-tabblad
én de automatische factuur-bijlage op de verzendpaden niets bij geïmporteerde
dossiers.

Dit script koppelt per vordering het dossierbestand waarvan het factuurnummer in
de bestandsnaam exact overeenkomt met `Claim.invoice_number`. Drie treden, in
aflopende striktheid (Fable-review S213):

1. Exacte naam-match, uniek binnen het dossier → koppelen.
2. Meerdere naam-matches → alleen koppelen als ALLE kandidaten byte-identiek
   zijn (sha256 van de echte bestanden; dubbele uploads) — dan deterministisch
   de oudste. Verschillende inhoud → overslaan.
3. Geen naam-match → nogmaals met kopie-achtervoegsel gestript
   (`Factuur_140005__1_.pdf` = gesanitiseerd "(1)"), zelfde uniek-garantie.

Alles daarbuiten (ander nummerschema, kostenpost-regels als "Griffierecht",
dossiers zonder factuurbestand) wordt overgeslagen en apart gerapporteerd.
Er wordt uitsluitend `invoice_file_id` gezet, niets anders.

Recept (S209/S211): eerst --dry-run (aantal + steekproef), dan akkoord Arsalan,
dan echt, dan natelling.

Run (op de VPS):
    docker compose exec -T backend python -m scripts.link_invoice_files --dry-run
    docker compose exec -T backend python -m scripts.link_invoice_files --commit
    docker compose exec -T backend python -m scripts.link_invoice_files --self-test
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import re
from pathlib import Path

from sqlalchemy import select, text

# Importeer main om alle SQLAlchemy modellen te registreren
import app.main  # noqa: F401
from app.auth.models import Tenant
from app.cases import files_service
from app.cases.models import CaseFile
from app.collections.models import Claim
from app.database import async_session

# Bestandsnaam-prefixen die vóór het factuurnummer kunnen staan, langste eerst.
_PREFIXES = ("factuurnummer", "factuurnr", "factuur", "fact", "fac")

# Kopie-achtervoegsels aan het eind van de stem: '__1_' (gesanitiseerde "(1)")
# of een letterlijke ' (1)'. Bewust NIET een kale '_1' — dat kan echt nummer zijn.
_COPY_SUFFIX = re.compile(r"(__\d+_|\s*\(\d+\))$")


def _norm(value: str) -> str:
    """Lowercase, trim, en spaties/underscores weg — hyphens blijven (zitten in
    factuurnummers als 2025-042)."""
    return value.strip().lower().replace(" ", "").replace("_", "")


def _key(stem: str) -> str:
    n = _norm(stem)
    for pre in _PREFIXES:
        if n.startswith(pre):
            n = n[len(pre):]
            break
    return n.strip("-–—. ")


def filename_invoice_key(filename: str) -> str:
    """Haal het genormaliseerde factuurnummer uit een bestandsnaam.

    `Factuur_2025-042.pdf` -> `2025-042`; `2025-042.pdf` -> `2025-042`.
    """
    stem = filename.rsplit(".", 1)[0] if "." in filename else filename
    return _key(stem)


def filename_invoice_key_v2(filename: str) -> str:
    """Als `filename_invoice_key`, maar met kopie-achtervoegsel gestript:
    `Factuur_140005__1_.pdf` -> `140005`."""
    stem = filename.rsplit(".", 1)[0] if "." in filename else filename
    return _key(_COPY_SUFFIX.sub("", stem))


def find_unique_file(invoice_number: str | None, files: list[CaseFile]) -> CaseFile | None:
    """Het ene actieve dossierbestand waarvan het factuurnummer exact matcht, of
    None bij geen/ambigue match of leeg factuurnummer. (Trede 1; puur, testbaar.)"""
    if not invoice_number or not invoice_number.strip():
        return None
    target = _norm(invoice_number)
    matches = [f for f in files if filename_invoice_key(f.original_filename) == target]
    return matches[0] if len(matches) == 1 else None


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_duplicates(matches: list[CaseFile]) -> CaseFile | None:
    """Meerdere naam-matches: alleen veilig als ALLE bestanden byte-identiek zijn
    (dubbele upload). Dan deterministisch de oudste (created_at, dan id).
    Ontbrekend bestand of afwijkende inhoud → None (overslaan)."""
    hashes = set()
    for f in matches:
        p = Path(files_service.get_file_path(f))
        if not p.exists():
            return None
        hashes.add(_sha256(p))
    if len(hashes) != 1:
        return None
    return sorted(matches, key=lambda f: (f.created_at, str(f.id)))[0]


async def link(dry_run: bool) -> None:
    async with async_session() as session:
        tenants = list((await session.execute(select(Tenant))).scalars().all())

    grand_candidates = 0  # vorderingen zonder PDF, mét factuurnummer
    grand_linked_exact = 0     # trede 1: unieke naam-match
    grand_linked_dup = 0       # trede 2: dubbelen, byte-identiek bewezen
    grand_linked_suffix = 0    # trede 3: kopie-achtervoegsel
    grand_ambiguous = 0        # meerdere kandidaten, inhoud verschilt/ontbreekt
    grand_unmatched = 0
    grand_no_number = 0
    samples: list[str] = []

    for tenant in tenants:
        async with async_session() as session:
            await session.execute(text(f"SET LOCAL app.current_tenant = '{tenant.id}'"))

            # Alle dossiers met hun actieve bestanden, plus de vorderingen zonder PDF.
            claims = list(
                (
                    await session.execute(
                        select(Claim).where(
                            Claim.tenant_id == tenant.id,
                            Claim.is_active.is_(True),
                            Claim.invoice_file_id.is_(None),
                        )
                    )
                )
                .scalars()
                .all()
            )
            if not claims:
                continue

            # Bestanden per dossier (alleen de betrokken dossiers), actief.
            case_ids = {c.case_id for c in claims}
            files = list(
                (
                    await session.execute(
                        select(CaseFile).where(
                            CaseFile.tenant_id == tenant.id,
                            CaseFile.case_id.in_(case_ids),
                            CaseFile.is_active.is_(True),
                        )
                    )
                )
                .scalars()
                .all()
            )
            files_by_case: dict = {}
            for f in files:
                files_by_case.setdefault(f.case_id, []).append(f)

            for claim in claims:
                if not claim.invoice_number or not claim.invoice_number.strip():
                    grand_no_number += 1
                    continue
                grand_candidates += 1
                case_files = files_by_case.get(claim.case_id, [])
                target = _norm(claim.invoice_number)

                chosen: CaseFile | None = None
                tier = ""
                # Trede 1: exacte naam-match, uniek.
                cand = [
                    f for f in case_files
                    if filename_invoice_key(f.original_filename) == target
                ]
                if len(cand) == 1:
                    chosen, tier = cand[0], "exact"
                elif len(cand) > 1:
                    # Trede 2: dubbelen — alleen bij bewezen identieke inhoud.
                    chosen = resolve_duplicates(cand)
                    if chosen is not None:
                        tier = "dup"
                    else:
                        grand_ambiguous += 1
                else:
                    # Trede 3: kopie-achtervoegsel, zelfde uniek-garantie.
                    cand2 = [
                        f for f in case_files
                        if filename_invoice_key_v2(f.original_filename) == target
                    ]
                    if len(cand2) == 1:
                        chosen, tier = cand2[0], "suffix"
                    elif len(cand2) > 1:
                        chosen = resolve_duplicates(cand2)
                        if chosen is not None:
                            tier = "dup"
                        else:
                            grand_ambiguous += 1
                    else:
                        grand_unmatched += 1

                if chosen is None:
                    continue
                if tier == "exact":
                    grand_linked_exact += 1
                elif tier == "dup":
                    grand_linked_dup += 1
                else:
                    grand_linked_suffix += 1
                if len(samples) < 20:
                    samples.append(
                        f"  [{tier}] {claim.invoice_number}  ->  {chosen.original_filename}"
                    )
                if not dry_run:
                    claim.invoice_file_id = chosen.id

            if not dry_run:
                await session.commit()

    grand_linked = grand_linked_exact + grand_linked_dup + grand_linked_suffix
    print("=== Steekproef (max 20 koppelingen) ===")
    for s in samples:
        print(s)
    print("---")
    print(f"Vorderingen zonder PDF, mét factuurnummer : {grand_candidates}")
    print(f"  -> gekoppeld totaal                     : {grand_linked}")
    print(f"     - trede 1 exacte naam, uniek         : {grand_linked_exact}")
    print(f"     - trede 2 dubbelen, byte-identiek    : {grand_linked_dup}")
    print(f"     - trede 3 kopie-achtervoegsel        : {grand_linked_suffix}")
    print(f"  -> meerdere kandidaten, inhoud verschilt: {grand_ambiguous}")
    print(f"  -> geen match (overgeslagen)            : {grand_unmatched}")
    print(f"Vorderingen zonder factuurnummer          : {grand_no_number}")
    if dry_run:
        print("Dry-run: niets geschreven.")
    else:
        print("Gecommit: alleen invoice_file_id gezet.")


def _self_test() -> None:
    """Pure matching-logica, geen DB."""
    assert filename_invoice_key("Factuur_2025-042.pdf") == "2025-042"
    assert filename_invoice_key("factuur 2025-042.PDF") == "2025-042"
    assert filename_invoice_key("2025-042.pdf") == "2025-042"
    assert filename_invoice_key("FactuurnummerF-100.pdf") == "f-100"
    assert filename_invoice_key("iets-anders.pdf") == "iets-anders"

    # Trede 3: kopie-achtervoegsel
    assert filename_invoice_key_v2("Factuur_140005__1_.pdf") == "140005"
    assert filename_invoice_key_v2("Factuur_140005 (2).pdf") == "140005"
    assert filename_invoice_key_v2("Factuur_134394__1_.rtf") == "134394"
    # Kale '_1' wordt NIET gestript (kan echt nummer zijn)
    assert filename_invoice_key_v2("Factuur_140005_1.pdf") == "1400051"
    # Zonder achtervoegsel: identiek aan trede 1
    assert filename_invoice_key_v2("Factuur_2025-042.pdf") == "2025-042"

    class F:
        def __init__(self, name):
            self.original_filename = name

    f1, f2 = F("Factuur_2025-042.pdf"), F("Factuur_2025-099.pdf")
    # Unieke match
    assert find_unique_file("2025-042", [f1, f2]) is f1
    # Geen match
    assert find_unique_file("2025-500", [f1, f2]) is None
    # Ambigu (twee bestanden met hetzelfde nummer) -> None (trede 1; dubbel-
    # resolutie gebeurt daarbuiten, met sha256-bewijs)
    dup = F("factuur-2025-042.pdf")
    assert find_unique_file("2025-042", [f1, dup]) is None
    # Leeg factuurnummer -> None
    assert find_unique_file(None, [f1]) is None
    assert find_unique_file("  ", [f1]) is None

    # resolve_duplicates: identieke inhoud -> oudste; verschillend -> None
    import tempfile
    from datetime import datetime, timedelta

    with tempfile.TemporaryDirectory() as td:
        pa, pb = Path(td) / "a.pdf", Path(td) / "b.pdf"
        pa.write_bytes(b"%PDF-zelfde")
        pb.write_bytes(b"%PDF-zelfde")

        class G:
            def __init__(self, path, created, fid):
                self._path = path
                self.created_at = created
                self.id = fid
                self.original_filename = path.name

        orig = files_service.get_file_path
        files_service.get_file_path = lambda f: f._path  # type: ignore[assignment]
        try:
            t0 = datetime(2026, 1, 1)
            ga = G(pa, t0 + timedelta(days=1), "b-id")
            gb = G(pb, t0, "a-id")
            picked = resolve_duplicates([ga, gb])
            assert picked is gb, "oudste hoort te winnen"
            pb.write_bytes(b"%PDF-anders")
            assert resolve_duplicates([ga, gb]) is None, "verschillende inhoud -> None"
            pb.unlink()
            assert resolve_duplicates([ga, gb]) is None, "ontbrekend bestand -> None"
        finally:
            files_service.get_file_path = orig
    print("self-test OK")


def main() -> None:
    parser = argparse.ArgumentParser(description="S213 koppel factuur-PDF's aan vorderingen")
    parser.add_argument("--dry-run", action="store_true", help="Alleen rapporteren")
    parser.add_argument("--commit", action="store_true", help="Echt koppelen (schrijft invoice_file_id)")
    parser.add_argument("--self-test", action="store_true", help="Test alleen de matching-logica")
    args = parser.parse_args()

    if args.self_test:
        _self_test()
        return
    if not args.commit and not args.dry_run:
        parser.error("Kies --dry-run of --commit (standaard doet niets, veilig).")
    asyncio.run(link(dry_run=not args.commit))


if __name__ == "__main__":
    main()
