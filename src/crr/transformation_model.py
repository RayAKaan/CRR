"""SQLAlchemy persistence model for the canonical Transformation object."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import ForeignKey, Index, JSON, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from crr.models import AwareDateTime, Base, ExactDecimal


class Transformation(Base):
    __tablename__ = "transformations"
    __table_args__ = (
        UniqueConstraint("organization_id", "id"),
        Index("ix_transformations_organization_status", "organization_id", "status"),
        Index("ix_transformations_organization_created", "organization_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    input_specifications: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    output_specifications: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    yield_min_value: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    yield_target_value: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    yield_max_value: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    loss_residuals: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    capacity_value: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    unit: Mapped[str] = mapped_column(String(80), nullable=False)
    unit_registry_version: Mapped[str] = mapped_column(String(80), nullable=False)
    cost_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    quality_effects: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    regulatory_requirements: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    eligible_capability_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    eligible_location_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by: Mapped[str] = mapped_column(ForeignKey("actors.id"), nullable=False)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
