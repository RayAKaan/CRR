"""SQLAlchemy persistence for commercial Offers."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from crr.models import AwareDateTime, Base, ExactDecimal


class Offer(Base):
    __tablename__ = "offers"
    __table_args__ = (
        UniqueConstraint("organization_id", "id"),
        UniqueConstraint("organization_id", "opportunity_id", "version"),
        Index("ix_offers_organization_status", "organization_id", "status"),
        Index("ix_offers_organization_opportunity", "organization_id", "opportunity_id"),
    )

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    opportunity_id: Mapped[str] = mapped_column(ForeignKey("opportunities.id"), nullable=False)
    opportunity_version: Mapped[int] = mapped_column(Integer, nullable=False)
    proposer_actor_id: Mapped[str] = mapped_column(ForeignKey("actors.id"), nullable=False)
    recipient_actor_id: Mapped[str] = mapped_column(ForeignKey("actors.id"), nullable=False)
    quantity_value: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    quantity_unit: Mapped[str] = mapped_column(String(80), nullable=False)
    unit_registry_version: Mapped[str] = mapped_column(String(80), nullable=False)
    price: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    delivery_terms: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    timing_terms: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    route_assumptions: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    conditions: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    valid_from: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    valid_until: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by: Mapped[str] = mapped_column(ForeignKey("actors.id"), nullable=False)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
