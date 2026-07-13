from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class StockItem(Base):
    __tablename__ = "stock_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    order_posting_number: Mapped[str] = mapped_column(
        String(50), ForeignKey("orders.posting_number"), index=True
    )

    supplier: Mapped[str] = mapped_column(String, nullable=False)

    serial_number: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)

    purchase_price: Mapped[int] = mapped_column(Integer, nullable=False)

    name: Mapped[str] = mapped_column(String)

    order: Mapped["Order"] = relationship(  # noqa: F821  # pyright: ignore[reportUndefinedVariable]
        back_populates="stock_items",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
