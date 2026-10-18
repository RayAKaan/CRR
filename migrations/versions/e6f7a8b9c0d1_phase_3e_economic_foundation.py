"""phase 3e economic foundation

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-10-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e6f7a8b9c0d1"
down_revision: Union[str, Sequence[str], None] = "d5e6f7a8b9c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "economic_models",
        sa.Column("id", sa.String(length=80), nullable=False),
        sa.Column("model_key", sa.String(length=120), nullable=False),
        sa.Column("organization_id", sa.String(length=80), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("calculation_version", sa.String(length=80), nullable=False),
        sa.Column("rounding_mode", sa.String(length=32), nullable=False),
        sa.Column("rounding_scale", sa.Integer(), nullable=False),
        sa.Column("components", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_by", sa.String(length=80), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["actors.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "model_key", "version"),
    )
    op.create_index(
        "ix_economic_models_organization_status",
        "economic_models",
        ["organization_id", "status"],
    )
    op.create_index(
        "ix_economic_models_organization_key",
        "economic_models",
        ["organization_id", "model_key"],
    )


def downgrade() -> None:
    op.drop_index("ix_economic_models_organization_key", table_name="economic_models")
    op.drop_index("ix_economic_models_organization_status", table_name="economic_models")
    op.drop_table("economic_models")
