"""Pydantic request models for Capability."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from crr.domain.quantity import exact_decimal


class CapabilityInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    accepted_inputs: list[dict[str, Any]] = Field(min_length=1)
    output_specifications: dict[str, Any] = Field(min_length=1)
    transformation_ids: list[str] = Field(default_factory=list)
    capacity: Decimal
    unit: str = Field(min_length=1, max_length=80)
    unit_registry_version: str = Field(min_length=1, max_length=80)
    minimum_batch: Decimal | None = None
    location_id: str = Field(min_length=1, max_length=80)
    operating_window_start: datetime
    operating_window_end: datetime
    processing_cost: dict[str, Any] = Field(default_factory=dict)
    certifications: list[str] = Field(default_factory=list)
    regulatory_constraints: dict[str, Any] = Field(default_factory=dict)
    status: str = Field(default="DRAFT", pattern="^(DRAFT|ACTIVE)$")
    provenance: dict[str, Any] = Field(min_length=1)

    @field_validator("capacity", "minimum_batch", mode="before")
    @classmethod
    def exact_non_negative_decimal(cls, value: object) -> Decimal | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("Canonical capability quantities must be decimal strings.")
        parsed = exact_decimal(value)
        if parsed < 0:
            raise ValueError("Capability quantity cannot be negative.")
        return parsed

    @field_validator("operating_window_start", "operating_window_end")
    @classmethod
    def timezone_required(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Capability operating window must include a timezone.")
        return value

    @model_validator(mode="after")
    def validate_window_and_batch(self):
        if self.operating_window_start >= self.operating_window_end:
            raise ValueError("Capability operating window start must be before end.")
        if self.minimum_batch is not None and self.minimum_batch > self.capacity:
            raise ValueError("Capability minimum_batch cannot exceed capacity.")
        return self


class CapabilityPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    accepted_inputs: list[dict[str, Any]] | None = Field(default=None, min_length=1)
    output_specifications: dict[str, Any] | None = Field(default=None, min_length=1)
    transformation_ids: list[str] | None = None
    capacity: Decimal | None = None
    unit: str | None = Field(default=None, min_length=1, max_length=80)
    unit_registry_version: str | None = Field(default=None, min_length=1, max_length=80)
    minimum_batch: Decimal | None = None
    location_id: str | None = Field(default=None, min_length=1, max_length=80)
    operating_window_start: datetime | None = None
    operating_window_end: datetime | None = None
    processing_cost: dict[str, Any] | None = None
    certifications: list[str] | None = None
    regulatory_constraints: dict[str, Any] | None = None
    status: str | None = Field(
        default=None,
        pattern="^(DRAFT|ACTIVE|SUSPENDED|EXPIRED|REVOKED)$",
    )
    provenance: dict[str, Any] | None = None

    @field_validator("capacity", "minimum_batch", mode="before")
    @classmethod
    def exact_non_negative_decimal(cls, value: object) -> Decimal | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("Canonical capability quantities must be decimal strings.")
        parsed = exact_decimal(value)
        if parsed < 0:
            raise ValueError("Capability quantity cannot be negative.")
        return parsed

    @field_validator("operating_window_start", "operating_window_end")
    @classmethod
    def timezone_required(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("Capability operating window must include a timezone.")
        return value
