"""Pydantic contracts for computation-only routing requests."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RoutingComputeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_resource_state_id: str = Field(min_length=1, max_length=80)
    target_demand_id: str = Field(min_length=1, max_length=80)
    valid_until: datetime | None = None

    @field_validator("valid_until")
    @classmethod
    def timezone_required(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("valid_until must include a timezone.")
        return value
