"""Append-only SQLAlchemy persistence for execution operations and exceptions."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from crr.models import AwareDateTime, Base, ExactDecimal


class ExecutionOperation(Base):
    __tablename__ = "execution_operations"
    __table_args__ = (
        UniqueConstraint("organization_id", "id"),
        UniqueConstraint("organization_id", "execution_id", "id"),
        UniqueConstraint("organization_id", "execution_id", "sequence"),
        CheckConstraint("sequence >= 1", name="ck_execution_operations_sequence_positive"),
        CheckConstraint(
            "operation_type IN ('PICKUP', 'SHIPMENT', 'RECEIPT', 'PROCESSING', 'OUTPUT', "
            "'DELIVERY', 'ACCEPTANCE')",
            name="ck_execution_operations_type",
        ),
        CheckConstraint(
            "mode IN ('PLANNED', 'REPORTED')",
            name="ck_execution_operations_mode",
        ),
        CheckConstraint(
            "(quantity_value IS NULL AND quantity_unit IS NULL AND "
            "unit_registry_version IS NULL) OR (quantity_value > 0 AND "
            "quantity_unit IS NOT NULL AND unit_registry_version IS NOT NULL)",
            name="ck_execution_operations_quantity_consistency",
        ),
        CheckConstraint(
            "(supersedes_operation_id IS NULL AND correction_reason IS NULL) OR "
            "(supersedes_operation_id IS NOT NULL AND correction_reason IS NOT NULL)",
            name="ck_execution_operations_correction_consistency",
        ),
        CheckConstraint(
            "(mode = 'PLANNED' AND planned_for IS NOT NULL AND occurred_at IS NULL) OR "
            "(mode = 'REPORTED' AND planned_operation_id IS NOT NULL AND occurred_at IS NOT NULL)",
            name="ck_execution_operations_time_mode",
        ),
        ForeignKeyConstraint(
            ["organization_id", "execution_id"],
            ["executions.organization_id", "executions.id"],
            name="fk_execution_operations_org_execution",
        ),
        ForeignKeyConstraint(
            ["organization_id", "actor_id"],
            ["actors.organization_id", "actors.id"],
            name="fk_execution_operations_org_actor",
        ),
        ForeignKeyConstraint(
            ["organization_id", "location_id"],
            ["locations.organization_id", "locations.id"],
            name="fk_execution_operations_org_location",
        ),
        ForeignKeyConstraint(
            ["organization_id", "execution_id", "planned_operation_id"],
            [
                "execution_operations.organization_id",
                "execution_operations.execution_id",
                "execution_operations.id",
            ],
            name="fk_execution_operations_plan",
        ),
        ForeignKeyConstraint(
            ["organization_id", "execution_id", "supersedes_operation_id"],
            [
                "execution_operations.organization_id",
                "execution_operations.execution_id",
                "execution_operations.id",
            ],
            name="fk_execution_operations_supersedes",
        ),
        Index(
            "ix_execution_operations_org_execution",
            "organization_id",
            "execution_id",
            "sequence",
        ),
    )

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    execution_id: Mapped[str] = mapped_column(String(80), nullable=False)
    operation_type: Mapped[str] = mapped_column(String(32), nullable=False)
    mode: Mapped[str] = mapped_column(String(16), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    actor_id: Mapped[str] = mapped_column(String(80), nullable=False)
    created_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    planned_for: Mapped[datetime | None] = mapped_column(AwareDateTime())
    occurred_at: Mapped[datetime | None] = mapped_column(AwareDateTime())
    location_id: Mapped[str | None] = mapped_column(String(80))
    quantity_value: Mapped[Decimal | None] = mapped_column(ExactDecimal())
    quantity_unit: Mapped[str | None] = mapped_column(String(80))
    unit_registry_version: Mapped[str | None] = mapped_column(String(80))
    planned_operation_id: Mapped[str | None] = mapped_column(String(80))
    supersedes_operation_id: Mapped[str | None] = mapped_column(String(80))
    correction_reason: Mapped[str | None] = mapped_column(Text)
    provenance: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False)


class ExecutionException(Base):
    __tablename__ = "execution_exceptions"
    __table_args__ = (
        UniqueConstraint("organization_id", "id"),
        UniqueConstraint("organization_id", "execution_id", "id"),
        ForeignKeyConstraint(
            ["organization_id", "execution_id"],
            ["executions.organization_id", "executions.id"],
            name="fk_execution_exceptions_org_execution",
        ),
        ForeignKeyConstraint(
            ["organization_id", "actor_id"],
            ["actors.organization_id", "actors.id"],
            name="fk_execution_exceptions_org_actor",
        ),
        Index("ix_execution_exceptions_org_execution", "organization_id", "execution_id"),
    )

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    execution_id: Mapped[str] = mapped_column(String(80), nullable=False)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    actor_id: Mapped[str] = mapped_column(String(80), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    provenance: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False)


class ExecutionExceptionResolution(Base):
    __tablename__ = "execution_exception_resolutions"
    __table_args__ = (
        UniqueConstraint("organization_id", "id"),
        UniqueConstraint("organization_id", "exception_id"),
        ForeignKeyConstraint(
            ["organization_id", "execution_id", "exception_id"],
            [
                "execution_exceptions.organization_id",
                "execution_exceptions.execution_id",
                "execution_exceptions.id",
            ],
            name="fk_execution_exception_resolutions_exception",
        ),
        ForeignKeyConstraint(
            ["organization_id", "actor_id"],
            ["actors.organization_id", "actors.id"],
            name="fk_execution_exception_resolutions_org_actor",
        ),
        Index(
            "ix_execution_exception_resolutions_org_execution",
            "organization_id",
            "execution_id",
        ),
    )

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    execution_id: Mapped[str] = mapped_column(String(80), nullable=False)
    exception_id: Mapped[str] = mapped_column(String(80), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(80), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    resolved_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    provenance: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False)
