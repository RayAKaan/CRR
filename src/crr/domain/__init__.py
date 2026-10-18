"""CRR domain types."""

from crr.domain.capability import Capability, CapabilityStatus, validate_capability_tenant
from crr.domain.demand import Demand, DemandStatus, validate_demand_tenant
from crr.domain.economics import (
    EconomicComponent,
    EconomicComponentKind,
    EconomicModel,
    EconomicModelStatus,
    EconomicPerspective,
    EconomicPerspectiveResult,
    EconomicResult,
    Money,
    RoundingPolicy,
    evaluate_economic_model,
)
from crr.domain.errors import DomainError, StaleVersionError, TenantBoundaryError
from crr.domain.logistics import (
    LogisticsEvaluation,
    LogisticsRejection,
    TransportMode,
    evaluate_logistics_leg,
)
from crr.domain.quantity import Quantity, QuantityValidationError, UnitDefinition, UnitRegistry
from crr.domain.regulatory import evaluate_regulatory_eligibility
from crr.domain.resource_state import (
    ResourceState,
    StateTransition,
    TransitionKind,
    transition_state,
)
from crr.domain.routing import (
    Rejection,
    RouteCandidate,
    RouteLeg,
    RouteStatus,
    evaluate_direct_route,
    evaluate_transformation_route,
)
from crr.domain.transformation import (
    Transformation,
    TransformationStatus,
    validate_transformation_tenant,
)

__all__ = [
    "Capability",
    "CapabilityStatus",
    "Demand",
    "DemandStatus",
    "DomainError",
    "EconomicComponent",
    "EconomicComponentKind",
    "EconomicModel",
    "EconomicModelStatus",
    "EconomicPerspective",
    "EconomicPerspectiveResult",
    "EconomicResult",
    "LogisticsEvaluation",
    "LogisticsRejection",
    "Money",
    "Quantity",
    "QuantityValidationError",
    "Rejection",
    "ResourceState",
    "RouteCandidate",
    "RouteLeg",
    "RouteStatus",
    "RoundingPolicy",
    "StaleVersionError",
    "StateTransition",
    "TenantBoundaryError",
    "Transformation",
    "TransformationStatus",
    "TransportMode",
    "TransitionKind",
    "UnitDefinition",
    "UnitRegistry",
    "evaluate_direct_route",
    "evaluate_economic_model",
    "evaluate_logistics_leg",
    "evaluate_regulatory_eligibility",
    "evaluate_transformation_route",
    "transition_state",
    "validate_capability_tenant",
    "validate_demand_tenant",
    "validate_transformation_tenant",
]
