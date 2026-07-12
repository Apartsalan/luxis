"""Settings models — globale (niet-tenant) app-configuratie."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, TimestampMixin


class AppConfig(Base, TimestampMixin):
    """Globale, één-rij app-configuratie (geen tenant_id — zoals interest_rates).

    Houdt operationele schakelaars die voor de héle installatie gelden. Nu alleen:
    het bouwfase-mailslot — vanuit Instellingen aan/uit te zetten en persistent
    zodat een herstart de gekozen stand behoudt. Fail-safe: standaard dicht.
    """

    __tablename__ = "app_config"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    outbound_mail_locked: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )


class SchedulerHeartbeat(Base):
    """Laatste-run-registratie per achtergrondtaak (S203 #2).

    Globaal (geen tenant_id — de scheduler draait installatiebreed). Zonder dit kon
    een job (m.n. de dagelijkse verjaringscheck) stil stoppen zonder dat iemand het
    merkte: geen verjaring-waarschuwingen meer, alleen server-log. Een dead-man-switch
    op deze tabel signaleert 'job draait niet meer'.
    """

    __tablename__ = "scheduler_heartbeat"

    job_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    last_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_error_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
