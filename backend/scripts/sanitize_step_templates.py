"""S220 blok 2 — saneer de 6 stap-mailteksten in incasso_pipeline_steps.

De AI-concept-route krijgt deze DB-teksten als voorbeeld mee met de instructie
"footer NOOIT wijzigen" → het oude kantooradres (IJsbaanpad 9 / 1076 CV) en het
oude e-mailadres (kesting@) uit de BaseNet-kopieën vervuilden ÁLLE AI-concepten.
Batch/follow-up gebruiken de code-sjablonen (die renderen al vers correct) — dit
raakt alleen de DB-teksten.

Wat het doet (idempotent — herhaald draaien is een no-op):
  1. Oud adres/e-mail → juist kantooradres (Willem Fenengastraat 16E, 1096 BN) +
     incasso@, in beide kolommen (plain + html).
  2. De 3 teksten zonder aanhef hebben een losse komma op de aanhef-plek
     (BaseNet-restant) → vul "Geachte heer, mevrouw," in de PLATTE tekst
     (de HTML-variant krijgt de aanhef al bij render via html_renderer).

Gebruik:
  python -m scripts.sanitize_step_templates            # dry-run (schrijft niets)
  python -m scripts.sanitize_step_templates --execute  # schrijft
"""

import asyncio
import sys

from sqlalchemy import text

from app.database import async_session

# (oud, nieuw) — deterministisch, beide kolommen
ADDRESS_REPLACEMENTS = [
    ("IJsbaanpad 9", "Willem Fenengastraat 16E"),
    # HTML-variant gebruikt een harde spatie (&nbsp;) tussen straat en huisnummer.
    ("IJsbaanpad&nbsp;9", "Willem Fenengastraat&nbsp;16E"),
    ("1076 CV", "1096 BN"),
    ("1076&nbsp;CV", "1096&nbsp;BN"),
    ("kesting@kestinglegal.nl", "incasso@kestinglegal.nl"),
]

# De losse komma op de aanhef-plek (na "Betreft: ... / /") → nette aanhef.
# Alleen in de PLATTE tekst; de HTML-variant injecteert de aanhef bij render.
LONE_COMMA_OLD = "/ /\r\n\r\n,\r\n"
LONE_COMMA_NEW = "/ /\r\n\r\nGeachte heer, mevrouw,\r\n"


def _apply_address(text: str | None) -> tuple[str | None, int]:
    if not text:
        return text, 0
    n = 0
    for old, new in ADDRESS_REPLACEMENTS:
        cnt = text.count(old)
        if cnt:
            text = text.replace(old, new)
            n += cnt
    return text, n


async def main(execute: bool) -> None:
    async with async_session() as db:
        rows = (
            await db.execute(
                text(
                    "SELECT id, name, email_body_template, email_body_template_html "
                    "FROM incasso_pipeline_steps "
                    "WHERE email_body_template IS NOT NULL AND email_body_template != ''"
                    "ORDER BY sort_order"
                )
            )
        ).fetchall()

        total_addr = 0
        total_aanhef = 0
        for row in rows:
            new_plain, a1 = _apply_address(row.email_body_template)
            new_html, a2 = _apply_address(row.email_body_template_html)

            # De losse komma staat alleen bij de 3 teksten zonder aanhef; na
            # vervanging is het patroon weg → herhaald draaien is vanzelf een no-op.
            aanhef_fix = 0
            if new_plain and LONE_COMMA_OLD in new_plain:
                new_plain = new_plain.replace(LONE_COMMA_OLD, LONE_COMMA_NEW, 1)
                aanhef_fix = 1

            changed = (
                new_plain != row.email_body_template
                or new_html != row.email_body_template_html
            )
            if not changed:
                print(f"  [ongewijzigd] {row.name}")
                continue

            total_addr += a1 + a2
            total_aanhef += aanhef_fix
            print(
                f"  [wijzigt]    {row.name}: {a1 + a2} adres/e-mail-vervangingen"
                + (", + aanhef ingevuld" if aanhef_fix else "")
            )

            if execute:
                await db.execute(
                    text(
                        "UPDATE incasso_pipeline_steps SET email_body_template = :p, "
                        "email_body_template_html = :h WHERE id = :id"
                    ),
                    {"p": new_plain, "h": new_html, "id": row.id},
                )

        if execute:
            await db.commit()
            print(f"\nGESCHREVEN. {total_addr} adres-vervangingen, {total_aanhef} aanhef-invullingen.")
        else:
            print(
                f"\nDRY-RUN — niets geschreven. Zou {total_addr} adres-vervangingen +"
                f" {total_aanhef} aanhef-invullingen doen. Draai met --execute om te schrijven."
            )


if __name__ == "__main__":
    asyncio.run(main(execute="--execute" in sys.argv))
