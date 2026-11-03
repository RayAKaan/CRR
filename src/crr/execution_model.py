"""SQLAlchemy persistence for tenant-scoped physical Execution aggregates."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from crr.models import AwareDateTime, Base, ExactDecimal


class Execution(Base):
    __tablename__ = "executions"
    __table_args__ = (
        UniqueConstraint("organization_id", "id"),
        UniqueConstraint("organization_id", "transaction_id"),
        CheckConstraint("quantity_value > 0", name="ck_executions_quantity_positive"),
        CheckConstraint(
            "resource_version >= 1",
            name="ck_executions_resource_version_positive",
        ),
        CheckConstraint("version >= 1", name="ck_executions_version_positive"),
        CheckConstraint(
            "status IN ('PLANNED', 'IN_PROGRESS', 'EXCEPTION', 'CLOSED', 'CANCELLED')",
            name="ck_executions_status",
        ),
        ForeignKeyConstraint(
            ["organization_id", "transaction_id"],
            ["transactions.organization_id", "transactions.id"],
            name="fk_executions_org_transaction",
        ),
        ForeignKeyConstraint(
            ["organization_id", "created_by"],
            ["actors.organization_id", "actors.id"],
            name="fk_executions_org_actor",
        ),
        Index("ix_executions_org_status", "organization_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    transaction_id: Mapped[str] = mapped_column(String(80), nullable=False)
    agreement_id: Mapped[str] = mapped_column(String(80), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(80), nullable=False)
    resource_state_id: Mapped[str] = mapped_column(String(80), nullable=False)
    resource_version: Mapped[int] = mapped_column(Integer, nullable=False)
    route_candidate_id: Mapped[str] = mapped_column(String(120), nullable=False)
    quantity_value: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    quantity_unit: Mapped[str] = mapped_column(String(80), nullable=False)
    unit_registry_version: Mapped[str] = mapped_column(String(80), nullable=False)
    scheduled_for: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by: Mapped[str] = mapped_column(String(80), nullable=False)
    created_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    provenance: Mapped[dict[str, str]] = mapped_column(nullable=False)
