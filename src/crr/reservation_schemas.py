"""Request schemas for the Reservation allocation boundary."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from crr.domain.quantity import exact_decimal


class ReservationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agreement_id: str = Field(min_length=1, max_length=80)
    resource_state_id: str = Field(min_length=1, max_length=80)
    resource_state_version: int = Field(ge=1)
    quantity_value: Decimal
    quantity_unit: str = Field(min_length=1, max_length=80)
    unit_registry_version: str = Field(min_length=1, max_length=80)
    expires_at: datetime

    @field_validator("quantity_value", mode="before")
    @classmethod
    def exact_quantity(cls, value: object) -> Decimal:
        if not isinstance(value, str):
            raise ValueError("Reservation quantities must be decimal strings.")
        return exact_decimal(value)

    @field_validator("quantity_value")
    @classmethod
    def positive_quantity(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("Reservation quantity must be greater than zero.")
        return value

    @field_validator("expires_at")
    @classmethod
    def timezone_required(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Reservation expiry must include a timezone.")
        return value


class ReservationLifecycleInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = Field(pattern="^(RELEASED|EXPIRED)$")
