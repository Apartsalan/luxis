"""Dagelijkse samenvattingsmail (S256) — Luxis komt naar de advocaat toe.

Waarom: in vijf weken (aug-sept 2026) logde Lisanne één keer in, terwijl negentien
dossiers 29-46 dagen wachtten op een brief die klaarstond en 162 van 164
meldingen ongelezen bleven. De bel in de app werkt alleen voor wie de app opent.
Deze mail landt in haar gewone Outlook: één bericht per ochtend met wat er op
haar wacht, en niets als er niets wacht (geen lege mails).

Drie blokken, bewust niet meer:
  1. brieven die klaarstaan (open follow-up-adviezen; "te laat" eerst)
  2. dossiers in "Verweer beantwoorden"
  3. gemiste termijnen op lopende betalingsregelingen

Verstuurt NOOIT iets naar een debiteur: het is een systeemmail aan de eigen
kantoorgebruikers, net als de wachtwoord-reset (zie de allowlist in
tests/test_send_route_drift_guard.py).
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from html import escape

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agent.followup_models import (
    ACTION_LABELS,
    FollowupRecommendation,
)
from app.cases.models import Case
from app.config import settings
from app.incasso.models import IncassoPipelineStep
from app.relations.models import Contact

logger = logging.getLogger(__name__)

OPEN_STATUSES = ("nieuw", "in_behandeling")
MAX_ROWS = 20  # per blok in de mail; de rest staat in de app


@dataclass
class SummaryData:
    """Alles wat de mail nodig heeft, zonder ORM-objecten (pure functie testbaar)."""

    brieven: list[dict] = field(default_factory=list)
    verweer: list[dict] = field(default_factory=list)
    termijnen: list[dict] = field(default_factory=list)
    app_url: str = ""
    vandaag: date = field(default_factory=date.today)

    @property
    def leeg(self) -> bool:
        return not (self.brieven or self.verweer or self.termijnen)


def _eur(bedrag: Decimal | float | int | str) -> str:
    d = Decimal(str(bedrag)).quantize(Decimal("0.01"))
    heel, cent = f"{abs(d):.2f}".split(".")
    heel = f"{int(heel):,}".replace(",", ".")
    return f"{'-' if d < 0 else ''}€ {heel},{cent}"


def _tabel(kop: str, kolommen: list[str], rijen: list[list[str]], totaal: int) -> str:
    if not rijen:
        return ""
    th = "".join(
        f'<th style="text-align:left;padding:6px 8px;border-bottom:1px solid #e2e8f0;'
        f'font-size:12px;color:#475569;">{escape(k)}</th>'
        for k in kolommen
    )
    trs = "".join(
        "<tr>"
        + "".join(
            f'<td style="padding:6px 8px;border-bottom:1px solid #f1f5f9;font-size:13px;">'
            f"{escape(str(c))}</td>"
            for c in rij
        )
        + "</tr>"
        for rij in rijen
    )
    meer = (
        f'<p style="margin:6px 0 0;font-size:12px;color:#64748b;">'
        f"… en nog {totaal - len(rijen)} in de app.</p>"
        if totaal > len(rijen)
        else ""
    )
    return (
        f'<h2 style="font-size:15px;margin:22px 0 8px;color:#0f172a;">{escape(kop)}</h2>'
        f'<table style="border-collapse:collapse;width:100%;"><tr>{th}</tr>{trs}</table>{meer}'
    )


def build_summary_html(data: SummaryData) -> str | None:
    """HTML van de mail, of None als er niets te melden is (dan geen mail)."""
    if data.leeg:
        return None

    blokken = []
    te_laat = sum(1 for b in data.brieven if b["urgency"] == "overdue")
    kop = f"{len(data.brieven)} brieven wachten op jouw akkoord"
    if te_laat:
        kop += f" ({te_laat} te laat)"
    blokken.append(
        _tabel(
            kop,
            ["Dossier", "Wederpartij", "Stap", "Dagen", "Bedrag", "Wat"],
            [
                [
                    b["case_number"],
                    b["party"] or "—",
                    b["step"],
                    str(b["days"]),
                    _eur(b["amount"]),
                    b["action"] + (" · te laat" if b["urgency"] == "overdue" else ""),
                ]
                for b in data.brieven[:MAX_ROWS]
            ],
            len(data.brieven),
        )
    )
    blokken.append(
        _tabel(
            f"{len(data.verweer)} dossiers wachten op een antwoord op verweer",
            ["Dossier", "Wederpartij", "Dagen in deze stap"],
            [[v["case_number"], v["party"] or "—", str(v["days"])] for v in data.verweer[:MAX_ROWS]],
            len(data.verweer),
        )
    )
    som = sum((Decimal(str(t["open"])) for t in data.termijnen), Decimal("0"))
    blokken.append(
        _tabel(
            f"{len(data.termijnen)} gemiste termijnen op betalingsregelingen ({_eur(som)})",
            ["Dossier", "Debiteur", "Vervaldatum", "Nog open"],
            [
                [
                    t["case_number"],
                    t["debtor_name"] or "—",
                    t["due_date"].strftime("%d-%m-%Y"),
                    _eur(t["open"]),
                ]
                for t in data.termijnen[:MAX_ROWS]
            ],
            len(data.termijnen),
        )
    )

    url = escape(data.app_url.rstrip("/"))
    datum = data.vandaag.strftime("%d-%m-%Y")
    return f"""<!DOCTYPE html>
