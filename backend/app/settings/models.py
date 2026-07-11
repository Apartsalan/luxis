"""Settings models — globale (niet-tenant) app-configuratie."""

from sqlalchemy import Boolean
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
