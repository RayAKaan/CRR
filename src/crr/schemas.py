"""Request models for the Phase 1 API."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from crr.domain.quantity import exact_decimal


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LocationCreate(InputModel):
    id: str | None = None
    name: str = Field(min_length=1, max_length=250)
    address: str | None = None
    latitude: str | None = None
    longitude: str | None = None
    jurisdiction: str | None = None
    provenance: dict[str, Any] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_coordinates(self):
        latitude = self.latitude
        longitude = self.longitude
        if (latitude is None) != (longitude is None):
            raise ValueError("Latitude and longitude must be supplied together.")
        if latitude is not None and longitude is not None:
            lat, lon = exact_decimal(latitude), exact_decimal(longitude)
            if not Decimal("-90") <= lat <= Decimal("90"):
                raise ValueError("Latitude is out of range.")
            if not Decimal("-180") <= lon <= Decimal("180"):
                raise ValueError("Longitude is out of range.")
        return self


class ResourceCreate(InputModel):
    id: str | None = None
    resource_type: str = Field(min_length=1, max_length=180)
    description: str | None = None
    provenance: dict[str, Any] = Field(min_length=1)


class QuantityInput(InputModel):
    value: Decimal
    unit: str = Field(min_length=1, max_length=80)
    unit_registry_version: str = Field(min_length=1, max_length=80)

    @field_validator("value", mode="before")
    @classmethod
    def require_decimal_string(cls, value: object) -> Decimal:
        if not isinstance(value, str):
            raise ValueError("Canonical quantity must be a decimal string.")
        parsed = exact_decimal(value)
        if parsed < 0:
            raise ValueError("Quantity cannot be negative.")
        return parsed


class ResourceStateCreate(InputModel):
    id: str | None = None
    resource_id: str
    state_type: str = Field(min_length=1, max_length=180)
    quantity: QuantityInput
    location_id: str
    effective_at: datetime
    provenance: dict[str, Any] = Field(min_length=1)
    quality: dict[str, Any] = Field(default_factory=dict)
    physical_properties: dict[str, Any] = Field(default_factory=dict)

    @field_validator("effective_at")
    @classmethod
    def require_timezone(cls, value):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Authoritative timestamps must include a timezone.")
        return value


class ResourceStateTransitionCreate(InputModel):
    kind: str = Field(pattern="^(PHYSICAL_CHANGE|CORRECTION)$")
    reason: str = Field(min_length=1)
    occurred_at: datetime
    state_type: str = Field(min_length=1, max_length=180)
    quantity: QuantityInput
    location_id: str
    provenance: dict[str, Any] = Field(min_length=1)
    quality: dict[str, Any] = Field(default_factory=dict)
    physical_properties: dict[str, Any] = Field(default_factory=dict)

    @field_validator("occurred_at")
    @classmethod
    def require_timezone(cls, value):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Authoritative timestamps must include a timezone.")
        return value


class ActorCreate(InputModel):
    id: str | None = None
    name: str = Field(min_length=1, max_length=250)
    role: str = Field(
        pattern="^(ORG_ADMIN|RESOURCE_MANAGER|OPERATOR|TRANSACTION_MANAGER|VERIFIER|AUDITOR|DEVELOPER|READ_ONLY)$"
    )
