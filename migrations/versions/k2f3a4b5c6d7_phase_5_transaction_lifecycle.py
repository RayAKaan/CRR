"""phase 5 transaction lifecycle

Revision ID: k2f3a4b5c6d7
Revises: j1e2f3a4b5c6
Create Date: 2026-11-03
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from crr.models import AwareDateTime

revision: str = "k2f3a4b5c6d7"
down_revision: Union[str, Sequence[str], None] = "j1e2f3a4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("transactions", sa.Column("scheduled_for", AwareDateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("transactions", "scheduled_for")
