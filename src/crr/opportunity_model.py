"""SQLAlchemy persistence for commercial Opportunities."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from crr.models import AwareDateTime, Base, ExactDecimal


class Opportunity(Base):
    __tablename__ = "opportunities"
    __table_args__ = (
        UniqueConstraint("organization_id", "id"),
        UniqueConstraint(
            "organization_id",
            "route_candidate_id",
            "candidate_set_fingerprint",
        ),
        Index("ix_opportunities_organization_status", "organization_id", "status"),
        Index("ix_opportunities_organization_demand", "organization_id", "target_demand_id"),
    )

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    route_candidate_id: Mapped[str] = mapped_column(String(120), nullable=False)
    candidate_set_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    source_resource_state_id: Mapped[str] = mapped_column(
        ForeignKey("resource_states.id"), nullable=False
    )
    source_resource_state_version: Mapped[int] = mapped_column(Integer, nullable=False)
    target_demand_id: Mapped[str] = mapped_column(ForeignKey("demands.id"), nullable=False)
    target_demand_version: Mapped[int] = mapped_column(Integer, nullable=False)
    route_provenance: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    advisory_provenance: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    economic_model_id: Mapped[str | None] = mapped_column(ForeignKey("economic_models.id"))
    economic_model_version: Mapped[int | None] = mapped_column(Integer)
    commercial_perspective: Mapped[str | None] = mapped_column(String(64))
    currency: Mapped[str | None] = mapped_column(String(3))
    quantity_value: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    quantity_unit: Mapped[str] = mapped_column(String(80), nullable=False)
    unit_registry_version: Mapped[str] = mapped_column(String(80), nullable=False)
    valid_from: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    valid_until: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by: Mapped[str] = mapped_column(ForeignKey("actors.id"), nullable=False)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
