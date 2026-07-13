from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class User(Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String, primary_key=True)

    hashed_password: Mapped[str] = mapped_column(String)

    database_url: Mapped[str] = mapped_column(String)
