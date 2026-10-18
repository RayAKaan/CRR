"""SQLAlchemy persistence model for EconomicModel definitions."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from crr.models import AwareDateTime, Base


class EconomicModel(Base):
    __tablename__ = "economic_models"
    __table_args__ = (
        UniqueConstraint("organization_id", "model_key", "version"),
        Index("ix_economic_models_organization_status", "organization_id", "status"),
        Index("ix_economic_models_organization_key", "organization_id", "model_key"),
    )

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    model_key: Mapped[str] = mapped_column(String(120), nullable=False)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    valid_from: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    valid_until: Mapped[datetime | None] = mapped_column(AwareDateTime())
    calculation_version: Mapped[str] = mapped_column(String(80), nullable=False)
    rounding_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    rounding_scale: Mapped[int] = mapped_column(Integer, nullable=False)
    components: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_by: Mapped[str] = mapped_column(ForeignKey("actors.id"), nullable=False)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
