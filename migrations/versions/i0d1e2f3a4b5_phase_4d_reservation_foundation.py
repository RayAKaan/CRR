"""phase 4d reservation foundation

Revision ID: i0d1e2f3a4b5
Revises: h9c0d1e2f3a4
Create Date: 2026-11-03
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from crr.models import AwareDateTime, ExactDecimal

revision: str = "i0d1e2f3a4b5"
down_revision: Union[str, Sequence[str], None] = "h9c0d1e2f3a4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reservations",
        sa.Column("id", sa.String(length=80), nullable=False),
        sa.Column("organization_id", sa.String(length=80), nullable=False),
        sa.Column("agreement_id", sa.String(length=80), nullable=False),
        sa.Column("resource_id", sa.String(length=80), nullable=False),
        sa.Column("resource_state_id", sa.String(length=80), nullable=False),
        sa.Column("resource_version", sa.Integer(), nullable=False),
        sa.Column("quantity_value", ExactDecimal(), nullable=False),
        sa.Column("quantity_unit", sa.String(length=80), nullable=False),
        sa.Column("unit_registry_version", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("expires_at", AwareDateTime(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.String(length=80), nullable=False),
        sa.Column("created_at", AwareDateTime(), nullable=False),
        sa.Column("updated_at", AwareDateTime(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["organization_id", "agreement_id"],
            ["agreements.organization_id", "agreements.id"],
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "resource_id"],
            ["resources.organization_id", "resources.id"],
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "resource_state_id"],
            ["resource_states.organization_id", "resource_states.id"],
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "created_by"],
            ["actors.organization_id", "actors.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "id"),
    )
    op.create_index(
        "ix_reservations_org_state_status",
        "reservations",
        ["organization_id", "resource_state_id", "status"],
    )
    op.create_index(
        "ix_reservations_org_agreement",
        "reservations",
        ["organization_id", "agreement_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_reservations_org_agreement", table_name="reservations")
    op.drop_index("ix_reservations_org_state_status", table_name="reservations")
    op.drop_table("reservations")
