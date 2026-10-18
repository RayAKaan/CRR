"""Exact, deterministic economic model contracts and evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import (
    ROUND_CEILING,
    ROUND_DOWN,
    ROUND_FLOOR,
    ROUND_HALF_EVEN,
    ROUND_HALF_UP,
    ROUND_UP,
    Decimal,
)
from enum import StrEnum
from typing import Any

from crr.domain.errors import DomainError, TenantBoundaryError


class EconomicModelStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"


class EconomicPerspective(StrEnum):
    SUPPLIER = "SUPPLIER"
    PROCESSOR = "PROCESSOR"
    BUYER = "BUYER"
    LOGISTICS = "LOGISTICS"
    NETWORK = "NETWORK"


class EconomicComponentKind(StrEnum):
    VALUE = "VALUE"
    COST = "COST"


_ROUNDING = {
    "HALF_EVEN": ROUND_HALF_EVEN,
    "HALF_UP": ROUND_HALF_UP,
    "DOWN": ROUND_DOWN,
    "UP": ROUND_UP,
    "FLOOR": ROUND_FLOOR,
    "CEILING": ROUND_CEILING,
}


@dataclass(frozen=True, slots=True)
class Money:
    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        if isinstance(self.amount, bool) or isinstance(self.amount, float):
            raise DomainError("Money must use an exact decimal representation.")
        if not isinstance(self.amount, Decimal) or not self.amount.is_finite():
            raise DomainError("Money amount must be a finite Decimal.")
        if (
            len(self.currency) != 3
            or not self.currency.isalpha()
            or self.currency != self.currency.upper()
        ):
            raise DomainError("Currency must be a three-letter uppercase code.")

    def add(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise DomainError("Monetary values with different currencies cannot be combined.")
        return Money(self.amount + other.amount, self.currency)


@dataclass(frozen=True, slots=True)
class EconomicComponent:
    perspective: EconomicPerspective
    kind: EconomicComponentKind
    label: str
    amount: Money
    source: str

    def __post_init__(self) -> None:
        if not self.label.strip():
            raise DomainError("Economic component label is required.")
        if not self.source.strip():
            raise DomainError("Economic component source is required.")
        if self.amount.amount < 0:
            raise DomainError(
                "Economic component amounts cannot be negative; "
                "represent negative net outcomes through costs exceeding value."
            )


@dataclass(frozen=True, slots=True)
class RoundingPolicy:
    mode: str
    scale: int

    def __post_init__(self) -> None:
        if self.mode not in _ROUNDING:
            raise DomainError(f"Unsupported rounding mode: {self.mode}.")
        if self.scale < 0 or self.scale > 18:
            raise DomainError("Rounding scale must be between 0 and 18.")

    def apply(self, value: Decimal) -> Decimal:
        quantum = Decimal(1).scaleb(-self.scale)
        return value.quantize(quantum, rounding=_ROUNDING[self.mode])


@dataclass(frozen=True, slots=True)
class EconomicModel:
    id: str
    model_key: str
    organization_id: str
    version: int
    currency: str
    valid_from: datetime
    valid_until: datetime | None
    calculation_version: str
    rounding: RoundingPolicy
    components: tuple[EconomicComponent, ...]
    status: EconomicModelStatus
    created_by: str
    provenance: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        if not self.id or not self.model_key or not self.organization_id or not self.created_by:
            raise DomainError("Economic model identity, organization, and creator are required.")
        if self.version < 1:
            raise DomainError("Economic model version must be positive.")
        if (
            len(self.currency) != 3
            or not self.currency.isalpha()
            or self.currency != self.currency.upper()
        ):
            raise DomainError("Currency must be a three-letter uppercase code.")
        if not self.calculation_version.strip():
            raise DomainError("Calculation version is required.")
        if not self.components:
            raise DomainError("Economic model requires at least one component.")
        if any(component.amount.currency != self.currency for component in self.components):
            raise DomainError("Every economic component must use the model currency.")
        for timestamp in (self.valid_from, self.created_at, self.updated_at):
            if timestamp.tzinfo is None or timestamp.utcoffset() is None:
                raise DomainError("Economic model timestamps must include a timezone.")
        if self.valid_until is not None:
            if self.valid_until.tzinfo is None or self.valid_until.utcoffset() is None:
                raise DomainError("Economic model validity timestamps must include a timezone.")
            if self.valid_until <= self.valid_from:
                raise DomainError("Economic model valid_until must be after valid_from.")
        object.__setattr__(self, "valid_from", self.valid_from.astimezone(UTC))
        if self.valid_until is not None:
            object.__setattr__(self, "valid_until", self.valid_until.astimezone(UTC))
        object.__setattr__(self, "created_at", self.created_at.astimezone(UTC))
        object.__setattr__(self, "updated_at", self.updated_at.astimezone(UTC))

    def validate_tenant(self, organization_id: str) -> None:
        if self.organization_id != organization_id:
            raise TenantBoundaryError("Economic model belongs to another organization.")

    def is_valid_at(self, evaluated_at: datetime) -> bool:
        if evaluated_at.tzinfo is None or evaluated_at.utcoffset() is None:
            raise DomainError("Economic evaluation time must include a timezone.")
        timestamp = evaluated_at.astimezone(UTC)
        return (
            self.status is EconomicModelStatus.ACTIVE
            and timestamp >= self.valid_from
            and (self.valid_until is None or timestamp < self.valid_until)
        )


@dataclass(frozen=True, slots=True)
class EconomicPerspectiveResult:
    perspective: EconomicPerspective
    value: Money
    cost: Money
    net: Money


@dataclass(frozen=True, slots=True)
class EconomicResult:
    model_id: str
    model_version: int
    organization_id: str
    calculated_at: datetime
    currency: str
    calculation_version: str
    perspectives: tuple[EconomicPerspectiveResult, ...]
    provenance: dict[str, Any]


def evaluate_economic_model(
    *,
    model: EconomicModel,
    organization_id: str,
    evaluated_at: datetime,
    context: dict[str, Any] | None = None,
) -> EconomicResult:
    """Evaluate a model without mutating canonical state or performing I/O."""
    model.validate_tenant(organization_id)
    if evaluated_at.tzinfo is None or evaluated_at.utcoffset() is None:
        raise DomainError("Economic evaluation time must include a timezone.")
    timestamp = evaluated_at.astimezone(UTC)
    if not model.is_valid_at(timestamp):
        raise DomainError("Economic model is not active within its validity window.")

    values: dict[EconomicPerspective, Decimal] = {
        item: Decimal("0") for item in EconomicPerspective
    }
    costs: dict[EconomicPerspective, Decimal] = {item: Decimal("0") for item in EconomicPerspective}
    for component in model.components:
        if component.amount.currency != model.currency:
            raise DomainError("Economic component currency does not match model currency.")
        amount = model.rounding.apply(component.amount.amount)
        if component.kind is EconomicComponentKind.VALUE:
            values[component.perspective] += amount
        else:
            costs[component.perspective] += amount

    perspectives: list[EconomicPerspectiveResult] = []
    for perspective in EconomicPerspective:
        value = model.rounding.apply(values[perspective])
        cost = model.rounding.apply(costs[perspective])
        net = model.rounding.apply(value - cost)
        if value or cost:
            perspectives.append(
                EconomicPerspectiveResult(
                    perspective=perspective,
                    value=Money(value, model.currency),
                    cost=Money(cost, model.currency),
                    net=Money(net, model.currency),
                )
            )

    return EconomicResult(
        model_id=model.id,
        model_version=model.version,
        organization_id=organization_id,
        calculated_at=timestamp,
        currency=model.currency,
        calculation_version=model.calculation_version,
        perspectives=tuple(perspectives),
        provenance={
            "source": "CRR_DETERMINISTIC_ECONOMICS",
            "economic_model_id": model.id,
            "economic_model_version": model.version,
            "context": context or {},
        },
    )
