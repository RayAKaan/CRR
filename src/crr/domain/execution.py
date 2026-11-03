"""Canonical Execution aggregate for operational work under a Transaction.

Execution records operational intent and status only. It does not prove that
pickup, shipment, receipt, processing, delivery, payment, or custody transfer occurred.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from crr.domain.errors import DomainError, TenantBoundaryError
from crr.domain.quantity import Quantity
from crr.domain.transaction import Transaction, TransactionStatus


class ExecutionStatus(StrEnum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    EXCEPTION = "EXCEPTION"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, slots=True)
class Execution:
    """Tenant-scoped operational aggregate anchored to an immutable Transaction snapshot."""

    id: str
    organization_id: str
    transaction_id: str
    agreement_id: str
    resource_id: str
    resource_state_id: str
    resource_version: int
    route_candidate_id: str
    quantity: Quantity
    scheduled_for: datetime
    status: ExecutionStatus
    version: int
    created_by: str
    created_at: datetime
    updated_at: datetime
    provenance: dict[str, str]

    def __post_init__(self) -> None:
        required = (
            self.id,
            self.organization_id,
            self.transaction_id,
            self.agreement_id,
            self.resource_id,
            self.resource_state_id,
            self.route_candidate_id,
            self.created_by,
        )
        if any(not value for value in required):
            raise DomainError("Execution identity, source references, and actor are required.")
        if self.resource_version < 1 or self.version < 1:
            raise DomainError("Execution source and aggregate versions must be positive.")
        if self.quantity.value <= Decimal("0"):
            raise DomainError("Execution quantity must be greater than zero.")
        for value in (self.scheduled_for, self.created_at, self.updated_at):
            if value.tzinfo is None or value.utcoffset() is None:
                raise DomainError("Execution timestamps must be timezone-aware.")
        if self.updated_at < self.created_at:
            raise DomainError("Execution update time cannot precede creation.")
        if not self.provenance:
            raise DomainError("Execution provenance is required.")

    @classmethod
    def from_transaction(
        cls,
        transaction: Transaction,
        *,
        execution_id: str,
        actor_id: str,
        at: datetime,
    ) -> Execution:
        """Create a planned operational record without mutating commercial or physical state."""
        if transaction.status is not TransactionStatus.SCHEDULED:
            raise DomainError("Execution requires a SCHEDULED Transaction.")
        if at.tzinfo is None or at.utcoffset() is None:
            raise DomainError("Execution creation time must be timezone-aware.")
        if not actor_id:
            raise DomainError("Execution creation requires an attributed actor.")
        if transaction.scheduled_for is None:
            raise DomainError("Execution requires the Transaction's accepted schedule.")
        return cls(
            id=execution_id,
            organization_id=transaction.organization_id,
            transaction_id=transaction.id,
            agreement_id=transaction.agreement_id,
            resource_id=transaction.resource_id,
            resource_state_id=transaction.resource_state_id,
            resource_version=transaction.resource_version,
            route_candidate_id=transaction.route_candidate_id,
            quantity=transaction.quantity,
            scheduled_for=transaction.scheduled_for,
            status=ExecutionStatus.PLANNED,
            version=1,
            created_by=actor_id,
            created_at=at,
            updated_at=at,
            provenance={
                "source_type": "TRANSACTION",
                "source_transaction_id": transaction.id,
                "source_transaction_version": str(transaction.version),
                "source_resource_state_id": transaction.resource_state_id,
                "source_resource_version": str(transaction.resource_version),
            },
        )

    def close(
        self,
        *,
        actor_id: str,
        at: datetime,
        reason: str,
        has_unresolved_exceptions: bool,
        has_reported_operations: bool,
    ) -> Execution:
        """Close the operational record; this is not verification or acceptance."""
        self._validate_actor_time(actor_id, at, reason)
        if self.status is not ExecutionStatus.IN_PROGRESS:
            raise DomainError("Only an IN_PROGRESS Execution can be closed.")
        if has_unresolved_exceptions:
            raise DomainError("Execution cannot close while exceptions remain unresolved.")
        if not has_reported_operations:
            raise DomainError("Execution cannot close without a reported operational event.")
        return replace(
            self,
            status=ExecutionStatus.CLOSED,
            version=self.version + 1,
            updated_at=at,
            provenance={
                **self.provenance,
                "operationally_closed_by": actor_id,
                "operationally_closed_at": at.isoformat(),
                "operational_closure_reason": reason.strip(),
                "verification_status": "NOT_VERIFIED",
            },
        )

    def cancel(
        self,
        *,
        actor_id: str,
        at: datetime,
        reason: str,
        has_reported_operations: bool,
        has_unresolved_exceptions: bool,
    ) -> Execution:
        """Cancel only before any actual operation has been reported."""
        self._validate_actor_time(actor_id, at, reason)
        if self.status is not ExecutionStatus.PLANNED:
            raise DomainError("Only a PLANNED Execution can be cancelled.")
        if has_reported_operations:
            raise DomainError(
                "Execution cannot be cancelled after an actual operation is reported."
            )
        if has_unresolved_exceptions:
            raise DomainError("Execution cannot be cancelled while exceptions remain unresolved.")
        return replace(
            self,
            status=ExecutionStatus.CANCELLED,
            version=self.version + 1,
            updated_at=at,
            provenance={
                **self.provenance,
                "cancelled_by": actor_id,
                "cancelled_at": at.isoformat(),
                "cancellation_reason": reason.strip(),
            },
        )

    @staticmethod
    def _validate_actor_time(actor_id: str, at: datetime, reason: str) -> None:
        if not actor_id:
            raise DomainError("Execution lifecycle changes require an attributed actor.")
        if at.tzinfo is None or at.utcoffset() is None:
            raise DomainError("Execution lifecycle timestamp must be timezone-aware.")
        if not reason.strip():
            raise DomainError("Execution lifecycle changes require a reason.")

    def validate_tenant(self, organization_id: str) -> None:
        if self.organization_id != organization_id:
            raise TenantBoundaryError("Execution belongs to another organization.")
