"""SQLAlchemy persistence for tenant-scoped resource Reservations."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from crr.models import AwareDateTime, Base, ExactDecimal


class Reservation(Base):
    __tablename__ = "reservations"
    __table_args__ = (
        UniqueConstraint("organization_id", "id"),
        ForeignKeyConstraint(
            ["organization_id", "agreement_id"],
            ["agreements.organization_id", "agreements.id"],
        ),
        ForeignKeyConstraint(
            ["organization_id", "resource_id"],
            ["resources.organization_id", "resources.id"],
        ),
        ForeignKeyConstraint(
            ["organization_id", "resource_state_id"],
            ["resource_states.organization_id", "resource_states.id"],
        ),
        ForeignKeyConstraint(
            ["organization_id", "created_by"],
            ["actors.organization_id", "actors.id"],
        ),
        Index("ix_reservations_org_state_status", "organization_id", "resource_state_id", "status"),
        Index("ix_reservations_org_agreement", "organization_id", "agreement_id"),
    )

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    agreement_id: Mapped[str] = mapped_column(String(80), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(80), nullable=False)
    resource_state_id: Mapped[str] = mapped_column(String(80), nullable=False)
    resource_version: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_value: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    quantity_unit: Mapped[str] = mapped_column(String(80), nullable=False)
    unit_registry_version: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by: Mapped[str] = mapped_column(String(80), nullable=False)
    created_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    provenance: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False)
