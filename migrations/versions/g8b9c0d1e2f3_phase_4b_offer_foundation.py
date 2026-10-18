"""phase 4b offer foundation

Revision ID: g8b9c0d1e2f3
Revises: f7a8b9c0d1e2
Create Date: 2026-10-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from crr.models import AwareDateTime, ExactDecimal

revision: str = "g8b9c0d1e2f3"
down_revision: Union[str, Sequence[str], None] = "f7a8b9c0d1e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "offers",
        sa.Column("id", sa.String(length=80), nullable=False),
        sa.Column("organization_id", sa.String(length=80), nullable=False),
        sa.Column("opportunity_id", sa.String(length=80), nullable=False),
        sa.Column("opportunity_version", sa.Integer(), nullable=False),
        sa.Column("proposer_actor_id", sa.String(length=80), nullable=False),
        sa.Column("recipient_actor_id", sa.String(length=80), nullable=False),
        sa.Column("quantity_value", ExactDecimal(), nullable=False),
        sa.Column("quantity_unit", sa.String(length=80), nullable=False),
        sa.Column("unit_registry_version", sa.String(length=80), nullable=False),
        sa.Column("price", ExactDecimal(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("delivery_terms", sa.JSON(), nullable=False),
        sa.Column("timing_terms", sa.JSON(), nullable=False),
        sa.Column("route_assumptions", sa.JSON(), nullable=False),
        sa.Column("conditions", sa.JSON(), nullable=False),
        sa.Column("valid_from", AwareDateTime(), nullable=False),
        sa.Column("valid_until", AwareDateTime(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.String(length=80), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("created_at", AwareDateTime(), nullable=False),
        sa.Column("updated_at", AwareDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"]),
        sa.ForeignKeyConstraint(["proposer_actor_id"], ["actors.id"]),
        sa.ForeignKeyConstraint(["recipient_actor_id"], ["actors.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["actors.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "id"),
        sa.UniqueConstraint("organization_id", "opportunity_id", "version"),
    )
    op.create_index(
        "ix_offers_organization_status",
        "offers",
        ["organization_id", "status"],
    )
    op.create_index(
        "ix_offers_organization_opportunity",
        "offers",
        ["organization_id", "opportunity_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_offers_organization_opportunity", table_name="offers")
    op.drop_index("ix_offers_organization_status", table_name="offers")
    op.drop_table("offers")
