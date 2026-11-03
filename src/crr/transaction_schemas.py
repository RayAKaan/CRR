"""Request schemas for commercial Transaction creation and lifecycle."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TransactionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agreement_id: str = Field(min_length=1, max_length=80)
    reservation_ids: list[str] = Field(min_length=1, max_length=100)

    @field_validator("reservation_ids")
    @classmethod
    def unique_reservations(cls, value: list[str]) -> list[str]:
        if any(not item or len(item) > 80 for item in value):
            raise ValueError("Reservation IDs must be non-empty and at most 80 characters.")
        if len(set(value)) != len(value):
            raise ValueError("Reservation IDs must be unique.")
        return value


class TransactionLifecycleInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = Field(pattern="^(SCHEDULED|DISPUTED|CANCELLED)$")
    scheduled_for: datetime | None = None
    reason: str | None = Field(default=None, max_length=2000)
    resolution_note: str | None = Field(default=None, max_length=2000)

    @field_validator("scheduled_for")
    @classmethod
    def timezone_required(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("Transaction schedule must include a timezone.")
        return value
