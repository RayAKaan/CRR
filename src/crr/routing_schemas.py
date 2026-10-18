"""Pydantic contracts for computation-only routing requests."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OptimizationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    objective: str = Field(min_length=1, max_length=40)
    policy_id: str = Field(min_length=1, max_length=80)
    policy_version: int = Field(ge=1)
    calculation_version: str = Field(min_length=1, max_length=80)
    metric: str | None = Field(default=None, max_length=80)
    weights: dict[str, Decimal] = Field(default_factory=dict, max_length=20)
    allow_negative: bool = False

    @field_validator("weights")
    @classmethod
    def exact_weights(cls, value: dict[str, Decimal]) -> dict[str, Decimal]:
        for name, weight in value.items():
            if not name.strip():
                raise ValueError("Optimization weight names must not be empty.")
            if not weight.is_finite():
                raise ValueError("Optimization weights must be finite decimals.")
        return value


class RoutingComputeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_resource_state_id: str = Field(min_length=1, max_length=80)
    target_demand_id: str = Field(min_length=1, max_length=80)
    valid_until: datetime | None = None
    optimization: OptimizationInput | None = None

    @field_validator("valid_until")
    @classmethod
    def timezone_required(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("valid_until must include a timezone.")
        return value
