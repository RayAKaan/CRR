"""Pydantic request models for Transformation."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from crr.domain.quantity import exact_decimal


class TransformationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    input_specifications: list[dict[str, Any]] = Field(min_length=1)
    output_specifications: list[dict[str, Any]] = Field(min_length=1)
    yield_min: Decimal
    yield_target: Decimal
    yield_max: Decimal
    loss_residuals: list[dict[str, Any]] = Field(default_factory=list)
    duration_seconds: int = Field(gt=0)
    capacity: Decimal
    unit: str = Field(min_length=1, max_length=80)
    unit_registry_version: str = Field(min_length=1, max_length=80)
    cost_metadata: dict[str, Any] = Field(default_factory=dict)
    quality_effects: dict[str, Any] = Field(default_factory=dict)
    regulatory_requirements: dict[str, Any] = Field(default_factory=dict)
    eligible_capability_ids: list[str] = Field(default_factory=list)
    eligible_location_ids: list[str] = Field(default_factory=list)
    status: str = Field(default="DRAFT", pattern="^(DRAFT|ACTIVE)$")
    provenance: dict[str, Any] = Field(min_length=1)

    @field_validator("yield_min", "yield_target", "yield_max", "capacity", mode="before")
    @classmethod
    def exact_decimal_string(cls, value: object) -> Decimal:
        if not isinstance(value, str):
            raise ValueError("Canonical transformation quantities must be decimal strings.")
        return exact_decimal(value)

    @model_validator(mode="after")
    def validate_values(self) -> TransformationInput:
        if any(value < 0 or value > 1 for value in self.yields):
            raise ValueError("Transformation yields must be between 0 and 1.")
        if not self.yield_min <= self.yield_target <= self.yield_max:
            raise ValueError("Transformation yield bounds must satisfy min <= target <= max.")
        if self.capacity < 0:
            raise ValueError("Transformation capacity cannot be negative.")
        return self

    @property
    def yields(self) -> tuple[Decimal, Decimal, Decimal]:
        return self.yield_min, self.yield_target, self.yield_max


class TransformationPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input_specifications: list[dict[str, Any]] | None = Field(default=None, min_length=1)
    output_specifications: list[dict[str, Any]] | None = Field(default=None, min_length=1)
    yield_min: Decimal | None = None
    yield_target: Decimal | None = None
    yield_max: Decimal | None = None
    loss_residuals: list[dict[str, Any]] | None = None
    duration_seconds: int | None = Field(default=None, gt=0)
    capacity: Decimal | None = None
    unit: str | None = Field(default=None, min_length=1, max_length=80)
    unit_registry_version: str | None = Field(default=None, min_length=1, max_length=80)
    cost_metadata: dict[str, Any] | None = None
    quality_effects: dict[str, Any] | None = None
    regulatory_requirements: dict[str, Any] | None = None
    eligible_capability_ids: list[str] | None = None
    eligible_location_ids: list[str] | None = None
    status: str | None = Field(default=None, pattern="^(DRAFT|ACTIVE|SUSPENDED|EXPIRED|REVOKED)$")
    provenance: dict[str, Any] | None = None

    @field_validator("yield_min", "yield_target", "yield_max", "capacity", mode="before")
    @classmethod
    def exact_decimal_string(cls, value: object) -> Decimal | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("Canonical transformation quantities must be decimal strings.")
        return exact_decimal(value)
