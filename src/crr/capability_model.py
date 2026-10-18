"""SQLAlchemy persistence model for the canonical Capability object."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from crr.models import AwareDateTime, Base, ExactDecimal


class Capability(Base):
    __tablename__ = "capabilities"
    __table_args__ = (
        UniqueConstraint("organization_id", "id"),
        Index("ix_capabilities_organization_status", "organization_id", "status"),
        Index(
            "ix_capabilities_organization_window",
            "organization_id",
            "operating_window_start",
            "operating_window_end",
        ),
        Index("ix_capabilities_organization_location", "organization_id", "location_id"),
    )

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    accepted_inputs: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    output_specifications: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    transformation_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    capacity_value: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    unit: Mapped[str] = mapped_column(String(80), nullable=False)
    unit_registry_version: Mapped[str] = mapped_column(String(80), nullable=False)
    minimum_batch_value: Mapped[Decimal | None] = mapped_column(ExactDecimal())
    location_id: Mapped[str] = mapped_column(ForeignKey("locations.id"), nullable=False)
    operating_window_start: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    operating_window_end: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    processing_cost: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    certifications: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    regulatory_constraints: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by: Mapped[str] = mapped_column(ForeignKey("actors.id"), nullable=False)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
