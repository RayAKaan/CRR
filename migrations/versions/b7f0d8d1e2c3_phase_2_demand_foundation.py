"""phase 2 demand foundation"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

import crr.models

revision: str = "b7f0d8d1e2c3"
down_revision: str | None = "a1ceba67ac02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "demands",
        sa.Column("id", sa.String(length=80), nullable=False),
        sa.Column("organization_id", sa.String(length=80), nullable=False),
        sa.Column("required_state", sa.String(length=180), nullable=False),
        sa.Column("quantity_min_value", crr.models.ExactDecimal(), nullable=False),
        sa.Column("quantity_target_value", crr.models.ExactDecimal(), nullable=False),
        sa.Column("quantity_max_value", crr.models.ExactDecimal(), nullable=False),
        sa.Column("remaining_quantity_value", crr.models.ExactDecimal(), nullable=False),
        sa.Column("unit", sa.String(length=80), nullable=False),
        sa.Column("unit_registry_version", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("location_constraints", sa.JSON(), nullable=False),
        sa.Column("timing_start", crr.models.AwareDateTime(timezone=True), nullable=False),
        sa.Column("timing_end", crr.models.AwareDateTime(timezone=True), nullable=False),
        sa.Column("quality_requirements", sa.JSON(), nullable=False),
        sa.Column("pricing_constraints", sa.JSON(), nullable=False),
        sa.Column("certifications", sa.JSON(), nullable=False),
        sa.Column("regulatory_constraints", sa.JSON(), nullable=False),
        sa.Column("substitutions", sa.JSON(), nullable=False),
        sa.Column("recurrence", sa.JSON(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.String(length=80), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("created_at", crr.models.AwareDateTime(timezone=True), nullable=False),
        sa.Column("updated_at", crr.models.AwareDateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["actors.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "id"),
    )
    op.create_index("ix_demands_organization_status", "demands", ["organization_id", "status"])
    op.create_index("ix_demands_organization_timing", "demands", ["organization_id", "timing_start", "timing_end"])


def downgrade() -> None:
    op.drop_index("ix_demands_organization_timing", table_name="demands")
    op.drop_index("ix_demands_organization_status", table_name="demands")
    op.drop_table("demands")
