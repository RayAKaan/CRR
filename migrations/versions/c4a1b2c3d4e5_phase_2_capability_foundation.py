"""Phase 2B Capability foundation.

Revision ID: c4a1b2c3d4e5
Revises: b7f0d8d1e2c3
"""

from alembic import op
import sqlalchemy as sa

from crr.models import AwareDateTime, ExactDecimal

revision = "c4a1b2c3d4e5"
down_revision = "b7f0d8d1e2c3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "capabilities",
        sa.Column("id", sa.String(length=80), nullable=False),
        sa.Column("organization_id", sa.String(length=80), nullable=False),
        sa.Column("accepted_inputs", sa.JSON(), nullable=False),
        sa.Column("output_specifications", sa.JSON(), nullable=False),
        sa.Column("transformation_ids", sa.JSON(), nullable=False),
        sa.Column("capacity_value", ExactDecimal(), nullable=False),
        sa.Column("unit", sa.String(length=80), nullable=False),
        sa.Column("unit_registry_version", sa.String(length=80), nullable=False),
        sa.Column("minimum_batch_value", ExactDecimal(), nullable=True),
        sa.Column("location_id", sa.String(length=80), nullable=False),
        sa.Column("operating_window_start", AwareDateTime(), nullable=False),
        sa.Column("operating_window_end", AwareDateTime(), nullable=False),
        sa.Column("processing_cost", sa.JSON(), nullable=False),
        sa.Column("certifications", sa.JSON(), nullable=False),
        sa.Column("regulatory_constraints", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.String(length=80), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("created_at", AwareDateTime(), nullable=False),
        sa.Column("updated_at", AwareDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["actors.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "id"),
    )
    op.create_index(
        "ix_capabilities_organization_status",
        "capabilities",
        ["organization_id", "status"],
    )
    op.create_index(
        "ix_capabilities_organization_window",
        "capabilities",
        ["organization_id", "operating_window_start", "operating_window_end"],
    )
    op.create_index(
        "ix_capabilities_organization_location",
        "capabilities",
        ["organization_id", "location_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_capabilities_organization_location", table_name="capabilities")
    op.drop_index("ix_capabilities_organization_window", table_name="capabilities")
    op.drop_index("ix_capabilities_organization_status", table_name="capabilities")
    op.drop_table("capabilities")
