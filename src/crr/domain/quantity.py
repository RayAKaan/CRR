"""Exact quantity values and versioned unit conversion rules."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from types import MappingProxyType

from crr.domain.errors import DomainError


class QuantityValidationError(DomainError):
    """Canonical quantity or unit validation failed."""


def exact_decimal(value: str | Decimal) -> Decimal:
    """Parse exact decimal input; binary floats are never canonical."""
    if isinstance(value, bool) or isinstance(value, float):
        raise QuantityValidationError(
            "Binary floating-point and booleans are not valid quantities."
        )
    if not isinstance(value, (str, Decimal)):
        raise QuantityValidationError("Quantity must be represented by a decimal string.")
    try:
        result = value if isinstance(value, Decimal) else Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise QuantityValidationError("Quantity is not a valid decimal.") from exc
    if not result.is_finite():
        raise QuantityValidationError("Quantity must be finite.")
    return result


def _fraction_to_decimal(value: Fraction) -> Decimal:
    denominator = value.denominator
    twos = fives = 0
    while denominator % 2 == 0:
        denominator //= 2
        twos += 1
    while denominator % 5 == 0:
        denominator //= 5
        fives += 1
    if denominator != 1:
        raise QuantityValidationError(
            "Conversion is non-terminating; an explicit versioned rounding policy is required."
        )
    scale = max(twos, fives)
    scaled = value.numerator * (2 ** (scale - twos)) * (5 ** (scale - fives))
    return Decimal(scaled).scaleb(-scale)


@dataclass(frozen=True, slots=True)
class Quantity:
    value: Decimal
    unit: str
    unit_registry_version: str

    def __post_init__(self) -> None:
        value = exact_decimal(self.value)
        if value < 0:
            raise QuantityValidationError("Quantity cannot be negative.")
        if not self.unit or self.unit.strip() != self.unit:
            raise QuantityValidationError("A canonical unit code is required.")
        if (
            not self.unit_registry_version
            or self.unit_registry_version.strip() != self.unit_registry_version
        ):
            raise QuantityValidationError("A unit registry version is required.")
        object.__setattr__(self, "value", value)


@dataclass(frozen=True, slots=True)
class UnitDefinition:
    code: str
    dimension: str
    to_base_factor: Decimal

    def __post_init__(self) -> None:
        factor = exact_decimal(self.to_base_factor)
        if not self.code or not self.dimension:
            raise QuantityValidationError("Unit code and dimension are required.")
        if factor <= 0:
            raise QuantityValidationError("Unit conversion factor must be positive.")
        object.__setattr__(self, "to_base_factor", factor)


@dataclass(frozen=True, slots=True)
class UnitRegistry:
    """An immutable, explicitly versioned unit catalog supplied by an implementation."""

    version: str
    units: Mapping[str, UnitDefinition]

    def __post_init__(self) -> None:
        if not self.version:
            raise QuantityValidationError("Unit registry version is required.")
        copied = dict(self.units)
        if any(code != definition.code for code, definition in copied.items()):
            raise QuantityValidationError("Registry keys must match unit codes.")
        object.__setattr__(self, "units", MappingProxyType(copied))

    def validate(self, quantity: Quantity) -> None:
        if quantity.unit_registry_version != self.version:
            raise QuantityValidationError("Quantity references a different unit registry version.")
        if quantity.unit not in self.units:
            raise QuantityValidationError(f"Unknown unit code: {quantity.unit}.")

    def convert(self, quantity: Quantity, target_unit: str) -> Quantity:
        self.validate(quantity)
        source = self.units[quantity.unit]
        target = self.units.get(target_unit)
        if target is None:
            raise QuantityValidationError(f"Unknown target unit code: {target_unit}.")
        if source.dimension != target.dimension:
            raise QuantityValidationError("Incompatible unit dimensions cannot be converted.")
        ratio = (
            Fraction(quantity.value)
            * Fraction(source.to_base_factor)
            / Fraction(target.to_base_factor)
        )
        return Quantity(
            value=_fraction_to_decimal(ratio),
            unit=target.code,
            unit_registry_version=self.version,
        )
