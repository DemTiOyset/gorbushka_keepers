from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class User(Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String, primary_key=True)

    hashed_password: Mapped[str] = mapped_column(String)

    database_url: Mapped[str] = mapped_column(String)

    market_type: Mapped[str] = mapped_column(String, nullable=True)

    api_key: Mapped[str] = mapped_column(String, nullable=True)

    business_id: Mapped[str] = mapped_column(String, nullable=True)

    campaign_ids: Mapped[list[int]] = mapped_column(ARRAY(Integer), default=list)
