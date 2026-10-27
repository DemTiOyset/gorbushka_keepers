from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class Cash(Base):
    """
    Глобальное состояние кассы селлера. В БД всегда ровно 1 запись.
    """

    __tablename__ = "cash"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # ТРЕБОВАНИЕ 1: Касса с первого дня ввода (Задается 1 раз при регистрации и не меняется)
    initial_cash: Mapped[int] = mapped_column(Integer, default=0)

    # ТРЕБОВАНИЕ 2: Касса с учетом ВСЕХ изменений на текущую секунду
    # Этот баланс обновляется автоматически при добавлении любого действия
    current_cash: Mapped[int] = mapped_column(Integer, default=0)
