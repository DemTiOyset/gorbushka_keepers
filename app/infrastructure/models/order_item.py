from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.order_id"), index=True
    )

    offer_id: Mapped[str] = mapped_column(String)

    offer_name: Mapped[str] = mapped_column(String)

    count: Mapped[int] = mapped_column(Integer)

    payment: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    subsidy: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    cashback: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    vat: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    returned_count: Mapped[int] = mapped_column(Integer)

    is_returned_finished: Mapped[bool] = mapped_column(Boolean, default=False)

    order: Mapped["Order"] = relationship(  # noqa: F821  # pyright: ignore[reportUndefinedVariable]
        back_populates="items",
    )
