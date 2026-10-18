"""phase 4a opportunity foundation

Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
Create Date: 2026-10-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from crr.models import AwareDateTime, ExactDecimal

revision: str = "f7a8b9c0d1e2"
down_revision: Union[str, Sequence[str], None] = "e6f7a8b9c0d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "opportunities",
        sa.Column("id", sa.String(length=80), nullable=False),
        sa.Column("organization_id", sa.String(length=80), nullable=False),
        sa.Column("route_candidate_id", sa.String(length=120), nullable=False),
        sa.Column("candidate_set_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("source_resource_state_id", sa.String(length=80), nullable=False),
        sa.Column("source_resource_state_version", sa.Integer(), nullable=False),
        sa.Column("target_demand_id", sa.String(length=80), nullable=False),
        sa.Column("target_demand_version", sa.Integer(), nullable=False),
        sa.Column("route_provenance", sa.JSON(), nullable=False),
        sa.Column("advisory_provenance", sa.JSON(), nullable=True),
        sa.Column("economic_model_id", sa.String(length=80), nullable=True),
        sa.Column("economic_model_version", sa.Integer(), nullable=True),
        sa.Column("commercial_perspective", sa.String(length=64), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("quantity_value", ExactDecimal(), nullable=False),
        sa.Column("quantity_unit", sa.String(length=80), nullable=False),
        sa.Column("unit_registry_version", sa.String(length=80), nullable=False),
        sa.Column("valid_from", AwareDateTime(), nullable=False),
        sa.Column("valid_until", AwareDateTime(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.String(length=80), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("created_at", AwareDateTime(), nullable=False),
        sa.Column("updated_at", AwareDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["source_resource_state_id"], ["resource_states.id"]),
        sa.ForeignKeyConstraint(["target_demand_id"], ["demands.id"]),
        sa.ForeignKeyConstraint(["economic_model_id"], ["economic_models.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["actors.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "id"),
        sa.UniqueConstraint(
            "organization_id", "route_candidate_id", "candidate_set_fingerprint"
        ),
    )
    op.create_index(
        "ix_opportunities_organization_status",
        "opportunities",
        ["organization_id", "status"],
    )
    op.create_index(
        "ix_opportunities_organization_demand",
        "opportunities",
        ["organization_id", "target_demand_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_opportunities_organization_demand", table_name="opportunities")
    op.drop_index("ix_opportunities_organization_status", table_name="opportunities")
    op.drop_table("opportunities")
