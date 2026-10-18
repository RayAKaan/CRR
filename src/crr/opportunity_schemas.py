"""Pydantic schemas for canonical Opportunity conversion."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from crr.domain.quantity import exact_decimal


class RouteLegReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: str = Field(min_length=1, max_length=32)
    object_id: str = Field(min_length=1, max_length=120)
    input_state_type: str = Field(min_length=1, max_length=180)
    output_state_type: str = Field(min_length=1, max_length=180)


class RouteRejectionReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=80)
    object_id: str = Field(min_length=1, max_length=120)
    message: str = Field(min_length=1, max_length=500)


class RouteCandidateReference(BaseModel):
    """Non-authoritative route provenance returned by the routing computation."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=120)
    organization_id: str = Field(min_length=1, max_length=80)
    source_resource_state_id: str = Field(min_length=1, max_length=80)
    target_demand_id: str = Field(min_length=1, max_length=80)
    legs: list[RouteLegReference] = Field(min_length=1)
    status: str = Field(pattern="^FEASIBLE$")
    rejections: list[RouteRejectionReference] = Field(default_factory=list)
    source_version: int = Field(ge=1)
    target_version: int = Field(ge=1)
    evaluated_at: datetime
    provenance: dict[str, Any] = Field(min_length=1)

    @field_validator("evaluated_at")
    @classmethod
    def timezone_required(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Route evaluation timestamp must include a timezone.")
        return value


class OpportunityInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str | None = Field(default=None, min_length=1, max_length=80)
    route_candidate: RouteCandidateReference
    candidate_set_fingerprint: str = Field(min_length=64, max_length=64, pattern="^[0-9a-f]{64}$")
    source_resource_state_id: str
    target_demand_id: str
    valid_from: datetime
    valid_until: datetime
    quantity_value: Decimal
    quantity_unit: str = Field(min_length=1, max_length=80)
    unit_registry_version: str = Field(min_length=1, max_length=80)
    economic_model_id: str | None = None
    economic_model_version: int | None = Field(default=None, ge=1)
    commercial_perspective: str | None = Field(default=None, min_length=1, max_length=64)
    currency: str | None = Field(default=None, min_length=3, max_length=3, pattern="^[A-Z]{3}$")
    advisory_provenance: dict[str, Any] | None = None
    provenance: dict[str, Any] = Field(min_length=1)
    status: str = Field(default="DRAFT", pattern="^(DRAFT|OPEN)$")

    @field_validator("quantity_value", mode="before")
    @classmethod
    def exact_quantity(cls, value: object) -> Decimal:
        if not isinstance(value, str):
            raise ValueError("Opportunity quantity must be a decimal string.")
        parsed = exact_decimal(value)
        if parsed < 0:
            raise ValueError("Opportunity quantity cannot be negative.")
        return parsed

    @field_validator("valid_from", "valid_until")
    @classmethod
    def timezone_required(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Opportunity validity timestamps must include a timezone.")
        return value

    @model_validator(mode="after")
    def validate_consistency(self):
        if self.valid_until <= self.valid_from:
            raise ValueError("Opportunity valid_until must be after valid_from.")
        if self.source_resource_state_id != self.route_candidate.source_resource_state_id:
            raise ValueError("Opportunity source ResourceState must match the route candidate.")
        if self.target_demand_id != self.route_candidate.target_demand_id:
            raise ValueError("Opportunity target Demand must match the route candidate.")
        if self.economic_model_id is None and self.economic_model_version is not None:
            raise ValueError("Economic model version requires an economic model ID.")
        return self


class OpportunityStatusInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = Field(pattern="^(OPEN|EXPIRED|CANCELLED|CLOSED)$")
