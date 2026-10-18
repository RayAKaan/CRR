"""CRR domain types."""

from crr.domain.capability import Capability, CapabilityStatus, validate_capability_tenant
from crr.domain.demand import Demand, DemandStatus, validate_demand_tenant
from crr.domain.errors import DomainError, StaleVersionError, TenantBoundaryError
from crr.domain.quantity import Quantity, QuantityValidationError, UnitDefinition, UnitRegistry
from crr.domain.resource_state import (
    ResourceState,
    StateTransition,
    TransitionKind,
    transition_state,
)
from crr.domain.routing import RouteCandidate, RouteLeg, RouteStatus, Rejection, evaluate_direct_route
from crr.domain.transformation import (
    Transformation,
    TransformationStatus,
    validate_transformation_tenant,
)

__all__ = [
    "Capability",
    "CapabilityStatus",
    "Demand",
    "DomainError",
    "Quantity",
    "QuantityValidationError",
    "ResourceState",
    "Rejection",
    "RouteCandidate",
    "RouteLeg",
    "RouteStatus",
    "StaleVersionError",
    "StateTransition",
    "TenantBoundaryError",
    "Transformation",
    "TransformationStatus",
    "TransitionKind",
    "UnitDefinition",
    "UnitRegistry",
    "evaluate_direct_route",
    "transition_state",
    "validate_capability_tenant",
    "validate_demand_tenant",
    "validate_transformation_tenant",
]
