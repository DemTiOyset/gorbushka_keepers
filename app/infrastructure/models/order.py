from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Order(Base):
    __tablename__ = "orders"

    order_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    campaign_id: Mapped[int] = mapped_column(Integer)

    # Дата создания заказа.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Дата изменения статуса. При создании ставим текущее время UTC,
    # а при любом изменении строки (onupdate) база сама обновит время на актуальное.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    status: Mapped[str] = mapped_column(String)

    expected_payout: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    payout: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=True)

    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False)

    is_cancelled_finished: Mapped[bool] = mapped_column(Boolean, default=False)

    has_returned: Mapped[bool] = mapped_column(Boolean, default=False)

    items: Mapped[list["OrderItem"]] = relationship(  # noqa: F821  # pyright: ignore[reportUndefinedVariable]
        back_populates="order",
        cascade="all, delete-orphan",
    )

    last_update_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    last_cancel_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    last_return_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # stock_items: Mapped[list["StockItem"]] = relationship(  # noqa: F821  # pyright: ignore[reportUndefinedVariable]
    #     back_populates="order",
    #     cascade="all, delete-orphan",
    # )
