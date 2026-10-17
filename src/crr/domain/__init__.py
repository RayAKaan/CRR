"""CRR domain types."""

from crr.domain.demand import Demand, DemandStatus, validate_demand_tenant
from crr.domain.errors import DomainError, StaleVersionError, TenantBoundaryError
from crr.domain.quantity import Quantity, QuantityValidationError, UnitDefinition, UnitRegistry
from crr.domain.resource_state import (
    ResourceState,
    StateTransition,
    TransitionKind,
    transition_state,
)

__all__ = [
    "Demand",
    "DemandStatus",
    "DomainError",
    "Quantity",
    "QuantityValidationError",
    "ResourceState",
    "StaleVersionError",
    "StateTransition",
    "TenantBoundaryError",
    "TransitionKind",
    "UnitDefinition",
    "UnitRegistry",
    "transition_state",
    "validate_demand_tenant",
]
