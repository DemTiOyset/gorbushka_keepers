from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    order_posting_number: Mapped[str] = mapped_column(
        String(50), ForeignKey("orders.posting_number"), index=True
    )

    name: Mapped[str] = mapped_column(String, nullable=False)

    sku: Mapped[int] = mapped_column(BigInteger, index=True)

    quantity: Mapped[int] = mapped_column(Integer)

    # Количество отмененного товара в этой позиции (по умолчанию 0)
    quantity_cancelled: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    # Сумма комиссии, которую Ozon забирает себе за продажу
    commission_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Чистая выплата на наш счет за товар (price - commission_amount)
    expected_payout: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    commission_percent: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    customer_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    old_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    discount_percent_from_seller: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    discount_value_from_seller: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    is_returned_finished: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    cancell_reason: Mapped[str] = mapped_column(String, nullable=True)

    comment: Mapped[str] = mapped_column(String, nullable=True)

    order: Mapped["Order"] = relationship(  # noqa: F821  # pyright: ignore[reportUndefinedVariable]
        back_populates="items",
    )
