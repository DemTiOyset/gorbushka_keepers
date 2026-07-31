from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database import Base


class Shop(Base):
    __tablename__ = "shops"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    username: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.username"),
    )

    market_type: Mapped[str] = mapped_column(String)

    api_key: Mapped[str] = mapped_column(String)

    buisness_id: Mapped[str] = mapped_column(String)

    user: Mapped["User"] = relationship(  # noqa: F821  # pyright: ignore[reportUndefinedVariable]
        back_populates="shops",
    )
