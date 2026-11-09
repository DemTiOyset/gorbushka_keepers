"""Add column bot token to a user model.

Revision ID: 311618b21a26
Revises: b6e6001fe30d
Create Date: 2026-10-30 16:26:59.818611

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "311618b21a26"
down_revision: Union[str, Sequence[str], None] = "b935b748ed6f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "users",
        sa.Column("bot_token", sa.String(), nullable=True),
    )


def downgrade():
    op.drop_column("users", "bot_token")
