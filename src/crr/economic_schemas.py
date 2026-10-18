"""Pydantic request models for deterministic economic models."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from crr.domain.economics import EconomicComponentKind, EconomicPerspective
from crr.domain.quantity import exact_decimal


class EconomicComponentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    perspective: EconomicPerspective
    kind: EconomicComponentKind
    label: str = Field(min_length=1, max_length=160)
    amount: Decimal
    source: str = Field(min_length=1, max_length=255)

    @field_validator("amount", mode="before")
    @classmethod
    def exact_non_negative_decimal(cls, value: object) -> Decimal:
        if not isinstance(value, str):
            raise ValueError("Economic amounts must be decimal strings.")
        parsed = exact_decimal(value)
        if parsed < 0:
            raise ValueError("Economic component amount cannot be negative.")
        return parsed


class RoundingPolicyInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: str = Field(pattern="^(HALF_EVEN|HALF_UP|DOWN|UP|FLOOR|CEILING)$")
    scale: int = Field(ge=0, le=18)


class EconomicModelInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str | None = Field(default=None, min_length=1, max_length=80)
    model_key: str = Field(min_length=1, max_length=120)
    version: int = Field(default=1, ge=1)
    currency: str = Field(min_length=3, max_length=3, pattern="^[A-Z]{3}$")
    valid_from: datetime
    valid_until: datetime | None = None
    calculation_version: str = Field(min_length=1, max_length=80)
    rounding: RoundingPolicyInput
    components: list[EconomicComponentInput] = Field(min_length=1)
    status: str = Field(default="DRAFT", pattern="^(DRAFT|ACTIVE|RETIRED)$")
    provenance: dict[str, Any] = Field(min_length=1)

    @field_validator("valid_from", "valid_until")
    @classmethod
    def timezone_required(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("Economic model validity timestamps must include a timezone.")
        return value

    @model_validator(mode="after")
    def validate_window(self):
        if self.valid_until is not None and self.valid_until <= self.valid_from:
            raise ValueError("Economic model valid_until must be after valid_from.")
        return self
