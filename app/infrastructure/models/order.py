from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .stock_item import StockItem


class Order(Base):
    __tablename__ = "orders"

    posting_number: Mapped[str] = mapped_column(String(50), primary_key=True)

    status: Mapped[str] = mapped_column(
        String(50),
        index=True,  # по статусам часто выборки делать будем
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    last_event_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    expected_payout: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), 
        nullable=False
    )

    payout: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    payout_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )

    # Дата изменения статуса. При создании ставим текущее время UTC,
    # а при любом изменении строки (onupdate) база сама обновит время на актуальное.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    items: Mapped[list["OrderItem"]] = relationship(  # noqa: F821  # pyright: ignore[reportUndefinedVariable]
        back_populates="order",
        cascade="all, delete-orphan",
    )

    stock_items: Mapped[list["StockItem"]] = relationship(  # noqa: F821  # pyright: ignore[reportUndefinedVariable]
        back_populates="order",
        cascade="all, delete-orphan",
    )
