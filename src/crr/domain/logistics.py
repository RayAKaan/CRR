"""Deterministic logistics feasibility contracts for Phase 3C."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from typing import Any

from crr.domain.errors import DomainError, TenantBoundaryError
from crr.domain.quantity import Quantity, UnitRegistry, exact_decimal


class TransportMode(StrEnum):
    ROAD = "ROAD"
    RAIL = "RAIL"
    SEA = "SEA"
    AIR = "AIR"
    OTHER = "OTHER"


@dataclass(frozen=True, slots=True)
class LogisticsRejection:
    code: str
    object_id: str
    message: str


@dataclass(frozen=True, slots=True)
class LogisticsEvaluation:
    organization_id: str
    source_location_id: str
    destination_location_id: str
    transport_mode: TransportMode
    source_quantity: Quantity
    transport_capacity: Quantity
    distance_km: Decimal
    travel_duration_seconds: int
    start_at: datetime
    arrival_at: datetime
    feasible: bool
    rejections: tuple[LogisticsRejection, ...]
    provenance: dict[str, Any]

    def __post_init__(self) -> None:
        distance = exact_decimal(self.distance_km)
        if not self.organization_id:
            raise DomainError("Logistics organization is required.")
        if not self.source_location_id or not self.destination_location_id:
            raise DomainError("Logistics source and destination locations are required.")
        if distance < 0:
            raise DomainError("Logistics distance cannot be negative.")
        if self.travel_duration_seconds < 0:
            raise DomainError("Logistics travel duration cannot be negative.")
        if self.start_at.tzinfo is None or self.start_at.utcoffset() is None:
            raise DomainError("Logistics start time must include a timezone.")
        if self.arrival_at.tzinfo is None or self.arrival_at.utcoffset() is None:
            raise DomainError("Logistics arrival time must include a timezone.")
        expected_arrival = self.start_at.astimezone(UTC) + timedelta(
            seconds=self.travel_duration_seconds
        )
        if self.arrival_at.astimezone(UTC) != expected_arrival:
            raise DomainError("Logistics arrival time must match the declared travel duration.")
        if self.feasible and self.rejections:
            raise DomainError("A feasible logistics evaluation cannot contain rejections.")
        if not self.feasible and not self.rejections:
            raise DomainError("An infeasible logistics evaluation requires rejection reasons.")
        object.__setattr__(self, "distance_km", distance)
        object.__setattr__(self, "start_at", self.start_at.astimezone(UTC))
        object.__setattr__(self, "arrival_at", self.arrival_at.astimezone(UTC))


def _reject(code: str, object_id: str, message: str) -> LogisticsRejection:
    return LogisticsRejection(code=code, object_id=object_id, message=message)


def evaluate_logistics_leg(
    *,
    organization_id: str,
    source_organization_id: str,
    destination_organization_id: str,
    source_location_id: str,
    destination_location_id: str,
    expected_source_location_id: str,
    expected_destination_location_id: str,
    source_quantity: Quantity,
    transport_capacity: Quantity,
    transport_mode: TransportMode,
    distance_km: Decimal,
    travel_duration_seconds: int,
    start_at: datetime,
    destination_window_start: datetime,
    destination_window_end: datetime,
    unit_registry: UnitRegistry,
    max_distance_km: Decimal | None = None,
) -> LogisticsEvaluation:
    """Evaluate one transport leg without mutation, reservation, or external routing."""
    if source_organization_id != destination_organization_id:
        raise TenantBoundaryError("Logistics endpoints must share an organization.")
    if organization_id != source_organization_id:
        raise TenantBoundaryError("Logistics request belongs to another organization.")
    if start_at.tzinfo is None or start_at.utcoffset() is None:
        raise DomainError("Logistics start time must include a timezone.")
    if destination_window_start.tzinfo is None or destination_window_start.utcoffset() is None:
        raise DomainError("Destination window start must include a timezone.")
    if destination_window_end.tzinfo is None or destination_window_end.utcoffset() is None:
        raise DomainError("Destination window end must include a timezone.")
    if destination_window_start >= destination_window_end:
        raise DomainError("Destination timing window must have start before end.")
    distance = exact_decimal(distance_km)
    max_distance = None if max_distance_km is None else exact_decimal(max_distance_km)
    if distance < 0:
        raise DomainError("Logistics distance cannot be negative.")
    if travel_duration_seconds < 0:
        raise DomainError("Logistics travel duration cannot be negative.")
    if max_distance is not None and max_distance < 0:
        raise DomainError("Maximum logistics distance cannot be negative.")

    start = start_at.astimezone(UTC)
    destination_start = destination_window_start.astimezone(UTC)
    destination_end = destination_window_end.astimezone(UTC)
    arrival = start + timedelta(seconds=travel_duration_seconds)
    rejections: list[LogisticsRejection] = []

    if source_location_id != expected_source_location_id:
        rejections.append(
            _reject(
                "LOCATION_INFEASIBLE",
                source_location_id,
                "Source location does not match the authoritative route endpoint.",
            )
        )
    if destination_location_id != expected_destination_location_id:
        rejections.append(
            _reject(
                "LOCATION_INFEASIBLE",
                destination_location_id,
                "Destination location does not match the authoritative route endpoint.",
            )
        )
    if source_quantity.value <= 0:
        rejections.append(
            _reject("INSUFFICIENT_QUANTITY", source_location_id, "Zero quantity is not routing supply.")
        )
    if max_distance is not None and distance > max_distance:
        rejections.append(
            _reject(
                "LOCATION_INFEASIBLE",
                destination_location_id,
                "Declared logistics distance exceeds the permitted maximum.",
            )
        )
    if arrival < destination_start or arrival > destination_end:
        rejections.append(
            _reject(
                "TIME_WINDOW_CONFLICT",
                destination_location_id,
                "Transport arrival does not fit the destination timing window.",
            )
        )

    try:
        capacity = unit_registry.convert(source_quantity, transport_capacity.unit)
    except DomainError as exc:
        rejections.append(_reject("UNIT_INCOMPATIBLE", source_location_id, str(exc)))
    else:
        if capacity.value > transport_capacity.value:
            rejections.append(
                _reject(
                    "CAPACITY_INSUFFICIENT",
                    destination_location_id,
                    "Transport payload exceeds declared transport capacity.",
                )
            )

    feasible = not rejections
    return LogisticsEvaluation(
        organization_id=organization_id,
        source_location_id=source_location_id,
        destination_location_id=destination_location_id,
        transport_mode=transport_mode,
        source_quantity=source_quantity,
        transport_capacity=transport_capacity,
        distance_km=distance,
        travel_duration_seconds=travel_duration_seconds,
        start_at=start,
        arrival_at=arrival,
        feasible=feasible,
        rejections=tuple(rejections),
        provenance={
            "source": "CRR_DETERMINISTIC_LOGISTICS",
            "unit_registry_version": unit_registry.version,
        },
    )
