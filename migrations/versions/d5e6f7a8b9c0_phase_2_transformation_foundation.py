"""Phase 2C Transformation foundation.

Revision ID: d5e6f7a8b9c0
Revises: c4a1b2c3d4e5
"""

from alembic import op
import sqlalchemy as sa

from crr.models import AwareDateTime, ExactDecimal

revision = "d5e6f7a8b9c0"
down_revision = "c4a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "transformations",
        sa.Column("id", sa.String(length=80), nullable=False),
        sa.Column("organization_id", sa.String(length=80), nullable=False),
        sa.Column("input_specifications", sa.JSON(), nullable=False),
        sa.Column("output_specifications", sa.JSON(), nullable=False),
        sa.Column("yield_min_value", ExactDecimal(), nullable=False),
        sa.Column("yield_target_value", ExactDecimal(), nullable=False),
        sa.Column("yield_max_value", ExactDecimal(), nullable=False),
        sa.Column("loss_residuals", sa.JSON(), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("capacity_value", ExactDecimal(), nullable=False),
        sa.Column("unit", sa.String(length=80), nullable=False),
        sa.Column("unit_registry_version", sa.String(length=80), nullable=False),
        sa.Column("cost_metadata", sa.JSON(), nullable=False),
        sa.Column("quality_effects", sa.JSON(), nullable=False),
        sa.Column("regulatory_requirements", sa.JSON(), nullable=False),
        sa.Column("eligible_capability_ids", sa.JSON(), nullable=False),
        sa.Column("eligible_location_ids", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.String(length=80), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("created_at", AwareDateTime(), nullable=False),
        sa.Column("updated_at", AwareDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["actors.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "id"),
    )
    op.create_index(
        "ix_transformations_organization_status",
        "transformations",
        ["organization_id", "status"],
    )
    op.create_index(
        "ix_transformations_organization_created",
        "transformations",
        ["organization_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_transformations_organization_created", table_name="transformations")
    op.drop_index("ix_transformations_organization_status", table_name="transformations")
    op.drop_table("transformations")
