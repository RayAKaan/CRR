"""phase 4c agreement foundation

Revision ID: h9c0d1e2f3a4
Revises: g8b9c0d1e2f3
Create Date: 2026-11-03
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from crr.models import AwareDateTime

revision: str = "h9c0d1e2f3a4"
down_revision: Union[str, Sequence[str], None] = "g8b9c0d1e2f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agreements",
        sa.Column("id", sa.String(length=80), nullable=False),
        sa.Column("organization_id", sa.String(length=80), nullable=False),
        sa.Column("offer_id", sa.String(length=80), nullable=False),
        sa.Column("offer_version", sa.Integer(), nullable=False),
        sa.Column("proposer_actor_id", sa.String(length=80), nullable=False),
        sa.Column("recipient_actor_id", sa.String(length=80), nullable=False),
        sa.Column("accepted_by", sa.String(length=80), nullable=False),
        sa.Column("accepted_at", AwareDateTime(), nullable=False),
        sa.Column("terms_snapshot", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", AwareDateTime(), nullable=False),
        sa.Column("updated_at", AwareDateTime(), nullable=False),
        sa.Column("provenance", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["offer_id"], ["offers.id"]),
        sa.ForeignKeyConstraint(["proposer_actor_id"], ["actors.id"]),
        sa.ForeignKeyConstraint(["recipient_actor_id"], ["actors.id"]),
        sa.ForeignKeyConstraint(["accepted_by"], ["actors.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "id"),
        sa.UniqueConstraint("organization_id", "offer_id"),
    )
    op.create_index(
        "ix_agreements_organization_status",
        "agreements",
        ["organization_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_agreements_organization_status", table_name="agreements")
    op.drop_table("agreements")
