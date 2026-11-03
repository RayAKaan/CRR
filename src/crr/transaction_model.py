"""SQLAlchemy persistence for canonical Transactions and Reservation links."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Column,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    JSON,
    Numeric,
    PrimaryKeyConstraint,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from crr.models import AwareDateTime, Base, ExactDecimal


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint("organization_id", "id"),
        UniqueConstraint("organization_id", "agreement_id"),
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
            ["organization_id", "proposer_actor_id"],
            ["actors.organization_id", "actors.id"],
        ),
        ForeignKeyConstraint(
            ["organization_id", "recipient_actor_id"],
            ["actors.organization_id", "actors.id"],
        ),
        ForeignKeyConstraint(
            ["organization_id", "created_by"],
            ["actors.organization_id", "actors.id"],
        ),
        Index("ix_transactions_org_status", "organization_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    agreement_id: Mapped[str] = mapped_column(String(80), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(80), nullable=False)
    resource_state_id: Mapped[str] = mapped_column(String(80), nullable=False)
    resource_version: Mapped[int] = mapped_column(Integer, nullable=False)
    proposer_actor_id: Mapped[str] = mapped_column(String(80), nullable=False)
    recipient_actor_id: Mapped[str] = mapped_column(String(80), nullable=False)
    quantity_value: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    quantity_unit: Mapped[str] = mapped_column(String(80), nullable=False)
    unit_registry_version: Mapped[str] = mapped_column(String(80), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    terms_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by: Mapped[str] = mapped_column(String(80), nullable=False)
    created_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    provenance: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False)


transaction_reservations = Table(
    "transaction_reservations",
    Base.metadata,
    Column("organization_id", String(80), nullable=False),
    Column("transaction_id", String(80), nullable=False),
    Column("reservation_id", String(80), nullable=False),
    ForeignKeyConstraint(
        ["organization_id", "transaction_id"],
        ["transactions.organization_id", "transactions.id"],
    ),
    ForeignKeyConstraint(
        ["organization_id", "reservation_id"],
        ["reservations.organization_id", "reservations.id"],
    ),
    PrimaryKeyConstraint("organization_id", "transaction_id", "reservation_id"),
    Index("ix_transaction_reservations_reservation", "organization_id", "reservation_id"),
)
