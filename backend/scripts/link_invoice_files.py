"""S213: eenmalige koppeling van factuur-PDF's aan vorderingen (`invoice_file_id`).

Bij de BaseNet-import kwamen de factuur-PDF's als dossierbestanden binnen
(±1.750 `Factuur_<nr>.pdf`), maar geen enkele vordering verwijst ernaar
(`invoice_file_id` leeg). Daardoor vindt de PDF-kolom in het Vorderingen-tabblad
én de automatische factuur-bijlage op de verzendpaden niets bij geïmporteerde
dossiers.

Dit script koppelt per vordering het dossierbestand waarvan het factuurnummer in
de bestandsnaam exact overeenkomt met `Claim.invoice_number` — en alléén als er
binnen hetzelfde dossier precies één zo'n bestand is (uniek). Twijfelgevallen
(meerdere kandidaten, geen match, leeg factuurnummer) worden overgeslagen en
apart gerapporteerd. Er wordt uitsluitend `invoice_file_id` gezet, niets anders.

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

from sqlalchemy import select, text

# Importeer main om alle SQLAlchemy modellen te registreren
import app.main  # noqa: F401
from app.auth.models import Tenant
from app.cases.models import CaseFile
from app.collections.models import Claim
from app.database import async_session

# Bestandsnaam-prefixen die vóór het factuurnummer kunnen staan, langste eerst.
_PREFIXES = ("factuurnummer", "factuurnr", "factuur", "fact", "fac")


def _norm(value: str) -> str:
    """Lowercase, trim, en spaties/underscores weg — hyphens blijven (zitten in
    factuurnummers als 2025-042)."""
    return value.strip().lower().replace(" ", "").replace("_", "")


def filename_invoice_key(filename: str) -> str:
    """Haal het genormaliseerde factuurnummer uit een bestandsnaam.

    `Factuur_2025-042.pdf` -> `2025-042`; `2025-042.pdf` -> `2025-042`.
    """
    stem = filename.rsplit(".", 1)[0] if "." in filename else filename
    n = _norm(stem)
    for pre in _PREFIXES:
        if n.startswith(pre):
            n = n[len(pre):]
            break
    return n.strip("-–—. ")


def find_unique_file(invoice_number: str | None, files: list[CaseFile]) -> CaseFile | None:
    """Het ene actieve dossierbestand waarvan het factuurnummer exact matcht, of
    None bij geen/ambigue match of leeg factuurnummer."""
    if not invoice_number or not invoice_number.strip():
        return None
    target = _norm(invoice_number)
    matches = [f for f in files if filename_invoice_key(f.original_filename) == target]
    return matches[0] if len(matches) == 1 else None


async def link(dry_run: bool) -> None:
    async with async_session() as session:
        tenants = list((await session.execute(select(Tenant))).scalars().all())

    grand_candidates = 0  # vorderingen zonder PDF, mét factuurnummer
    grand_linked = 0
    grand_ambiguous = 0
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
                cand = [
                    f for f in case_files
                    if filename_invoice_key(f.original_filename) == target
                ]
                if len(cand) == 1:
                    grand_linked += 1
                    if len(samples) < 20:
                        samples.append(
                            f"  {claim.invoice_number}  ->  {cand[0].original_filename}"
                        )
                    if not dry_run:
                        claim.invoice_file_id = cand[0].id
                elif len(cand) > 1:
                    grand_ambiguous += 1
                else:
                    grand_unmatched += 1

            if not dry_run:
                await session.commit()

    print("=== Steekproef (max 20 koppelingen) ===")
    for s in samples:
        print(s)
    print("---")
    print(f"Vorderingen zonder PDF, mét factuurnummer : {grand_candidates}")
    print(f"  -> uniek koppelbaar (gekoppeld)         : {grand_linked}")
    print(f"  -> meerdere kandidaten (overgeslagen)   : {grand_ambiguous}")
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

    class F:
        def __init__(self, name):
            self.original_filename = name

    f1, f2 = F("Factuur_2025-042.pdf"), F("Factuur_2025-099.pdf")
    # Unieke match
    assert find_unique_file("2025-042", [f1, f2]) is f1
    # Geen match
    assert find_unique_file("2025-500", [f1, f2]) is None
    # Ambigu (twee bestanden met hetzelfde nummer) -> None
    dup = F("factuur-2025-042.pdf")
    assert find_unique_file("2025-042", [f1, dup]) is None
    # Leeg factuurnummer -> None
    assert find_unique_file(None, [f1]) is None
    assert find_unique_file("  ", [f1]) is None
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
