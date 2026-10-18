"""Pydantic schemas for the Offer commercial proposal boundary."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from crr.domain.quantity import exact_decimal


class OfferInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str | None = Field(default=None, min_length=1, max_length=80)
    opportunity_id: str = Field(min_length=1, max_length=80)
    opportunity_version: int = Field(ge=1)
    proposer_actor_id: str = Field(min_length=1, max_length=80)
    recipient_actor_id: str = Field(min_length=1, max_length=80)
    quantity_value: Decimal
    quantity_unit: str = Field(min_length=1, max_length=80)
    unit_registry_version: str = Field(min_length=1, max_length=80)
    price: Decimal
    currency: str = Field(min_length=3, max_length=3, pattern="^[A-Z]{3}$")
    delivery_terms: dict[str, Any] = Field(min_length=1)
    timing_terms: dict[str, Any] = Field(min_length=1)
    route_assumptions: dict[str, Any] = Field(min_length=1)
    conditions: dict[str, Any] = Field(default_factory=dict)
    valid_from: datetime
    valid_until: datetime
    status: str = Field(default="DRAFT", pattern="^(DRAFT|OPEN)$")
    provenance: dict[str, Any] = Field(min_length=1)

    @field_validator("quantity_value", "price", mode="before")
    @classmethod
    def exact_money_or_quantity(cls, value: object) -> Decimal:
        if not isinstance(value, str):
            raise ValueError("Offer numeric values must be decimal strings.")
        return exact_decimal(value)

    @field_validator("quantity_value")
    @classmethod
    def positive_quantity(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("Offer quantity must be greater than zero.")
        return value

    @field_validator("price")
    @classmethod
    def non_negative_price(cls, value: Decimal) -> Decimal:
        if value < 0:
            raise ValueError("Offer price cannot be negative.")
        return value

    @field_validator("valid_from", "valid_until")
    @classmethod
    def timezone_required(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Offer validity timestamps must include a timezone.")
        return value

    @model_validator(mode="after")
    def validate_window(self):
        if self.valid_until <= self.valid_from:
            raise ValueError("Offer valid_until must be after valid_from.")
        if self.proposer_actor_id == self.recipient_actor_id:
            raise ValueError("Offer proposer and recipient must be different actors.")
        return self


class OfferStatusInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = Field(pattern="^(OPEN|ACCEPTED|REJECTED|EXPIRED|WITHDRAWN)$")
