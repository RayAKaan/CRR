"""SQLAlchemy schema for the CRR reference implementation."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

from crr.domain.quantity import exact_decimal


class Base(DeclarativeBase):
    pass


class AwareDateTime(TypeDecorator):
    """Persist UTC offsets in SQLite text columns and timezone-aware datetimes in PostgreSQL."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "sqlite":
            return dialect.type_descriptor(String(40))
        return dialect.type_descriptor(DateTime(timezone=True))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Authoritative timestamps must include a timezone.")
        value = value.astimezone(__import__("datetime").timezone.utc)
        return value.isoformat() if dialect.name == "sqlite" else value

    def process_result_value(self, value, dialect):
        if value is None or dialect.name != "sqlite":
            return value
        from datetime import datetime

        return datetime.fromisoformat(value)


class ExactDecimal(TypeDecorator):
    """Use PostgreSQL NUMERIC and exact decimal text in SQLite test/development databases."""

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(Numeric())
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        decimal_value = exact_decimal(value)
        return decimal_value if dialect.name == "postgresql" else str(decimal_value)

    def process_result_value(self, value, dialect):
        return None if value is None else Decimal(value)


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)


class Actor(Base):
    __tablename__ = "actors"
    __table_args__ = (UniqueConstraint("organization_id", "id"),)

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    role: Mapped[str] = mapped_column(String(40), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)


class Location(Base):
    __tablename__ = "locations"
    __table_args__ = (UniqueConstraint("organization_id", "id"),)

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    address: Mapped[str | None] = mapped_column(Text)
    latitude: Mapped[str | None] = mapped_column(String(64))
    longitude: Mapped[str | None] = mapped_column(String(64))
    jurisdiction: Mapped[str | None] = mapped_column(String(120))
    provenance: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)


class Resource(Base):
    __tablename__ = "resources"
    __table_args__ = (UniqueConstraint("organization_id", "id"),)

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_by: Mapped[str] = mapped_column(ForeignKey("actors.id"), nullable=False)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)


class ResourceState(Base):
    __tablename__ = "resource_states"
    __table_args__ = (
        UniqueConstraint("resource_id", "resource_version"),
        UniqueConstraint("organization_id", "id"),
    )

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    resource_id: Mapped[str] = mapped_column(ForeignKey("resources.id"), nullable=False)
    resource_version: Mapped[int] = mapped_column(Integer, nullable=False)
    state_type: Mapped[str] = mapped_column(String(180), nullable=False)
    quantity_value: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    unit: Mapped[str] = mapped_column(String(80), nullable=False)
    unit_registry_version: Mapped[str] = mapped_column(String(80), nullable=False)
    location_id: Mapped[str] = mapped_column(ForeignKey("locations.id"), nullable=False)
    effective_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    created_by: Mapped[str] = mapped_column(ForeignKey("actors.id"), nullable=False)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    quality: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    physical_properties: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    predecessor_state_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)


class StateTransition(Base):
    __tablename__ = "state_transitions"
    __table_args__ = (
        UniqueConstraint("organization_id", "idempotency_key"),
        UniqueConstraint("resource_id", "aggregate_version"),
    )

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    resource_id: Mapped[str] = mapped_column(ForeignKey("resources.id"), nullable=False)
    predecessor_state_id: Mapped[str] = mapped_column(
        ForeignKey("resource_states.id"), nullable=False
    )
    successor_state_id: Mapped[str] = mapped_column(
        ForeignKey("resource_states.id"), nullable=False
    )
    aggregate_version: Mapped[int] = mapped_column(Integer, nullable=False)
    transition_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    actor_id: Mapped[str] = mapped_column(ForeignKey("actors.id"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)


class APIKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    actor_id: Mapped[str] = mapped_column(ForeignKey("actors.id"), nullable=False)
    secret_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    scopes: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)


class OutboxEvent(Base):
    __tablename__ = "outbox_events"
    __table_args__ = (UniqueConstraint("aggregate_type", "aggregate_id", "aggregate_version"),)

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    event_version: Mapped[int] = mapped_column(Integer, nullable=False)
    aggregate_type: Mapped[str] = mapped_column(String(80), nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String(80), nullable=False)
    aggregate_version: Mapped[int] = mapped_column(Integer, nullable=False)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    actor_id: Mapped[str] = mapped_column(ForeignKey("actors.id"), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(AwareDateTime())
    correlation_id: Mapped[str] = mapped_column(String(80), nullable=False)
    causation_id: Mapped[str | None] = mapped_column(String(80))
    idempotency_key: Mapped[str | None] = mapped_column(String(255))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    schema_version: Mapped[str] = mapped_column(String(40), nullable=False, default="0.1")


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    __table_args__ = (UniqueConstraint("organization_id", "idempotency_key"),)

    id: Mapped[str] = mapped_column(
        String(80), primary_key=True, default=lambda: "idm_" + uuid4().hex
    )
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    object_type: Mapped[str] = mapped_column(String(80), nullable=False)
    object_id: Mapped[str] = mapped_column(String(80), nullable=False)
    created_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
