"""Pydantic contracts for the Phase 3A deterministic routing boundary."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RoutingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_resource_state_id: str = Field(min_length=1, max_length=80)
    target_demand_id: str = Field(min_length=1, max_length=80)
    valid_until: datetime | None = None
    constraints: dict[str, Any] = Field(default_factory=dict)

    @field_validator("valid_until")
    @classmethod
    def timezone_required(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("valid_until must include a timezone.")
        return value


class RouteLegResponse(BaseModel):
    kind: str
    object_id: str
    input_state_type: str
    output_state_type: str


class RouteRejectionResponse(BaseModel):
    code: str
    object_id: str
    message: str


class RouteCandidateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    organization_id: str
    source_resource_state_id: str
    target_demand_id: str
    legs: list[RouteLegResponse]
    status: str
    rejections: list[RouteRejectionResponse]
    source_version: int
    target_version: int
    evaluated_at: datetime
    provenance: dict[str, Any]
