"""SQLAlchemy persistence model for the canonical Demand object."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from crr.models import AwareDateTime, Base, ExactDecimal


class Demand(Base):
    __tablename__ = "demands"
    __table_args__ = (UniqueConstraint("organization_id", "id"),)

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    required_state: Mapped[str] = mapped_column(String(180), nullable=False)
    quantity_min_value: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    quantity_target_value: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    quantity_max_value: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    remaining_quantity_value: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    unit: Mapped[str] = mapped_column(String(80), nullable=False)
    unit_registry_version: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    location_constraints: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    timing_start: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    timing_end: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    quality_requirements: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    pricing_constraints: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    certifications: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    regulatory_constraints: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    substitutions: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    recurrence: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by: Mapped[str] = mapped_column(ForeignKey("actors.id"), nullable=False)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
