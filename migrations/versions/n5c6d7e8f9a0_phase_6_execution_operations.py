"""phase 6 execution operations and exception history

Revision ID: n5c6d7e8f9a0
Revises: m4b5c6d7e8f9
Create Date: 2026-11-03
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from crr.models import AwareDateTime, ExactDecimal

revision: str = "n5c6d7e8f9a0"
down_revision: Union[str, Sequence[str], None] = "m4b5c6d7e8f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "execution_operations",
        sa.Column("id", sa.String(80), nullable=False),
        sa.Column("organization_id", sa.String(80), nullable=False),
        sa.Column("execution_id", sa.String(80), nullable=False),
        sa.Column("operation_type", sa.String(32), nullable=False),
        sa.Column("mode", sa.String(16), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.String(80), nullable=False),
        sa.Column("created_at", AwareDateTime(), nullable=False),
        sa.Column("planned_for", AwareDateTime(), nullable=True),
        sa.Column("occurred_at", AwareDateTime(), nullable=True),
        sa.Column("location_id", sa.String(80), nullable=True),
        sa.Column("quantity_value", ExactDecimal(), nullable=True),
        sa.Column("quantity_unit", sa.String(80), nullable=True),
        sa.Column("unit_registry_version", sa.String(80), nullable=True),
        sa.Column("planned_operation_id", sa.String(80), nullable=True),
        sa.Column("supersedes_operation_id", sa.String(80), nullable=True),
        sa.Column("correction_reason", sa.Text(), nullable=True),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.CheckConstraint("sequence >= 1", name="ck_execution_operations_sequence_positive"),
        sa.CheckConstraint(
            "operation_type IN ('PICKUP', 'SHIPMENT', 'RECEIPT', 'PROCESSING', 'OUTPUT', 'DELIVERY', 'ACCEPTANCE')",
            name="ck_execution_operations_type",
        ),
        sa.CheckConstraint(
            "mode IN ('PLANNED', 'REPORTED')",
            name="ck_execution_operations_mode",
        ),
        sa.CheckConstraint(
            "(quantity_value IS NULL AND quantity_unit IS NULL AND "
            "unit_registry_version IS NULL) OR (quantity_value > 0 AND "
            "quantity_unit IS NOT NULL AND unit_registry_version IS NOT NULL)",
            name="ck_execution_operations_quantity_consistency",
        ),
        sa.CheckConstraint(
            "(supersedes_operation_id IS NULL AND correction_reason IS NULL) OR "
            "(supersedes_operation_id IS NOT NULL AND correction_reason IS NOT NULL)",
            name="ck_execution_operations_correction_consistency",
        ),
        sa.CheckConstraint(
            "(mode = 'PLANNED' AND planned_for IS NOT NULL AND occurred_at IS NULL) OR "
            "(mode = 'REPORTED' AND planned_operation_id IS NOT NULL AND occurred_at IS NOT NULL)",
            name="ck_execution_operations_time_mode",
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["organization_id", "execution_id"],
            ["executions.organization_id", "executions.id"],
            name="fk_execution_operations_org_execution",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "actor_id"],
            ["actors.organization_id", "actors.id"],
            name="fk_execution_operations_org_actor",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "location_id"],
            ["locations.organization_id", "locations.id"],
            name="fk_execution_operations_org_location",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "execution_id", "planned_operation_id"],
            [
                "execution_operations.organization_id",
                "execution_operations.execution_id",
                "execution_operations.id",
            ],
            name="fk_execution_operations_plan",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "execution_id", "supersedes_operation_id"],
            [
                "execution_operations.organization_id",
                "execution_operations.execution_id",
                "execution_operations.id",
            ],
            name="fk_execution_operations_supersedes",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "id"),
        sa.UniqueConstraint("organization_id", "execution_id", "id"),
        sa.UniqueConstraint("organization_id", "execution_id", "sequence"),
        sa.UniqueConstraint("organization_id", "supersedes_operation_id"),
    )
    op.create_index(
        "ix_execution_operations_org_execution",
        "execution_operations",
        ["organization_id", "execution_id", "sequence"],
    )

    op.create_table(
        "execution_exceptions",
        sa.Column("id", sa.String(80), nullable=False),
        sa.Column("organization_id", sa.String(80), nullable=False),
        sa.Column("execution_id", sa.String(80), nullable=False),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("actor_id", sa.String(80), nullable=False),
        sa.Column("occurred_at", AwareDateTime(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["organization_id", "execution_id"],
            ["executions.organization_id", "executions.id"],
            name="fk_execution_exceptions_org_execution",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "actor_id"],
            ["actors.organization_id", "actors.id"],
            name="fk_execution_exceptions_org_actor",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "id"),
        sa.UniqueConstraint("organization_id", "execution_id", "id"),
    )
    op.create_index(
        "ix_execution_exceptions_org_execution",
        "execution_exceptions",
        ["organization_id", "execution_id"],
    )

    op.create_table(
        "execution_exception_resolutions",
        sa.Column("id", sa.String(80), nullable=False),
        sa.Column("organization_id", sa.String(80), nullable=False),
        sa.Column("execution_id", sa.String(80), nullable=False),
        sa.Column("exception_id", sa.String(80), nullable=False),
        sa.Column("actor_id", sa.String(80), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("resolved_at", AwareDateTime(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["organization_id", "execution_id", "exception_id"],
            [
                "execution_exceptions.organization_id",
                "execution_exceptions.execution_id",
                "execution_exceptions.id",
            ],
            name="fk_execution_exception_resolutions_exception",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "actor_id"],
            ["actors.organization_id", "actors.id"],
            name="fk_execution_exception_resolutions_org_actor",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "id"),
        sa.UniqueConstraint("organization_id", "exception_id"),
    )
    op.create_index(
        "ix_execution_exception_resolutions_org_execution",
        "execution_exception_resolutions",
        ["organization_id", "execution_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_execution_exception_resolutions_org_execution",
        table_name="execution_exception_resolutions",
    )
    op.drop_table("execution_exception_resolutions")
    op.drop_index(
        "ix_execution_exceptions_org_execution",
        table_name="execution_exceptions",
    )
    op.drop_table("execution_exceptions")
    op.drop_index(
        "ix_execution_operations_org_execution",
        table_name="execution_operations",
    )
    op.drop_table("execution_operations")
