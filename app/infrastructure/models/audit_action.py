from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class AuditAction(Base):
    """
    Журнал всех операций в кассе
    """

    __tablename__ = "audit_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor: Mapped[str] = mapped_column(String)
    action: Mapped[str] = mapped_column(String)

    # Сумма операции (например: 5000 или -2300)
    money: Mapped[int] = mapped_column(Integer)

    # Дата операционного дня, к которому относится действие (например: 2026-07-09)
    creation_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Точное время создания записи в БД
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
