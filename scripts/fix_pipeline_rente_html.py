"""Maak de Rente-cel in HTML pipeline-templates leeg (was hardcoded 0,00)."""

import asyncio
import os
import re
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Patroon: <td>...Rente...</td><td>...€...</td><td>...0,00...</td>
# Replace de 0,00 cell met &nbsp; zodat de server-renderer (_fill_amount_cell)
# de daadwerkelijke waarde invult.
PATTERN = re.compile(
    r"(<td[^>]*>(?:<[^>]+>)*\s*Rente\s*(?:</[^>]+>)*\s*</td>"
    r"\s*<td[^>]*>(?:<[^>]+>)*\s*€\s*(?:</[^>]+>)*\s*</td>"
    r"\s*<td[^>]*>)(?:<[^>]+>)*\s*0,00\s*(?:</[^>]+>)*(\s*</td>)",
    re.DOTALL,
)


async def main() -> None:
    engine = create_async_engine(os.environ["DATABASE_URL"])
    async with engine.begin() as conn:
        rows = await conn.execute(
            text("SELECT id, name, email_body_template_html FROM incasso_pipeline_steps WHERE email_body_template_html IS NOT NULL")
        )
        total = 0
        for row in rows:
            step_id, name, html = row
            if html is None:
                continue
            new_html, count = PATTERN.subn(r"\1&nbsp;\2", html)
            if count > 0:
                await conn.execute(
                    text(
                        "UPDATE incasso_pipeline_steps "
                        "SET email_body_template_html = :body WHERE id = :id"
                    ),
                    {"body": new_html, "id": step_id},
                )
                print(f"  - {name}: {count} Rente-cel(len) leeg gemaakt")
                total += count
            else:
                print(f"  - {name}: geen Rente-cel met 0,00 gevonden")
        print(f"Klaar: {total} cel(len) bijgewerkt")


if __name__ == "__main__":
    asyncio.run(main())
