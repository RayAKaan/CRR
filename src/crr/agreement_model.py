"""SQLAlchemy persistence for canonical Agreements."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from crr.models import AwareDateTime, Base


class Agreement(Base):
    __tablename__ = "agreements"
    __table_args__ = (
        UniqueConstraint("organization_id", "id"),
        UniqueConstraint("organization_id", "offer_id"),
        Index("ix_agreements_organization_status", "organization_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    offer_id: Mapped[str] = mapped_column(ForeignKey("offers.id"), nullable=False)
    offer_version: Mapped[int] = mapped_column(Integer, nullable=False)
    proposer_actor_id: Mapped[str] = mapped_column(ForeignKey("actors.id"), nullable=False)
    recipient_actor_id: Mapped[str] = mapped_column(ForeignKey("actors.id"), nullable=False)
    accepted_by: Mapped[str] = mapped_column(ForeignKey("actors.id"), nullable=False)
    accepted_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    terms_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    provenance: Mapped[str] = mapped_column(Text, nullable=False)