<html lang="nl"><body style="margin:0;padding:24px;background:#f8fafc;font-family:Arial,Helvetica,sans-serif;color:#0f172a;">
  <div style="max-width:720px;margin:0 auto;background:#fff;border:1px solid #e2e8f0;border-radius:8px;padding:24px;">
    <h1 style="font-size:18px;margin:0 0 4px;">Wat vandaag op je wacht — {datum}</h1>
    <p style="margin:0 0 8px;font-size:13px;color:#475569;">Luxis verstuurt niets zelf. Alles hieronder wacht op jouw akkoord of beoordeling.</p>
    {"".join(blokken)}
    <p style="margin:24px 0 0;">
      <a href="{url}/followup" style="display:inline-block;background:#1d4ed8;color:#fff;text-decoration:none;padding:10px 16px;border-radius:6px;font-size:14px;">Open de werklijst in Luxis</a>
    </p>
    <p style="margin:18px 0 0;font-size:11px;color:#94a3b8;">Je ontvangt deze mail elke ochtend als er iets op je wacht. Is er niets, dan komt er geen mail.</p>
  </div>
</body></html>"""


async def collect_summary(db: AsyncSession, tenant_id: uuid.UUID) -> SummaryData:
    """Verzamel de drie blokken voor één kantoor. Alleen open dossiers."""
    data = SummaryData(app_url=settings.cors_origins.split(",")[0].strip())

    # 1. brieven: open follow-up-adviezen op open dossiers
    rows = await db.execute(
        select(
            FollowupRecommendation.urgency,
            FollowupRecommendation.days_in_step,
            FollowupRecommendation.outstanding_amount,
            FollowupRecommendation.recommended_action,
            Case.case_number,
            Contact.name.label("party"),
            IncassoPipelineStep.name.label("step"),
        )
        .join(Case, FollowupRecommendation.case_id == Case.id)
        .outerjoin(Contact, Case.opposing_party_id == Contact.id)
        .outerjoin(IncassoPipelineStep, Case.incasso_step_id == IncassoPipelineStep.id)
        .where(
            FollowupRecommendation.tenant_id == tenant_id,
            FollowupRecommendation.status == "pending",
            Case.is_active.is_(True),
            Case.status.in_(OPEN_STATUSES),
        )
        .order_by(
            (FollowupRecommendation.urgency == "overdue").desc(),
            FollowupRecommendation.days_in_step.desc(),
        )
    )
    for r in rows.all():
        data.brieven.append(
            {
                "case_number": r.case_number,
                "party": r.party,
                "step": r.step or "—",
                "days": r.days_in_step,
                "amount": r.outstanding_amount,
                "urgency": r.urgency,
                "action": ACTION_LABELS.get(r.recommended_action, r.recommended_action),
            }
        )

    # 2. verweer: dossiers op de hold-stap "Verweer beantwoorden"
    rows = await db.execute(
        select(Case.case_number, Case.step_entered_at, Contact.name.label("party"))
        .join(IncassoPipelineStep, Case.incasso_step_id == IncassoPipelineStep.id)
        .outerjoin(Contact, Case.opposing_party_id == Contact.id)
        .where(
            Case.tenant_id == tenant_id,
            Case.is_active.is_(True),
            Case.status.in_(OPEN_STATUSES),
            IncassoPipelineStep.name == "Verweer beantwoorden",
        )
        .order_by(Case.step_entered_at)
    )
    vandaag = date.today()
    for r in rows.all():
        dagen = (vandaag - r.step_entered_at.date()).days if r.step_entered_at else 0
        data.verweer.append({"case_number": r.case_number, "party": r.party, "days": dagen})

    # 3. gemiste termijnen: hergebruik de vooruitblik (overdue/partial altijd, pending
    #    binnen 0 dagen = niets extra), gefilterd op open dossiers.
    from app.collections.service import list_upcoming_installments

    open_nrs = {
        r[0]
        for r in (
            await db.execute(
                select(Case.case_number).where(
                    Case.tenant_id == tenant_id,
                    Case.is_active.is_(True),
                    Case.status.in_(OPEN_STATUSES),
                )
            )
        ).all()
    }
    for t in await list_upcoming_installments(db, tenant_id, days=0):
        if t["status"] in ("overdue", "partial") and t["case_number"] in open_nrs:
            data.termijnen.append(
                {
                    "case_number": t["case_number"],
                    "debtor_name": t["debtor_name"],
                    "due_date": t["due_date"],
                    "open": Decimal(str(t["amount"])) - Decimal(str(t["paid_amount"])),
                }
            )
    return data


async def send_daily_summaries(only_to: str | None = None) -> int:
    """Scheduler-job: per actief kantoor één mail naar elke actieve gebruiker.

    `only_to`: alleen naar dat adres (proefdraai) — de inhoud is verder identiek.
    Geeft het aantal verstuurde mails terug.
    """
    from app.auth.models import Tenant, User
    from app.database import async_session
    from app.email.service import is_configured, send_email

    if not is_configured():
        logger.warning("Samenvattingsmail: SMTP niet geconfigureerd — overgeslagen")
        return 0

    verstuurd = 0
    async with async_session() as session:
        tenants = list(
            (await session.execute(select(Tenant).where(Tenant.is_active.is_(True)))).scalars()
        )
        for tenant in tenants:
            await session.execute(text(f"SET app.current_tenant = '{tenant.id}'"))
            data = await collect_summary(session, tenant.id)
            html = build_summary_html(data)
            if html is None:
                logger.info("Samenvattingsmail %s: niets te melden, geen mail", tenant.name)
                continue
            users = list(
                (
                    await session.execute(
                        select(User).where(User.tenant_id == tenant.id, User.is_active.is_(True))
                    )
                ).scalars()
            )
            onderwerp = (
                f"Luxis — {len(data.brieven)} brieven, {len(data.verweer)} verweren, "
                f"{len(data.termijnen)} gemiste termijnen ({data.vandaag.strftime('%d-%m')})"
            )
            for user in users:
                if only_to and user.email != only_to:
                    continue
                try:
                    await send_email(to=user.email, subject=onderwerp, html_body=html)
                    verstuurd += 1
                    logger.info("Samenvattingsmail verstuurd naar %s", user.email)
                except Exception:
                    logger.exception("Samenvattingsmail naar %s mislukt", user.email)
    return verstuurd
