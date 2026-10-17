"""Pydantic request models for Demand."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from crr.domain.quantity import exact_decimal


class DemandInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    required_state: str = Field(min_length=1, max_length=180)
    quantity_min: Decimal
    quantity_target: Decimal
    quantity_max: Decimal
    unit: str = Field(min_length=1, max_length=80)
    unit_registry_version: str = Field(min_length=1, max_length=80)
    location_constraints: dict[str, Any] = Field(default_factory=dict)
    timing_start: datetime
    timing_end: datetime
    quality_requirements: dict[str, Any] = Field(default_factory=dict)
    pricing_constraints: dict[str, Any] = Field(default_factory=dict)
    certifications: list[str] = Field(default_factory=list)
    regulatory_constraints: dict[str, Any] = Field(default_factory=dict)
    substitutions: list[str] = Field(default_factory=list)
    recurrence: dict[str, Any] = Field(default_factory=dict)
    status: str = Field(default="DRAFT", pattern="^(DRAFT|ACTIVE)$")
    provenance: dict[str, Any] = Field(min_length=1)

    @field_validator("quantity_min", "quantity_target", "quantity_max", mode="before")
    @classmethod
    def exact_non_negative_decimal(cls, value: object) -> Decimal:
        if not isinstance(value, str):
            raise ValueError("Canonical demand quantities must be decimal strings.")
        parsed = exact_decimal(value)
        if parsed < 0:
            raise ValueError("Demand quantity cannot be negative.")
        return parsed

    @field_validator("timing_start", "timing_end")
    @classmethod
    def timezone_required(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Demand timing must include a timezone.")
        return value

    @model_validator(mode="after")
    def validate_bounds(self):
        if not self.quantity_min <= self.quantity_target <= self.quantity_max:
            raise ValueError("Demand quantities must satisfy min <= target <= max.")
        if self.timing_start >= self.timing_end:
            raise ValueError("Demand timing_start must be before timing_end.")
        return self


class DemandPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    required_state: str | None = Field(default=None, min_length=1, max_length=180)
    quantity_min: Decimal | None = None
    quantity_target: Decimal | None = None
    quantity_max: Decimal | None = None
    unit: str | None = Field(default=None, min_length=1, max_length=80)
    unit_registry_version: str | None = Field(default=None, min_length=1, max_length=80)
    location_constraints: dict[str, Any] | None = None
    timing_start: datetime | None = None
    timing_end: datetime | None = None
    quality_requirements: dict[str, Any] | None = None
    pricing_constraints: dict[str, Any] | None = None
    certifications: list[str] | None = None
    regulatory_constraints: dict[str, Any] | None = None
    substitutions: list[str] | None = None
    recurrence: dict[str, Any] | None = None
    status: str | None = Field(
        default=None,
        pattern="^(DRAFT|ACTIVE|PAUSED|FULFILLED|EXPIRED|CANCELLED|DISPUTED)$",
    )
    provenance: dict[str, Any] | None = None

    @field_validator("quantity_min", "quantity_target", "quantity_max", mode="before")
    @classmethod
    def exact_non_negative_decimal(cls, value: object) -> Decimal | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("Canonical demand quantities must be decimal strings.")
        parsed = exact_decimal(value)
        if parsed < 0:
            raise ValueError("Demand quantity cannot be negative.")
        return parsed

    @field_validator("timing_start", "timing_end")
    @classmethod
    def timezone_required(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("Demand timing must include a timezone.")
        return value
