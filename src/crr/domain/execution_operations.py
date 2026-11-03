"""Typed, append-only operational history and exception contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from crr.domain.errors import DomainError
from crr.domain.execution import Execution
from crr.domain.quantity import Quantity


class ExecutionOperationType(StrEnum):
    PICKUP = "PICKUP"
    SHIPMENT = "SHIPMENT"
    RECEIPT = "RECEIPT"
    PROCESSING = "PROCESSING"
    OUTPUT = "OUTPUT"
    DELIVERY = "DELIVERY"
    ACCEPTANCE = "ACCEPTANCE"


class OperationMode(StrEnum):
    PLANNED = "PLANNED"
    REPORTED = "REPORTED"


class ExecutionExceptionStatus(StrEnum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"


@dataclass(frozen=True, slots=True)
class ExecutionOperation:
    """An immutable planned milestone or actor-reported operational fact."""

    id: str
    organization_id: str
    execution_id: str
    operation_type: ExecutionOperationType
    mode: OperationMode
    sequence: int
    actor_id: str
    created_at: datetime
    planned_for: datetime | None = None
    occurred_at: datetime | None = None
    location_id: str | None = None
    quantity: Quantity | None = None
    planned_operation_id: str | None = None
    supersedes_operation_id: str | None = None
    correction_reason: str | None = None
    provenance: dict[str, str] | None = None

    def __post_init__(self) -> None:
        if not all((self.id, self.organization_id, self.execution_id, self.actor_id)):
            raise DomainError("Operation identity and actor attribution are required.")
        if self.sequence < 1:
            raise DomainError("Operation sequence must be positive.")
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise DomainError("Operation creation time must be timezone-aware.")
        if self.mode is OperationMode.PLANNED:
            if self.planned_for is None or self.occurred_at is not None:
                raise DomainError("Planned operations require planned_for and forbid occurred_at.")
        else:
            if self.occurred_at is None:
                raise DomainError("Reported operations require an actual occurred_at timestamp.")
            if self.occurred_at.tzinfo is None or self.occurred_at.utcoffset() is None:
                raise DomainError("Reported operation time must be timezone-aware.")
            if self.planned_operation_id is None:
                raise DomainError("Reported operations must reference a planned operation.")
        for value in (self.planned_for,):
            if value is not None and (value.tzinfo is None or value.utcoffset() is None):
                raise DomainError("Planned operation time must be timezone-aware.")
        if self.quantity is not None and self.quantity.value <= Decimal("0"):
            raise DomainError("Reported operation quantity must be positive.")
        if self.supersedes_operation_id is not None:
            if self.mode is not OperationMode.REPORTED:
                raise DomainError("Corrections must be reported operational records.")
            if not self.correction_reason or not self.correction_reason.strip():
                raise DomainError("Corrections require an explicit reason.")
        if self.provenance is None or not self.provenance:
            raise DomainError("Operation provenance is required.")

    def validate_against_execution(self, execution: Execution) -> None:
        if self.organization_id != execution.organization_id:
            raise DomainError("Operation and Execution tenant do not match.")
        if self.execution_id != execution.id:
            raise DomainError("Operation belongs to another Execution.")
        if self.quantity is not None and (
            self.quantity.unit != execution.quantity.unit
            or self.quantity.unit_registry_version != execution.quantity.unit_registry_version
        ):
            raise DomainError("Operation quantity must use the Execution's canonical unit.")


@dataclass(frozen=True, slots=True)
class ExecutionException:
    """Append-only operational exception raised by an attributed actor."""

    id: str
    organization_id: str
    execution_id: str
    code: str
    reason: str
    actor_id: str
    occurred_at: datetime
    provenance: dict[str, str]

    def __post_init__(self) -> None:
        if not all((self.id, self.organization_id, self.execution_id, self.code, self.actor_id)):
            raise DomainError("Execution exception identity and actor are required.")
        if not self.reason.strip() or not self.provenance:
            raise DomainError("Execution exception reason and provenance are required.")
        if self.occurred_at.tzinfo is None or self.occurred_at.utcoffset() is None:
            raise DomainError("Execution exception time must be timezone-aware.")


@dataclass(frozen=True, slots=True)
class ExecutionExceptionResolution:
    """Append-only resolution statement; the original exception remains unchanged."""

    id: str
    organization_id: str
    execution_id: str
    exception_id: str
    actor_id: str
    reason: str
    resolved_at: datetime
    provenance: dict[str, str]

    def __post_init__(self) -> None:
        if not all(
            (self.id, self.organization_id, self.execution_id, self.exception_id, self.actor_id)
        ):
            raise DomainError("Exception resolution identity and actor are required.")
        if not self.reason.strip() or not self.provenance:
            raise DomainError("Exception resolution reason and provenance are required.")
        if self.resolved_at.tzinfo is None or self.resolved_at.utcoffset() is None:
            raise DomainError("Exception resolution time must be timezone-aware.")


def validate_reported_operation(
    *,
    execution: Execution,
    planned_operation: ExecutionOperation,
    reported_operation: ExecutionOperation,
    prior_reported_operations: tuple[ExecutionOperation, ...] = (),
    authorization_scopes: frozenset[str],
) -> None:
    """Enforce plan linkage, explicit human authorization, chronology and operation dependencies."""
    if "execution:operate" not in authorization_scopes and "admin:*" not in authorization_scopes:
        raise DomainError("An explicit execution:operate authorization is required.")
    planned_operation.validate_against_execution(execution)
    reported_operation.validate_against_execution(execution)
    if planned_operation.mode is not OperationMode.PLANNED:
        raise DomainError("Actual reports must reference a planned operation.")
    if reported_operation.mode is not OperationMode.REPORTED:
        raise DomainError("Only a reported operation can be recorded as actual.")
    if reported_operation.planned_operation_id != planned_operation.id:
        raise DomainError("Reported operation does not reference the supplied plan.")
    if reported_operation.operation_type is not planned_operation.operation_type:
        raise DomainError("Reported operation type must match its planned milestone.")
    if reported_operation.occurred_at is None:
        raise DomainError("Reported operation timestamp is required.")
    if reported_operation.occurred_at < planned_operation.created_at:
        raise DomainError("Reported operation cannot precede its plan.")
    if any(item.sequence == reported_operation.sequence for item in prior_reported_operations):
        raise DomainError("Execution operation sequence has already been reported.")
    if any(item.planned_operation_id == planned_operation.id for item in prior_reported_operations):
        raise DomainError("The planned milestone has already been reported.")
    if (
        reported_operation.quantity is not None
        and reported_operation.quantity.value > execution.quantity.value
    ):
        raise DomainError("A reported quantity cannot exceed the Transaction quantity.")
    reported_types = {item.operation_type for item in prior_reported_operations}
    dependencies: dict[ExecutionOperationType, frozenset[ExecutionOperationType]] = {
        ExecutionOperationType.PICKUP: frozenset(),
        ExecutionOperationType.SHIPMENT: frozenset({ExecutionOperationType.PICKUP}),
        ExecutionOperationType.RECEIPT: frozenset({ExecutionOperationType.SHIPMENT}),
        ExecutionOperationType.PROCESSING: frozenset({ExecutionOperationType.RECEIPT}),
        ExecutionOperationType.OUTPUT: frozenset({ExecutionOperationType.PROCESSING}),
        ExecutionOperationType.DELIVERY: frozenset(
            {
                ExecutionOperationType.PICKUP,
                ExecutionOperationType.SHIPMENT,
                ExecutionOperationType.RECEIPT,
                ExecutionOperationType.OUTPUT,
            }
        ),
        ExecutionOperationType.ACCEPTANCE: frozenset(
            {
                ExecutionOperationType.RECEIPT,
                ExecutionOperationType.DELIVERY,
            }
        ),
    }
    required = dependencies[reported_operation.operation_type]
    if required and not (required & reported_types):
        raise DomainError(
            f"{reported_operation.operation_type.value} has no eligible reported predecessor."
        )
    predecessors = [
        item
        for item in prior_reported_operations
        if item.operation_type in required and item.occurred_at is not None
    ]
    if predecessors and reported_operation.occurred_at < max(
        item.occurred_at for item in predecessors if item.occurred_at is not None
    ):
        raise DomainError("Reported operation time precedes its required predecessor.")


def validate_correction(
    *,
    original: ExecutionOperation,
    correction: ExecutionOperation,
    authorization_scopes: frozenset[str],
) -> None:
    """Require a separately authorized compensating record; never rewrite original history."""
    if "execution:correct" not in authorization_scopes and "admin:*" not in authorization_scopes:
        raise DomainError("An explicit execution:correct authorization is required.")
    if original.mode is not OperationMode.REPORTED:
        raise DomainError("Only a reported operation can be corrected.")
    if correction.supersedes_operation_id != original.id:
        raise DomainError("Correction must reference the exact operation it supersedes.")
    if correction.operation_type is not original.operation_type:
        raise DomainError("Correction must preserve the original operation type.")
    if correction.mode is not OperationMode.REPORTED or not correction.correction_reason:
        raise DomainError("Correction must be a reported record with a reason.")
    if correction.organization_id != original.organization_id:
        raise DomainError("Correction cannot cross tenant boundaries.")
    if correction.execution_id != original.execution_id:
        raise DomainError("Correction must belong to the original Execution.")
    if correction.created_at <= original.created_at:
        raise DomainError("Correction must be recorded after the original operation.")
