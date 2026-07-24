from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Market(Base):
    __tablename__ = "markets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    market_name: Mapped[str] = mapped_column(
        String,
    )

    shop_name: Mapped[str] = mapped_column(String)

    api_key: Mapped[str] = mapped_column(String)

    seller_id: Mapped[str] = mapped_column(String)

    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.username"))

    user: Mapped["User"] = relationship(back_populates="markets")  # pyright: ignore[reportUndefinedVariable]  # noqa: F821
