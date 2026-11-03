"""phase 5 transaction foundation

Revision ID: j1e2f3a4b5c6
Revises: i0d1e2f3a4b5
Create Date: 2026-11-03
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from crr.models import AwareDateTime, ExactDecimal

revision: str = "j1e2f3a4b5c6"
down_revision: Union[str, Sequence[str], None] = "i0d1e2f3a4b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "transactions",
        sa.Column("id", sa.String(length=80), nullable=False),
        sa.Column("organization_id", sa.String(length=80), nullable=False),
        sa.Column("agreement_id", sa.String(length=80), nullable=False),
        sa.Column("resource_id", sa.String(length=80), nullable=False),
        sa.Column("resource_state_id", sa.String(length=80), nullable=False),
        sa.Column("resource_version", sa.Integer(), nullable=False),
        sa.Column("proposer_actor_id", sa.String(length=80), nullable=False),
        sa.Column("recipient_actor_id", sa.String(length=80), nullable=False),
        sa.Column("quantity_value", ExactDecimal(), nullable=False),
        sa.Column("quantity_unit", sa.String(length=80), nullable=False),
        sa.Column("unit_registry_version", sa.String(length=80), nullable=False),
        sa.Column("price", ExactDecimal(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("terms_snapshot", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
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
            ["organization_id", "proposer_actor_id"],
            ["actors.organization_id", "actors.id"],
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "recipient_actor_id"],
            ["actors.organization_id", "actors.id"],
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "created_by"],
            ["actors.organization_id", "actors.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "id"),
        sa.UniqueConstraint("organization_id", "agreement_id"),
    )
    op.create_index(
        "ix_transactions_org_status",
        "transactions",
        ["organization_id", "status"],
    )
    op.create_table(
        "transaction_reservations",
        sa.Column("organization_id", sa.String(length=80), nullable=False),
        sa.Column("transaction_id", sa.String(length=80), nullable=False),
        sa.Column("reservation_id", sa.String(length=80), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id", "transaction_id"],
            ["transactions.organization_id", "transactions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "reservation_id"],
            ["reservations.organization_id", "reservations.id"],
        ),
        sa.PrimaryKeyConstraint("organization_id", "transaction_id", "reservation_id"),
    )
    op.create_index(
        "ix_transaction_reservations_reservation",
        "transaction_reservations",
        ["organization_id", "reservation_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_transaction_reservations_reservation",
        table_name="transaction_reservations",
    )
    op.drop_table("transaction_reservations")
    op.drop_index("ix_transactions_org_status", table_name="transactions")
    op.drop_table("transactions")
