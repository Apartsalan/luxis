"""Replace old footer paragraph in pipeline-step HTML body via Python regex."""

import asyncio
import os
import re
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

STEP_ID = "b45261b0-2fed-438e-bee2-a27242d715b7"

NEW_FOOTER_HTML = (
    'Heeft u financiële zorgen en ziet u geen uitweg meer? '
    'Wij informeren u graag over uw rechten als schuldenaar: '
    '<a href="https://kestinglegal.nl/debiteuren">kestinglegal.nl/debiteuren</a>. '
    'Voor schuldhulpverlening kunt u terecht bij uw gemeente. '
    'Heeft u dringend emotionele steun nodig? Bel dan gratis en anoniem met '
    'Stichting 113 Zelfmoordpreventie via 0800-0113 of kijk op '
    '<a href="http://www.113.nl">www.113.nl</a>.'
)

PATTERN = re.compile(
    r"Heeft u financiële zorgen.*?om uw problemen op te lossen",
    re.DOTALL,
)


async def main() -> None:
    engine = create_async_engine(os.environ["DATABASE_URL"])
    async with engine.begin() as conn:
        result = await conn.execute(
            text("SELECT email_body_template_html FROM incasso_pipeline_steps WHERE id = :id"),
            {"id": STEP_ID},
        )
        row = result.first()
        if not row or row[0] is None:
            print("step or html-body not found")
            return
        body = row[0]
        new_body, count = PATTERN.subn(NEW_FOOTER_HTML, body)
        if count == 0:
            print("Patroon niet gevonden")
            return
        await conn.execute(
            text("UPDATE incasso_pipeline_steps SET email_body_template_html = :body WHERE id = :id"),
            {"body": new_body, "id": STEP_ID},
        )
        print(f"vervangen: {count} match(es), nieuwe lengte: {len(new_body)}")


if __name__ == "__main__":
    asyncio.run(main())
