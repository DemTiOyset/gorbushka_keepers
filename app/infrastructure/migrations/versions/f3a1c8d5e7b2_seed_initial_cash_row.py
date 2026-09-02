"""Seed initial cash row.

Revision ID: f3a1c8d5e7b2
Revises: e1c4fbe269cd
Create Date: 2026-08-29 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f3a1c8d5e7b2"
down_revision: Union[str, Sequence[str], None] = "e1c4fbe269cd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Создаёт единственную запись в таблице cash с нулевым балансом.

    Запись добавляется ровно один раз при накатывании миграции: Alembic
    фиксирует ревизию в alembic_version, поэтому при последующих запусках
    она не выполняется повторно. Дополнительно ON CONFLICT DO NOTHING
    защищает от дубликата, если строка уже существует.
    """
    op.execute(
        """
        INSERT INTO cash (id, initial_cash, current_cash)
        VALUES (1, 0, 0)
        ON CONFLICT (id) DO NOTHING
        """
    )


def downgrade() -> None:
    """Удаляет только нетронутую стартовую запись (нулевой баланс)."""
    op.execute(
        """
        DELETE FROM cash
        WHERE id = 1 AND initial_cash = 0 AND current_cash = 0
        """
    )
