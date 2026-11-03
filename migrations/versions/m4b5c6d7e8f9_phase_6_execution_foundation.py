"""phase 6 execution foundation

Revision ID: m4b5c6d7e8f9
Revises: k2f3a4b5c6d7
Create Date: 2026-11-03
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from crr.models import AwareDateTime, ExactDecimal

revision: str = "m4b5c6d7e8f9"
down_revision: Union[str, Sequence[str], None] = "l3a4b5c6d7e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "executions",
        sa.Column("id", sa.String(length=80), nullable=False),
        sa.Column("organization_id", sa.String(length=80), nullable=False),
        sa.Column("transaction_id", sa.String(length=80), nullable=False),
        sa.Column("agreement_id", sa.String(length=80), nullable=False),
        sa.Column("resource_id", sa.String(length=80), nullable=False),
        sa.Column("resource_state_id", sa.String(length=80), nullable=False),
        sa.Column("resource_version", sa.Integer(), nullable=False),
        sa.Column("route_candidate_id", sa.String(length=120), nullable=False),
        sa.Column("quantity_value", ExactDecimal(), nullable=False),
        sa.Column("quantity_unit", sa.String(length=80), nullable=False),
        sa.Column("unit_registry_version", sa.String(length=80), nullable=False),
        sa.Column("scheduled_for", AwareDateTime(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.String(length=80), nullable=False),
        sa.Column("created_at", AwareDateTime(), nullable=False),
        sa.Column("updated_at", AwareDateTime(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.CheckConstraint("quantity_value > 0", name="ck_executions_quantity_positive"),
        sa.CheckConstraint(
            "resource_version >= 1",
            name="ck_executions_resource_version_positive",
        ),
        sa.CheckConstraint("version >= 1", name="ck_executions_version_positive"),
        sa.CheckConstraint(
            "status IN ('PLANNED', 'IN_PROGRESS', 'EXCEPTION', 'CLOSED', 'CANCELLED')",
            name="ck_executions_status",
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["organization_id", "transaction_id"],
            ["transactions.organization_id", "transactions.id"],
            name="fk_executions_org_transaction",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "created_by"],
            ["actors.organization_id", "actors.id"],
            name="fk_executions_org_actor",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "id"),
        sa.UniqueConstraint("organization_id", "transaction_id"),
    )
    op.create_index(
        "ix_executions_org_status",
        "executions",
        ["organization_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_executions_org_status", table_name="executions")
    op.drop_table("executions")
