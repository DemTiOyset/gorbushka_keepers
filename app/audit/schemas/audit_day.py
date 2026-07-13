from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.audit.schemas.audit_action import AuditActionResponse


class CashResponse(BaseModel):
    """Базовая схема для дня (без списка вложенных действий)."""

    model_config = ConfigDict(from_attributes=True)

    initial_cash: int
    current_cash: int


class AuditDaySetInitialCashResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    initial_cash: int
    current_cash: int


class AuditDayFullResponse(CashResponse):
    """Полная схема для загрузки страницы кассы за выбранный день (GET /api/audit/{date}).
    Собирает всю таблицу: верхнюю строку, массив действий, нижнюю строку и защиту.
    """

    model_config = ConfigDict(from_attributes=True)

    creation_date: date

    # Вложенный список всех действий за этот день
    actions: list[AuditActionResponse] = Field(
        default=[], description="Действия за день"
    )

    cash_by_day: int | None
