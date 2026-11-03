"""Strict request contracts for the Execution API."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from crr.domain.execution_operations import ExecutionOperationType


class ExecutionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transaction_id: str = Field(min_length=1, max_length=80)


class ExecutionPlanInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation_type: ExecutionOperationType
    planned_for: datetime
    location_id: str | None = Field(default=None, max_length=80)
    quantity_value: Decimal | None = None
    quantity_unit: str | None = Field(default=None, max_length=80)
    unit_registry_version: str | None = Field(default=None, max_length=80)

    @field_validator("planned_for")
    @classmethod
    def planned_time_is_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Planned operation time must include a timezone.")
        return value

    @field_validator("quantity_value")
    @classmethod
    def planned_quantity_is_positive(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and value <= 0:
            raise ValueError("Planned quantity must be positive.")
        return value

    @field_validator("unit_registry_version")
    @classmethod
    def quantity_fields_are_complete(cls, value: str | None, info):
        quantity_value = info.data.get("quantity_value")
        quantity_unit = info.data.get("quantity_unit")
        if quantity_value is None and (value is not None or quantity_unit is not None):
            raise ValueError("Quantity value, unit and registry must be supplied together.")
        if quantity_value is not None and (not quantity_unit or not value):
            raise ValueError("Quantity value, unit and registry must be supplied together.")
        return value


class ExecutionReportInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    planned_operation_id: str = Field(min_length=1, max_length=80)
    occurred_at: datetime
    location_id: str | None = Field(default=None, max_length=80)
    quantity_value: Decimal | None = None
    quantity_unit: str | None = Field(default=None, max_length=80)
    unit_registry_version: str | None = Field(default=None, max_length=80)

    @field_validator("occurred_at")
    @classmethod
    def occurred_time_is_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Actual operation time must include a timezone.")
        return value

    @field_validator("quantity_value")
    @classmethod
    def actual_quantity_is_positive(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and value <= 0:
            raise ValueError("Actual quantity must be positive.")
        return value

    @field_validator("unit_registry_version")
    @classmethod
    def quantity_fields_are_complete(cls, value: str | None, info):
        quantity_value = info.data.get("quantity_value")
        quantity_unit = info.data.get("quantity_unit")
        if quantity_value is None and (value is not None or quantity_unit is not None):
            raise ValueError("Quantity value, unit and registry must be supplied together.")
        if quantity_value is not None and (not quantity_unit or not value):
            raise ValueError("Quantity value, unit and registry must be supplied together.")
        return value


class ExecutionExceptionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=80, pattern=r"^[A-Z0-9_]+$")
    reason: str = Field(min_length=1, max_length=2000)


class ExecutionExceptionResolutionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=1, max_length=2000)


class ExecutionCorrectionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    original_operation_id: str = Field(min_length=1, max_length=80)
    occurred_at: datetime
    reason: str = Field(min_length=1, max_length=2000)
    location_id: str | None = Field(default=None, max_length=80)
    quantity_value: Decimal | None = None
    quantity_unit: str | None = Field(default=None, max_length=80)
    unit_registry_version: str | None = Field(default=None, max_length=80)

    @field_validator("occurred_at")
    @classmethod
    def correction_time_is_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Correction time must include a timezone.")
        return value

    @field_validator("quantity_value")
    @classmethod
    def correction_quantity_is_positive(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and value <= 0:
            raise ValueError("Corrected quantity must be positive.")
        return value

    @field_validator("unit_registry_version")
    @classmethod
    def quantity_fields_are_complete(cls, value: str | None, info):
        quantity_value = info.data.get("quantity_value")
        quantity_unit = info.data.get("quantity_unit")
        if quantity_value is None and (value is not None or quantity_unit is not None):
            raise ValueError("Quantity value, unit and registry must be supplied together.")
        if quantity_value is not None and (not quantity_unit or not value):
            raise ValueError("Quantity value, unit and registry must be supplied together.")
        return value
